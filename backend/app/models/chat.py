import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models._mixins import cuid_pk


class ConversationStatus(str, enum.Enum):
    active = "active"
    awaiting_human = "awaiting_human"
    closed = "closed"


class MessageDirection(str, enum.Enum):
    in_ = "in"
    out = "out"


class MessageSender(str, enum.Enum):
    customer = "customer"
    ai = "ai"
    agent = "agent"
    system = "system"


class Customer(Base):
    __tablename__ = "customers"

    id:                Mapped[str] = mapped_column(String, primary_key=True, default=cuid_pk)
    phone:             Mapped[str] = mapped_column(String, unique=True, index=True)
    name:              Mapped[str | None] = mapped_column(String, nullable=True)
    locale:            Mapped[str] = mapped_column(String, default="en")
    opt_in_marketing:  Mapped[bool] = mapped_column(Boolean, default=False)
    tags:              Mapped[list] = mapped_column(JSON, default=list)
    summary:           Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_at:      Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:        Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversations: Mapped[list["Conversation"]] = relationship(back_populates="customer")


class Conversation(Base):
    __tablename__ = "conversations"

    id:               Mapped[str] = mapped_column(String, primary_key=True, default=cuid_pk)
    customer_id:      Mapped[str] = mapped_column(String, ForeignKey("customers.id"))
    status:           Mapped[ConversationStatus] = mapped_column(Enum(ConversationStatus), default=ConversationStatus.active)
    category_context: Mapped[str | None] = mapped_column(String, nullable=True)
    assigned_agent:   Mapped[str | None] = mapped_column(String, nullable=True)
    chat_token_hash:  Mapped[str] = mapped_column(String, unique=True, index=True)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at:       Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at:        Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    close_reason:     Mapped[str | None] = mapped_column(String, nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", order_by="Message.created_at")

    __table_args__ = (Index("ix_conv_customer_status", "customer_id", "status"),)


class Message(Base):
    __tablename__ = "messages"

    id:              Mapped[str] = mapped_column(String, primary_key=True, default=cuid_pk)
    conversation_id: Mapped[str] = mapped_column(String, ForeignKey("conversations.id"))
    direction:       Mapped[MessageDirection] = mapped_column(Enum(MessageDirection, name="message_direction"))
    sender:          Mapped[MessageSender] = mapped_column(Enum(MessageSender, name="message_sender"))
    body:            Mapped[str] = mapped_column(Text)
    media_url:       Mapped[str | None] = mapped_column(String, nullable=True)
    intent_label:    Mapped[str | None] = mapped_column(String, nullable=True)
    confidence:      Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at:      Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[Conversation] = relationship(back_populates="messages")

    __table_args__ = (Index("ix_msg_conv_created", "conversation_id", "created_at"),)
