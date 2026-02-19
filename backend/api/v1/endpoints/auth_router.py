from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from bson import ObjectId
import secrets
import os
from backend.core.config import settings
from pathlib import Path
from backend.core.security import verify_password, get_password_hash, create_access_token
from backend.database.schema import Candidate, HR, DeliveryHead
from backend.services.email_service import email_service

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/candidate")

# Pydantic Models for Registration Requests
class CandidateRegisterRequest(BaseModel):
    username: str
    password: str

class HRRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class DeliveryHeadRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

# Pydantic Models for Login Requests
class CandidateLoginRequest(BaseModel):
    email: EmailStr
    password: str

class AdminLoginRequest(BaseModel):
    email: EmailStr
    
    @field_validator('email')
    @classmethod
    def validate_coforge_email(cls, v):
        if not v.endswith('@coforge.com'):
            raise ValueError('Admin email must be from @coforge.com domain')
        return v

class HRLoginRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class DeliveryHeadLoginRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

# Pydantic Models for Responses
class CandidateResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    created_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        from_attributes = True

class HRResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    created_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        from_attributes = True

class DeliveryHeadResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    created_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_objectid_to_str(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_type: str
    user_data: dict

class TokenData(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    user_type: Optional[str] = None

# Helper Functions
async def get_current_candidate(token: str = Depends(oauth2_scheme)):
    """Get current authenticated candidate from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        user_type: str = payload.get("user_type")
        if email is None or user_type != "candidate":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    candidate = await Candidate.find_one(Candidate.email == email)
    if candidate is None:
        raise credentials_exception
    if not candidate.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return candidate

async def get_current_hr(token: str = Depends(oauth2_scheme)):
    """Get current authenticated HR from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        user_type: str = payload.get("user_type")
        if email is None or user_type != "hr":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    hr = await HR.find_one(HR.email == email)
    if hr is None:
        raise credentials_exception
    if not hr.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return hr

async def get_current_delivery_head(token: str = Depends(oauth2_scheme)):
    """Get current authenticated Delivery Head from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        user_type: str = payload.get("user_type")
        if email is None or user_type != "delivery_head":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    dh = await DeliveryHead.find_one(DeliveryHead.email == email)
    if dh is None:
        raise credentials_exception
    if not dh.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return dh

async def get_current_admin(token: str = Depends(oauth2_scheme)):
    """Get current authenticated admin from token - no database validation"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        user_type: str = payload.get("user_type")
        if email is None or user_type != "admin":
            raise credentials_exception
        # Validate email domain
        if not email.endswith("@coforge.com"):
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Return a simple dict with email info (no database lookup)
    return {"email": email, "user_type": user_type}

# Registration Routes
@router.post("/register/candidate", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def register_candidate(register_data: CandidateRegisterRequest):
    """
    Register a new candidate - requires username and password
    """
    # Check if candidate already exists
    existing_candidate = await Candidate.find_one(Candidate.username == register_data.username)
    if existing_candidate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Hash password and create new candidate
    hashed_password = get_password_hash(register_data.password)
    new_candidate = Candidate(
        username=register_data.username,
        hashed_password=hashed_password,
        is_active=True
    )
    await new_candidate.insert()
    return new_candidate

@router.post("/register/hr", response_model=HRResponse, status_code=status.HTTP_201_CREATED)
async def register_hr(register_data: HRRegisterRequest):
    """
    Register a new HR user - requires username, email, and password
    """
    # Check if HR user already exists by username
    existing_hr_username = await HR.find_one(HR.username == register_data.username)
    if existing_hr_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if HR user already exists by email
    existing_hr_email = await HR.find_one(HR.email == register_data.email)
    if existing_hr_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create new HR user
    hashed_password = get_password_hash(register_data.password)
    new_hr = HR(
        username=register_data.username,
        email=register_data.email,
        hashed_password=hashed_password,
        is_active=True
    )
    await new_hr.insert()
    return new_hr

@router.post("/register/delivery-head", response_model=DeliveryHeadResponse, status_code=status.HTTP_201_CREATED)
async def register_delivery_head(register_data: DeliveryHeadRegisterRequest):
    """
    Register a new Delivery Head - requires username, email, and password
    """
    # Check if Delivery Head already exists by username
    existing_dh_username = await DeliveryHead.find_one(DeliveryHead.username == register_data.username)
    if existing_dh_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if Delivery Head already exists by email
    existing_dh_email = await DeliveryHead.find_one(DeliveryHead.email == register_data.email)
    if existing_dh_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create new Delivery Head
    hashed_password = get_password_hash(register_data.password)
    new_dh = DeliveryHead(
        username=register_data.username,
        email=register_data.email,
        hashed_password=hashed_password,
        is_active=True
    )
    await new_dh.insert()
    return new_dh

@router.post("/admin/register-candidate", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def admin_register_candidate(
    current_admin = Depends(get_current_admin),
    candidate_name: str = Form(...),
    candidate_email: EmailStr = Form(...),
    job_description: str = Form(...),
    resume: UploadFile = File(...)
):
    """
    Admin endpoint to register a new candidate with job description and resume.
    Generates a random password and sends it via email.
    """
    # Check if candidate already exists
    existing_candidate = await Candidate.find_one(Candidate.email == candidate_email)
    if existing_candidate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate with this email already exists"
        )
    
    # Generate random password
    password = secrets.token_urlsafe(12)
    hashed_password = get_password_hash(password)
    
    # Create uploads directory if it doesn't exist
    # Get backend directory (parent of api directory)
    backend_dir = Path(__file__).resolve().parent.parent.parent.parent
    upload_dir = backend_dir / "uploads" / "resumes"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save resume file
    file_extension = os.path.splitext(resume.filename)[1]
    resume_filename = f"{candidate_email.replace('@', '_at_')}_{secrets.token_hex(8)}{file_extension}"
    resume_path = upload_dir / resume_filename
    
    with open(resume_path, "wb") as buffer:
        content = await resume.read()
        buffer.write(content)
    
    # Store relative path in database
    resume_path_str = str(resume_path.relative_to(backend_dir))
    
    # Create username from email (before @)
    username = candidate_email.split('@')[0]
    
    # Create new candidate
    new_candidate = Candidate(
        username=username,
        email=candidate_email,
        hashed_password=hashed_password,
        job_description=job_description,
        resume_path=resume_path_str,
        is_active=True
    )
    await new_candidate.insert()
    
    # Send password email to candidate
    await email_service.send_candidate_password_email(
        candidate_email=candidate_email,
        candidate_name=candidate_name,
        password=password
    )
    
    return new_candidate

# Login Routes
@router.post("/login/candidate", response_model=Token)
async def candidate_login(login_data: CandidateLoginRequest):
    """
    Candidate login endpoint - requires email and password
    """
    # Find candidate by email
    candidate = await Candidate.find_one(Candidate.email == login_data.email)
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, candidate.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if candidate is active
    if not candidate.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Check if login is disabled
    if candidate.login_disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Login has been disabled for this account. Please contact the administrator."
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": candidate.email,
            "user_type": "candidate"
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_type": "candidate",
        "user_data": {
            "id": str(candidate.id),
            "username": candidate.username,
            "email": candidate.email
        }
    }

@router.post("/login/admin", response_model=Token)
async def admin_login(login_data: AdminLoginRequest):
    """
    Admin login endpoint - requires email only (must be @coforge.com)
    No database validation, just checks email domain
    """
    # Email domain validation is already done in AdminLoginRequest validator
    # Extract username from email (part before @)
    username = login_data.email.split('@')[0]
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": login_data.email,
            "user_type": "admin"
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_type": "admin",
        "user_data": {
            "id": login_data.email,  # Use email as ID since no database record
            "username": username,
            "email": login_data.email
        }
    }

@router.post("/login/hr", response_model=Token)
async def hr_login(login_data: HRLoginRequest):
    """
    HR login endpoint - requires username, email, and password
    """
    # Find HR by username and email
    hr = await HR.find_one(
        HR.username == login_data.username,
        HR.email == login_data.email
    )
    
    if not hr:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username, email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, hr.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username, email or password"
        )
    
    # Check if HR is active
    if not hr.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": hr.username,
            "email": hr.email,
            "user_type": "hr"
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_type": "hr",
        "user_data": {
            "id": str(hr.id),
            "username": hr.username,
            "email": hr.email
        }
    }

