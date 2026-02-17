from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import TokenResponse
from app.db.database import get_database
from app.db.repositories.user_repository import UserRepository
from app.db.models.user import UserCreate

router = APIRouter()

from app.core.security import verify_password
from app.schemas.auth import LoginRequest

@router.post("/register/candidate", response_model=TokenResponse)
async def register_candidate(user: UserCreate, db = Depends(get_database)):
    # Validate that role is candidate
    if user.role != "candidate":
        raise HTTPException(status_code=400, detail="This endpoint is for candidate registration only")
    
    repo = UserRepository(db)
    existing_user = await repo.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = await repo.create_user(user)
    return {
        "access_token": f"mock_token_{new_user.username}",
        "token_type": "bearer",
        "username": new_user.username,
        "role": new_user.role
    }

@router.post("/register/admin", response_model=TokenResponse)
async def register_admin(user: UserCreate, db = Depends(get_database)):
    # Validate that role is admin
    if user.role != "admin":
        raise HTTPException(status_code=400, detail="This endpoint is for admin registration only")
    
    repo = UserRepository(db)
    existing_user = await repo.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = await repo.create_user(user)
    return {
        "access_token": f"mock_token_{new_user.username}",
        "token_type": "bearer",
        "username": new_user.username,
        "role": new_user.role
    }

@router.post("/login/admin", response_model=TokenResponse)
async def login_admin(request: LoginRequest, db = Depends(get_database)):
    repo = UserRepository(db)
    user = await repo.get_user_by_username(request.username)
    
    if not user or not verify_password(request.password, user.hashed_password):
        # Fallback to hardcoded admin check for bootstrapping if DB is empty? 
        # Or just enforce DB. Let's enforce DB but maybe keep fallback if user doesn't exist?
        # No, let's just stick to DB.
        # Wait, if I change this, the default admin/admin won't work unless I seed it or register it.
        # I should probably auto-seed admin or just let them register.
        # For now, I'll allow the hardcoded admin/admin to PROCEED if not found in DB, OR just fail.
        # The prompt says "update the mock backend to intergate mongodb database for auth".
        # I'll stick to DB. But I'll make sure to register admin first or provide a way.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.role != "admin":
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not an admin",
        )

    return {
        "access_token": f"mock_token_{user.username}",
        "token_type": "bearer",
        "username": user.username,
        "role": "admin"
    }

@router.post("/login/candidate", response_model=TokenResponse)
async def login_candidate(request: LoginRequest, db = Depends(get_database)):
    repo = UserRepository(db)
    user = await repo.get_user_by_username(request.username)
    
    if not user or not verify_password(request.password, user.hashed_password):
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect candidate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.role != "candidate":
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a candidate",
        )

    return {
        "access_token": f"mock_token_{user.username}",
        "token_type": "bearer",
        "username": user.username,
        "role": "candidate"
    }
