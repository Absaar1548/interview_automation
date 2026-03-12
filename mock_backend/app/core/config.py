import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Postgres
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/interview_db")

    # LLM for question generation (OpenAI or Azure OpenAI)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "")  # e.g. Azure: https://xxx.openai.azure.com/
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # or gpt-4, etc.

    # Azure Container Instances for Code Execution
    AZURE_ACI_RESOURCE_GROUP: str = os.getenv("AZURE_ACI_RESOURCE_GROUP", "")
    AZURE_ACI_LOCATION: str = os.getenv("AZURE_ACI_LOCATION", "eastus")
    AZURE_SUBSCRIPTION_ID: str = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    AZURE_ACR_SERVER: str = os.getenv("AZURE_ACR_SERVER", "") # e.g. myregistry.azurecr.io
    AZURE_ACR_USERNAME: str = os.getenv("AZURE_ACR_USERNAME", "")
    AZURE_ACR_PASSWORD: str = os.getenv("AZURE_ACR_PASSWORD", "")

    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
 
settings = Settings()
