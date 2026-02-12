from fastapi import APIRouter, HTTPException, Header, Path
from pydantic import BaseModel

# Import mock backend components
from mock_backend.interview_store import get_interview
from mock_backend.state_machine import InterviewState

router = APIRouter()

class CodeTemplateResponse(BaseModel):
    language: str
    starter_code: str

@router.get("/template/{question_id}", response_model=CodeTemplateResponse)
def get_code_template(
    question_id: str = Path(..., description="The ID of the coding question"),
    x_interview_id: str = Header(..., alias="X-Interview-Id")
):
    session = get_interview(x_interview_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    if session.state != InterviewState.IN_PROGRESS:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_STATE",
                "message": f"Cannot access code template in state {session.state.value}",
                "current_state": session.state.value
            }
        )

    # Deterministic template as requested (ignoring question_id for Phase 1)
    return {
        "language": "python",
        "starter_code": "# Write your solution here\n"
    }
