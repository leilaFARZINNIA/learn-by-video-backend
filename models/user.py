# models/user.py
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text, DateTime, text
from db.postgres import Base

class UserORM(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)

   
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)

    google_sub: Mapped[str | None] = mapped_column(Text, unique=True, index=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()"),onupdate=text("NOW()"), nullable=False
    )
