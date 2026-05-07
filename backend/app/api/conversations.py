from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import require_auth
from app.db.session import get_db
from app.models.chat import Conversation, ConversationStatus, MessageDirection, MessageSender
from app.services.conversation import (
    append_message,
    close_conversation,
    flag_awaiting_human,
)
from app.services.whatsapp import send_text

router = APIRouter()


@router.get("")
async def list_conversations(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth()),
):
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.customer), selectinload(Conversation.messages))
        .order_by(Conversation.started_at.desc())
        .limit(100)
    )
    if status:
        stmt = stmt.where(Conversation.status == ConversationStatus(status))
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth()),
):
    res = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.customer), selectinload(Conversation.messages))
    )
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "not found")
    return c


@router.post("/{conversation_id}/takeover")
async def takeover(
    conversation_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner", "staff"])),
):
    res = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.customer))
    )
    convo = res.scalar_one_or_none()
    if not convo:
        raise HTTPException(404, "not found")

    await flag_awaiting_human(db, convo.id)
    text = (body.get("text") or "").strip()
    if text:
        await send_text(convo.customer.phone, text)
        await append_message(
            db,
            conversation_id=convo.id,
            direction=MessageDirection.out,
            sender=MessageSender.agent,
            body=text,
        )
    return {"ok": True}


@router.post("/{conversation_id}/close")
async def close(
    conversation_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner", "staff"])),
):
    await close_conversation(db, conversation_id, body.get("reason", "manual"))
    return {"ok": True}
