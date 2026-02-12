from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

# Import mock backend components
from mock_backend.interview_store import (
    get_interview,
    submit_answer,
    InterviewState
)
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
        
        # 3. Deterministic progression check for q4 (Mock Logic override/ensure)
        # mock_evaluation.py already handles is_last_question logic based on index.
        # But user requested "If question_id == 'q4' -> COMPLETED else IN_PROGRESS".
        # Since mock_evaluation.py logic is:
        # if (index + 1) >= total: COMPLETED
        # And we have 4 questions.
        # So it naturally works. If index was 3 (q4), (3+1)>=4 -> COMPLETED.
        
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
