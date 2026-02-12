# Database schema definitions
# Placeholder for SQLAlchemy models or Tortoise ORM models
from beanie import Document
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class Candidate(Document):
    username: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Settings:
        name = "candidates"  # Collection name
        indexes = [
            [("username", 1)],  # Unique index on username
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "username": "candidate123",
                "is_active": True
            }
        }

class HR(Document):
    username: str
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Settings:
        name = "hr_users"  # Collection name
        indexes = [
            [("username", 1)],  # Unique index on username
            [("email", 1)],  # Unique index on email
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "username": "hr_user",
                "email": "hr@example.com",
                "is_active": True
            }
        }

class DeliveryHead(Document):
    username: str
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Settings:
        name = "delivery_heads"  # Collection name
        indexes = [
            [("username", 1)],  # Unique index on username
            [("email", 1)],  # Unique index on email
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "username": "dh_user",
                "email": "dh@example.com",
                "is_active": True
            }
        }