from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_auth
from app.db.session import get_db
from app.models.marketing import Broadcast

router = APIRouter()


@router.get("")
async def list_broadcasts(db: AsyncSession = Depends(get_db), _: dict = Depends(require_auth())):
    res = await db.execute(select(Broadcast).order_by(Broadcast.scheduled_at.desc()))
    return list(res.scalars().all())


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_broadcast(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner", "staff"])),
):
    b = Broadcast(**body)
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return b


@router.delete("/{broadcast_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_broadcast(
    broadcast_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_auth(["owner"])),
):
    b = await db.get(Broadcast, broadcast_id)
    if not b:
        raise HTTPException(404, "not found")
    await db.delete(b)
    await db.commit()
