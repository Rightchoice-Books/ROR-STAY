from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from models import User, UserInDB, UserCreate, UserLogin, TokenData, UserRole, generate_id, get_current_timestamp
from config import get_settings, get_database
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
security = HTTPBearer()

settings = get_settings()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[UserInDB]:
    """Get user by email from database"""
    try:
        user_doc = await db.users.find_one({"email": email})
        if user_doc:
            # Convert MongoDB document to UserInDB model
            user_doc["id"] = str(user_doc.pop("_id", user_doc.get("id")))
            return UserInDB(**user_doc)
        return None
    except Exception as e:
        logger.error(f"Error fetching user by email {email}: {e}")
        return None

async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[User]:
    """Get user by ID from database"""
    try:
        user_doc = await db.users.find_one({"id": user_id})
        if user_doc:
            # Convert MongoDB document to User model
            user_doc["id"] = str(user_doc.pop("_id", user_doc.get("id")))
            # Remove sensitive fields
            user_doc.pop("hashed_password", None)
            return User(**user_doc)
        return None
    except Exception as e:
        logger.error(f"Error fetching user by ID {user_id}: {e}")
        return None

async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user with email and password"""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def create_user(db: AsyncIOMotorDatabase, user_data: UserCreate) -> User:
    """Create a new user"""
    try:
        # Check if user already exists
        existing_user = await get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user document
        hashed_password = get_password_hash(user_data.password)
        current_time = get_current_timestamp()
        
        user_doc = {
            "id": generate_id(),
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "phone": user_data.phone,
            "role": user_data.role,
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": current_time,
            "updated_at": current_time
        }
        
        # Insert into database
        result = await db.users.insert_one(user_doc)
        
        if result.inserted_id:
            # Return user without sensitive information
            user_doc.pop("hashed_password")
            return User(**user_doc)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> User:
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    
    # Convert to User model (without sensitive information)
    return User(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get the current user if they are an admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_current_agent_or_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get the current user if they are an agent or admin"""
    if current_user.role not in [UserRole.ADMIN, UserRole.AGENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Agent or Admin role required."
        )
    return current_user

# Utility functions for role checking
def is_admin(user: User) -> bool:
    """Check if user is an admin"""
    return user.role == UserRole.ADMIN

def is_agent(user: User) -> bool:
    """Check if user is an agent"""
    return user.role == UserRole.AGENT

def is_agent_or_admin(user: User) -> bool:
    """Check if user is an agent or admin"""
    return user.role in [UserRole.ADMIN, UserRole.AGENT]

# Admin functions
async def promote_user_to_agent(db: AsyncIOMotorDatabase, user_id: str, admin_user: User) -> User:
    """Promote a user to agent role (admin only)"""
    if not is_admin(admin_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can promote users"
        )
    
    try:
        result = await db.users.update_one(
            {"id": user_id},
            {
                "$set": {
                    "role": UserRole.AGENT,
                    "updated_at": get_current_timestamp()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Return updated user
        updated_user = await get_user_by_id(db, user_id)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated user"
            )
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error promoting user to agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to promote user"
        )

async def deactivate_user(db: AsyncIOMotorDatabase, user_id: str, admin_user: User) -> User:
    """Deactivate a user (admin only)"""
    if not is_admin(admin_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can deactivate users"
        )
    
    try:
        result = await db.users.update_one(
            {"id": user_id},
            {
                "$set": {
                    "is_active": False,
                    "updated_at": get_current_timestamp()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Return updated user
        updated_user = await get_user_by_id(db, user_id)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated user"
            )
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )