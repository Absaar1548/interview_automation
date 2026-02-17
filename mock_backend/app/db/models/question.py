from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime

PyObjectId = str

class QuestionBase(BaseModel):
    title: str
    description: str
    difficulty: Literal["easy", "medium", "hard"]
    category: str
    tags: List[str] = []
    expected_answer_keywords: List[str] = []
    is_active: bool = True

class QuestionCreate(QuestionBase):
    created_by: PyObjectId

class QuestionInDB(QuestionBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_by: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
