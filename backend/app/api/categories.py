from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_auth
from app.db.session import get_db
from app.models.catalog import Category
from app.schemas.catalog import CategoryIn, CategoryOut

router = APIRouter()


@router.get("", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Category).order_by(Category.sort_order))
    return list(res.scalars().all())


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryIn,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner", "staff"])),
):
    c = Category(**payload.model_dump())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: str,
    payload: CategoryIn,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner", "staff"])),
):
    c = await db.get(Category, category_id)
    if not c:
        raise HTTPException(404, "not found")
    for k, v in payload.model_dump().items():
        setattr(c, k, v)
    await db.commit()
    await db.refresh(c)
    return c


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner"])),
):
    c = await db.get(Category, category_id)
    if not c:
        raise HTTPException(404, "not found")
    await db.delete(c)
    await db.commit()
