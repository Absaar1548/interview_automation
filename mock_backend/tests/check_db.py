import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:Password%401548@localhost:5432/interview_db"

async def main():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT id, username, email, role FROM users"))
        for row in result:
            print(f"User: {row}")

if __name__ == "__main__":
    asyncio.run(main())
