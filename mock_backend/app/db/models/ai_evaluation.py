from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

PyObjectId = str

class AIEvaluationBase(BaseModel):
    response_id: PyObjectId
    model_used: str
    prompt_version: str
    raw_prompt: str
    raw_response: str
    confidence_score: float

class AIEvaluationCreate(AIEvaluationBase):
    pass

class AIEvaluationInDB(AIEvaluationBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
