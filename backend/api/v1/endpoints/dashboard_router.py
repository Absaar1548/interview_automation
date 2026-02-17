from fastapi import APIRouter
from typing import List, Dict
from pydantic import BaseModel
from datetime import datetime
from mock_backend.interview_store import INTERVIEWS, InterviewState

router = APIRouter()

class InterviewSummary(BaseModel):
    interview_id: str
    candidate_token: str
    state: str
    cheat_score: int
    created_at: datetime

class DashboardStats(BaseModel):
    total_interviews: int
    completed: int
    pending: int
    flagged: int

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats():
    total = len(INTERVIEWS)
    completed = 0
    pending = 0
    flagged = 0
    
    for session in INTERVIEWS.values():
        if session.state == InterviewState.COMPLETED:
            completed += 1
        elif session.state not in [InterviewState.COMPLETED, InterviewState.TERMINATED]:
            pending += 1
            
        if session.cheat_score > 50: # Arbitrary threshold for "flagged" for now
            flagged += 1
            
    return {
        "total_interviews": total,
        "completed": completed,
        "pending": pending,
        "flagged": flagged
    }

@router.get("/interviews", response_model=List[InterviewSummary])
def get_interviews():
    summary_list = []
    # Sort by created_at desc (newest first)
    # Note: InterviewSession in mock store might not have created_at populated by default if it's old code
    # But dataclasses usually work fine.
    
    sorted_sessions = sorted(INTERVIEWS.values(), key=lambda x: x.created_at, reverse=True)
    
    for session in sorted_sessions:
        summary_list.append({
            "interview_id": session.interview_id,
            "candidate_token": session.candidate_token,
            "state": session.state.value,
            "cheat_score": session.cheat_score,
            "created_at": session.created_at
        })
        
    return summary_list
