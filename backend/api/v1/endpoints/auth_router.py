from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from bson import ObjectId
from backend.core.config import settings
from backend.core.security import verify_password, get_password_hash, create_access_token
from backend.database.schema import Candidate, HR, DeliveryHead

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
    username: str
    password: str

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
        username: str = payload.get("sub")
        user_type: str = payload.get("user_type")
        if username is None or user_type != "candidate":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    candidate = await Candidate.find_one(Candidate.username == username)
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
        username: str = payload.get("sub")
        user_type: str = payload.get("user_type")
        if username is None or user_type != "hr":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    hr = await HR.find_one(HR.username == username)
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
        username: str = payload.get("sub")
        user_type: str = payload.get("user_type")
        if username is None or user_type != "delivery_head":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    dh = await DeliveryHead.find_one(DeliveryHead.username == username)
    if dh is None:
        raise credentials_exception
    if not dh.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return dh

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

# Login Routes
@router.post("/login/candidate", response_model=Token)
async def candidate_login(login_data: CandidateLoginRequest):
    """
    Candidate login endpoint - requires username and password
    """
    # Find candidate by username
    candidate = await Candidate.find_one(Candidate.username == login_data.username)
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, candidate.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check if candidate is active
    if not candidate.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": candidate.username,
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
            "username": candidate.username
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