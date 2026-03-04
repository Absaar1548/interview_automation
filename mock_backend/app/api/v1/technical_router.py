"""
Technical Questions Router — endpoints for subjective DS/AI questions.

GET  /question        — Get a random technical question (with exclude_ids)
POST /answer          — Submit an answer for a question
"""

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional

from app.db.sql.session import get_db_session
from app.db.sql.models.technical_question import TechnicalQuestion, TechnicalAnswer

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────


class QuestionResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    difficulty: str
    time_limit_sec: int


class AnswerRequest(BaseModel):
    question_id: str
    answer_text: str
    interview_id: Optional[str] = None
    candidate_id: Optional[str] = None


class AnswerResponse(BaseModel):
    answer_id: str
    status: str


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/question", response_model=QuestionResponse)
async def get_technical_question(
    question_id: Optional[str] = None,
    exclude_ids: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """Get a random technical question, optionally excluding already-answered ones."""

    if question_id:
        stmt = select(TechnicalQuestion).where(
            TechnicalQuestion.id == uuid.UUID(question_id)
        )
    else:
        stmt = select(TechnicalQuestion)

        if exclude_ids:
            excluded = [
                uuid.UUID(pid.strip())
                for pid in exclude_ids.split(",")
                if pid.strip()
            ]
            if excluded:
                stmt = stmt.where(TechnicalQuestion.id.notin_(excluded))

        stmt = stmt.order_by(func.random()).limit(1)

    result = await db.execute(stmt)
    question = result.scalar_one_or_none()

    if not question:
        raise HTTPException(status_code=404, detail="No technical questions found")

    return QuestionResponse(
        id=str(question.id),
        title=question.title,
        description=question.description,
        category=question.category.value,
        difficulty=question.difficulty,
        time_limit_sec=question.time_limit_sec,
    )


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(
    request: AnswerRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Submit a written answer for a technical question."""

    answer = TechnicalAnswer(
        question_id=uuid.UUID(request.question_id),
        interview_id=uuid.UUID(request.interview_id) if request.interview_id else None,
        candidate_id=uuid.UUID(request.candidate_id) if request.candidate_id else None,
        answer_text=request.answer_text,
    )
    db.add(answer)
    await db.commit()
    await db.refresh(answer)

    return AnswerResponse(
        answer_id=str(answer.id),
        status="submitted",
    )
