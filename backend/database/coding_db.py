from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from database.connection import get_database


# ============ Models ============

class TestCase(BaseModel):
    """Single test case for a coding problem"""
    input: str
    expected_output: str
    is_hidden: bool = False
    points: int = 10


class CodingProblem(BaseModel):
    """Coding problem with test cases"""
    title: str
    description: str
    difficulty: str  # "easy", "medium", "hard"
    time_limit_sec: int = 5
    memory_limit_mb: int = 256
    test_cases: List[TestCase] = []
    sample_code: dict = {}  # language -> default code template
    
    
class CodingProblemInDB(CodingProblem):
    """Coding problem as stored in database"""
    id: str = Field(alias="_id")
    created_at: datetime


class ExecutionResult(BaseModel):
    """Result of executing code against a single test case"""
    test_case_index: int
    passed: bool
    actual_output: Optional[str] = None
    expected_output: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    points_earned: int = 0


class Submission(BaseModel):
    """User's code submission"""
    problem_id: str
    user_id: str
    code: str
    language: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SubmissionInDB(Submission):
    """Submission as stored in database"""
    id: str = Field(alias="_id")
    status: str  # "pending", "running", "completed", "error"
    score: int = 0
    total_points: int = 0
    passed_count: int = 0
    total_count: int = 0
    results: List[ExecutionResult] = []


# ============ Database Helper Functions ============

async def create_problem(problem: CodingProblem) -> CodingProblemInDB:
    """Create a new coding problem"""
    db = get_database()
    problem_dict = problem.dict()
    problem_dict["created_at"] = datetime.utcnow()
    
    result = await db.coding_problems.insert_one(problem_dict)
    problem_dict["_id"] = str(result.inserted_id)
    
    return CodingProblemInDB(**problem_dict)


async def get_problem_by_id(problem_id: str, include_hidden: bool = False) -> Optional[CodingProblemInDB]:
    """Get a coding problem by ID"""
    db = get_database()
    
    try:
        problem_doc = await db.coding_problems.find_one({"_id": ObjectId(problem_id)})
    except:
        return None
    
    if not problem_doc:
        return None
    
    problem_doc["_id"] = str(problem_doc["_id"])
    
    # Filter out hidden test cases if requested
    if not include_hidden and "test_cases" in problem_doc:
        problem_doc["test_cases"] = [
            tc for tc in problem_doc["test_cases"] 
            if not tc.get("is_hidden", False)
        ]
    
    return CodingProblemInDB(**problem_doc)


async def get_all_problems() -> List[CodingProblemInDB]:
    """Get all coding problems (without hidden test cases)"""
    db = get_database()
    
    cursor = db.coding_problems.find({})
    problems = []
    
    async for problem_doc in cursor:
        problem_doc["_id"] = str(problem_doc["_id"])
        
        # Filter out hidden test cases
        if "test_cases" in problem_doc:
            problem_doc["test_cases"] = [
                tc for tc in problem_doc["test_cases"] 
                if not tc.get("is_hidden", False)
            ]
        
        problems.append(CodingProblemInDB(**problem_doc))
    
    return problems


async def save_submission(submission: Submission, results: List[ExecutionResult]) -> SubmissionInDB:
    """Save a code submission with results"""
    db = get_database()
    
    # Calculate score
    score = sum(r.points_earned for r in results)
    total_points = sum(r.points_earned for r in results if r.passed)
    passed_count = sum(1 for r in results if r.passed)
    
    submission_dict = submission.dict()
    submission_dict.update({
        "status": "completed",
        "score": score,
        "total_points": total_points,
        "passed_count": passed_count,
        "total_count": len(results),
        "results": [r.dict() for r in results]
    })
    
    result = await db.submissions.insert_one(submission_dict)
    submission_dict["_id"] = str(result.inserted_id)
    
    return SubmissionInDB(**submission_dict)


async def get_submission_by_id(submission_id: str) -> Optional[SubmissionInDB]:
    """Get a submission by ID"""
    db = get_database()
    
    try:
        submission_doc = await db.submissions.find_one({"_id": ObjectId(submission_id)})
    except:
        return None
    
    if not submission_doc:
        return None
    
    submission_doc["_id"] = str(submission_doc["_id"])
    
    return SubmissionInDB(**submission_doc)
