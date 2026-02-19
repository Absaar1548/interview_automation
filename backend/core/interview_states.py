from enum import Enum

class InterviewState(Enum):
    """
    Enum for interview states.
    """
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EVALUATED = "evaluated"
