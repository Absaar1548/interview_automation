"""
seed.py — Application startup data seeding
-------------------------------------------
Idempotent seed functions that run on FastAPI startup.
They check before inserting — safe to re-run on every restart.
"""

import logging
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


async def seed_interview_templates(db: AsyncIOMotorDatabase) -> None:
    """
    Inserts one default interview template if no active templates exist.

    Idempotent: does nothing when at least one active template is found.
    """
    collection = db["interview_templates"]

    count = await collection.count_documents({"is_active": True})

    if count > 0:
        logger.info("Interview templates already exist. Skipping seed.")
        return

    default_template = {
        "_id": ObjectId(),
        "name": "Default Technical Round",
        "description": "Auto-seeded default template for technical screening.",
        "created_by": ObjectId(),          # placeholder admin ObjectId
        "questions": [],
        "total_duration_sec": 1800,        # 30 minutes
        "is_active": True,
        "created_at": datetime.utcnow(),
    }

    await collection.insert_one(default_template)
    logger.info("Default interview template seeded.")
