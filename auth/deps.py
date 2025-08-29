# auth/deps.py
import os, uuid
from fastapi import Depends, HTTPException, Header, Request
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres import get_db
from models.user import UserORM
from dotenv import load_dotenv

load_dotenv()

SESSION_SECRET = os.getenv("SESSION_SECRET", "change-me")
COOKIE_NAME    = os.getenv("SESSION_COOKIE_NAME", "sid") 

async def current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> UserORM:
    token: str | None = None

   
    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()


    if not token:
        token = request.cookies.get(COOKIE_NAME)

    if not token:
        raise HTTPException(401, "No session")

    try:
        payload = jwt.decode(token, SESSION_SECRET, algorithms=["HS256"])
        uid_str = payload.get("uid")
        if not uid_str:
            raise HTTPException(401, "Bad session")
        uid = uuid.UUID(uid_str)
    except (JWTError, ValueError):
        raise HTTPException(401, "Bad session")

    user = await db.get(UserORM, uid)
    if not user:
        raise HTTPException(401, "User not found")
    return user
