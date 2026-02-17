from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

# Import mock backend components
from mock_backend.interview_store import (
    create_interview,
    get_interview,
    transition_state,
    INTERVIEWS,
    InterviewState
)

router = APIRouter()

class InitSessionRequest(BaseModel):
    candidate_token: str

class InitSessionResponse(BaseModel):
    interview_id: str
    state: str

class StartSessionResponse(BaseModel):
    state: str
    first_question_ready: bool

@router.post("/init", response_model=InitSessionResponse)
def init_session(request: InitSessionRequest):
    try:
        session = create_interview(request.candidate_token)
        
        # Immediate transitions as per requirement (Mock behavior)
        transition_state(session, InterviewState.RESUME_PARSED)
        
        return {
            "interview_id": session.interview_id,
            "state": session.state.value
        }
    except ValueError as e:
        # Standardized Error Response
        # Search for existing active session to provide context
        current_state = "UNKNOWN"
        for s in INTERVIEWS.values():
            if s.candidate_token == request.candidate_token and s.state not in [InterviewState.COMPLETED, InterviewState.TERMINATED]:
                current_state = s.state.value
                break
        
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_STATE",
                "message": str(e),
                "current_state": current_state
            }
        )

@router.post("/start", response_model=StartSessionResponse)
def start_session(x_interview_id: str = Header(..., alias="X-Interview-Id")):
    session = get_interview(x_interview_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
        
    # Allow start if READY.
    # If already IN_PROGRESS, ideally strictly we might error, but for idempotency/refresh we might allow returning current state?
    # Spec says: "READY -> IN_PROGRESS".
    
    if session.state == InterviewState.IN_PROGRESS:
         return {
            "state": session.state.value,
            "first_question_ready": True
        }

    # Auto-advance if in RESUME_PARSED (Mock Logic to skip resume parsing step manually)
    if session.state == InterviewState.RESUME_PARSED:
        transition_state(session, InterviewState.READY)

    if session.state != InterviewState.READY:
        raise HTTPException(status_code=400, detail={
            "error_code": "INVALID_STATE",
            "message": f"Cannot start session in state {session.state.value}. Expecting READY.",
            "current_state": session.state.value
        })

    try:
        transition_state(session, InterviewState.IN_PROGRESS)
        return {
            "state": session.state.value,
            "first_question_ready": True
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
