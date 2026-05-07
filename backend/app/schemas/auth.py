from pydantic import BaseModel, EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    token: str
    user: dict
