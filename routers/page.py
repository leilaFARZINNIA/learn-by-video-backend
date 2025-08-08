from fastapi import APIRouter
from typing import List
from db.mongo import db 
from models.page import Page 

router = APIRouter()

def clean_mongo_id(obj):
    obj.pop('_id', None)
    return obj

@router.get("/pages", response_model=List[Page])
async def get_pages():
    pages = []
    async for page in db.pages.find():
        pages.append(Page(**clean_mongo_id(page)))
    return pages

@router.post("/pages", response_model=Page)
async def create_page(page: Page):
    await db.pages.insert_one(page.dict())
    return page
