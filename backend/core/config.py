import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AI Interview Automation"
    PROJECT_VERSION: str = "1.0.0"
    
    # Database
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb+srv://maif95689_db_user:NIBeARXXpHW6Dq0G@cluster0.qsdaad6.mongodb.net/?appName=Cluster0")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "interview_db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-it")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()
