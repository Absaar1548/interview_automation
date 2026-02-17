from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

PyObjectId = str

class TemplateQuestion(BaseModel):
    question_id: PyObjectId
    order: int
    time_limit_sec: int

class InterviewTemplateBase(BaseModel):
    name: str
    description: str
    questions: List[TemplateQuestion] = []
    total_duration_sec: int
    is_active: bool = True

class InterviewTemplateCreate(InterviewTemplateBase):
    created_by: PyObjectId

class InterviewTemplateInDB(InterviewTemplateBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_by: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
