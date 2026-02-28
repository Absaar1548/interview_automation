import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.sql.unit_of_work import UnitOfWork
from app.db.sql.enums import InterviewStatus
from app.db.sql.models.interview_session import InterviewSession

class InterviewSQLService:
    @staticmethod
    async def get_active_interview_for_candidate(session: AsyncSession, candidate_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        async with UnitOfWork(session) as uow:
            # Replaces repo.get_active_or_inprogress_for_candidate
            interview = await uow.interviews.get_active_or_inprogress_for_candidate(candidate_id)
            if not interview:
                return None

            interview_id = interview.id
            interview_status = interview.status

            if interview_status == InterviewStatus.SCHEDULED:
                scheduled_at = interview.scheduled_at
                now_utc = datetime.now(timezone.utc)
                can_start = scheduled_at is not None and scheduled_at <= now_utc
                return {
                    "interview_id": str(interview_id),
                    "session_id": None,
                    "status": interview_status.value,
                    "scheduled_at": scheduled_at,
                    "can_start": can_start,
                }

            if interview_status == InterviewStatus.IN_PROGRESS:
                # Get the active session if one exists
                active_session = next((s for s in interview.sessions if s.status == "active"), None)
                session_id = str(active_session.id) if active_session else None
                return {
                    "interview_id": str(interview_id),
                    "session_id": session_id,
                    "status": interview_status.value,
                    "scheduled_at": interview.scheduled_at,
                    "can_start": True,
                }
            
            return None

    @staticmethod
    async def start_interview(session: AsyncSession, interview_id: uuid.UUID, candidate_id: uuid.UUID) -> Dict[str, Any]:
        async with UnitOfWork(session) as uow:
            interview = await uow.interviews.get_by_id(interview_id, with_for_update=True)
            
            if not interview:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Interview not found"
                )

            # Ownership check
            if interview.candidate_id != candidate_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This interview does not belong to you"
                )

            current_status = interview.status

            # Idempotent rejoin if already in_progress
            if current_status == InterviewStatus.IN_PROGRESS:
                active_session = next((s for s in interview.sessions if s.status == "active"), None)
                return {
                    "session_id": str(active_session.id) if active_session else None,
                    "interview_id": str(interview_id),
                    "status": current_status.value,
                }

            if current_status != InterviewStatus.SCHEDULED:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Cannot start interview with status '{current_status.value}'"
                )

            # Time gate: scheduled_at must be <= now (UTC)
            if interview.scheduled_at:
                now_utc = datetime.now(timezone.utc)
                if interview.scheduled_at > now_utc:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Interview cannot be started before the scheduled time"
                    )

            # Transition interview to in_progress
            interview.status = InterviewStatus.IN_PROGRESS
            now = datetime.now(timezone.utc)
            interview.started_at = now
            
            # Create a new session
            new_session = InterviewSession(
                interview_id=interview_id,
                candidate_id=candidate_id,
                started_at=now,
                status="active"
            )
            uow.interviews.create_session(new_session)
            
            # Automatically committed by the context wrapper closing
            await uow.flush() # Needed so we can return the ID

            return {
                "session_id": str(new_session.id),
                "interview_id": str(interview_id),
                "status": InterviewStatus.IN_PROGRESS.value,
            }

    @staticmethod
    async def list_candidate_interviews(session: AsyncSession, candidate_id: uuid.UUID) -> list:
        async with UnitOfWork(session) as uow:
            interviews = await uow.interviews.list_by_candidate(candidate_id)
            
            return [{
                "id": str(i.id),
                "template_id": str(i.template_id) if i.template_id else None,
                "status": i.status.value,
                "scheduled_at": i.scheduled_at,
                "started_at": i.started_at,
                "completed_at": i.completed_at,
                "overall_score": i.overall_score
            } for i in interviews]
