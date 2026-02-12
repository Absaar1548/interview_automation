from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
import uuid

# Import mock backend components
from mock_backend.interview_store import (
    get_interview,
    submit_answer
)
from mock_backend.state_machine import InterviewState
from mock_backend.mock_evaluation import evaluate_answer

router = APIRouter()

class SubmitAnswerRequest(BaseModel):
    question_id: str
    answer_type: str = Field(..., pattern="^(AUDIO|CODE)$")
    answer_payload: str

class SubmitAnswerResponse(BaseModel):
    state: str

@router.post("/submit", response_model=SubmitAnswerResponse)
def submit_evaluation(
    request: SubmitAnswerRequest,
    x_interview_id: str = Header(..., alias="X-Interview-Id")
):
    session = get_interview(x_interview_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
        
    try:
        # 1. Submit answer (transitions to ANSWER_SUBMITTED)
        submit_answer(session)
        
        # 2. Evaluate answer (transitions to EVALUATING -> IN_PROGRESS/COMPLETED)
        evaluate_answer(session)
        
        return {
            "state": session.state.value
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_STATE",
                "message": str(e),
                "current_state": session.state.value
            }
        )
