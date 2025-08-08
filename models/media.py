from pydantic import BaseModel
from typing import List, Union, Optional

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
