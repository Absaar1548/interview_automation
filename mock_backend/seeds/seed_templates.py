import logging
from sqlalchemy import select, literal
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sql.models.interview_template import InterviewTemplate, TemplateQuestion
from app.db.sql.models.question import Question, CategoryEnum, DifficultyEnum

logger = logging.getLogger(__name__)

async def seed_templates(session: AsyncSession):
    """Seed default interview templates if none exist."""
    logger.info("Checking for existing interview templates...")
    
    stmt = (
        select(literal(1))
        .select_from(InterviewTemplate)
        .where(InterviewTemplate.is_active == True)
        .limit(1)
    )
    result = await session.execute(stmt)
    already_exists = result.scalar() is not None

    if already_exists:
        logger.info("[template_seed] Active template already exists. Checking for Default Rule Template...")
    
    # 1. Ensure a rule-based template exists
    rule_stmt = select(InterviewTemplate).where(InterviewTemplate.title == "Default Rule Template")
    rule_res = await session.execute(rule_stmt)
    if not rule_res.scalar_one_or_none():
        logger.info("[template_seed] Creating 'Default Rule Template'...")
        rule_template = InterviewTemplate(
            title="Default Rule Template",
            description="Automatic question selection based on complexity",
            is_active=True,
            is_rule_based=True,
            settings={
                "difficulty_distribution": {
                    "EASY": 2,
                    "MEDIUM": 2,
                    "HARD": 1
                }
            }
        )
        session.add(rule_template)
        await session.flush()

    if already_exists:
        return

    logger.info("[OK] Template seeding check completed.")
