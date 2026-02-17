from pydantic import BaseModel, Field, EmailStr, BeforeValidator, ConfigDict, model_validator
from typing import Optional, Annotated, List, Literal, Union
from datetime import datetime
from bson import ObjectId

# Represents an ObjectId field in the database.
# It will be represented as a string in the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]

class AdminProfile(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None

class CandidateProfile(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    resume_id: Optional[PyObjectId] = None
    experience_years: Optional[int] = None
    skills: List[str] = Field(default_factory=list)  # Fixed mutable default

# Union type for profile - can be either admin or candidate profile
UserProfile = Union[AdminProfile, CandidateProfile]

class UserBase(BaseModel):
    username: str
    email: EmailStr  # Required, not optional
    role: Literal["admin", "candidate"]
    is_active: bool = True
    profile: UserProfile  # Required, not optional
    
    @model_validator(mode='after')
    def validate_role_profile_match(self):
        """Ensure role matches profile type"""
        if self.role == "admin" and not isinstance(self.profile, AdminProfile):
            raise ValueError("Admin role must have AdminProfile")
        if self.role == "candidate" and not isinstance(self.profile, CandidateProfile):
            raise ValueError("Candidate role must have CandidateProfile")
        return self

class UserCreate(BaseModel):
    username: str
    email: EmailStr  # Required
    password: str
    role: Literal["admin", "candidate"]  # Required
    profile: UserProfile  # Required

class UserInDB(UserBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )
