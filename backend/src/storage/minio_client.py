from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile
from io import BytesIO
import os
import logging
from typing import Optional
from datetime import timedelta
from PIL import Image
import uuid

# MinIO configuration from environment variables
# Use 'minio:9000' for Docker (backend connects via service name)
# For presigned URLs, we need 'localhost:9000' so browsers can access them
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_PRESIGNED_ENDPOINT = os.getenv("MINIO_PRESIGNED_ENDPOINT", "localhost:9000")  # For browser-accessible URLs
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "profile-pics")

# Initialize MinIO client (lazy initialization) - for operations
_minio_client: Optional[Minio] = None
# Separate client for presigned URLs (uses localhost so browsers can access)
_minio_presigned_client: Optional[Minio] = None


def get_minio_client() -> Minio:
    """Get or create MinIO client instance for operations."""
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        # Ensure bucket exists
        ensure_bucket_exists()
    return _minio_client


def get_minio_presigned_client() -> Minio:
    """Get or create MinIO client instance for presigned URL generation.
    Uses localhost:9000 for URL generation (browsers can access this)."""
    global _minio_presigned_client
    if _minio_presigned_client is None:
        # Use localhost:9000 for presigned URLs (browsers can access this)
        _minio_presigned_client = Minio(
            MINIO_PRESIGNED_ENDPOINT,  # localhost:9000
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
    return _minio_presigned_client


def ensure_bucket_exists():
    """Ensure the profile pictures bucket exists."""
    try:
        client = get_minio_client()
        if not client.bucket_exists(MINIO_BUCKET_NAME):
            client.make_bucket(MINIO_BUCKET_NAME)
            logging.info(f"Created bucket: {MINIO_BUCKET_NAME}")
        else:
            logging.info(f"Bucket {MINIO_BUCKET_NAME} already exists")
    except S3Error as e:
        logging.error(f"Error ensuring bucket exists: {e}")
        raise


async def upload_profile_picture(
    file: UploadFile,
    user_id: int,
    max_size_mb: int = 5,
    max_dimensions: tuple = (2000, 2000)
) -> str:
    """
    Upload a profile picture to MinIO.
    
    Args:
        file: The uploaded file
        user_id: The ID of the user
        max_size_mb: Maximum file size in MB
        max_dimensions: Maximum image dimensions (width, height)
    
    Returns:
        The object path/name in MinIO
    
    Raises:
        ValueError: If file is too large or invalid
        S3Error: If upload fails
    """
    # Validate file size
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    
    if file_size_mb > max_size_mb:
        raise ValueError(f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)")
    
    # Validate and process image
    try:
        image = Image.open(BytesIO(file_content))
        image_format = image.format.lower() if image.format else "jpeg"
        
        # Validate image format
        if image_format not in ["jpeg", "jpg", "png", "webp"]:
            raise ValueError(f"Unsupported image format: {image_format}. Supported formats: JPEG, PNG, WebP")
        
        # Resize if necessary
        if image.size[0] > max_dimensions[0] or image.size[1] > max_dimensions[1]:
            image.thumbnail(max_dimensions, Image.Resampling.LANCZOS)
            logging.info(f"Resized image from {image.size} to {max_dimensions}")
        
        # Convert to RGB if necessary (for JPEG)
        if image_format in ["jpeg", "jpg"] and image.mode != "RGB":
            image = image.convert("RGB")
        
        # Save processed image to bytes
        output = BytesIO()
        save_format = "JPEG" if image_format in ["jpeg", "jpg"] else image_format.upper()
        image.save(output, format=save_format, quality=85, optimize=True)
        output.seek(0)
        
        # Generate unique filename
        file_extension = "jpg" if image_format in ["jpeg", "jpg"] else image_format
        object_name = f"users/{user_id}/{uuid.uuid4()}.{file_extension}"
        
        # Upload to MinIO
        client = get_minio_client()
        output_bytes = output.getvalue()
        output.seek(0)
        client.put_object(
            MINIO_BUCKET_NAME,
            object_name,
            BytesIO(output_bytes),
            length=len(output_bytes),
            content_type=f"image/{image_format}"
        )
        
        logging.info(f"Successfully uploaded profile picture for user {user_id}: {object_name}")
        return object_name
        
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        raise ValueError(f"Invalid image file: {str(e)}")


def get_profile_picture_url(object_name: str, expires_seconds: int = 3600) -> str:
    """
    Get a presigned URL for a profile picture.
    
    Args:
        object_name: The object name/path in MinIO
        expires_seconds: URL expiration time in seconds (default: 1 hour)
    
    Returns:
        Presigned URL string
    
    Raises:
        Exception: If unable to generate URL
    """
    try:
        # Use minio:9000 for connection (backend can reach this)
        # Generate URL with minio:9000, then replace with localhost:9000 for browsers
        client = Minio(
            MINIO_ENDPOINT,  # minio:9000
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        expires = timedelta(seconds=expires_seconds)
        url = client.presigned_get_object(MINIO_BUCKET_NAME, object_name, expires=expires)
        # Replace minio:9000 with localhost:9000 for browser access
        url = url.replace("minio:9000", "localhost:9000")
        return url
    except S3Error as e:
        logging.error(f"S3Error generating presigned URL: {e}")
        raise Exception(f"MinIO error: {str(e)}")
    except Exception as e:
        error_msg = str(e)
        if "Failed to resolve" in error_msg or "NameResolutionError" in error_msg:
            logging.error(f"DNS resolution error connecting to MinIO at {MINIO_ENDPOINT}: {e}")
            raise Exception(f"Cannot connect to MinIO server at {MINIO_ENDPOINT}. Please check your network connection and MinIO configuration.")
        else:
            logging.error(f"Error generating presigned URL: {e}")
            raise Exception(f"Failed to generate profile picture URL: {str(e)}")


def delete_profile_picture(object_name: str) -> bool:
    """
    Delete a profile picture from MinIO.
    
    Args:
        object_name: The object name/path in MinIO
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_minio_client()
        client.remove_object(MINIO_BUCKET_NAME, object_name)
        logging.info(f"Successfully deleted profile picture: {object_name}")
        return True
    except S3Error as e:
        logging.error(f"Error deleting profile picture: {e}")
        return False


async def upload_post_image(
    file: UploadFile,
    post_id: int,
    user_id: int,
    max_size_mb: int = 10,
    max_dimensions: tuple = (1920, 1920)
) -> str:
    """
    Upload a post image to MinIO.
    
    Args:
        file: The uploaded file
        post_id: The ID of the post
        user_id: The ID of the user
        max_size_mb: Maximum file size in MB
        max_dimensions: Maximum image dimensions (width, height)
    
    Returns:
        The object path/name in MinIO
    
    Raises:
        ValueError: If file is too large or invalid
        S3Error: If upload fails
    """
    # Validate file size
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    
    if file_size_mb > max_size_mb:
        raise ValueError(f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)")
    
    # Validate and process image
    try:
        image = Image.open(BytesIO(file_content))
        image_format = image.format.lower() if image.format else "jpeg"
        
        # Validate image format
        if image_format not in ["jpeg", "jpg", "png", "webp"]:
            raise ValueError(f"Unsupported image format: {image_format}. Supported formats: JPEG, PNG, WebP")
        
        # Resize if necessary
        if image.size[0] > max_dimensions[0] or image.size[1] > max_dimensions[1]:
            image.thumbnail(max_dimensions, Image.Resampling.LANCZOS)
            logging.info(f"Resized image from {image.size} to {max_dimensions}")
        
        # Convert to RGB if necessary (for JPEG)
        if image_format in ["jpeg", "jpg"] and image.mode != "RGB":
            image = image.convert("RGB")
        
        # Save processed image to bytes
        output = BytesIO()
        save_format = "JPEG" if image_format in ["jpeg", "jpg"] else image_format.upper()
        image.save(output, format=save_format, quality=85, optimize=True)
        output.seek(0)
        
        # Generate unique filename
        file_extension = "jpg" if image_format in ["jpeg", "jpg"] else image_format
        object_name = f"posts/{user_id}/{post_id}/{uuid.uuid4()}.{file_extension}"
        
        # Upload to MinIO
        client = get_minio_client()
        output_bytes = output.getvalue()
        output.seek(0)
        client.put_object(
            MINIO_BUCKET_NAME,
            object_name,
            BytesIO(output_bytes),
            length=len(output_bytes),
            content_type=f"image/{image_format}"
        )
        
        logging.info(f"Successfully uploaded post image for post {post_id}: {object_name}")
        return object_name
        
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        raise ValueError(f"Invalid image file: {str(e)}")


def get_post_image_url(object_name: str, expires_seconds: int = 3600) -> str:
    """
    Get a presigned URL for a post image.
    
    Args:
        object_name: The object name/path in MinIO
        expires_seconds: URL expiration time in seconds (default: 1 hour)
    
    Returns:
        Presigned URL string
    
    Raises:
        Exception: If unable to generate URL
    """
    try:
        # Use minio:9000 for connection (backend can reach this)
        client = Minio(
            MINIO_ENDPOINT,  # minio:9000
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        expires = timedelta(seconds=expires_seconds)
        url = client.presigned_get_object(MINIO_BUCKET_NAME, object_name, expires=expires)
        # Replace minio:9000 with localhost:9000 for browser access
        url = url.replace("minio:9000", "localhost:9000")
        return url
    except S3Error as e:
        logging.error(f"S3Error generating presigned URL: {e}")
        raise Exception(f"MinIO error: {str(e)}")
    except Exception as e:
        error_msg = str(e)
        if "Failed to resolve" in error_msg or "NameResolutionError" in error_msg:
            logging.error(f"DNS resolution error connecting to MinIO at {MINIO_ENDPOINT}: {e}")
            raise Exception(f"Cannot connect to MinIO server at {MINIO_ENDPOINT}. Please check your network connection and MinIO configuration.")
        else:
            logging.error(f"Error generating presigned URL: {e}")
            raise Exception(f"Failed to generate post image URL: {str(e)}")


def delete_post_image(object_name: str) -> bool:
    """
    Delete a post image from MinIO.
    
    Args:
        object_name: The object name/path in MinIO
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_minio_client()
        client.remove_object(MINIO_BUCKET_NAME, object_name)
        logging.info(f"Successfully deleted post image: {object_name}")
        return True
    except S3Error as e:
        logging.error(f"Error deleting post image: {e}")
        return False

