"""Lightweight intent classifier — uses gpt-4o-mini as a cheap pre-filter.

Returns one of: greeting, product_inquiry, price_check, stock_check,
                complaint, human_request, goodbye, spam, other
"""
from openai import AsyncOpenAI
from app.core.config import settings

LABELS = [
    "greeting", "product_inquiry", "price_check", "stock_check",
    "complaint", "human_request", "goodbye", "spam", "other",
]

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    global _client
    if not settings.OPENAI_API_KEY:
        return None
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


SYSTEM = (
    "You are a strict intent classifier for a mobile-phone-shop WhatsApp bot.\n"
    f"Return ONLY one label (lowercase, no punctuation) from: {', '.join(LABELS)}\n"
    "Rules:\n"
    "- greeting      = hi / hello / hey\n"
    "- goodbye       = thanks / bye / ok that's all / no more\n"
    "- human_request = 'talk to a person', 'agent', 'human'\n"
    "- complaint     = unhappy, broken, refund, return\n"
    "- spam          = scam links, repeated identical messages\n"
    "- price_check   = asks 'how much'\n"
    "- stock_check   = asks 'do you have'\n"
    "- product_inquiry = anything else about products\n"
    "- other         = none of the above"
)


async def classify(text: str) -> dict:
    client = _get_client()
    if client is None:
        return {"label": "other", "confidence": 0.0}

    res = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=10,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user",   "content": text},
        ],
    )
    raw = (res.choices[0].message.content or "").strip().lower()
    label = raw if raw in LABELS else "other"
    return {"label": label, "confidence": 0.4 if label == "other" else 0.9}
