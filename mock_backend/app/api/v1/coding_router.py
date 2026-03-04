"""
Coding Router — endpoints for the LeetCode-style code editor.

GET  /problem          — Get a random coding problem for the candidate
POST /run              — Run code against visible test cases only
POST /submit           — Submit code against ALL test cases (including hidden)
"""

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional

from app.db.sql.session import get_db_session
from app.db.sql.models.coding_problem import (
    CodingProblem,
    TestCase,
    CodeSubmission,
    SubmissionStatus,
)
from app.services.code_execution_service import run_test_cases

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Request / Response schemas ───────────────────────────────────────────────


class CodeRunRequest(BaseModel):
    problem_id: str
    language: str  # python3, javascript, java, cpp
    source_code: str
    interview_id: Optional[str] = None
    candidate_id: Optional[str] = None


class TestCaseResult(BaseModel):
    test_case_id: str
    input: str
    expected_output: str
    actual_output: str
    passed: bool
    error: Optional[str] = None


class CodeRunResponse(BaseModel):
    passed: int
    total: int
    results: list[TestCaseResult]


class SubmitResponse(BaseModel):
    submission_id: str
    status: str
    passed: int
    total: int
    results: list[TestCaseResult]


class ProblemResponse(BaseModel):
    id: str
    title: str
    description: str
    difficulty: str
    time_limit_sec: int
    starter_code: dict
    examples: list[dict]  # visible test cases as examples


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/problem", response_model=ProblemResponse)
async def get_coding_problem(
    problem_id: Optional[str] = None,
    exclude_ids: Optional[str] = None,  # comma-separated problem IDs to exclude
    db: AsyncSession = Depends(get_db_session),
):
    """Get a coding problem. If problem_id is provided, fetch that specific one.
    Otherwise, return a problem not in exclude_ids."""

    if problem_id:
        stmt = (
            select(CodingProblem)
            .options(selectinload(CodingProblem.test_cases))
            .where(CodingProblem.id == uuid.UUID(problem_id))
        )
    else:
        stmt = (
            select(CodingProblem)
            .options(selectinload(CodingProblem.test_cases))
        )

        # Exclude already-solved problems
        if exclude_ids:
            excluded = [uuid.UUID(pid.strip()) for pid in exclude_ids.split(",") if pid.strip()]
            if excluded:
                stmt = stmt.where(CodingProblem.id.notin_(excluded))

        stmt = stmt.order_by(func.random()).limit(1)

    result = await db.execute(stmt)
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(status_code=404, detail="No coding problems found")

    # Only include visible test cases as examples
    visible_cases = [
        {
            "input": tc.input,
            "expected_output": tc.expected_output,
            "order": tc.order,
        }
        for tc in sorted(problem.test_cases, key=lambda t: t.order)
        if not tc.is_hidden
    ]

    return ProblemResponse(
        id=str(problem.id),
        title=problem.title,
        description=problem.description,
        difficulty=problem.difficulty.value,
        time_limit_sec=problem.time_limit_sec,
        starter_code=problem.starter_code,
        examples=visible_cases,
    )


@router.get("/problems", response_model=list[ProblemResponse])
async def list_coding_problems(
    db: AsyncSession = Depends(get_db_session),
):
    """List all coding problems (for admin/debug)."""
    stmt = (
        select(CodingProblem)
        .options(selectinload(CodingProblem.test_cases))
        .order_by(CodingProblem.created_at)
    )
    result = await db.execute(stmt)
    problems = result.scalars().all()

    return [
        ProblemResponse(
            id=str(p.id),
            title=p.title,
            description=p.description,
            difficulty=p.difficulty.value,
            time_limit_sec=p.time_limit_sec,
            starter_code=p.starter_code,
            examples=[
                {
                    "input": tc.input,
                    "expected_output": tc.expected_output,
                    "order": tc.order,
                }
                for tc in sorted(p.test_cases, key=lambda t: t.order)
                if not tc.is_hidden
            ],
        )
        for p in problems
    ]


