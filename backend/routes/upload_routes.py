from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List
from models import User, APIResponse, ImageUploadResponse
from s3_service import get_s3_service, S3Service
from auth import get_current_agent_or_admin_user
from config import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["file upload"])

@router.post("/property/{property_id}/images", response_model=ImageUploadResponse)
async def upload_property_images(
    property_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_agent_or_admin_user),
    s3_service: S3Service = Depends(get_s3_service),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Upload images for a property (agents and admins only)"""
    try:
        # Check if property exists and user has permission
        property_doc = await db.properties.find_one({"id": property_id})
        if not property_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Check permissions - agents can only upload to their own properties
        if (current_user.role == "agent" and 
            property_doc.get("agent_id") != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload images to your own properties"
            )
        
        # Validate file count
        if len(files) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 20 images allowed per upload"
            )
        
        # Upload images to S3
        uploaded_urls = await s3_service.upload_multiple_property_images(property_id, files)
        
        if not uploaded_urls:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload any images"
            )
        
        # Update property with new image URLs
        existing_images = property_doc.get("images", [])
        all_images = existing_images + uploaded_urls
        
        await db.properties.update_one(
            {"id": property_id},
            {"$set": {"images": all_images}}
        )
        
        logger.info(f"Uploaded {len(uploaded_urls)} images for property {property_id} by user {current_user.id}")
        
        return ImageUploadResponse(
            property_id=property_id,
            uploaded_images=uploaded_urls,
            message=f"Successfully uploaded {len(uploaded_urls)} images"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading images for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload images"
        )

@router.post("/property/{property_id}/image", response_model=dict)
async def upload_single_property_image(
    property_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_agent_or_admin_user),
    s3_service: S3Service = Depends(get_s3_service),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Upload a single image for a property"""
    try:
        # Check if property exists and user has permission
        property_doc = await db.properties.find_one({"id": property_id})
        if not property_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Check permissions
        if (current_user.role == "agent" and 
            property_doc.get("agent_id") != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload images to your own properties"
            )
        
        # Upload image to S3
        uploaded_url = await s3_service.upload_property_image(property_id, file)
        
        if not uploaded_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image"
            )
        
        # Update property with new image URL
        existing_images = property_doc.get("images", [])
        updated_images = existing_images + [uploaded_url]
        
        await db.properties.update_one(
            {"id": property_id},
            {"$set": {"images": updated_images}}
        )
        
        logger.info(f"Uploaded single image for property {property_id} by user {current_user.id}")
        
        return {
            "success": True,
            "message": "Image uploaded successfully",
            "image_url": uploaded_url,
            "property_id": property_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading single image for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )

@router.delete("/property/{property_id}/image", response_model=APIResponse)
async def delete_property_image(
    property_id: str,
    image_url: str = Form(...),
    current_user: User = Depends(get_current_agent_or_admin_user),
    s3_service: S3Service = Depends(get_s3_service),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete a specific image from a property"""
    try:
        # Check if property exists and user has permission
        property_doc = await db.properties.find_one({"id": property_id})
        if not property_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Check permissions
        if (current_user.role == "agent" and 
            property_doc.get("agent_id") != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete images from your own properties"
            )
        
        # Check if image exists in property
        existing_images = property_doc.get("images", [])
        if image_url not in existing_images:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found in property"
            )
        
        # Delete from S3
        deleted = await s3_service.delete_property_image(image_url)
        
        if deleted:
            # Remove from property images list
            updated_images = [img for img in existing_images if img != image_url]
            
            await db.properties.update_one(
                {"id": property_id},
                {"$set": {"images": updated_images}}
            )
            
            logger.info(f"Deleted image from property {property_id} by user {current_user.id}")
            
            return APIResponse(
                success=True,
                message="Image deleted successfully"
            )
        else:
            return APIResponse(
                success=False,
                message="Failed to delete image from storage"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image from property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image"
        )

@router.get("/property/{property_id}/images", response_model=List[str])
async def get_property_images(
    property_id: str,
    s3_service: S3Service = Depends(get_s3_service),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all image URLs for a property"""
    try:
        # Check if property exists
        property_doc = await db.properties.find_one({"id": property_id})
        if not property_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Return images from database (faster than S3 listing)
        images = property_doc.get("images", [])
        
        # Optionally, also get images directly from S3 to ensure sync
        # s3_images = await s3_service.get_property_images(property_id)
        
        return images
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving images for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve property images"
        )

@router.delete("/property/{property_id}/images/all", response_model=APIResponse)
async def delete_all_property_images(
    property_id: str,
    current_user: User = Depends(get_current_agent_or_admin_user),
    s3_service: S3Service = Depends(get_s3_service),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete all images for a property"""
    try:
        # Check if property exists and user has permission
        property_doc = await db.properties.find_one({"id": property_id})
        if not property_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        # Check permissions
        if (current_user.role == "agent" and 
            property_doc.get("agent_id") != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete images from your own properties"
            )
        
        # Delete all images from S3
        deleted = await s3_service.delete_property_images(property_id)
        
        # Clear images list in database
        await db.properties.update_one(
            {"id": property_id},
            {"$set": {"images": []}}
        )
        
        logger.info(f"Deleted all images for property {property_id} by user {current_user.id}")
        
        return APIResponse(
            success=True,
            message="All property images deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting all images for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete all property images"
        )