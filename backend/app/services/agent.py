"""Tool-using LLM agent (OpenAI function calling).

The model is grounded entirely in tool outputs — the system prompt forbids
inventing prices, stock, or specs.
"""
import json
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.tools.registry import TOOL_SCHEMAS, execute as execute_tool

SYSTEM_PROMPT = """You are the sales assistant for a mobile phone shop.

HARD RULES — NEVER VIOLATE:
- NEVER invent prices, stock numbers, model names, or specs. Only use data
  returned by tool calls. If you don't have a tool result for a fact, do not
  state it.
- If the customer asks about a product, you MUST call search_products before
  replying. Don't pre-empt with a guessed price.
- If the customer asks for something not in inventory, say so honestly and
  offer the closest match from search_products.
- If the customer is unhappy / asks for a person / you cannot answer,
  call start_human_handoff with a brief reason.
- When the customer says goodbye / thanks / "ok" / "no more", call
  end_conversation. Do NOT keep chatting after a clear goodbye.
- Keep replies under 60 words. No markdown — WhatsApp doesn't render it well.
- Reply in the same language the customer used."""

# Convert Anthropic-style tool schemas → OpenAI function schemas
def _to_openai_tools(schemas: list[dict]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": s["name"],
                "description": s["description"],
                "parameters": s.get("input_schema", {"type": "object", "properties": {}}),
            },
        }
        for s in schemas
    ]

OPENAI_TOOLS = _to_openai_tools(TOOL_SCHEMAS)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    global _client
    if not settings.OPENAI_API_KEY:
        return None
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def run_agent(
    db: AsyncSession,
    *,
    user_text: str,
    history: list[dict],
    summary: str = "",
    rag_hits: list[str] | None = None,
) -> dict:
    client = _get_client()
    if client is None:
        return {
            "reply": "(LLM not configured — set OPENAI_API_KEY in .env)",
            "flags": {},
            "tool_calls": [],
        }

    rag_hits = rag_hits or []
    ctx: dict = {}
    tool_calls_log: list[dict] = []

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Inject memory context as an initial assistant-acknowledged block
    context_parts: list[str] = []
    if summary:
        context_parts.append(f"Customer summary:\n{summary}")
    if rag_hits:
        context_parts.append("Relevant past messages:\n" + "\n".join(f"- {h}" for h in rag_hits))
    if context_parts:
        messages.append({"role": "user",      "content": "[CONTEXT]\n\n" + "\n\n".join(context_parts)})
        messages.append({"role": "assistant", "content": "Got it."})

    # Add recent conversation history
    for m in history:
        messages.append({
            "role": "user" if m["direction"] == "in" else "assistant",
            "content": m["body"],
        })
    messages.append({"role": "user", "content": user_text})

    final_text = ""
    for _ in range(5):  # cap tool-use rounds to prevent runaway loops
        res = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            max_tokens=600,
            temperature=0.3,
            tools=OPENAI_TOOLS,
            tool_choice="auto",
            messages=messages,
        )
        choice = res.choices[0]

        if choice.finish_reason == "tool_calls":
            # Append the assistant message with tool_calls
            messages.append(choice.message.model_dump())
            for tc in choice.message.tool_calls or []:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                result = await execute_tool(db, tc.function.name, args, ctx)
                tool_calls_log.append({"name": tc.function.name, "input": args, "result": result})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })
            continue

        final_text = (choice.message.content or "").strip()
        break

    return {"reply": final_text, "flags": ctx, "tool_calls": tool_calls_log}
