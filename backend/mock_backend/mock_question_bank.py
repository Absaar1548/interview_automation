def get_questions():
    """
    Returns a deterministic list of 4 fixed questions.
    """
    return [
        {
            "id": "q1",
            "type": "AUDIO",
            "category": "CONVERSATIONAL",
            "text": "Tell me about yourself and your experience with Python.",
            "duration_seconds": 30
        },
        {
            "id": "q2",
            "type": "AUDIO",
            "category": "STATIC",
            "text": "What is the difference between specific and generic exceptions in Python?",
            "duration_seconds": 45
        },
        {
            "id": "q3",
            "type": "CODE",
            "category": "CODING",
            "text": "Write a function to reverse a string in Python without using slicing.",
            "duration_seconds": 300
        },
        {
            "id": "q4",
            "type": "CODE",
            "category": "CODING",
            "text": "Implement a binary search algorithm in Python.",
            "duration_seconds": 300
        }
    ]
