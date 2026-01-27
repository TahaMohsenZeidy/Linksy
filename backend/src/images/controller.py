from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from ..storage import get_image_from_minio
import logging

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/{object_path:path}")
async def get_image(object_path: str):
    """
    Proxy endpoint to retrieve images from MinIO.
    
    Args:
        object_path: The full object path in MinIO (e.g., users/1/uuid.jpg or posts/1/uuid.jpg)
    
    Returns:
        Image binary data with appropriate content type
    """
    try:
        # Fetch image from MinIO
        image_data, content_type = get_image_from_minio(object_path)
        
        # Return image with appropriate headers
        return Response(
            content=image_data,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Content-Disposition": f"inline; filename={object_path.split('/')[-1]}"
            }
        )
    except Exception as e:
        logging.error(f"Error retrieving image {object_path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image not found: {object_path}"
        )