@router.post("/login/delivery-head", response_model=Token)
async def delivery_head_login(login_data: DeliveryHeadLoginRequest):
    """
    Delivery Head login endpoint - requires username, email, and password
    """
    # Find Delivery Head by username and email
    dh = await DeliveryHead.find_one(
        DeliveryHead.username == login_data.username,
        DeliveryHead.email == login_data.email
    )
    
    if not dh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username, email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, dh.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username, email or password"
        )
    
    # Check if Delivery Head is active
    if not dh.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": dh.username,
            "email": dh.email,
            "user_type": "delivery_head"
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_type": "delivery_head",
        "user_data": {
            "id": str(dh.id),
            "username": dh.username,
            "email": dh.email
        }
    }

@router.get("/me/candidate", response_model=CandidateResponse)
async def get_current_candidate_info(current_candidate: Candidate = Depends(get_current_candidate)):
    """Get current authenticated candidate information"""
    return current_candidate

@router.get("/me/hr", response_model=HRResponse)
async def get_current_hr_info(current_hr: HR = Depends(get_current_hr)):
    """Get current authenticated HR information"""
    return current_hr

@router.get("/me/delivery-head", response_model=DeliveryHeadResponse)
async def get_current_dh_info(current_dh: DeliveryHead = Depends(get_current_delivery_head)):
    """Get current authenticated Delivery Head information"""
    return current_dh

