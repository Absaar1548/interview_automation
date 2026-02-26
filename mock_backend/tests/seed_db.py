import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.security import get_password_hash
import uuid

DATABASE_URL = "postgresql+asyncpg://postgres:Password%401548@localhost:5432/interview_db"

async def seed():
    engine = create_async_engine(DATABASE_URL)
    admin_id = uuid.uuid4()
    admin_hashed_pw = get_password_hash("admin123")
    
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO users (id, username, email, role, hashed_password, is_active, login_disabled)
            VALUES (:id, 'admin', 'admin@example.com', 'ADMIN', :pw, true, false)
            ON CONFLICT DO NOTHING
        """), {"id": admin_id, "pw": admin_hashed_pw})
        
        await conn.execute(text("""
            INSERT INTO admin_profiles (id, user_id, first_name, last_name, department, designation)
            VALUES (:id, :user_id, 'Admin', 'User', 'HR', 'Recruiter')
            ON CONFLICT DO NOTHING
        """), {"id": uuid.uuid4(), "user_id": admin_id})

    print("Admin seeded")

if __name__ == "__main__":
    asyncio.run(seed())
