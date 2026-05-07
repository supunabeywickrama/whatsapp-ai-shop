from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_auth
from app.db.session import get_db
from app.models.catalog import Brand, Category, Product
from app.schemas.catalog import ProductIn, ProductOut

router = APIRouter()


@router.get("", response_model=list[ProductOut])
async def list_products(
    category_id: str | None = None,
    brand_id: str | None = None,
    q: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Product)
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if brand_id:
        stmt = stmt.where(Product.brand_id == brand_id)
    if is_active is not None:
        stmt = stmt.where(Product.is_active.is_(is_active))
    if q:
        stmt = stmt.where(Product.title.ilike(f"%{q}%"))
    stmt = stmt.limit(200).order_by(Product.created_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductIn,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner", "staff"])),
):
    cat = await db.get(Category, payload.category_id)
    if not cat:
        raise HTTPException(400, "invalid category_id")
    if payload.brand_id:
        br = await db.get(Brand, payload.brand_id)
        if not br:
            raise HTTPException(400, "invalid brand_id")
    p = Product(**payload.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: str,
    payload: ProductIn,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner", "staff"])),
):
    p = await db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "not found")
    for k, v in payload.model_dump().items():
        setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    return p


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner"])),
):
    p = await db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "not found")
    await db.delete(p)
    await db.commit()
