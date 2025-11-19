from fastapi import APIRouter, status, UploadFile, File, HTTPException
import logging

from ..database.core import DbSession
from ..auth.service import CurrentUser
from . import models
from . import service
from ..storage.minio_client import upload_profile_picture, get_profile_picture_url

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get("/me", response_model=models.UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser,
    db: DbSession
):
    """Get current user's profile."""
    user = await service.get_current_user_profile(db, current_user.id)
    return user


@router.put("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_change: models.PasswordChange,
    db: DbSession,
    current_user: CurrentUser
):
    """Change user password."""
    await service.change_password(
        db,
        current_user.id,
        password_change.current_password,
        password_change.new_password,
        password_change.new_password_confirm
    )
    return {"message": "Password changed successfully"}


@router.put("/me", response_model=models.UserResponse)
async def update_user_profile(
    user_update: models.UserUpdate,
    current_user: CurrentUser,
    db: DbSession
):
    """Update current user's profile."""
    user = await service.update_user(
        db,
        current_user.id,
        username=user_update.username,
        email=user_update.email
    )
    return user


@router.post("/me/profile-picture", response_model=models.UserResponse)
async def upload_profile_picture_endpoint(
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...)
):
    """Upload a profile picture for the current user."""
    try:
        # Upload file to MinIO
        object_name = await upload_profile_picture(
            file=file,
            user_id=current_user.id
        )
        
        # Update user's profile picture URL in database
        user = await service.update_profile_picture(
            db=db,
            user_id=current_user.id,
            profile_picture_url=object_name
        )
        
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile picture: {str(e)}"
        )


@router.get("/me/profile-picture-url")
async def get_profile_picture_url_endpoint(
    current_user: CurrentUser,
    db: DbSession
):
    """Get a presigned URL for the current user's profile picture."""
    user = await service.get_current_user_profile(db, current_user.id)
    
    if not user.profile_picture_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found"
        )
    
    try:
        url = get_profile_picture_url(user.profile_picture_url)
        return {"url": url, "object_name": user.profile_picture_url}
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e)
        logging.error(f"Error generating profile picture URL for user {current_user.id}: {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.get("/{user_id}/profile-picture-url")
async def get_user_profile_picture_url_endpoint(
    user_id: int,
    db: DbSession
):
    """Get a presigned URL for a user's profile picture by user ID."""
    user = await service.get_user_by_id(db, user_id)
    
    if not user.profile_picture_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found"
        )
    
    try:
        url = get_profile_picture_url(user.profile_picture_url)
        return {"url": url, "object_name": user.profile_picture_url}
    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e)
        logging.error(f"Error generating profile picture URL for user {user_id}: {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.delete("/me/profile-picture", response_model=models.UserResponse)
async def delete_profile_picture_endpoint(
    current_user: CurrentUser,
    db: DbSession
):
    """Delete the current user's profile picture."""
    user = await service.get_current_user_profile(db, current_user.id)
    
    if not user.profile_picture_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found"
        )
    
    # Delete from MinIO
    from ..storage.minio_client import delete_profile_picture
    delete_profile_picture(user.profile_picture_url)
    
    # Update user's profile picture URL to None
    user.profile_picture_url = None
    await db.commit()
    await db.refresh(user)
    
    return user

