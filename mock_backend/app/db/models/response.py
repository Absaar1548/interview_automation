from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

PyObjectId = str

class ResponseBase(BaseModel):
    session_id: PyObjectId
    question_id: PyObjectId
    answer_text: str
    video_url: Optional[str] = None
    audio_url: Optional[str] = None

class ResponseCreate(ResponseBase):
    pass

class ResponseInDB(ResponseBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    ai_score: Optional[float] = None
    ai_feedback: Optional[str] = None
    manual_score: Optional[float] = None
    final_score: Optional[float] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
