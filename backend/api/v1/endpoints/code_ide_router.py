from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database.coding_db import (
    CodingProblem,
    CodingProblemInDB,
    Submission,
    SubmissionInDB,
    get_problem_by_id,
    get_all_problems,
    save_submission
)
from services.coding_service import CodingService

router = APIRouter()
coding_service = CodingService()


# ============ Request/Response Models ============

class ExecuteCodeRequest(BaseModel):
    code: str
    language: str


class ExecuteCodeResponse(BaseModel):
    output: Optional[str]
    error: Optional[str]
    execution_time_ms: float


class TestCodeRequest(BaseModel):
    problem_id: str
    code: str
    language: str


class TestCaseResult(BaseModel):
    test_case_index: int
    passed: bool
    actual_output: Optional[str] = None
    expected_output: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    is_hidden: bool = False


class TestCodeResponse(BaseModel):
    results: List[TestCaseResult]
    passed_count: int
    total_count: int


class SubmitCodeRequest(BaseModel):
    problem_id: str
    code: str
    language: str
    user_id: str = "test_user"  # TODO: Get from auth


class SubmitCodeResponse(BaseModel):
    submission_id: str
    score: int
    total_points: int
    passed_count: int
    total_count: int


class ProblemListItem(BaseModel):
    id: str
    title: str
    difficulty: str


# ============ Endpoints ============

@router.get("/problems", response_model=List[ProblemListItem])
async def list_problems():
    """
    List all available coding problems.
    Returns basic info without test cases.
    """
    problems = await get_all_problems()
    
    return [
        ProblemListItem(
            id=p.id,
            title=p.title,
            difficulty=p.difficulty
        )
        for p in problems
    ]


@router.get("/problems/{problem_id}", response_model=CodingProblemInDB)
async def get_problem(problem_id: str):
    """
    Get a specific coding problem with visible test cases only.
    Hidden test cases are excluded.
    """
    problem = await get_problem_by_id(problem_id, include_hidden=False)
    
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    return problem


@router.post("/execute", response_model=ExecuteCodeResponse)
async def execute_code(request: ExecuteCodeRequest):
    """
    Execute code without any test cases (for quick testing).
    Returns output, error, and execution time.
    """
    result = await coding_service.execute_code(
        code=request.code,
        language=request.language,
        stdin_input="",
        timeout=5
    )
    
    return ExecuteCodeResponse(
        output=result["output"],
        error=result["error"],
        execution_time_ms=result["execution_time_ms"]
    )


@router.post("/test", response_model=TestCodeResponse)
async def test_code(request: TestCodeRequest):
    """
    Run code against visible test cases only.
    Returns results for each test case.
    """
    # Get problem with visible test cases only
    problem = await get_problem_by_id(request.problem_id, include_hidden=False)
    
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    if not problem.test_cases:
        raise HTTPException(status_code=400, detail="No test cases available")
    
    # Run against visible test cases
    results = await coding_service.evaluate_submission(
        code=request.code,
        language=request.language,
        test_cases=problem.test_cases,
        timeout=problem.time_limit_sec
    )
    
    # Convert to response format
    test_results = [
        TestCaseResult(
            test_case_index=r.test_case_index,
            passed=r.passed,
            actual_output=r.actual_output,
            expected_output=r.expected_output,
            error=r.error,
            execution_time_ms=r.execution_time_ms,
            is_hidden=False
        )
        for r in results
    ]
    
    return TestCodeResponse(
        results=test_results,
        passed_count=sum(1 for r in results if r.passed),
        total_count=len(results)
    )


@router.post("/submit", response_model=SubmitCodeResponse)
async def submit_code(request: SubmitCodeRequest):
    """
    Submit solution for full evaluation.
    Runs against ALL test cases (visible + hidden).
    Returns submission ID and score.
    """
    # Get problem with ALL test cases (including hidden)
    problem = await get_problem_by_id(request.problem_id, include_hidden=True)
    
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    if not problem.test_cases:
        raise HTTPException(status_code=400, detail="No test cases available")
    
    # Run against all test cases
    results = await coding_service.evaluate_submission(
        code=request.code,
        language=request.language,
        test_cases=problem.test_cases,
        timeout=problem.time_limit_sec
    )
    
    # Create submission
    submission = Submission(
        problem_id=request.problem_id,
        user_id=request.user_id,
        code=request.code,
        language=request.language
    )
    
    # Save to database
    saved_submission = await save_submission(submission, results)
    
    return SubmitCodeResponse(
        submission_id=saved_submission.id,
        score=saved_submission.score,
        total_points=saved_submission.total_points,
        passed_count=saved_submission.passed_count,
        total_count=saved_submission.total_count
    )


@router.get("/submissions/{submission_id}", response_model=SubmissionInDB)
async def get_submission(submission_id: str):
    """
    Get submission details and results.
    Note: Hidden test case details are included in results.
    """
    from database.coding_db import get_submission_by_id
    
    submission = await get_submission_by_id(submission_id)
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return submission
