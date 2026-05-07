import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models._mixins import cuid_pk


class ProductCondition(str, enum.Enum):
    new = "new"
    used = "used"
    refurbished = "refurbished"


class Category(Base):
    __tablename__ = "categories"

    id:         Mapped[str] = mapped_column(String, primary_key=True, default=cuid_pk)
    name:       Mapped[str] = mapped_column(String, unique=True)
    parent_id:  Mapped[str | None] = mapped_column(String, ForeignKey("categories.id"), nullable=True)
    icon_url:   Mapped[str | None] = mapped_column(String, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parent:   Mapped["Category | None"] = relationship("Category", remote_side="Category.id", backref="children")
    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Brand(Base):
    __tablename__ = "brands"

    id:         Mapped[str] = mapped_column(String, primary_key=True, default=cuid_pk)
    name:       Mapped[str] = mapped_column(String, unique=True)
    logo_url:   Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    products: Mapped[list["Product"]] = relationship(back_populates="brand")


class Product(Base):
    __tablename__ = "products"

    id:               Mapped[str] = mapped_column(String, primary_key=True, default=cuid_pk)
    sku:              Mapped[str] = mapped_column(String, unique=True, index=True)
    title:            Mapped[str] = mapped_column(String)
    description:      Mapped[str | None] = mapped_column(Text, nullable=True)
    condition:        Mapped[ProductCondition] = mapped_column(Enum(ProductCondition), default=ProductCondition.new)
    price:            Mapped[Decimal] = mapped_column(Numeric(12, 2))
    discounted_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    stock_qty:        Mapped[int] = mapped_column(Integer, default=0)
    images:           Mapped[list] = mapped_column(JSON, default=list)
    specs:            Mapped[dict] = mapped_column(JSON, default=dict)
    is_active:        Mapped[bool] = mapped_column(Boolean, default=True)

    category_id: Mapped[str] = mapped_column(String, ForeignKey("categories.id"))
    brand_id:    Mapped[str | None] = mapped_column(String, ForeignKey("brands.id"), nullable=True)

    category: Mapped[Category] = relationship(back_populates="products")
    brand:    Mapped[Brand | None] = relationship(back_populates="products")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
