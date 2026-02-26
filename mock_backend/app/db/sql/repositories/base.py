from typing import Generic, TypeVar, Type, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model_class: Type[T]):
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, id: uuid.UUID) -> Optional[T]:
        result = await self.session.execute(select(self.model_class).where(self.model_class.id == id))
        return result.scalar_one_or_none()

    def add(self, obj: T) -> None:
        self.session.add(obj)
