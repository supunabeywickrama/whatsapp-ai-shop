"""Cheap pre-filter intent classifier (Claude Haiku)."""

from anthropic import AsyncAnthropic

from app.core.config import settings

LABELS = [
    "greeting", "product_inquiry", "price_check", "stock_check",
    "complaint", "human_request", "goodbye", "spam", "other",
]

_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic | None:
    global _client
    if not settings.ANTHROPIC_API_KEY:
        return None
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


SYSTEM = (
    "You are a strict intent classifier for a mobile-phone-shop WhatsApp bot.\n"
    f"Return ONLY one label from this list (lowercase, no punctuation):\n{', '.join(LABELS)}\n"
    "Rules:\n"
    "- greeting = hi/hello/hey only\n"
    "- goodbye = thanks/bye/ok-thats-all/no-more\n"
    "- human_request = 'talk to a person', 'agent', 'human'\n"
    "- complaint = unhappy, broken, refund, return\n"
    "- spam = links to scams, repeated identical messages\n"
    "- price_check = asks 'how much'\n"
    "- stock_check = asks 'do you have'\n"
    "- product_inquiry = anything else about products\n"
    "- other = none of the above"
)


async def classify(text: str) -> dict:
    client = _get_client()
    if client is None:
        return {"label": "other", "confidence": 0.0}

    res = await client.messages.create(
        model=settings.ANTHROPIC_CLASSIFIER_MODEL,
        max_tokens=60,
        system=SYSTEM,
        messages=[{"role": "user", "content": text}],
    )
    raw = (res.content[0].text if res.content else "").strip().lower()
    label = raw if raw in LABELS else "other"
    return {"label": label, "confidence": 0.4 if label == "other" else 0.9}
