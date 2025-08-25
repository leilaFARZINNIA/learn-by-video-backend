# routes/course_routes.py

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.postgres import get_db
from models.course import Course, CourseORM
from models.media import Media, MediaORM

router = APIRouter()

# --- List/Create Courses ---

@router.get("/courses", response_model=List[Course])
async def get_courses(
    course_type: Optional[str] = Query(None, alias="type"),  # /courses?type=video
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CourseORM)
    if course_type:
        stmt = stmt.where(CourseORM.course_type == course_type)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [Course.model_validate(r.__dict__) for r in rows]

@router.post("/courses", response_model=Course)
async def create_course(course: Course, db: AsyncSession = Depends(get_db)):
    exists = await db.execute(select(CourseORM).where(CourseORM.course_id == course.course_id))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="course_id already exists")
    row = CourseORM(**course.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return Course.model_validate(row.__dict__)

# --- Medias by Course ---

@router.get("/courses/{course_id}/medias", response_model=List[Media])
async def get_medias_by_course(course_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MediaORM).where(MediaORM.course_id == course_id))
    medias = result.scalars().all()
    if not medias:
        raise HTTPException(status_code=404, detail=f"No medias found for course_id '{course_id}'")
    return [Media.model_validate(m.__dict__) for m in medias]
