import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, Integer, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models._mixins import cuid_pk


class DiscountType(str, enum.Enum):
    percent = "percent"
    flat = "flat"


class Discount(Base):
    __tablename__ = "discounts"

    id:         Mapped[str] = mapped_column(String, primary_key=True, default=cuid_pk)
    code:       Mapped[str] = mapped_column(String, unique=True, index=True)
    type:       Mapped[DiscountType] = mapped_column(Enum(DiscountType))
    value:      Mapped[Decimal] = mapped_column(Numeric(12, 2))
    applies_to: Mapped[dict] = mapped_column(JSON, default=dict)
    starts_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True))
    max_uses:   Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active:  Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id:              Mapped[str] = mapped_column(String, primary_key=True, default=cuid_pk)
    title:           Mapped[str] = mapped_column(String)
    audience_filter: Mapped[dict] = mapped_column(JSON, default=dict)
    template_name:   Mapped[str] = mapped_column(String)
    scheduled_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sent_count:      Mapped[int] = mapped_column(Integer, default=0)
    status:          Mapped[str] = mapped_column(String, default="scheduled")
    created_at:      Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