@router.post("/logout/candidate")
async def candidate_logout(current_candidate: Candidate = Depends(get_current_candidate)):
    """Candidate logout endpoint"""
    return {"message": "Successfully logged out"}

@router.post("/logout/hr")
async def hr_logout(current_hr: HR = Depends(get_current_hr)):
    """HR logout endpoint"""
    return {"message": "Successfully logged out"}

@router.post("/logout/delivery-head")
async def delivery_head_logout(current_dh: DeliveryHead = Depends(get_current_delivery_head)):
    """Delivery Head logout endpoint"""
    return {"message": "Successfully logged out"}

# Admin endpoints for candidate management
@router.get("/admin/candidates")
async def get_all_candidates(current_admin = Depends(get_current_admin)):
    """
    Get all registered candidates (admin only)
    """
    # Use raw MongoDB query to handle old records that might be missing email field
    from backend.database.connection import get_database
    db = await get_database()
    candidates_collection = db.candidates
    
    candidates_list = []
    async for doc in candidates_collection.find({}):
        # Skip candidates without email field (old records)
        if 'email' not in doc or not doc.get('email'):
            continue
            
        candidates_list.append({
            "id": str(doc.get('_id', '')),
            "username": doc.get('username', 'N/A'),
            "email": doc.get('email', ''),
            "is_active": doc.get('is_active', True),
            "login_disabled": doc.get('login_disabled', False),
            "created_at": doc.get('created_at'),
            "job_description": (
                doc.get('job_description', '')[:100] + "..." 
                if doc.get('job_description') and len(doc.get('job_description', '')) > 100 
                else doc.get('job_description')
            )
        })
    
    return candidates_list

@router.post("/admin/candidates/{candidate_id}/toggle-login")
async def toggle_candidate_login(candidate_id: str, current_admin = Depends(get_current_admin)):
    """
    Toggle candidate login status (disable/enable) - admin only
    """
    try:
        candidate = await Candidate.get(candidate_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    # Toggle login_disabled status
    candidate.login_disabled = not candidate.login_disabled
    candidate.updated_at = datetime.utcnow()
    await candidate.save()
    
    return {
        "message": f"Candidate login has been {'disabled' if candidate.login_disabled else 'enabled'}",
        "candidate_id": str(candidate.id),
        "email": candidate.email,
        "login_disabled": candidate.login_disabled
    }