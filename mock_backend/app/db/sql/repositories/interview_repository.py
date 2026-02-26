import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.sql.repositories.base import BaseRepository
from app.db.sql.models.interview import Interview
from app.db.sql.models.interview_session import InterviewSession
from app.db.sql.enums import InterviewStatus

class InterviewRepository(BaseRepository[Interview]):
    def __init__(self, session):
        super().__init__(session, Interview)

    def create_interview(self, interview: Interview) -> Interview:
        self.add(interview)
        return interview

    async def get_by_id(self, id: uuid.UUID, with_for_update: bool = False) -> Optional[Interview]:
        stmt = select(Interview).where(Interview.id == id).options(
            selectinload(Interview.sessions)
        )
        if with_for_update:
            stmt = stmt.with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_candidate(self, candidate_id: uuid.UUID) -> List[Interview]:
        stmt = select(Interview).where(Interview.candidate_id == candidate_id).order_by(Interview.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, id: uuid.UUID, status: InterviewStatus) -> Optional[Interview]:
        interview = await self.get_by_id(id)
        if interview:
            interview.status = status
        return interview

    def create_session(self, session_obj: InterviewSession) -> InterviewSession:
        self.session.add(session_obj)
        return session_obj

    async def get_active_or_inprogress_for_candidate(self, candidate_id: uuid.UUID) -> Optional[Interview]:
        stmt = select(Interview).where(
            Interview.candidate_id == candidate_id,
            Interview.status.in_([InterviewStatus.SCHEDULED, InterviewStatus.IN_PROGRESS])
        ).options(selectinload(Interview.sessions))
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all_summary(self) -> List[dict]:
        stmt = select(Interview.id, Interview.candidate_id, Interview.status, Interview.scheduled_at)
        result = await self.session.execute(stmt)
        return [
            {
                "interview_id": row.id,
                "candidate_id": row.candidate_id,
                "status": row.status,
                "scheduled_at": row.scheduled_at
            }
            for row in result.all()
        ]
