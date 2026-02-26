"""
template_seed_service.py
------------------------
Idempotent seed function that ensures at least one active InterviewTemplate
exists in the database.

Called once during application startup (main.py lifespan).
Uses UnitOfWork — no direct session.commit() calls.
"""

import logging
from sqlalchemy import select, literal
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.sql.unit_of_work import UnitOfWork
from app.db.sql.models.interview_template import InterviewTemplate, TemplateQuestion

logger = logging.getLogger(__name__)


async def ensure_default_template_exists(session: AsyncSession) -> None:
    """
    Check if any active interview template exists.
    If none exist, insert a default template with 3 seed questions.

    Idempotent: safe to call on every startup.
    All writes go through UnitOfWork — commit is delegated to UoW.__aexit__.
    """
    async with UnitOfWork(session) as uow:
        # ── Optimised existence check: SELECT 1 LIMIT 1, no full object hydration ──
        stmt = (
            select(literal(1))
            .select_from(InterviewTemplate)
            .where(InterviewTemplate.is_active == True)
            .limit(1)
        )
        result = await uow.session.execute(stmt)
        already_exists = result.scalar() is not None

        if already_exists:
            logger.info(
                "[template_seed] Active template already exists. Skipping seed."
            )
            return

        logger.info(
            "[template_seed] No active templates found. Creating default template..."
        )

        # ── Create default template ──
        # total_duration_sec stored inside settings JSON (no schema migration needed)
        template = InterviewTemplate(
            title="Default Data Science Interview",
            description="Baseline template with coding + conversational questions",
            is_active=True,
            settings={"total_duration_sec": 3600},
        )
        uow.session.add(template)
        await uow.session.flush()  # materialise template.id for FK references

        # ── Seed questions — plain question_type values, no encoded strings ──
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

        # ── Commit is handled by UnitOfWork.__aexit__ — no direct commit() here ──
        logger.info(
            "[template_seed] Default template '%s' created successfully.",
            template.title,
        )
