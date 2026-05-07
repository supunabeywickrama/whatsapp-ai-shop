import hashlib
import hmac
from typing import Optional

import httpx
from loguru import logger

from app.core.config import settings


def verify_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    if not settings.WHATSAPP_APP_SECRET or not signature_header:
        return False
    expected = "sha256=" + hmac.new(
        settings.WHATSAPP_APP_SECRET.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def _api_base() -> str:
    return f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


async def send_text(to: str, body: str) -> dict:
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(_api_base(), headers=_headers(), json=payload)
    if r.status_code >= 400:
        logger.error(f"WhatsApp send failed {r.status_code}: {r.text}")
        r.raise_for_status()
    return r.json()


async def send_template(to: str, template_name: str, language_code: str = "en", components: list | None = None) -> dict:
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
            "components": components or [],
        },
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(_api_base(), headers=_headers(), json=payload)
    if r.status_code >= 400:
        logger.error(f"WhatsApp template send failed {r.status_code}: {r.text}")
        r.raise_for_status()
    return r.json()
