from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class CategoryIn(BaseModel):
    name: str
    parent_id: Optional[str] = None
    icon_url: Optional[str] = None
    sort_order: int = 0


class CategoryOut(CategoryIn):
    model_config = ConfigDict(from_attributes=True)
    id: str


class BrandIn(BaseModel):
    name: str
    logo_url: Optional[str] = None


class BrandOut(BrandIn):
    model_config = ConfigDict(from_attributes=True)
    id: str


class ProductIn(BaseModel):
    sku: str
    title: str
    description: Optional[str] = None
    condition: Literal["new", "used", "refurbished"] = "new"
    price: Decimal
    discounted_price: Optional[Decimal] = None
    stock_qty: int = 0
    images: list[str] = Field(default_factory=list)
    specs: dict = Field(default_factory=dict)
    is_active: bool = True
    category_id: str
    brand_id: Optional[str] = None


class ProductOut(ProductIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
