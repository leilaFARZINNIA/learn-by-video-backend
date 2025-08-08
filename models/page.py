from pydantic import BaseModel

class Page(BaseModel):
    page_id: str
    page_title: str
    page_description: str
