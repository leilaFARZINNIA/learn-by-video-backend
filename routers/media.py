from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.postgres import get_db
from models.media import Media, MediaORM

router = APIRouter()

# --- Get all medias (with simple pagination) ---
@router.get("/medias", response_model=List[Media])
async def get_medias(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    stmt = select(MediaORM).limit(limit).offset(offset)
    result = await db.execute(stmt)
    rows = result.scalars().all()
  
    return [Media.model_validate(r) for r in rows]

# --- Create a new media ---
@router.post("/medias", response_model=Media, status_code=status.HTTP_201_CREATED)
async def create_media(media: Media, db: AsyncSession = Depends(get_db)):
    
    exists = await db.execute(select(MediaORM).where(MediaORM.media_id == media.media_id))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="media_id already exists")

    row = MediaORM(**media.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return Media.model_validate(row)

# --- Get medias by course_id (collection: return [] when empty) ---
@router.get("/courses/{course_id}/medias", response_model=List[Media])
async def get_medias_by_course(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    stmt = select(MediaORM).where(MediaORM.course_id == course_id).limit(limit).offset(offset)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [Media.model_validate(r) for r in rows]

# --- Get media by media_id (item: 404 if not found) ---
@router.get("/medias/{media_id}", response_model=Media)
async def get_media_by_id(media_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MediaORM).where(MediaORM.media_id == media_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=f"Media with id '{media_id}' not found")
    return Media.model_validate(row)
