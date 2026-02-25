from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

PyObjectId = str

class InterviewSessionBase(BaseModel):
    interview_id: PyObjectId
    candidate_id: PyObjectId
    status: Literal["active", "terminated", "completed"] = "active"
    proctoring_flags: List[str] = []
    browser_metadata: Dict[str, Any] = {}
    ip_address: str = ""

class InterviewSessionCreate(InterviewSessionBase):
    pass

class InterviewSessionInDB(InterviewSessionBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    termination_reason: Optional[Literal["timeout", "manual_exit", "network_issue"]] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
