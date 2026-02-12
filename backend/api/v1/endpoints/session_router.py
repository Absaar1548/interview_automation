from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel
from typing import Optional
import uuid

# Fix imports: assume uvicorn runs from backend root
from mock_backend.interview_store import (
    create_interview,
    get_interview,
    transition_state,
    INTERVIEWS
)
from mock_backend.state_machine import InterviewState

router = APIRouter()

class InitSessionRequest(BaseModel):
    candidate_token: str

class InitSessionResponse(BaseModel):
    interview_id: str
    state: str

class StartSessionResponse(BaseModel):
    state: str
    first_question_ready: bool

# Removed status_code=201, defaults to 200
@router.post("/init", response_model=InitSessionResponse)
def init_session(request: InitSessionRequest):
    try:
        session = create_interview(request.candidate_token)
        
        # Transition to RESUME_PARSED and stop there
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
        
    # Allow starting from RESUME_PARSED or READY
    if session.state not in [InterviewState.RESUME_PARSED, InterviewState.READY]:
        raise HTTPException(status_code=400, detail={
            "error_code": "INVALID_STATE",
            "message": f"Cannot start session in state {session.state.value}",
            "current_state": session.state.value
        })

    try:
        # If in RESUME_PARSED, move to READY first
        if session.state == InterviewState.RESUME_PARSED:
            transition_state(session, InterviewState.READY)
            
        transition_state(session, InterviewState.IN_PROGRESS)
        return {
            "state": session.state.value,
            "first_question_ready": True
        }
    except ValueError as e:
        # Standardized Error Response
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_STATE",
                "message": str(e),
                "current_state": session.state.value
            }
        )