@router.post("/run", response_model=CodeRunResponse)
async def run_code(
    request: CodeRunRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Run code against visible test cases only (for the Run button)."""

    # Fetch visible test cases
    stmt = (
        select(TestCase)
        .where(
            TestCase.problem_id == uuid.UUID(request.problem_id),
            TestCase.is_hidden == False,
        )
        .order_by(TestCase.order)
    )
    result = await db.execute(stmt)
    test_cases = result.scalars().all()

    if not test_cases:
        raise HTTPException(status_code=404, detail="No test cases found")

    tc_dicts = [
        {"id": str(tc.id), "input": tc.input, "expected_output": tc.expected_output}
        for tc in test_cases
    ]

    results = run_test_cases(request.language, request.source_code, tc_dicts)
    passed = sum(1 for r in results if r["passed"])

    return CodeRunResponse(
        passed=passed,
        total=len(results),
        results=[TestCaseResult(**r) for r in results],
    )


@router.post("/submit", response_model=SubmitResponse)
async def submit_code(
    request: CodeRunRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Submit code — runs against ALL test cases (including hidden). Saves submission."""

    # Fetch ALL test cases
    stmt = (
        select(TestCase)
        .where(TestCase.problem_id == uuid.UUID(request.problem_id))
        .order_by(TestCase.order)
    )
    result = await db.execute(stmt)
    test_cases = result.scalars().all()

    if not test_cases:
        raise HTTPException(status_code=404, detail="No test cases found")

    tc_dicts = [
        {"id": str(tc.id), "input": tc.input, "expected_output": tc.expected_output}
        for tc in test_cases
    ]

    results = run_test_cases(request.language, request.source_code, tc_dicts)
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    status = SubmissionStatus.PASSED if passed == total else SubmissionStatus.FAILED

    # Save submission
    submission = CodeSubmission(
        problem_id=uuid.UUID(request.problem_id),
        interview_id=uuid.UUID(request.interview_id) if request.interview_id else None,
        candidate_id=uuid.UUID(request.candidate_id) if request.candidate_id else None,
        language=request.language,
        source_code=request.source_code,
        status=status,
        results=results,
        passed_count=passed,
        total_count=total,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    return SubmitResponse(
        submission_id=str(submission.id),
        status=status.value,
        passed=passed,
        total=total,
        results=[TestCaseResult(**r) for r in results],
    )


# ─── Interview Completion ────────────────────────────────────────────────────


class CompleteInterviewRequest(BaseModel):
    candidate_id: Optional[str] = None


@router.post("/complete-interview")
async def complete_interview(
    request: CompleteInterviewRequest = CompleteInterviewRequest(),
    db: AsyncSession = Depends(get_db_session),
):
    """Mark the interview as completed and disable candidate login."""
    from app.db.sql.models.interview import Interview
    from app.db.sql.models.user import User
    from app.db.sql.enums import InterviewStatus
    from datetime import datetime, timezone

    candidate_id = None
    if request.candidate_id:
        candidate_id = uuid.UUID(request.candidate_id)

    # If candidate_id provided, update their interview and disable login
    if candidate_id:
        # Update interview status
        stmt = (
            select(Interview)
            .where(Interview.candidate_id == candidate_id)
            .order_by(Interview.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        interview = result.scalar_one_or_none()

        if interview:
            interview.status = InterviewStatus.COMPLETED
            interview.completed_at = datetime.now(timezone.utc)

        # Disable login
        user_stmt = select(User).where(User.id == candidate_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if user:
            user.login_disabled = True

        await db.commit()

        return {
            "status": "completed",
            "message": "Interview completed. Your login has been disabled.",
            "interview_id": str(interview.id) if interview else None,
        }

    # No candidate_id — just return success (anonymous mode)
    return {
        "status": "completed",
        "message": "Interview completed successfully.",
        "interview_id": None,
    }
