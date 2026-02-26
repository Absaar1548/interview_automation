import uuid
import random
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.sql.unit_of_work import UnitOfWork
from app.db.sql.enums import InterviewStatus
from app.db.sql.models.interview_session import InterviewSession
from app.db.sql.models.interview import Interview

# ── Mock score generation ──────────────────────────────────────────────────────
_STRENGTH_POOL = [
    "Clear communication and structured thinking",
    "Strong grasp of SQL and data manipulation",
    "Good understanding of ML model evaluation",
    "Solid problem-solving approach",
    "Confident and concise answers",
]
_GAP_POOL = [
    "Could improve depth on neural network architecture",
    "Limited exposure to distributed computing",
    "Overfitting discussion lacked concrete techniques",
    "Could elaborate more on production deployment",
]
_RECOMMENDATIONS = [
    ("PROCEED",  "Strong candidate — recommend moving forward."),
    ("REVIEW",   "Good potential — recommend technical panel review."),
    ("PROCEED",  "Meets bar — proceed to next round."),
]


def _generate_mock_result(interview_id: uuid.UUID) -> Dict[str, Any]:
    """
    Seeded deterministic mock scoring — same interview always gets same result.
    Score range: 70–95.
    """
    rng = random.Random(interview_id.int)
    score = round(rng.uniform(70.0, 95.0), 1)
    recommendation, note = rng.choice(_RECOMMENDATIONS)
    strengths = rng.sample(_STRENGTH_POOL, k=2)
    gaps = rng.sample(_GAP_POOL, k=1)
    fraud_risk = rng.choice(["LOW", "LOW", "LOW", "MEDIUM"])
    return {
        "final_score": score,
        "recommendation": recommendation,
        "fraud_risk": fraud_risk,
        "strengths": strengths,
        "gaps": gaps,
        "notes": note,
    }


class InterviewSessionSQLService:

    @staticmethod
    async def _get_session_and_interview(
        uow: UnitOfWork,
        session_id: uuid.UUID,
        candidate_id: Optional[uuid.UUID] = None,
        with_for_update: bool = False,
    ):
        stmt = select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.status == "active",
        )
        if with_for_update:
            stmt = stmt.with_for_update()

        result = await uow.session.execute(stmt)
        session_obj = result.scalar_one_or_none()

        if not session_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or not active",
            )

        if candidate_id and session_obj.candidate_id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to you",
            )

        interview = await uow.interviews.get_by_id(
            session_obj.interview_id, with_for_update=with_for_update
        )
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
            )

        return session_obj, interview

    @staticmethod
    async def validate_session(
        session: AsyncSession,
        session_id: uuid.UUID,
        candidate_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        async with UnitOfWork(session) as uow:
            session_obj, interview = await InterviewSessionSQLService._get_session_and_interview(
                uow, session_id, candidate_id
            )
            return {
                "session_id": str(session_obj.id),
                "interview_id": str(interview.id),
                "candidate_id": str(session_obj.candidate_id),
                "status": session_obj.status,
            }

    @staticmethod
    async def get_session_state(
        session: AsyncSession,
        session_id: uuid.UUID,
        candidate_id: uuid.UUID,
    ) -> Dict[str, Any]:
        async with UnitOfWork(session) as uow:
            session_obj, interview = await InterviewSessionSQLService._get_session_and_interview(
                uow, session_id, candidate_id
            )

            curated = interview.curated_questions or {}
            questions = curated.get("questions", []) if isinstance(curated, dict) else []
            answered_count = session_obj.answered_count

            if answered_count >= len(questions):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="No more questions"
                )

            q = questions[answered_count]
            answer_mode = "TEXT"
            if q.get("question_type") == "coding":
                answer_mode = "CODE"
            elif q.get("question_type") == "conversational":
                answer_mode = "AUDIO"

            return {
                "question_id": q.get("question_id", f"q_{answered_count}"),
                "question_text": q.get("prompt", ""),
                "answer_mode": answer_mode,
                "time_limit_sec": q.get("time_limit_sec", 120),
                "question_number": answered_count + 1,
                "total_questions": len(questions),
            }

    @staticmethod
    async def get_answered_count(
        session: AsyncSession, session_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> int:
        async with UnitOfWork(session) as uow:
            session_obj, _ = await InterviewSessionSQLService._get_session_and_interview(
                uow, session_id, candidate_id
            )
            return session_obj.answered_count

    @staticmethod
    async def submit_answer(
        session: AsyncSession,
        session_id: uuid.UUID,
        candidate_id: uuid.UUID,
        answer_payload: dict,
    ) -> Dict[str, Any]:
        async with UnitOfWork(session) as uow:
            session_obj, interview = await InterviewSessionSQLService._get_session_and_interview(
                uow, session_id, candidate_id, with_for_update=True
            )

            curated = interview.curated_questions or {}
            questions = curated.get("questions", []) if isinstance(curated, dict) else []

            new_count = session_obj.answered_count + 1
            session_obj.answered_count = new_count

            if new_count >= len(questions):
                # ── All questions answered → generate mock score and complete ──
                now = datetime.now(timezone.utc)
                mock = _generate_mock_result(interview.id)

                session_obj.status = "completed"
                session_obj.completed_at = now

                interview.status = InterviewStatus.COMPLETED
                interview.completed_at = now
                interview.overall_score = mock["final_score"]
                interview.feedback = (
                    f"Recommendation: {mock['recommendation']}. "
                    f"Strengths: {'; '.join(mock['strengths'])}. "
                    f"Gaps: {'; '.join(mock['gaps'])}. "
                    f"{mock['notes']}"
                )
                return {"state": "COMPLETED"}
            else:
                return {"state": "IN_PROGRESS"}

    @staticmethod
    async def complete_session(
        session: AsyncSession, session_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> Dict[str, Any]:
        async with UnitOfWork(session) as uow:
            session_obj, interview = await InterviewSessionSQLService._get_session_and_interview(
                uow, session_id, candidate_id, with_for_update=True
            )

            now = datetime.now(timezone.utc)
            session_obj.status = "completed"
            session_obj.completed_at = now
            interview.status = InterviewStatus.COMPLETED
            interview.completed_at = now

            return {"state": "COMPLETED"}

    @staticmethod
    async def get_summary(
        session: AsyncSession,
        session_id: uuid.UUID,
        candidate_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Return the mock evaluation summary for a completed interview session.
        Score is retrieved from interview.overall_score (written at completion).
        All other fields are regenerated deterministically from the interview ID seed.
        """
        async with UnitOfWork(session) as uow:
            # Allow completed sessions (status != "active") — no active filter here
            stmt = select(InterviewSession).where(InterviewSession.id == session_id)
            result = await uow.session.execute(stmt)
            session_obj = result.scalar_one_or_none()

            if not session_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
                )
            if session_obj.candidate_id != candidate_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Session does not belong to you",
                )

            interview = await uow.interviews.get_by_id(session_obj.interview_id)
            if not interview:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
                )

            if interview.overall_score is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Interview not yet completed",
                )

            # Use persisted score; regenerate other fields deterministically
            mock = _generate_mock_result(interview.id)
            return {
                "final_score": interview.overall_score,
                "recommendation": mock["recommendation"],
                "fraud_risk": mock["fraud_risk"],
                "strengths": mock["strengths"],
                "gaps": mock["gaps"],
                "notes": mock["notes"],
                "completed_at": session_obj.completed_at,
            }
