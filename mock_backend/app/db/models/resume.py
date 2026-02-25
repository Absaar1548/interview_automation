from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

PyObjectId = str

class ParsedStructured(BaseModel):
    education: List[Dict[str, Any]] = []
    experience: List[Dict[str, Any]] = []
    skills: List[str] = []

class ResumeBase(BaseModel):
    candidate_id: PyObjectId
    file_url: str
    parsed_text: Optional[str] = None
    parsed_structured: Optional[ParsedStructured] = None

class ResumeCreate(ResumeBase):
    pass

class ResumeInDB(ResumeBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
