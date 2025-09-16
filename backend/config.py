import os
from typing import Optional
from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    mongo_url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name: str = os.getenv("DB_NAME", "ror_stay_database")
    
    # CORS
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    
    # Authentication
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Email Integration (SendGrid)
    sendgrid_api_key: Optional[str] = os.getenv("SENDGRID_API_KEY")
    sender_email: Optional[str] = os.getenv("SENDER_EMAIL")
    
    # Google Maps API
    google_maps_api_key: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")
    
    # AWS S3 Configuration
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_bucket_name: Optional[str] = os.getenv("AWS_BUCKET_NAME")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    
    # Emergent LLM Key
    emergent_llm_key: Optional[str] = os.getenv("EMERGENT_LLM_KEY")
    
    # Application Settings
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings():
    return Settings()

# Database connection
def get_database():
    from motor.motor_asyncio import AsyncIOMotorClient
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]

# Utility functions
def get_cors_origins():
    settings = get_settings()
    if settings.cors_origins == "*":
        return ["*"]
    return [origin.strip() for origin in settings.cors_origins.split(",")]