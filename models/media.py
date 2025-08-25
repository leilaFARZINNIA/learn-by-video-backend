from typing import List, Union, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from db.postgres import Base
from pydantic import BaseModel, ConfigDict

# --- ORM ---
class MediaORM(Base):
    __tablename__ = "medias"

    media_id: Mapped[str] = mapped_column(Text, primary_key=True)
    media_title: Mapped[str] = mapped_column(Text, nullable=False)
    media_description: Mapped[str] = mapped_column(Text, nullable=True)
    course_id: Mapped[str] = mapped_column(Text, ForeignKey("courses.course_id", ondelete="CASCADE"))
    media_url: Mapped[str] = mapped_column(Text, nullable=False)
    media_transcript: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

# --- Pydantic ---
class TranscriptLine(BaseModel):
    time: int
    text: str

class Media(BaseModel):
    media_id: str
    media_title: str
    media_description: str
    course_id: str
    media_url: str
    media_transcript: Optional[Union[str, List[TranscriptLine]]] = None
    model_config = ConfigDict(from_attributes=True)
