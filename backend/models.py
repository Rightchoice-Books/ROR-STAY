from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# Enums
class PropertyType(str, Enum):
    HOUSE = "house"
    APARTMENT = "apartment"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    COMMERCIAL = "commercial"

class PropertyStatus(str, Enum):
    AVAILABLE = "available"
    SOLD = "sold"
    PENDING = "pending"
    OFF_MARKET = "off_market"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    AGENT = "agent"

class InquiryStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    CLOSED = "closed"

# Base Models
class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    
    @validator('latitude', 'longitude')
    def validate_coordinates(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Coordinates must be numeric')
        return float(v)

class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "United States"
    full_address: Optional[str] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.full_address:
            self.full_address = f"{self.street}, {self.city}, {self.state} {self.zip_code}"

# User Models
class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str

# Property Models
class PropertyBase(BaseModel):
    title: str
    property_type: PropertyType
    status: PropertyStatus
    price: int = Field(..., gt=0, description="Property price in USD")
    bedrooms: Optional[int] = Field(None, ge=0, description="Number of bedrooms")
    bathrooms: Optional[float] = Field(None, ge=0, description="Number of bathrooms")
    square_feet: Optional[int] = Field(None, gt=0, description="Property size in square feet")
    description: Optional[str] = None
    features: List[str] = []
    images: List[str] = []

class PropertyCreate(PropertyBase):
    address: Address
    coordinates: Optional[Coordinates] = None
    agent_id: Optional[str] = None

class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    property_type: Optional[PropertyType] = None
    status: Optional[PropertyStatus] = None
    price: Optional[int] = Field(None, gt=0)
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[float] = Field(None, ge=0)
    square_feet: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None
    features: Optional[List[str]] = None
    images: Optional[List[str]] = None
    address: Optional[Address] = None
    coordinates: Optional[Coordinates] = None

class Property(PropertyBase):
    id: str
    address: Address
    coordinates: Coordinates
    created_at: datetime
    updated_at: datetime
    agent_id: Optional[str] = None
    
    class Config:
        from_attributes = True

# Search and Filter Models
class MapBounds(BaseModel):
    northeast: Coordinates
    southwest: Coordinates
    
    @validator('northeast', 'southwest')
    def validate_bounds(cls, v, values):
        if 'northeast' in values and 'southwest' in values:
            ne = values.get('northeast', v)
            sw = values.get('southwest', v)
            if isinstance(ne, Coordinates) and isinstance(sw, Coordinates):
                if ne.latitude <= sw.latitude or ne.longitude <= sw.longitude:
                    raise ValueError('Northeast coordinate must be greater than southwest')
        return v

class PropertySearchFilters(BaseModel):
    bounds: Optional[MapBounds] = None
    property_types: List[PropertyType] = []
    min_price: Optional[int] = Field(None, ge=0)
    max_price: Optional[int] = Field(None, ge=0)
    min_bedrooms: Optional[int] = Field(None, ge=0)
    max_bedrooms: Optional[int] = Field(None, ge=0)
    min_bathrooms: Optional[float] = Field(None, ge=0)
    max_bathrooms: Optional[float] = Field(None, ge=0)
    min_square_feet: Optional[int] = Field(None, gt=0)
    max_square_feet: Optional[int] = Field(None, gt=0)
    status: List[PropertyStatus] = [PropertyStatus.AVAILABLE]
    
    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('Max price must be greater than min price')
        return v

# Contact and Inquiry Models
class ContactSubmission(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    message: str
    property_id: Optional[str] = None

class ContactSubmissionResponse(BaseModel):
    id: str
    status: str = "received"
    message: str = "Thank you for your message. We'll get back to you soon!"

class InquiryBase(BaseModel):
    property_id: str
    user_id: str
    message: str
    contact_method: str = "email"  # email, phone, in-person

class InquiryCreate(InquiryBase):
    pass

class Inquiry(InquiryBase):
    id: str
    status: InquiryStatus = InquiryStatus.NEW
    created_at: datetime
    updated_at: datetime
    response: Optional[str] = None
    
    class Config:
        from_attributes = True

# Authentication Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Image Upload Models
class ImageUpload(BaseModel):
    property_id: str
    image_urls: List[str]

class ImageUploadResponse(BaseModel):
    property_id: str
    uploaded_images: List[str]
    message: str

# API Response Models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    total_pages: int

# Email Models
class EmailNotification(BaseModel):
    to_email: str
    subject: str
    content: str
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None

# Static helper functions
def generate_id() -> str:
    """Generate a unique ID for database records"""
    return str(uuid.uuid4())

def get_current_timestamp() -> datetime:
    """Get current UTC timestamp"""
    return datetime.utcnow()