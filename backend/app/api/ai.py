"""Internal endpoint that n8n calls (with the server-side chat token) to run
one AI turn against an active conversation."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.redis import redis_client
from app.db.session import get_db
from app.models.chat import Conversation, ConversationStatus, MessageDirection, MessageSender
from app.services.agent import run_agent
from app.services.conversation import (
    append_message,
    close_conversation,
    flag_awaiting_human,
    get_recent_messages,
)
from app.services.intent import classify
from app.services.whatsapp import send_text

router = APIRouter()


class TurnIn(BaseModel):
    conversation_id: str
    text: str
    chat_token: str


@router.post("/turn")
async def run_turn(payload: TurnIn, db: AsyncSession = Depends(get_db)):
    stored = await redis_client.get(f"chat:token:{payload.conversation_id}")
    if not stored or stored != payload.chat_token:
        raise HTTPException(401, "bad token")

    res = await db.execute(
        select(Conversation)
        .where(Conversation.id == payload.conversation_id)
        .options(selectinload(Conversation.customer))
    )
    convo = res.scalar_one_or_none()
    if not convo or convo.status == ConversationStatus.closed:
        raise HTTPException(409, "conversation not active")

    intent = await classify(payload.text)

    if intent["label"] in ("human_request", "complaint"):
        await flag_awaiting_human(db, convo.id)
        reply = "Thanks — I'm connecting you with a team member. They'll reply shortly."
        await send_text(convo.customer.phone, reply)
        await append_message(
            db,
            conversation_id=convo.id,
            direction=MessageDirection.out,
            sender=MessageSender.system,
            body=reply,
            intent_label=intent["label"],
            confidence=intent["confidence"],
        )
        return {"action": "handoff", "intent": intent}

    if intent["label"] == "goodbye":
        reply = "Thanks for chatting! Reply anytime — we're happy to help."
        await send_text(convo.customer.phone, reply)
        await append_message(
            db,
            conversation_id=convo.id,
            direction=MessageDirection.out,
            sender=MessageSender.system,
            body=reply,
            intent_label="goodbye",
            confidence=intent["confidence"],
        )
        await close_conversation(db, convo.id, "goodbye")
        return {"action": "closed", "intent": intent}

    history_rows = await get_recent_messages(db, convo.id, limit=10)
    history = [{"direction": m.direction.value, "body": m.body} for m in history_rows]

    result = await run_agent(
        db,
        user_text=payload.text,
        history=history,
        summary=convo.customer.summary or "",
        rag_hits=[],  # wired in Phase 4 (Qdrant)
    )

    if result["flags"].get("handoff"):
        await flag_awaiting_human(db, convo.id)

    if result["reply"]:
        await send_text(convo.customer.phone, result["reply"])
        await append_message(
            db,
            conversation_id=convo.id,
            direction=MessageDirection.out,
            sender=MessageSender.ai,
            body=result["reply"],
            intent_label=intent["label"],
            confidence=intent["confidence"],
        )

    if result["flags"].get("end"):
        await close_conversation(db, convo.id, result["flags"]["end"])

    return {
        "action": "replied",
        "intent": intent,
        "tool_calls": result["tool_calls"],
        "flags": result["flags"],
    }
