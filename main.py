from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.page import router as page_router
from routers.course import router as course_router
from routers.media import router as media_router




app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(page_router)
app.include_router(course_router)
app.include_router(media_router)
