# routers/auth_local.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.hash import argon2
from jose import jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

from db.postgres import get_db
from models.user import UserORM
from auth.cookies import set_session_cookie, clear_session_cookie

load_dotenv()
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-me")
SESSION_DAYS   = int(os.getenv("SESSION_MAX_AGE_DAYS", "7"))

router = APIRouter(prefix="/auth/local", tags=["auth-local"])

class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("password")
    @classmethod
    def strong(cls, v: str):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return v

class LoginIn(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v

def _issue_session_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=SESSION_DAYS)
    payload = {
        "uid": user_id,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, SESSION_SECRET, algorithm="HS256")

def _user_payload(u: UserORM) -> dict:
    return {
        "uid": str(u.user_id),
        "email": u.email,
        "name": u.name,
        "avatar": u.avatar,
        "has_password": bool(u.password_hash),
        "provider": "google" if u.google_sub else "local",
    }

@router.post("/register")
async def register(body: RegisterIn, db: AsyncSession = Depends(get_db)):
    exists = (await db.execute(
        select(UserORM).where(UserORM.email == body.email)
    )).scalar_one_or_none()
    if exists:
        raise HTTPException(409, "Email already exists. Please sign in.")

    user = UserORM(
        email=body.email,
        name=body.name,
        password_hash=argon2.hash(body.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = _issue_session_token(str(user.user_id))
    res = JSONResponse({"ok": True, "user": _user_payload(user)})
    set_session_cookie(res, token, days=SESSION_DAYS)
    return res

@router.post("/login")
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(
        select(UserORM).where(UserORM.email == body.email)
    )).scalar_one_or_none()

    if not user or not user.password_hash or not argon2.verify(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")

    token = _issue_session_token(str(user.user_id))
    res = JSONResponse({"ok": True, "user": _user_payload(user)})
    set_session_cookie(res, token, days=SESSION_DAYS)
    return res

@router.post("/logout")
async def logout_local():
    res = JSONResponse({"ok": True})
    clear_session_cookie(res)
    return res
