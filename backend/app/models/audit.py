from datetime import datetime
from sqlalchemy import DateTime, Index, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models._mixins import cuid_pk


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id:         Mapped[str] = mapped_column(String, primary_key=True, default=cuid_pk)
    actor_id:   Mapped[str | None] = mapped_column(String, nullable=True)
    action:     Mapped[str] = mapped_column(String)
    entity:     Mapped[str] = mapped_column(String)
    entity_id:  Mapped[str | None] = mapped_column(String, nullable=True)
    payload:    Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_audit_entity", "entity", "entity_id"),)
