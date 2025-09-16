from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
import uuid
from datetime import datetime

# Import configuration
from config import get_settings, get_cors_origins

# Import routes
from routes.auth_routes import router as auth_router
from routes.property_routes import router as property_router
from routes.contact_routes import router as contact_router
from routes.upload_routes import router as upload_router
from routes.maps_routes import router as maps_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# MongoDB connection
client = AsyncIOMotorClient(settings.mongo_url)
db = client[settings.db_name]

# Create the main app
app = FastAPI(
    title="ROR STAY Real Estate API",
    description="A comprehensive real estate platform API with property management, user authentication, and third-party integrations.",
    version="1.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models for basic status endpoints
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Basic status endpoints
@api_router.get("/")
async def root():
    return {
        "message": "Welcome to ROR STAY Real Estate API",
        "version": "1.0.0",
        "status": "running"
    }

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "services": {
            "email": settings.sendgrid_api_key is not None,
            "maps": settings.google_maps_api_key is not None,
            "s3": all([settings.aws_access_key_id, settings.aws_secret_access_key, settings.aws_bucket_name])
        }
    }

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include all route modules
api_router.include_router(auth_router)
api_router.include_router(property_router)
api_router.include_router(contact_router)
api_router.include_router(upload_router)
api_router.include_router(maps_router)

# Include the main API router in the app
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=get_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "ROR STAY Real Estate Platform",
        "api_docs": "/docs",
        "api_version": "v1",
        "endpoints": {
            "auth": "/api/auth",
            "properties": "/api/properties", 
            "contact": "/api/contact",
            "upload": "/api/upload",
            "maps": "/api/maps"
        }
    }

# Startup and shutdown events
@app.on_event("startup")
async def startup_db_client():
    logger.info("Starting ROR STAY Real Estate API")
    logger.info(f"Database: {settings.db_name}")
    logger.info(f"Environment: {settings.environment}")
    
    # Test database connection
    try:
        await db.command("ping")
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("Shutting down ROR STAY Real Estate API")
    client.close()
