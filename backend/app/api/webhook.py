"""WhatsApp Cloud API webhook — Meta verification (GET) + inbound (POST)."""

import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.chat import MessageDirection, MessageSender
from app.services.conversation import (
    append_message,
    get_or_create_active_conversation,
    get_or_create_customer,
)
from app.services.whatsapp import verify_signature

router = APIRouter()


@router.get("/whatsapp")
async def verify(request: Request):
    """Meta verification handshake — must echo hub.challenge."""
    qp = request.query_params
    if (
        qp.get("hub.mode") == "subscribe"
        and qp.get("hub.verify_token") == settings.WHATSAPP_VERIFY_TOKEN
    ):
        return Response(content=qp.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(403, "verification failed")


@router.post("/whatsapp")
async def inbound(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
):
    raw = await request.body()
    if not verify_signature(raw, x_hub_signature_256):
        raise HTTPException(401, "bad signature")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise HTTPException(400, "bad json") from e

    try:
        entry = (payload.get("entry") or [{}])[0]
        change = (entry.get("changes") or [{}])[0].get("value", {})
        for msg in change.get("messages") or []:
            from_phone = msg.get("from")
            text = (msg.get("text") or {}).get("body", "")
            if not from_phone or not text:
                continue
            customer = await get_or_create_customer(db, from_phone)
            convo, _ = await get_or_create_active_conversation(db, customer.id)
            await append_message(
                db,
                conversation_id=convo.id,
                direction=MessageDirection.in_,
                sender=MessageSender.customer,
                body=text,
            )
            # Hand off to n8n (or call /api/ai/turn) — wired in Phase 3.
    except Exception as e:
        logger.error(f"webhook process error: {e}")

    return {"ok": True}
