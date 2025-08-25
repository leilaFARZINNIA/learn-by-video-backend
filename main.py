from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.course import router as course_router
from routers.media import router as media_router
from db.postgres import engine, Base  

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(course_router)
app.include_router(media_router)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
