import os
from pathlib import Path
from dotenv import load_dotenv

# Get the directory where this config file is located (backend/core)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from the backend directory
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    """
    Application configuration settings.
    """
    PROJECT_NAME = "AI Interview Automation"
    API_V1_STR = "/api/v1"
    
    # Security settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # MongoDB Atlas settings
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
    )
    DATABASE_NAME = os.getenv("DATABASE_NAME", "interview_automation")

settings = Settings()