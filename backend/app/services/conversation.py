import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import redis_client
from app.models.chat import (
    Conversation,
    ConversationStatus,
    Customer,
    Message,
    MessageDirection,
    MessageSender,
)

CONV_TTL_SECONDS = 24 * 60 * 60


async def get_or_create_customer(db: AsyncSession, phone: str, name: Optional[str] = None) -> Customer:
    res = await db.execute(select(Customer).where(Customer.phone == phone))
    customer = res.scalar_one_or_none()
    now = datetime.now(tz=timezone.utc)
    if customer:
        customer.last_seen_at = now
        if name:
            customer.name = name
    else:
        customer = Customer(phone=phone, name=name, last_seen_at=now)
        db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


async def get_or_create_active_conversation(db: AsyncSession, customer_id: str) -> tuple[Conversation, Optional[str]]:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(seconds=CONV_TTL_SECONDS)
    res = await db.execute(
        select(Conversation)
        .where(Conversation.customer_id == customer_id)
        .where(Conversation.status == ConversationStatus.active)
        .where(Conversation.started_at >= cutoff)
        .order_by(Conversation.started_at.desc())
    )
    convo = res.scalars().first()
    if convo:
        return convo, None

    token = secrets.token_hex(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    convo = Conversation(
        customer_id=customer_id,
        chat_token_hash=token_hash,
        token_expires_at=datetime.now(tz=timezone.utc) + timedelta(seconds=CONV_TTL_SECONDS),
    )
    db.add(convo)
    await db.commit()
    await db.refresh(convo)

    await redis_client.setex(f"chat:token:{convo.id}", CONV_TTL_SECONDS, token)
    return convo, token


async def append_message(
    db: AsyncSession,
    *,
    conversation_id: str,
    direction: MessageDirection,
    sender: MessageSender,
    body: str,
    intent_label: Optional[str] = None,
    confidence: Optional[float] = None,
) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        direction=direction,
        sender=sender,
        body=body,
        intent_label=intent_label,
        confidence=confidence,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_recent_messages(db: AsyncSession, conversation_id: str, limit: int = 10) -> list[Message]:
    res = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    rows = list(res.scalars().all())
    rows.reverse()
    return rows


async def close_conversation(db: AsyncSession, conversation_id: str, reason: str) -> None:
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(
            status=ConversationStatus.closed,
            closed_at=datetime.now(tz=timezone.utc),
            close_reason=reason,
        )
    )
    await db.commit()


async def flag_awaiting_human(db: AsyncSession, conversation_id: str) -> None:
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(status=ConversationStatus.awaiting_human)
    )
    await db.commit()
