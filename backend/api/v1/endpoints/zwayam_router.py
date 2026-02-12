from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

# Import mock backend components
from mock_backend.interview_store import (
    get_interview,
    InterviewState
)

router = APIRouter()

class ZwayamPushRequest(BaseModel):
    decision: str = Field(..., pattern="^(PROCEED|HOLD|REJECT)$")
    final_score: int
    fraud_summary: str

class ZwayamPushResponse(BaseModel):
    status: str

@router.post("/push-feedback", response_model=ZwayamPushResponse)
def push_feedback(
    request: ZwayamPushRequest,
    x_interview_id: str = Header(..., alias="X-Interview-Id")
):
    session = get_interview(x_interview_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
        
    if session.state not in [InterviewState.COMPLETED, InterviewState.TERMINATED]:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_STATE",
                "message": f"Cannot push feedback in state {session.state.value}",
                "current_state": session.state.value
            }
        )
    
    # Mock integration - just return success
    return {"status": "SYNCED"}
