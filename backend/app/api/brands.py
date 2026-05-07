from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_auth
from app.db.session import get_db
from app.models.catalog import Brand
from app.schemas.catalog import BrandIn, BrandOut

router = APIRouter()


@router.get("", response_model=list[BrandOut])
async def list_brands(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Brand).order_by(Brand.name))
    return list(res.scalars().all())


@router.post("", response_model=BrandOut, status_code=status.HTTP_201_CREATED)
async def create_brand(
    payload: BrandIn,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner", "staff"])),
):
    b = Brand(**payload.model_dump())
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return b


@router.put("/{brand_id}", response_model=BrandOut)
async def update_brand(
    brand_id: str,
    payload: BrandIn,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner", "staff"])),
):
    b = await db.get(Brand, brand_id)
    if not b:
        raise HTTPException(404, "not found")
    for k, v in payload.model_dump().items():
        setattr(b, k, v)
    await db.commit()
    await db.refresh(b)
    return b


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner"])),
):
    b = await db.get(Brand, brand_id)
    if not b:
        raise HTTPException(404, "not found")
    await db.delete(b)
    await db.commit()
