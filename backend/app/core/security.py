from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(*, sub: str, role: str, email: str, hours: int = 8) -> str:
    expire = datetime.now(tz=timezone.utc) + timedelta(hours=hours)
    payload = {"sub": sub, "role": role, "email": email, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token") from e


def require_auth(roles: Optional[Iterable[str]] = None):
    allowed = set(roles) if roles else None

    async def _dep(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer)) -> dict:
        if not creds:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing token")
        claims = decode_token(creds.credentials)
        if allowed and claims.get("role") not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "forbidden")
        return claims

    return _dep
