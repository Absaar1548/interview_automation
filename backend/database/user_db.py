from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from database.connection import get_database

class User(BaseModel):
    username: str
    password_hash: str
    role: str = "candidate"

class UserInDB(User):
    id: str = Field(alias="_id")

async def get_user_by_username(username: str) -> Optional[UserInDB]:
    db = get_database()
    user_doc = await db.users.find_one({"username": username})
    if user_doc:
        user_doc["_id"] = str(user_doc["_id"])
        return UserInDB(**user_doc)
    return None

async def create_user(user: User) -> UserInDB:
    db = get_database()
    user_dict = user.dict()
    result = await db.users.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)
    return UserInDB(**user_dict)
