from fastapi import APIRouter
from typing import List
from db.mongo import db
from models.course import Course

router = APIRouter()

def clean_mongo_id(obj):
    obj.pop('_id', None)
    return obj

@router.get("/courses", response_model=List[Course])
async def get_courses():
    courses = []
    async for course in db.courses.find():
        courses.append(Course(**clean_mongo_id(course)))
    return courses

@router.post("/courses", response_model=Course)
async def create_course(course: Course):
    await db.courses.insert_one(course.dict())
    return course
