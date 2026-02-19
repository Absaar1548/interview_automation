# Database connection logic
# Placeholder for connection pool and session management
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from backend.core.config import settings
from backend.database.schema import Candidate, HR, DeliveryHead

class Database:
    client: AsyncIOMotorClient = None

database = Database()

async def connect_to_mongo():
    """Create database connection"""
    database.client = AsyncIOMotorClient(settings.DATABASE_URL)
    await init_beanie(
        database=database.client[settings.DATABASE_NAME],
        document_models=[Candidate, HR, DeliveryHead]
    )
    print("Connected to MongoDB Atlas")

async def close_mongo_connection():
    """Close database connection"""
    if database.client:
        database.client.close()
        print("Disconnected from MongoDB Atlas")

async def get_database():
    """Get database instance"""
    return database.client[settings.DATABASE_NAME]