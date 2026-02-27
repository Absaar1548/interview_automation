import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Support both DATABASE_URL/MONGODB_URL and DATABASE_NAME/DB_NAME for .env compatibility
MONGODB_URL = os.getenv("DATABASE_URL") or os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DATABASE_NAME") or os.getenv("DB_NAME", "interview_automation")

class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(MONGODB_URL)
    logger.info("Connected to MongoDB successfully")

async def close_mongo_connection():
    if db.client:
        db.client.close()
        logger.info("Closed MongoDB connection")

def get_database():
    return db.client[DB_NAME]
