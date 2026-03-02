import asyncio
import subprocess
import sys
import uuid

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text, select, literal

# Use the same settings as the application so we always target the correct DB.
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.sql.unit_of_work import UnitOfWork
from app.db.sql.models.interview_template import InterviewTemplate, TemplateQuestion


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

    print("Checking for existing interview templates...")
    async with AsyncSession(engine) as session:
        async with UnitOfWork(session) as uow:
            stmt = (
                select(literal(1))
                .select_from(InterviewTemplate)
                .where(InterviewTemplate.is_active == True)
                .limit(1)
            )
            result = await uow.session.execute(stmt)
            already_exists = result.scalar() is not None

            if already_exists:
                print("[template_seed] Active template already exists. Skipping seed.")
            else:
                print("[template_seed] No active templates found. Creating default template...")
                template = InterviewTemplate(
                    title="Default Data Science Interview",
                    description="Baseline template with coding + conversational questions",
                    is_active=True,
                    settings={"total_duration_sec": 3600},
                )
                uow.session.add(template)
                await uow.session.flush()

                questions = [
                    TemplateQuestion(
                        template_id=template.id,
                        question_text="Explain a machine learning project you worked on.",
                        question_type="CONVERSATIONAL",
                        time_limit_sec=120,
                        order=1,
                    ),
                    TemplateQuestion(
                        template_id=template.id,
                        question_text="Write a SQL query to find the second highest salary.",
                        question_type="CODING",
                        time_limit_sec=300,
                        order=2,
                    ),
                    TemplateQuestion(
                        template_id=template.id,
                        question_text="How do you handle model overfitting?",
                        question_type="CONVERSATIONAL",
                        time_limit_sec=120,
                        order=3,
                    ),
                ]
                uow.session.add_all(questions)
                print("[template_seed] Default template created successfully.")

    await engine.dispose()


if __name__ == "__main__":
    run_migrations()
    asyncio.run(seed())
