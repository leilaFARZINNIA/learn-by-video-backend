# db/postgres.py
import os
from typing import AsyncGenerator
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

load_dotenv()

# ---- ENV ----
DATABASE_URL      = os.getenv("DATABASE_URL", "postgresql+asyncpg://learn_user:12345@localhost:5432/learn_by_video")
DB_ECHO           = os.getenv("DB_ECHO", "false").lower() == "true"
DB_POOL_SIZE      = int(os.getenv("DB_POOL_SIZE", "5"))          
DB_MAX_OVERFLOW   = int(os.getenv("DB_MAX_OVERFLOW", "10"))      
DB_POOL_RECYCLE_S = int(os.getenv("DB_POOL_RECYCLE_S", "1800"))  
DB_POOL_TIMEOUT_S = int(os.getenv("DB_POOL_TIMEOUT_S", "30"))


CONNECT_ARGS = {}
if os.getenv("DB_DISABLE_STMT_CACHE", "false").lower() == "true":
    CONNECT_ARGS["statement_cache_size"] = 0  # asyncpg

# ---- Naming convention Alembic ----
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = sa.MetaData(naming_convention=NAMING_CONVENTION)
Base = declarative_base(metadata=metadata)

# ---- Engine & Session ----
engine = create_async_engine(
    DATABASE_URL,
    echo=DB_ECHO,
    future=True,               
    pool_pre_ping=True,       
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_recycle=DB_POOL_RECYCLE_S,
    pool_timeout=DB_POOL_TIMEOUT_S,
    connect_args=CONNECT_ARGS,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
           
            await session.rollback()
            raise
       
