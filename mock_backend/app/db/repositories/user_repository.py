from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.models.user import UserCreate, UserInDB
from datetime import datetime
from typing import Optional
from bson import ObjectId

from app.core.security import get_password_hash

class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.get_collection("users")

    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        user = await self.collection.find_one({"username": username})
        if user:
            return UserInDB(**user)
        return None

    async def get_user_by_username_or_id(self, user_id: str) -> Optional[UserInDB]:
        """
        Fetch a user by their MongoDB ObjectId string.
        Used by the interview service to validate candidate existence.
        """
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None
        user = await self.collection.find_one({"_id": oid})
        if user:
            return UserInDB(**user)
        return None

    async def create_user(self, user: UserCreate) -> UserInDB:
        now = datetime.utcnow()
        user_in_db = UserInDB(
            username=user.username,
            email=user.email,
            role=user.role,
            profile=user.profile,
            is_active=True,
            hashed_password=get_password_hash(user.password),
            created_at=now,
            updated_at=now
        )
        user_dict = user_in_db.dict(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(user_dict)
        user_in_db.id = str(result.inserted_id)
        return user_in_db
