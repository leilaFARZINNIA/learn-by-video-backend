from pydantic import BaseModel

class Course(BaseModel):
    course_id: str
    course_title: str
    course_description: str
