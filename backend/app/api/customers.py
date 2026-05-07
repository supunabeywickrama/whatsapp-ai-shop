from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import require_auth
from app.db.session import get_db
from app.models.chat import Customer

router = APIRouter()


@router.get("")
async def list_customers(
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth()),
):
    stmt = select(Customer).order_by(Customer.last_seen_at.desc().nullslast()).limit(200)
    if q:
        stmt = stmt.where(or_(Customer.phone.ilike(f"%{q}%"), Customer.name.ilike(f"%{q}%")))
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [
        {
            "id": c.id, "phone": c.phone, "name": c.name, "tags": c.tags,
            "last_seen_at": c.last_seen_at, "created_at": c.created_at,
        }
        for c in rows
    ]


@router.get("/{customer_id}")
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth()),
):
    res = await db.execute(
        select(Customer)
        .where(Customer.id == customer_id)
        .options(selectinload(Customer.conversations))
    )
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "not found")
    return c


@router.put("/{customer_id}/tags")
async def set_tags(
    customer_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner", "staff"])),
):
    c = await db.get(Customer, customer_id)
    if not c:
        raise HTTPException(404, "not found")
    c.tags = body.get("tags", [])
    await db.commit()
    await db.refresh(c)
    return c
