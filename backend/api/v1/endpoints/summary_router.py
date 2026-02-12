from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional

# Import mock backend components
from mock_backend.interview_store import (
    get_interview
)
from mock_backend.state_machine import InterviewState

router = APIRouter()

class SummaryResponse(BaseModel):
    final_score: int
    recommendation: str
    fraud_risk: str
    strengths: List[str]
    gaps: List[str]
    notes: str

@router.get("", response_model=SummaryResponse)
def get_summary(x_interview_id: str = Header(..., alias="X-Interview-Id")):
    session = get_interview(x_interview_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
        
    if session.state not in [InterviewState.COMPLETED, InterviewState.TERMINATED]:
         raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_STATE",
                "message": f"Cannot get summary in state {session.state.value}",
                "current_state": session.state.value
            }
        )
    
    # Deterministic summary as requested
    return {
        "final_score": 80,
        "recommendation": "PROCEED",
        "fraud_risk": "LOW",
        "strengths": ["Good communication", "Strong Python basics"],
        "gaps": ["Algorithm optimization"],
        "notes": "Mock evaluation summary"
    }
