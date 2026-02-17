from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime

PyObjectId = str

class InterviewBase(BaseModel):
    candidate_id: PyObjectId
    template_id: PyObjectId
    assigned_by: PyObjectId
    status: Literal["scheduled", "in_progress", "completed", "cancelled"] = "scheduled"
    scheduled_at: Optional[datetime] = None

class InterviewCreate(InterviewBase):
    pass

class InterviewInDB(InterviewBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    overall_score: Optional[float] = None
    feedback: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
