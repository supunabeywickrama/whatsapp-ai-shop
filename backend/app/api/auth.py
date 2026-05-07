from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.admin import AdminUser
from app.schemas.auth import LoginIn, TokenOut

router = APIRouter()


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AdminUser).where(AdminUser.email == payload.email))
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    token = create_access_token(sub=user.id, role=user.role.value, email=user.email)
    return TokenOut(
        token=token,
        user={"id": user.id, "email": user.email, "role": user.role.value, "name": user.name},
    )
