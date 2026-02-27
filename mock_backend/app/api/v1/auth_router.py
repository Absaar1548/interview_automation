import logging
from datetime import timedelta, datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Form, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import secrets
import os
from pathlib import Path

from app.schemas.auth import TokenResponse, LoginRequest, TokenData, CandidateResponse
from app.db.database import get_database
from app.db.repositories.user_repository import UserRepository
from app.db.models.user import UserCreate, UserInDB, CandidateProfile
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.services.email_service import email_service
from app.services.resume_parser import save_resume_and_extract_text

logger = logging.getLogger(__name__)
CANDIDATE_MATERIALS_COLLECTION = "candidate_materials"
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_database)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    repo = UserRepository(db)
    user = await repo.get_user_by_username(token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin(current_user: UserInDB = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

@router.post("/register/candidate", response_model=TokenResponse)
async def register_candidate(user: UserCreate, db = Depends(get_database)):
    # Always treat as candidate registration (ignore or fix role/profile in body)
    if user.role != "candidate" or not isinstance(user.profile, CandidateProfile):
        profile = user.profile if isinstance(user.profile, CandidateProfile) else CandidateProfile()
        user = user.model_copy(update={"role": "candidate", "profile": profile})

    repo = UserRepository(db)
    existing_user = await repo.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=409, detail="Username already registered")
    
    new_user = await repo.create_user(user)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=new_user.username, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
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
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=new_user.username, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": new_user.username,
        "role": new_user.role
    }

@router.post("/login/admin", response_model=TokenResponse)
async def login_admin(request: LoginRequest, db = Depends(get_database)):
    repo = UserRepository(db)
    user = await repo.get_user_by_username(request.username)
    
    if not user or not verify_password(request.password, user.hashed_password):
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

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
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
        
    if user.login_disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Login has been disabled for this account. Please contact the administrator."
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": "candidate"
    }

@router.get("/me", response_model=UserInDB)
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    return current_user

@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out"}

# --- Admin Features ---

@router.post("/admin/register-candidate", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def admin_register_candidate(
    candidate_name: str = Form(...),
    candidate_email: str = Form(...),
    job_description: str = Form(""),
    resume: UploadFile = File(...),
    current_admin: UserInDB = Depends(get_current_admin),
    db = Depends(get_database)
):
    repo = UserRepository(db)
    
    # Check existing (using email as proxy for username check or we should check email uniqueness if we enforced it)
    # The real backend uses email as unique, mock uses username.
    # We will derive username from email.
    username = candidate_email.split('@')[0]
    
    existing_user = await repo.get_user_by_username(username)
    if existing_user:
        raise HTTPException(status_code=409, detail="Candidate with this email/username already exists")

    # Generate random password
    password = secrets.token_urlsafe(12)
    hashed_password = get_password_hash(password)
    
    resume_id = secrets.token_hex(8)
    resume_bytes = await resume.read()
    if len(resume_bytes) == 0:
        raise HTTPException(status_code=400, detail="Resume file is empty")

    # Create Candidate Profile
    # Splitting name for first/last
    names = candidate_name.split(" ", 1)
    first_name = names[0]
    last_name = names[1] if len(names) > 1 else ""
    
    profile = CandidateProfile(
        first_name=first_name,
        last_name=last_name,
        resume_id=resume_id,
        skills=[] # Default empty
    )
    
    # Create User
    # Note: UserCreate expects 'password', but we are creating manually.
    # Repository `create_user` method takes `UserCreate` which performs hashing.
    # So we should pass the raw password to `UserCreate`.
    
    user_create = UserCreate(
        username=username,
        email=candidate_email,
        password=password,
        role="candidate",
        profile=profile
    )
    
    new_user = await repo.create_user(user_create)
    candidate_id = str(new_user.id)

    # Save resume to disk, parse text, and store resume + JD for question generation
    resume_text, resume_path = save_resume_and_extract_text(
        candidate_id, resume_id, resume_bytes, resume.content_type or ""
    )
    materials_coll = db[CANDIDATE_MATERIALS_COLLECTION]
    await materials_coll.update_one(
        {"candidate_id": candidate_id},
        {
            "$set": {
                "resume_text": resume_text,
                "jd_text": job_description or "",
                "resume_file_path": str(resume_path) if resume_path else None,
                "updated_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )

    # Send email to candidate
    await email_service.send_candidate_password_email(candidate_email, candidate_name, password)

    # Log credentials to terminal so admin can see them
    logger.info(
        "Candidate registered by admin — login credentials (also sent via email): "
        "username=%s, email=%s, password=%s",
        username, candidate_email, password,
    )
    print(
        "\n"
        "  --- New candidate credentials (also sent via email) ---\n"
        f"  Username: {username}\n"
        f"  Email:    {candidate_email}\n"
        f"  Password: {password}\n"
        "  ------------------------------------------------\n"
    )

    # Return response suitable for CandidateResponse
    # We need to map UserInDB to CandidateResponse
    return CandidateResponse(
        id=str(new_user.id),
        username=new_user.username,
        email=new_user.email,
        is_active=new_user.is_active,
        login_disabled=new_user.login_disabled,
        created_at=new_user.created_at,
        job_description=job_description or None 
        # Wait, Real backend stores JD in Candidate model. UserInDB doesn't have JD field.
        # We can just echo it back or ignore it since we are mocking.
        # Let's echo it back.
    )

@router.get("/admin/candidates", response_model=List[CandidateResponse])
async def get_all_candidates(
    current_admin: UserInDB = Depends(get_current_admin),
    db = Depends(get_database)
):
    repo = UserRepository(db)
    # We need a method in repo to specific roles? Or raw find.
    # Repository extraction:
    cursor = repo.collection.find({"role": "candidate"})
    candidates = []
    async for doc in cursor:
        # Map doc to CandidateResponse (use .get() so old docs missing email/username don't raise KeyError)
        c = CandidateResponse(
            id=str(doc["_id"]),
            username=doc.get("username", ""),
            email=doc.get("email", ""),
            is_active=doc.get("is_active", True),
            login_disabled=doc.get("login_disabled", False),
            created_at=doc.get("created_at", datetime.utcnow()),
            job_description="Mock JD"  # JD not stored in User model
        )
        candidates.append(c)
    return candidates

@router.post("/admin/candidates/{candidate_id}/toggle-login")
async def toggle_candidate_login(
    candidate_id: str, 
    current_admin: UserInDB = Depends(get_current_admin),
    db = Depends(get_database)
):
    repo = UserRepository(db)
    from bson import ObjectId
    try:
        oid = ObjectId(candidate_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    user = await repo.collection.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    if user["role"] != "candidate":
        raise HTTPException(status_code=400, detail="User is not a candidate")
    
    new_status = not user.get("login_disabled", False)
    
    await repo.collection.update_one(
        {"_id": oid},
        {"$set": {"login_disabled": new_status, "updated_at": datetime.utcnow()}}
    )
    
    return {
        "message": f"Candidate login has been {'disabled' if new_status else 'enabled'}",
        "candidate_id": str(user["_id"]),
        "email": user["email"],
        "login_disabled": new_status
    }
