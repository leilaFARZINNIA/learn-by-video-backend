from fastapi import APIRouter, HTTPException
from typing import List
from db.mongo import db
from models.media import Media

router = APIRouter()

def clean_mongo_id(obj):
    obj.pop('_id', None)
    return obj

@router.get("/medias", response_model=List[Media])
async def get_medias():
    medias = []
    async for media in db.medias.find():
        medias.append(Media(**clean_mongo_id(media)))
    return medias

@router.post("/medias", response_model=Media)
async def create_media(media: Media):
    await db.medias.insert_one(media.dict())
    return media

@router.get("/courses/{course_id}/medias", response_model=List[Media])
async def get_medias_by_course(course_id: str):
    medias = []
    async for media in db.medias.find({"course_id": course_id}):
        medias.append(Media(**clean_mongo_id(media)))
    return medias

@router.get("/medias/{media_id}", response_model=Media)
async def get_media_by_id(media_id: str):
    media = await db.medias.find_one({"media_id": media_id})
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return Media(**clean_mongo_id(media))
