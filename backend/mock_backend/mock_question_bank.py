def get_questions():
    """
    Returns a deterministic list of 4 fixed questions.
    """
    return [
        {
            "question_id": "q1",
            "category": "CONVERSATIONAL",
            "answer_mode": "AUDIO",
            "difficulty": "EASY",
            "prompt": "Tell me about yourself and your experience with Python.",
            "time_limit_sec": 30
        },
        {
            "question_id": "q2",
            "category": "STATIC",
            "answer_mode": "AUDIO",
            "difficulty": "MEDIUM",
            "prompt": "What is the difference between specific and generic exceptions in Python?",
            "time_limit_sec": 45
        },
        {
            "question_id": "q3",
            "category": "CODING",
            "answer_mode": "CODE",
            "difficulty": "MEDIUM",
            "prompt": "Write a function to reverse a string in Python without using slicing.",
            "time_limit_sec": 300
        },
        {
            "question_id": "q4",
            "category": "CODING",
            "answer_mode": "CODE",
            "difficulty": "HARD",
            "prompt": "Implement a binary search algorithm in Python.",
            "time_limit_sec": 300
        }
    ]
