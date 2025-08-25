from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text
from db.postgres import Base


class CourseORM(Base):
    __tablename__ = "courses"

    course_id: Mapped[str] = mapped_column(Text, primary_key=True)
    course_title: Mapped[str] = mapped_column(Text, nullable=False)
    course_description: Mapped[str] = mapped_column(Text, nullable=True)
    course_type: Mapped[str] = mapped_column(Text, nullable=False)


class Course(BaseModel):
    course_id: str
    course_title: str
    course_description: str | None = None
    course_type: str
