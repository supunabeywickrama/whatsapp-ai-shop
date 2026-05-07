from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_auth
from app.db.session import get_db
from app.models.marketing import Discount

router = APIRouter()


@router.get("")
async def list_discounts(db: AsyncSession = Depends(get_db), _: dict = Depends(require_auth())):
    res = await db.execute(select(Discount).order_by(Discount.created_at.desc()))
    return list(res.scalars().all())


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_discount(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner", "staff"])),
):
    d = Discount(**body)
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return d


@router.put("/{discount_id}")
async def update_discount(
    discount_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner", "staff"])),
):
    d = await db.get(Discount, discount_id)
    if not d:
        raise HTTPException(404, "not found")
    for k, v in body.items():
        setattr(d, k, v)
    await db.commit()
    await db.refresh(d)
    return d


@router.delete("/{discount_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discount(
    discount_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner"])),
):
    d = await db.get(Discount, discount_id)
    if not d:
        raise HTTPException(404, "not found")
    await db.delete(d)
    await db.commit()
