from fastapi import APIRouter
from pydantic import BaseModel

# Import mock backend components
from mock_backend.interview_store import (
    create_interview,
    transition_state,
    InterviewState,
    INTERVIEWS
)

router = APIRouter()

class BootstrapResponse(BaseModel):
    interview_id: str
    candidate_token: str

@router.get("/bootstrap", response_model=BootstrapResponse)
def dev_bootstrap():
    """
    Development-only endpoint to create a real session in memory.
    1. Creates session with fixed token 'dev-candidate-token'.
    2. Transitions to READY state (skipping resume parsing for dev speed).
    3. Returns session details.
    """
    token = "dev-candidate-token"
    
    # Clean up existing dev session if any, to allow repeated bootstraps
    # Find existing session for this token and remove/terminate it or just let create_interview handle it (it raises error)
    # create_interview raises ValueError if active session exists.
    # For dev bootstrap, we probably want to FORCE a new session.
    
    # 1. Force cleanup of old dev session
    keys_to_remove = []
    for iid, session in INTERVIEWS.items():
        if session.candidate_token == token:
            keys_to_remove.append(iid)
    
    for k in keys_to_remove:
        print(f"Cleaning up old dev session: {k}")
        del INTERVIEWS[k]

    # 2. Create new session
    session = create_interview(token)
    
    # 3. Fast-forward state to READY
    # Current: CREATED
    transition_state(session, InterviewState.RESUME_PARSED)
    transition_state(session, InterviewState.READY)
    
    return {
        "interview_id": session.interview_id,
        "candidate_token": session.candidate_token
    }
