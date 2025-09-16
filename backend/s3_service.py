import boto3
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, UploadFile
from config import get_settings
import logging
from io import BytesIO
from PIL import Image
import uuid
import os

logger = logging.getLogger(__name__)
settings = get_settings()

class S3Service:
    def __init__(self):
        if not all([settings.aws_access_key_id, settings.aws_secret_access_key, settings.aws_bucket_name]):
            logger.warning("AWS S3 credentials not configured. Image upload functionality will be disabled.")
            self.client = None
            self.bucket_name = None
        else:
            try:
                self.client = boto3.client(
                    's3',
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region
                )
                self.bucket_name = settings.aws_bucket_name
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                self.client = None
                self.bucket_name = None
    
    def _is_configured(self) -> bool:
        """Check if S3 service is properly configured"""
        return self.client is not None and self.bucket_name is not None
    
    def _generate_file_key(self, property_id: str, filename: str) -> str:
        """Generate a unique S3 key for the file"""
        file_extension = os.path.splitext(filename)[1].lower()
        unique_id = str(uuid.uuid4())
        return f"properties/{property_id}/images/{unique_id}{file_extension}"
    
    def _validate_image_file(self, file: UploadFile) -> bool:
        """Validate that the uploaded file is a valid image"""
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        max_size = 10 * 1024 * 1024  # 10MB
        
        # Check content type
        if file.content_type not in allowed_types:
            return False
        
        # Check file size
        if hasattr(file, 'size') and file.size > max_size:
            return False
        
        return True
    
    async def _process_image(self, file_content: bytes, max_width: int = 1920, quality: int = 85) -> bytes:
        """Process and optimize image"""
        try:
            with Image.open(BytesIO(file_content)) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large
                if img.width > max_width:
                    aspect_ratio = img.height / img.width
                    new_height = int(max_width * aspect_ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Save optimized image
                output = BytesIO()
                img.save(output, format='JPEG', quality=quality, optimize=True)
                return output.getvalue()
                
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            # Return original if processing fails
            return file_content
    
    async def upload_property_image(
        self, 
        property_id: str, 
        file: UploadFile,
        process_image: bool = True
    ) -> Optional[str]:
        """
        Upload a property image to S3
        
        Args:
            property_id: Property ID
            file: Uploaded file
            process_image: Whether to process/optimize the image
            
        Returns:
            S3 URL of the uploaded image or None if upload fails
        """
        if not self._is_configured():
            logger.warning("S3 service not configured. Cannot upload image.")
            return None
        
        try:
            # Validate file
            if not self._validate_image_file(file):
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid image file. Only JPEG, PNG, and WebP files under 10MB are allowed."
                )
            
            # Read file content
            file_content = await file.read()
            
            # Process image if requested
            if process_image:
                file_content = await self._process_image(file_content)
            
            # Generate S3 key
            s3_key = self._generate_file_key(property_id, file.filename or "image.jpg")
            
            # Upload to S3
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType='image/jpeg',
                Metadata={
                    'property_id': property_id,
                    'original_filename': file.filename or 'unknown'
                }
            )
            
            # Generate public URL
            url = f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{s3_key}"
            
            logger.info(f"Successfully uploaded image for property {property_id}: {s3_key}")
            return url
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to upload image for property {property_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Image upload failed: {str(e)}"
            )
    
    async def upload_multiple_property_images(
        self, 
        property_id: str, 
        files: List[UploadFile]
    ) -> List[str]:
        """
        Upload multiple property images to S3
        
        Args:
            property_id: Property ID
            files: List of uploaded files
            
        Returns:
            List of S3 URLs for successfully uploaded images
        """
        if not self._is_configured():
            logger.warning("S3 service not configured. Cannot upload images.")
            return []
        
        uploaded_urls = []
        failed_uploads = []
        
        for file in files:
            try:
                url = await self.upload_property_image(property_id, file)
                if url:
                    uploaded_urls.append(url)
                else:
                    failed_uploads.append(file.filename or "unknown")
            except Exception as e:
                logger.error(f"Failed to upload {file.filename}: {e}")
                failed_uploads.append(file.filename or "unknown")
        
        if failed_uploads:
            logger.warning(f"Failed to upload {len(failed_uploads)} images: {failed_uploads}")
        
        logger.info(f"Successfully uploaded {len(uploaded_urls)} images for property {property_id}")
        return uploaded_urls
    
    async def delete_property_image(self, image_url: str) -> bool:
        """
        Delete a property image from S3
        
        Args:
            image_url: S3 URL of the image to delete
            
        Returns:
            True if deletion was successful
        """
        if not self._is_configured():
            logger.warning("S3 service not configured. Cannot delete image.")
            return False
        
        try:
            # Extract S3 key from URL
            if self.bucket_name in image_url:
                s3_key = image_url.split(f"{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/")[1]
            else:
                logger.error(f"Invalid S3 URL format: {image_url}")
                return False
            
            # Delete from S3
            self.client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            
            logger.info(f"Successfully deleted image: {s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete image {image_url}: {e}")
            return False
    
    async def delete_property_images(self, property_id: str) -> bool:
        """
        Delete all images for a property
        
        Args:
            property_id: Property ID
            
        Returns:
            True if deletion was successful
        """
        if not self._is_configured():
            logger.warning("S3 service not configured. Cannot delete images.")
            return False
        
        try:
            # List all objects with the property prefix
            prefix = f"properties/{property_id}/images/"
            
            paginator = self.client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            objects_to_delete = []
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        objects_to_delete.append({'Key': obj['Key']})
            
            if objects_to_delete:
                # Delete objects in batch
                self.client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects_to_delete}
                )
                
                logger.info(f"Successfully deleted {len(objects_to_delete)} images for property {property_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete images for property {property_id}: {e}")
            return False
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for temporary access to an S3 object
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL or None if generation fails
        """
        if not self._is_configured():
            logger.warning("S3 service not configured. Cannot generate presigned URL.")
            return None
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned URL for {s3_key}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
            return None
    
    async def get_property_images(self, property_id: str) -> List[str]:
        """
        Get all image URLs for a property
        
        Args:
            property_id: Property ID
            
        Returns:
            List of image URLs
        """
        if not self._is_configured():
            logger.warning("S3 service not configured. Cannot retrieve image URLs.")
            return []
        
        try:
            prefix = f"properties/{property_id}/images/"
            
            paginator = self.client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            
            image_urls = []
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        url = f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{obj['Key']}"
                        image_urls.append(url)
            
            logger.info(f"Found {len(image_urls)} images for property {property_id}")
            return image_urls
            
        except Exception as e:
            logger.error(f"Failed to retrieve images for property {property_id}: {e}")
            return []

# Create a singleton instance
s3_service = S3Service()

# Dependency for FastAPI
def get_s3_service() -> S3Service:
    return s3_service