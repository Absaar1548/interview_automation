"""
Interview Service
------------------
Orchestrates all business logic and validation for interview scheduling,
rescheduling, and cancellation. Delegates DB calls to InterviewRepository
and UserRepository. Questino curation is delegated to mock_question_curator.
"""

from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.repositories.interview_repository import InterviewRepository
from app.db.repositories.user_repository import UserRepository
from app.services.mock_question_curator import generate_curated_questions


def _validate_object_id(value: str, field_name: str) -> ObjectId:
    """Raise 422 if value is not a valid ObjectId."""
    try:
        return ObjectId(value)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"'{field_name}' is not a valid ObjectId: {value}",
        )


class InterviewService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.interview_repo = InterviewRepository(db)
        self.user_repo = UserRepository(db)

    # ─── Schedule ─────────────────────────────────────────────────────────────

    async def schedule_interview(
        self,
        candidate_id: str,
        template_id: str,
        scheduled_at: datetime,
        admin_id: str,
    ) -> dict:
        """
        Validate all rules, prepare curated questions, and insert the interview.

        Validation sequence (short-circuits on first failure):
          1. candidate_id is a valid ObjectId
          2. Candidate exists in users
          3. Candidate role == "candidate"
          4. Candidate is_active == True
          5. No existing scheduled/in_progress interview for this candidate
          6. template_id is a valid ObjectId
          7. Template exists
          8. Template is_active == True
          9. scheduled_at is in the future (UTC)
        """

        # 1. Validate ObjectIds
        _validate_object_id(candidate_id, "candidate_id")
        _validate_object_id(template_id, "template_id")

        # 2. Candidate must exist
        candidate = await self.user_repo.get_user_by_username_or_id(candidate_id)
        if candidate is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found",
            )

        # 3. Must be a candidate role
        if candidate.role != "candidate":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a candidate",
            )

        # 4. Must be active
        if not candidate.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate account is inactive",
            )

        # 5. One active interview per candidate
        active = await self.interview_repo.get_active_interview_for_candidate(candidate_id)
        if active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Candidate already has an active interview (status: scheduled or in_progress)",
            )

        # 6–8. Template must exist and be active
        template = await self._get_template(template_id)

        # 9. scheduled_at must be future
        self._assert_future_datetime(scheduled_at)

        # Build curated questions
        resume_id = None
        if hasattr(candidate.profile, "resume_id"):
            resume_id = candidate.profile.resume_id
        curated_questions = generate_curated_questions(
            template_id=template_id,
            candidate_id=candidate_id,
            resume_id=resume_id,
        )

        now = datetime.utcnow()
        interview_doc = {
            "candidate_id": candidate_id,
            "template_id": template_id,
            "assigned_by": admin_id,
            "status": "scheduled",
            "scheduled_at": scheduled_at,
            "started_at": None,
            "completed_at": None,
            "overall_score": None,
            "feedback": None,
            "curated_questions": curated_questions,
            "created_at": now,
            "updated_at": now,
        }

        created = await self.interview_repo.create_interview(interview_doc)
        return created

    # ─── Reschedule ───────────────────────────────────────────────────────────

    async def reschedule_interview(
        self, interview_id: str, scheduled_at: datetime
    ) -> dict:
        """
        Move a scheduled interview to a new datetime.
        Only allowed when status == 'scheduled'.
        """
        _validate_object_id(interview_id, "interview_id")

        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found",
            )

        if interview["status"] != "scheduled":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only scheduled interviews can be rescheduled",
            )

        self._assert_future_datetime(scheduled_at)

        await self.interview_repo.update_scheduled_at(interview_id, scheduled_at)
        now = datetime.utcnow()
        return {
            "id": str(interview["_id"]),
            "status": "scheduled",
            "scheduled_at": scheduled_at,
            "updated_at": now,
        }

    # ─── Cancel ───────────────────────────────────────────────────────────────

    async def cancel_interview(
        self, interview_id: str, reason: Optional[str] = None
    ) -> dict:
        """
        Cancel an interview. Allowed for any status except 'completed'.
        Document is never deleted — status becomes 'cancelled'.
        """
        _validate_object_id(interview_id, "interview_id")

        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found",
            )

        if interview["status"] == "completed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Completed interviews cannot be cancelled",
            )

        await self.interview_repo.cancel_interview(interview_id, reason)
        now = datetime.utcnow()
        return {
            "id": str(interview["_id"]),
            "status": "cancelled",
            "cancelled_at": now,
            "reason": reason,
        }

    # ─── Private helpers ──────────────────────────────────────────────────────

    async def _get_template(self, template_id: str) -> dict:
        """Fetch template from DB; raise 404/400 as appropriate."""
        try:
            oid = ObjectId(template_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"'template_id' is not a valid ObjectId: {template_id}",
            )
        template = await self.db.get_collection("interview_templates").find_one(
            {"_id": oid}
        )
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview template not found",
            )
        if not template.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview template is not active",
            )
        return template

    @staticmethod
    def _assert_future_datetime(dt: datetime) -> None:
        """Raise 400 if dt is more than 10 minutes in the past (UTC).
        A 10-minute grace window lets admins schedule 'now' without clock skew issues.
        """
        now_utc = datetime.utcnow()
        dt_naive = dt.replace(tzinfo=None) if dt.tzinfo is not None else dt
        grace = timedelta(minutes=10)
        if dt_naive < now_utc - grace:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="scheduled_at must not be more than 10 minutes in the past (UTC)",
            )
