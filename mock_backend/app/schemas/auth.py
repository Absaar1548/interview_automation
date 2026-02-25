from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str

class CandidateResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    login_disabled: bool
    created_at: datetime
    job_description: Optional[str] = None

    class Config:
        from_attributes = True
