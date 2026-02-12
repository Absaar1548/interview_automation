import uuid
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .state_machine import InterviewState, validate_transition
from .mock_question_bank import get_questions

@dataclass
class InterviewSession:
    interview_id: str
    candidate_token: str
    state: InterviewState
    current_question_index: int
    cheat_score: int
    questions: List[dict]
    created_at: datetime = field(default_factory=datetime.now)

# Global in-memory storage
INTERVIEWS = {}

def create_interview(candidate_token: str) -> InterviewSession:
    """
    Creates a new interview session.
    """
    interview_id = str(uuid.uuid4())
    session = InterviewSession(
        interview_id=interview_id,
        candidate_token=candidate_token,
        state=InterviewState.CREATED,
        current_question_index=0,
        cheat_score=0,
        questions=get_questions()
    )
    INTERVIEWS[interview_id] = session
    return session

def get_interview(interview_id: str) -> Optional[InterviewSession]:
    """
    Retrieves an interview session by ID.
    """
    return INTERVIEWS.get(interview_id)

def transition_state(session: InterviewSession, new_state: InterviewState):
    """
    Transitions the session to a new state after validation.
    """
    validate_transition(session.state, new_state)
    session.state = new_state

def add_cheat_score(session: InterviewSession, score: int):
    """
    Adds to the accumulated cheat score.
    """
    session.cheat_score += score

def terminate_interview(session: InterviewSession):
    """
    Forcefully terminates the interview.
    """
    transition_state(session, InterviewState.TERMINATED)
