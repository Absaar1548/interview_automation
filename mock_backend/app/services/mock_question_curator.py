"""
Mock Question Curator Service
------------------------------
Returns a static curated questions payload that simulates what a real
AI resume+JD parsing agent would produce.

EXTENSION POINT: Replace the body of `generate_curated_questions` with
a call to your AI agent (e.g., AIQuestionGeneratorAgent) when ready.
The shape of the returned dict must remain identical so that the
interview_service and schemas require no changes.
"""

from datetime import datetime
from typing import Optional


def generate_curated_questions(
    template_id: str,
    candidate_id: str,
    resume_id: Optional[str] = None,
    jd_id: str = "mock_jd_001",
) -> dict:
    """
    Returns a mock curated questions payload for the given template and candidate.

    Args:
        template_id: ObjectId string of the interview template.
        candidate_id: ObjectId string of the candidate.
        resume_id: ObjectId string of the candidate's resume (optional).
        jd_id: Job description identifier (defaults to mock).

    Returns:
        dict conforming to CuratedQuestionsPayload schema.
    """
    return {
        "template_id": template_id,
        "generated_from": {
            "resume_id": resume_id or candidate_id,
            "jd_id": jd_id,
        },
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "generation_method": "mock_static_v2",
        "questions": [
            {
                "question_id": "static_q_001",
                "question_type": "static",
                "order": 1,
                "prompt": "Explain the concept of overfitting in Machine Learning.",
                "difficulty": "medium",
                "time_limit_sec": 120,
                "evaluation_mode": "text",
                "source": "question_bank"
            },
            {
                "question_id": "conv_q_001",
                "question_type": "conversational",
                "order": 2,
                "prompt": "Tell me about a challenging ML project you worked on.",
                "difficulty": "medium",
                "time_limit_sec": 300,
                "conversation_config": {
                    "follow_up_depth": 3,
                    "ai_model": "gpt-4",
                    "evaluation_mode": "contextual"
                }
            },
            {
                "question_id": "code_q_001",
                "question_type": "coding",
                "order": 3,
                "prompt": "Write a Python function to detect if a string is a palindrome.",
                "difficulty": "medium",
                "time_limit_sec": 900,
                "coding_config": {
                    "language": "python",
                    "starter_code": "def is_palindrome(s: str) -> bool:\n    pass",
                    "test_cases": [
                        {"input": "\"madam\"", "expected_output": "True"},
                        {"input": "\"hello\"", "expected_output": "False"}
                    ],
                    "execution_timeout_sec": 5
                }
            }
        ]
    }

