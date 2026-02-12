from .state_machine import InterviewState, validate_transition
from .interview_store import InterviewSession, transition_state

def evaluate_answer(session: InterviewSession) -> None:
    """
    Simulates deterministic scoring and manages state progression.
    Validates current state is ANSWER_SUBMITTED.
    Transitions to EVALUATING first.
    Then determines if last question:
        If last -> COMPLETED
        Else -> Increment index, transition to IN_PROGRESS
    """
    if session.state != InterviewState.ANSWER_SUBMITTED:
        raise ValueError(f"Cannot evaluate answer in state {session.state}. Must be ANSWER_SUBMITTED.")

    transition_state(session, InterviewState.EVALUATING)

    # Deterministic scoring simulation (logic placeholder)
    
    total_questions = len(session.questions)
    # indices are 0-based.
    is_last_question = (session.current_question_index + 1) >= total_questions

    if is_last_question:
        transition_state(session, InterviewState.COMPLETED)
    else:
        # ONLY increment if NOT last question to avoid index out of bounds on next get
        session.current_question_index += 1
        transition_state(session, InterviewState.IN_PROGRESS)
