from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import timedelta
from models import User, UserCreate, UserLogin, Token, APIResponse
from auth import (
    authenticate_user, create_user, create_access_token, 
    get_current_active_user, get_current_admin_user
)
from config import get_database, get_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()

@router.post("/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Register a new user"""
    try:
        user = await create_user(db, user_data)
        logger.info(f"New user registered: {user.email}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Login user and return access token"""
    try:
        user = await authenticate_user(db, user_credentials.email, user_credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(hours=settings.jwt_expiration_hours)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        logger.info(f"User logged in: {user.email}")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user

@router.get("/users", response_model=list[User])
async def get_all_users(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all users (admin only)"""
    try:
        users = []
        cursor = db.users.find({})
        
        async for user_doc in cursor:
            try:
                # Convert MongoDB document to User model
                user_doc["id"] = str(user_doc.pop("_id", user_doc.get("id")))
                # Remove sensitive information
                user_doc.pop("hashed_password", None)
                users.append(User(**user_doc))
            except Exception as e:
                logger.warning(f"Error processing user document: {e}")
                continue
        
        logger.info(f"Admin {current_user.email} retrieved {len(users)} users")
        return users
        
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.put("/users/{user_id}/promote", response_model=APIResponse)
async def promote_user_to_agent(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Promote a user to agent role (admin only)"""
    try:
        from auth import promote_user_to_agent as promote_user
        await promote_user(db, user_id, current_user)
        
        logger.info(f"User {user_id} promoted to agent by admin {current_user.email}")
        return APIResponse(
            success=True,
            message="User successfully promoted to agent"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error promoting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to promote user"
        )

@router.put("/users/{user_id}/deactivate", response_model=APIResponse)
async def deactivate_user_account(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Deactivate a user account (admin only)"""
    try:
        from auth import deactivate_user
        await deactivate_user(db, user_id, current_user)
        
        logger.info(f"User {user_id} deactivated by admin {current_user.email}")
        return APIResponse(
            success=True,
            message="User account successfully deactivated"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )