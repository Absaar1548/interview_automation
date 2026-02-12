from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

# Import mock backend components
from mock_backend.interview_store import (
    get_interview,
    get_next_question
)
from mock_backend.state_machine import InterviewState

router = APIRouter()

class QuestionResponse(BaseModel):
    question_id: str
    category: str
    answer_mode: str
    difficulty: str
    prompt: str
    time_limit_sec: int

@router.get("/next", response_model=QuestionResponse)
def get_next_question_endpoint(x_interview_id: str = Header(..., alias="X-Interview-Id")):
    session = get_interview(x_interview_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
        
    try:
        question = get_next_question(session)
        return question
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_STATE",
                "message": str(e),
                "current_state": session.state.value
            }
        )
