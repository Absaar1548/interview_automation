from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sql.repositories.user_repository import UserRepository
from app.db.sql.repositories.interview_repository import InterviewRepository

class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.interviews = InterviewRepository(session)

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
        
    async def flush(self):
        await self.session.flush()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
