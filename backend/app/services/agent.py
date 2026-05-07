"""Tool-using LLM agent. The model is grounded entirely in tool outputs —
the system prompt forbids inventing prices, stock, or specs."""

from anthropic import AsyncAnthropic
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
- Use the same language the customer used."""


_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic | None:
    global _client
    if not settings.ANTHROPIC_API_KEY:
        return None
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
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
            "reply": "(LLM not configured — set ANTHROPIC_API_KEY)",
            "flags": {},
            "tool_calls": [],
        }

    rag_hits = rag_hits or []
    ctx: dict = {}
    tool_calls: list[dict] = []

    context_blocks: list[str] = []
    if summary:
        context_blocks.append(f"Customer summary:\n{summary}")
    if rag_hits:
        joined = "\n".join(f"- {h}" for h in rag_hits)
        context_blocks.append(f"Relevant past messages:\n{joined}")

    messages: list[dict] = []
    if context_blocks:
        messages.append({"role": "user", "content": f"[CONTEXT]\n\n" + "\n\n".join(context_blocks)})
        messages.append({"role": "assistant", "content": "Got it."})
    for m in history:
        messages.append({
            "role": "user" if m["direction"] == "in" else "assistant",
            "content": m["body"],
        })
    messages.append({"role": "user", "content": user_text})

    final_text = ""
    for _ in range(5):  # cap tool-use rounds to prevent loops
        res = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=600,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        if res.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": [b.model_dump() for b in res.content]})
            tool_results = []
            for block in res.content:
                if block.type != "tool_use":
                    continue
                result = await execute_tool(db, block.name, block.input, ctx)
                tool_calls.append({"name": block.name, "input": block.input, "result": result})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })
            messages.append({"role": "user", "content": tool_results})
            continue

        final_text = "\n".join(b.text for b in res.content if b.type == "text").strip()
        break

    return {"reply": final_text, "flags": ctx, "tool_calls": tool_calls}
