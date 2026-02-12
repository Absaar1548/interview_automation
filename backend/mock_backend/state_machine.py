from enum import Enum

class InterviewState(Enum):
    CREATED = "CREATED"
    RESUME_PARSED = "RESUME_PARSED"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    QUESTION_ASKED = "QUESTION_ASKED"
    ANSWER_SUBMITTED = "ANSWER_SUBMITTED"
    EVALUATING = "EVALUATING"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"

VALID_TRANSITIONS = {
    InterviewState.CREATED: {InterviewState.RESUME_PARSED, InterviewState.TERMINATED},
    InterviewState.RESUME_PARSED: {InterviewState.READY, InterviewState.TERMINATED},
    InterviewState.READY: {InterviewState.IN_PROGRESS, InterviewState.TERMINATED},
    InterviewState.IN_PROGRESS: {InterviewState.QUESTION_ASKED, InterviewState.TERMINATED},
    InterviewState.QUESTION_ASKED: {InterviewState.ANSWER_SUBMITTED, InterviewState.TERMINATED},
    InterviewState.ANSWER_SUBMITTED: {InterviewState.EVALUATING, InterviewState.TERMINATED},
    InterviewState.EVALUATING: {InterviewState.IN_PROGRESS, InterviewState.COMPLETED, InterviewState.TERMINATED},
    InterviewState.COMPLETED: {InterviewState.TERMINATED},
    InterviewState.TERMINATED: set()
}

def validate_transition(current_state: InterviewState, new_state: InterviewState):
    """
    Validates if a transition from current_state to new_state is allowed.
    Raises ValueError if transition is invalid.
    """
    allowed_next_states = VALID_TRANSITIONS.get(current_state, set())
    
    if new_state not in allowed_next_states:
        raise ValueError(f"Invalid transition from {current_state} to {new_state}")
