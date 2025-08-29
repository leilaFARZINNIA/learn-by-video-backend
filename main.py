# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from routers.course import router as course_router
from routers.media import router as media_router
from routers.auth_google import router as google_router
from routers import auth_local
from routers.auth_public import router as public_router

from db.postgres import engine, Base


load_dotenv()


CLIENT_ORIGINS = [
    o.strip() for o in os.getenv(
        "CLIENT_ORIGINS",
        "http://localhost:8081,http://localhost:19006"
    ).split(",") if o.strip()
]


CLIENT_ORIGIN_REGEX = os.getenv(
    "CLIENT_ORIGIN_REGEX",
    r"^https?://(localhost|127\.0\.0\.1|10\.0\.2\.2|192\.168\.\d+\.\d+)(:\d+)?$"
)

app = FastAPI(
    title="Learn By Video API",
    version="1.0.0",
    description="Backend for Learn by Video platform with Google OAuth and Local Auth",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CLIENT_ORIGINS,
    allow_origin_regex=CLIENT_ORIGIN_REGEX,  
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(course_router)
app.include_router(media_router)
app.include_router(google_router)
app.include_router(public_router)
app.include_router(auth_local.router)

@app.on_event("startup")
async def on_startup():
    # CORS 
    print("CORS allow_origins:", CLIENT_ORIGINS)
    print("CORS allow_origin_regex:", CLIENT_ORIGIN_REGEX)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
async def health():
    return {"ok": True}
