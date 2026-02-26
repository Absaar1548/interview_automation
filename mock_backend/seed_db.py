import asyncio
import subprocess
import sys
import uuid

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Use the same settings as the application so we always target the correct DB.
from app.core.config import settings
from app.core.security import get_password_hash


def run_migrations():
    """Run Alembic migrations to ensure all tables exist before seeding."""
    print(f"Target database : {settings.DATABASE_URL}")
    print("Running Alembic migrations...")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    # Alembic writes INFO logs to stderr; merge both for display.
    output = (result.stdout + result.stderr).strip()
    if output:
        print(output)
    if result.returncode != 0:
        print("Migration FAILED — aborting seed.")
        sys.exit(1)
    print("Migrations applied successfully.\n")


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    admin_hashed_pw = get_password_hash("admin")

    async with engine.begin() as conn:
        # Seed admin user (skip if already exists)
        await conn.execute(
            text("""
                INSERT INTO users (id, username, email, role, hashed_password, is_active, login_disabled)
                VALUES (:id, 'admin', 'admin@example.com', 'ADMIN', :pw, true, false)
                ON CONFLICT (username) DO UPDATE SET hashed_password = EXCLUDED.hashed_password
            """),
            {"id": uuid.uuid4(), "pw": admin_hashed_pw},
        )

        # Always look up the existing admin to avoid FK issues on re-seed
        result = await conn.execute(
            text("SELECT id FROM users WHERE username = 'admin'")
        )
        admin_id = result.scalar()

        # Seed admin profile (skip if already exists)
        await conn.execute(
            text("""
                INSERT INTO admin_profiles (id, user_id, first_name, last_name, department, designation)
                VALUES (:id, :user_id, 'Admin', 'User', 'HR', 'Recruiter')
                ON CONFLICT (user_id) DO NOTHING
            """),
            {"id": uuid.uuid4(), "user_id": admin_id},
        )

    print("[OK] Admin user seeded successfully.")
    print("   Username : admin")
    print("   Password : admin")
    print("   Email    : admin@example.com")
    await engine.dispose()


if __name__ == "__main__":
    run_migrations()
    asyncio.run(seed())
