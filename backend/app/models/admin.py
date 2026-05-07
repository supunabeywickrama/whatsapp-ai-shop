import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models._mixins import cuid_pk


class AdminRole(str, enum.Enum):
    owner = "owner"
    staff = "staff"
    viewer = "viewer"


class AdminUser(Base):
    __tablename__ = "admin_users"

    id:            Mapped[str] = mapped_column(String, primary_key=True, default=cuid_pk)
    email:         Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    name:          Mapped[str | None] = mapped_column(String, nullable=True)
    role:          Mapped[AdminRole] = mapped_column(Enum(AdminRole), default=AdminRole.staff)
    created_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
