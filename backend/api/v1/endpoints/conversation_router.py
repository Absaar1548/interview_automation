from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

# Import mock backend components
from mock_backend.interview_store import get_interview
from mock_backend.state_machine import InterviewState

router = APIRouter()

class ConversationPromptResponse(BaseModel):
    prompt: str
    followup_allowed: bool

@router.get("/prompt", response_model=ConversationPromptResponse)
def get_conversation_prompt(
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
                "message": f"Cannot get conversation prompt in state {session.state.value}",
                "current_state": session.state.value
            }
        )

    # Deterministic conversational prompt as requested
    return {
        "prompt": "Can you elaborate more on your previous experience?",
        "followup_allowed": True
    }
