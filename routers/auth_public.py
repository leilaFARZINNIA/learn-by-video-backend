from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import os

from db.postgres import get_db
from models.user import UserORM

ENV = os.getenv("ENV", "development").lower()

router = APIRouter(prefix="/auth", tags=["auth-public"])

class CheckOut(BaseModel):
    exists: bool
    has_password: bool | None = None
    provider: str | None = None

@router.get("/check", response_model=CheckOut)
async def check(
    response: Response,
    email: EmailStr = Query(...),
    db: AsyncSession = Depends(get_db),
):
    
    email_norm = str(email).lower()

   
    result = await db.execute(
        select(UserORM).where(func.lower(UserORM.email) == email_norm)
    )
    u = result.scalar_one_or_none()


    response.headers["Cache-Control"] = "no-store"

    if not u:
        return {"exists": False}

  
    if ENV == "production":
       
        return {
            "exists": True,
            "has_password": bool(u.password_hash),
            "provider": "google" if u.google_sub else "local",
        }

    
    return {
        "exists": True,
        "has_password": bool(u.password_hash),
        "provider": "google" if u.google_sub else "local",
    }
