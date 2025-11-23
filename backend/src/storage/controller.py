from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from ..database.core import DbSession
from ..users import service as user_service
from ..posts.service import PostService
from ..exceptions import PostNotFoundError
from .minio_client import get_minio_client
from minio.error import S3Error
import logging
import os

router = APIRouter(
    prefix="/storage",
    tags=["storage"]
)

MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "profile-pics")


@router.get("/users/{user_id}/profile-picture")
async def get_profile_picture_proxy(
    user_id: int,
    db: DbSession
):
    """Proxy endpoint to serve profile pictures from MinIO (bypasses CORS)."""
    try:
        # Get user to find profile picture object name
        user = await user_service.get_user_by_id(db, user_id)
        
        if not user or not user.profile_picture_url:
            raise HTTPException(
                status_code=404,
                detail="Profile picture not found"
            )
        
        # Get object from MinIO
        client = get_minio_client()
        try:
            obj = client.get_object(MINIO_BUCKET_NAME, user.profile_picture_url)
            # Determine media type from file extension
            file_ext = user.profile_picture_url.split('.')[-1].lower()
            media_type_map = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'webp': 'image/webp',
                'gif': 'image/gif'
            }
            media_type = media_type_map.get(file_ext, 'image/jpeg')
            return StreamingResponse(
                obj,
                media_type=media_type
            )
        except S3Error as e:
            logging.error(f"MinIO error fetching profile picture: {e}")
            raise HTTPException(
                status_code=404,
                detail="Profile picture not found in storage"
            )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching profile picture: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch profile picture: {str(e)}"
        )


@router.get("/posts/{post_id}/image")
async def get_post_image_proxy(
    post_id: int,
    db: DbSession
):
    """Proxy endpoint to serve post images from MinIO (bypasses CORS)."""
    try:
        # Get post to find image object name
        service = PostService(db)
        try:
            post = await service.get_post(post_id)
        except PostNotFoundError:
            raise HTTPException(
                status_code=404,
                detail="Post not found"
            )
        
        if not post.image_url:
            raise HTTPException(
                status_code=404,
                detail="Post image not found"
            )
        
        # Get object from MinIO
        client = get_minio_client()
        try:
            obj = client.get_object(MINIO_BUCKET_NAME, post.image_url)
            # Determine media type from file extension
            file_ext = post.image_url.split('.')[-1].lower()
            media_type_map = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'webp': 'image/webp',
                'gif': 'image/gif'
            }
            media_type = media_type_map.get(file_ext, 'image/jpeg')
            return StreamingResponse(
                obj,
                media_type=media_type
            )
        except S3Error as e:
            logging.error(f"MinIO error fetching post image: {e}")
            raise HTTPException(
                status_code=404,
                detail="Post image not found in storage"
            )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching post image: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch post image: {str(e)}"
        )

