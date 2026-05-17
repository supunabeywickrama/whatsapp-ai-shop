"""WhatsApp Cloud API webhook — verification (GET) + inbound messages (POST).

Phase 3: After persisting the inbound message, runs the AI turn inline so
the customer gets a real reply. Rate-limited per phone number via Redis.
"""
import asyncio
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.redis import redis_client
from app.db.session import get_db
from app.models.chat import (
    ConversationStatus, MessageDirection, MessageSender,
)
from app.services.conversation import (
    append_message,
    close_conversation,
    flag_awaiting_human,
    get_or_create_active_conversation,
    get_or_create_customer,
    get_recent_messages,
)
from app.services.intent import classify
from app.services.agent import run_agent
from app.services.whatsapp import send_text, verify_signature

router = APIRouter()

RATE_WINDOW = 300   # 5 minutes
RATE_LIMIT   = settings.RATE_LIMIT_MSG_PER_5MIN


@router.get("/whatsapp")
async def verify(request: Request):
    """Meta verification handshake — echoes hub.challenge."""
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

    # Signature check (skip if APP_SECRET not configured yet — dev mode)
    if settings.WHATSAPP_APP_SECRET:
        if not verify_signature(raw, x_hub_signature_256):
            raise HTTPException(401, "bad signature")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise HTTPException(400, "bad json") from e

    # Always 200 fast — Meta retries on any non-200
    asyncio.create_task(_process(payload, db))
    return {"ok": True}


async def _process(payload: dict, db: AsyncSession) -> None:
    try:
        entry  = (payload.get("entry") or [{}])[0]
        change = (entry.get("changes") or [{}])[0].get("value", {})

        for msg in change.get("messages") or []:
            phone = msg.get("from", "")
            text  = (msg.get("text") or {}).get("body", "").strip()
            if not phone or not text:
                continue

            # STOP / UNSUBSCRIBE — WhatsApp policy compliance
            if text.upper() in ("STOP", "UNSUBSCRIBE", "OPT OUT"):
                customer = await get_or_create_customer(db, phone)
                customer.opt_in_marketing = False
                await db.commit()
                await send_text(phone, "You have been unsubscribed. Reply START to re-subscribe.")
                continue

            # Per-phone rate limit
            rate_key = f"rate:{phone}"
            count = await redis_client.incr(rate_key)
            if count == 1:
                await redis_client.expire(rate_key, RATE_WINDOW)
            if count > RATE_LIMIT:
                logger.warning(f"Rate limit hit for {phone}")
                continue

            customer = await get_or_create_customer(db, phone)
            convo, token = await get_or_create_active_conversation(db, customer.id)

            # Skip if already handed off to human
            if convo.status == ConversationStatus.awaiting_human:
                await append_message(
                    db, conversation_id=convo.id,
                    direction=MessageDirection.in_, sender=MessageSender.customer, body=text,
                )
                continue

            await append_message(
                db, conversation_id=convo.id,
                direction=MessageDirection.in_, sender=MessageSender.customer, body=text,
            )

            # ── Intent pre-filter ─────────────────────────────────────
            intent = await classify(text)
            logger.info(f"Intent [{phone}]: {intent['label']} ({intent['confidence']:.2f})")

            if intent["label"] in ("human_request", "complaint"):
                await flag_awaiting_human(db, convo.id)
                reply = "I'm connecting you with a team member. They'll reply shortly."
                await send_text(phone, reply)
                await append_message(
                    db, conversation_id=convo.id,
                    direction=MessageDirection.out, sender=MessageSender.system,
                    body=reply, intent_label=intent["label"], confidence=intent["confidence"],
                )
                continue

            if intent["label"] == "goodbye":
                reply = "Thanks for chatting! Reply anytime — we're happy to help. 👋"
                await send_text(phone, reply)
                await append_message(
                    db, conversation_id=convo.id,
                    direction=MessageDirection.out, sender=MessageSender.system,
                    body=reply, intent_label="goodbye", confidence=intent["confidence"],
                )
                await close_conversation(db, convo.id, "goodbye")
                continue

            if intent["label"] == "greeting":
                reply = "Hi! Welcome to our shop. How can I help you today? 😊"
                await send_text(phone, reply)
                await append_message(
                    db, conversation_id=convo.id,
                    direction=MessageDirection.out, sender=MessageSender.ai,
                    body=reply, intent_label="greeting", confidence=intent["confidence"],
                )
                continue

            # ── LLM Agent turn ────────────────────────────────────────
            history_rows = await get_recent_messages(db, convo.id, limit=10)
            history = [{"direction": m.direction.value, "body": m.body} for m in history_rows]

            result = await run_agent(
                db,
                user_text=text,
                history=history,
                summary=customer.summary or "",
                rag_hits=[],   # Phase 4: Qdrant
            )

            if result["flags"].get("handoff"):
                await flag_awaiting_human(db, convo.id)
                notify = "I'm connecting you with a team member. They'll reply shortly."
                await send_text(phone, notify)
                await append_message(
                    db, conversation_id=convo.id,
                    direction=MessageDirection.out, sender=MessageSender.system,
                    body=notify, intent_label=intent["label"],
                )
                continue

            reply = result["reply"]
            if reply:
                await send_text(phone, reply)
                await append_message(
                    db, conversation_id=convo.id,
                    direction=MessageDirection.out, sender=MessageSender.ai,
                    body=reply, intent_label=intent["label"], confidence=intent["confidence"],
                )

            if result["flags"].get("end"):
                await close_conversation(db, convo.id, result["flags"]["end"])

    except Exception as e:
        logger.error(f"webhook _process error: {e}", exc_info=True)
