from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
from database.user_db import create_user, get_user_by_username, User, UserInDB
from core.security import verify_password, get_password_hash, create_access_token
from core.config import settings
from mock_backend.interview_store import create_interview

router = APIRouter()

class AuthRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str

class RegisterResponse(BaseModel):
    username: str
    message: str

@router.post("/register", response_model=RegisterResponse)
async def register(request: AuthRequest):
    # Check if user exists
    existing_user = await get_user_by_username(request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(request.password)
    new_user = User(
        username=request.username,
        password_hash=hashed_password,
        role="candidate" # Default role
    )
    
    await create_user(new_user)
    
    # Auto-schedule interview for the new candidate
    try:
        create_interview(request.username)
    except ValueError:
        # Should not happen for a new user, but log/ignore if it does
        pass

    return {"username": request.username, "message": "User registered successfully"}

@router.post("/login", response_model=Token)
async def login(request: AuthRequest):
    user = await get_user_by_username(request.username)
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role
    }

