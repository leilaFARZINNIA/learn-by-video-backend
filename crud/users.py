# crud/users.py
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from models.user import UserORM

# ----------------------------
#  Queries (help functions)
# ----------------------------

async def get_user_by_sub(db: AsyncSession, sub: str) -> Optional[UserORM]:
    """Find user by Firebase UID (stored in UserORM.sub)."""
    res = await db.execute(select(UserORM).where(UserORM.sub == sub))
    return res.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserORM]:
    """Case-insensitive email lookup."""
    email_norm = email.lower()
    res = await db.execute(
        select(UserORM).where(func.lower(UserORM.email) == email_norm)
    )
    return res.scalar_one_or_none()

async def is_username_taken(db: AsyncSession, username: str) -> bool:
    """Case-insensitive username existence check."""
    uname = username.lower()
    res = await db.execute(
        select(UserORM.id).where(func.lower(UserORM.username) == uname)
    )
    return res.scalar_one_or_none() is not None

# ----------------------------
#  Upsert from Identity (Firebase)
# ----------------------------

async def upsert_user_from_identity(
    db: AsyncSession,
    *,
    uid: str,                   
    email: Optional[str] = None,
    name: Optional[str] = None,
    avatar: Optional[str] = None,
) -> UserORM:

    email_norm = email.lower() if email else None

   
    u = await get_user_by_sub(db, uid)
    if u:
        changed = False
        if email_norm and u.email != email_norm:
            u.email = email_norm; changed = True
        if name is not None and getattr(u, "name", None) != name:
            u.name = name; changed = True
        if avatar is not None and getattr(u, "avatar", None) != avatar:
            u.avatar = avatar; changed = True
        if changed:
            await db.commit()
            await db.refresh(u)
        return u

    
    if email_norm:
        u = await get_user_by_email(db, email_norm)
        if u:
            changed = False
            if u.sub != uid:
                u.sub = uid; changed = True
            if name is not None and getattr(u, "name", None) != name:
                u.name = name; changed = True
            if avatar is not None and getattr(u, "avatar", None) != avatar:
                u.avatar = avatar; changed = True
            if changed:
                try:
                    await db.commit()
                    await db.refresh(u)
                except IntegrityError:
                    # احتمالاً همزمان ردیفی با همین UID ساخته شده
                    await db.rollback()
                    existing = await get_user_by_sub(db, uid)
                    if existing:
                        return existing
                    raise
            return u


    u = UserORM(sub=uid, email=email_norm, name=name, avatar=avatar)
    db.add(u)
    try:
        await db.commit()
        await db.refresh(u)
        return u
    except IntegrityError:
   
        await db.rollback()
        existing = await get_user_by_sub(db, uid)
        if existing:
            return existing
        if email_norm:
            existing = await get_user_by_email(db, email_norm)
            if existing:
                if existing.sub != uid:
                    existing.sub = uid
                    try:
                        await db.commit()
                        await db.refresh(existing)
                    except IntegrityError:
                        await db.rollback()
                return existing
        raise

# ----------------------------
#  Profile updates
# ----------------------------

async def update_username(
    db: AsyncSession,
    *,
    uid: str,
    new_username: str,
) -> UserORM:
 
    uname = new_username.strip().lower()
 
    if await is_username_taken(db, uname):
        raise ValueError("USERNAME_TAKEN")

    u = await get_user_by_sub(db, uid)
    if not u:
        raise ValueError("USER_NOT_FOUND")

    if u.username == uname:
        return u

    u.username = uname
    try:
        await db.commit()
        await db.refresh(u)
        return u
    except IntegrityError:
        await db.rollback()
    
        raise

async def update_profile_fields(
    db: AsyncSession,
    *,
    uid: str,
    name: Optional[str] = None,
    avatar: Optional[str] = None,
) -> UserORM:

    u = await get_user_by_sub(db, uid)
    if not u:
        raise ValueError("USER_NOT_FOUND")

    changed = False
    if name is not None and getattr(u, "name", None) != name:
        u.name = name; changed = True
    if avatar is not None and getattr(u, "avatar", None) != avatar:
        u.avatar = avatar; changed = True

    if changed:
        await db.commit()
        await db.refresh(u)
    return u
