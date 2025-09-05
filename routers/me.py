# routers/me.py

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, constr
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from auth.deps import get_identity, Identity
from db.postgres import get_db
from models.user import UserORM

router = APIRouter(tags=["me"])


# ---------- Schemas ----------
class MeOut(BaseModel):
    email: str | None
    username: str | None


class UsernameIn(BaseModel):
   
    username: constr(
        strip_whitespace=True,
        min_length=3,
        max_length=20,
        pattern=r"^[a-z0-9_]+$",
    )


# ---------- Endpoints ----------

@router.get("/me", response_model=MeOut)
async def me(
    idn: Identity = Depends(get_identity),
    db: AsyncSession = Depends(get_db),
):
   
    user = await db.scalar(select(UserORM).where(UserORM.sub == idn.uid))
    if not user:
        user = UserORM(sub=idn.uid, email=idn.email)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return MeOut.model_validate(user, from_attributes=True)


@router.patch("/me/username", status_code=status.HTTP_204_NO_CONTENT)
async def change_username(
    payload: UsernameIn,
    idn: Identity = Depends(get_identity),
    db: AsyncSession = Depends(get_db),
):
 
    uname = payload.username.lower()

  
    taken = await db.scalar(
        select(UserORM.user_id).where(func.lower(UserORM.username) == uname)
    )
    if taken:
        raise HTTPException(status_code=409, detail="Username already taken")

    user = await db.scalar(select(UserORM).where(UserORM.sub == idn.uid))
    if not user:
        
        user = UserORM(sub=idn.uid, email=idn.email)
        db.add(user)
        await db.flush()  

    user.username = uname
    await db.commit()

    # 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)
