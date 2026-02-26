import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.sql.unit_of_work import UnitOfWork
from app.db.sql.models.user import User, AdminProfile
from app.db.sql.enums import UserRole
from app.core.security import get_password_hash
from app.schemas.auth import AdminRegistrationRequest

class AdminAuthSQLService:
    @staticmethod
    async def register_admin(session: AsyncSession, request: AdminRegistrationRequest) -> User:
        async with UnitOfWork(session) as uow:
            # 1. Unique validations
            existing_user_by_email = await uow.users.get_by_email(request.email)
            if existing_user_by_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
                
            existing_user_by_username = await uow.users.get_by_username(request.username)
            if existing_user_by_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this username already exists"
                )

            # 2. Hash password securely
            hashed_password = get_password_hash(request.password)

            # 3. Create Admin Instance
            new_user = User(
                username=request.username,
                email=request.email,
                role=UserRole.ADMIN,
                hashed_password=hashed_password,
            )

            profile = AdminProfile(
                first_name=request.profile.first_name,
                last_name=request.profile.last_name,
                department=request.profile.department,
                designation=request.profile.designation
            )
            
            new_user.admin_profile = profile
            
            # 4. Attach to Unit of Work Layer
            uow.users.create_user(new_user)
            
            # Flush to hydrate DB ids for response
            await uow.flush()
            
            # 5. Commit naturally when escaping the context block
            return new_user
