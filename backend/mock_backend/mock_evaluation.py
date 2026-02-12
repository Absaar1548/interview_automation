from .state_machine import InterviewState
from .interview_store import InterviewSession, transition_state

def evaluate_answer(session: InterviewSession) -> None:
    """
    Simulates deterministic scoring and manages state progression.
    Transition to COMPLETED if last question, else IN_PROGRESS.
    """
    # Deterministic scoring simulation (logic placeholder as no score field exists in session)
    # In a real app, we would update a score field here.
    
    total_questions = len(session.questions)
    # indices are 0-based. If index is 3 and valid length is 4, we define that as last.
    is_last_question = (session.current_question_index + 1) >= total_questions

    if is_last_question:
        transition_state(session, InterviewState.COMPLETED)
    else:
        session.current_question_index += 1
        transition_state(session, InterviewState.IN_PROGRESS)
