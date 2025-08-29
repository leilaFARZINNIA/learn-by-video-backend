# crud/users.py
from typing import Optional
import sqlalchemy as sa
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from models.user import UserORM

async def get_user_by_google_sub(db: AsyncSession, sub: str) -> Optional[UserORM]:
    res = await db.execute(select(UserORM).where(UserORM.google_sub == sub))
    return res.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserORM]:
    # جست‌وجوی case-insensitive
    email_norm = email.lower()
    res = await db.execute(
        select(UserORM).where(func.lower(UserORM.email) == email_norm)
    )
    return res.scalar_one_or_none()

async def upsert_user_google(
    db: AsyncSession, *, google_sub: str, email: Optional[str], name: Optional[str], avatar: Optional[str]
) -> UserORM:
    email_norm = email.lower() if email else None


    u = await get_user_by_google_sub(db, google_sub)
    if u:
        changed = False
        if email_norm and u.email != email_norm:
            u.email = email_norm; changed = True
        if name and u.name != name:
            u.name = name; changed = True
        if avatar and u.avatar != avatar:
            u.avatar = avatar; changed = True
        if changed:
            await db.commit()
            await db.refresh(u)
        return u


    if email_norm:
        u = await get_user_by_email(db, email_norm)
        if u:
            changed = False
            if not u.google_sub:
                u.google_sub = google_sub; changed = True
            if name and u.name != name:
                u.name = name; changed = True
            if avatar and u.avatar != avatar:
                u.avatar = avatar; changed = True
            if changed:
                await db.commit()
                await db.refresh(u)
            return u

   
    u = UserORM(google_sub=google_sub, email=email_norm, name=name, avatar=avatar)
    db.add(u)
    try:
        await db.commit()
        await db.refresh(u)
        return u
    except IntegrityError:
        
        await db.rollback()
       
        u2 = await get_user_by_google_sub(db, google_sub)
        if u2:
            return u2
      
        if email_norm:
            u2 = await get_user_by_email(db, email_norm)
            if u2:
        
                if not u2.google_sub:
                    u2.google_sub = google_sub
                    await db.commit()
                    await db.refresh(u2)
                return u2
       
        raise
