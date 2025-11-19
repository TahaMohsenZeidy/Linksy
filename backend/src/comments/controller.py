from fastapi import APIRouter, Depends, status, HTTPException
from typing import List

from ..database.core import DbSession
from ..auth.service import CurrentUser
from . import models
from . import service
from ..storage.minio_client import get_profile_picture_url

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/posts/{post_id}", response_model=models.CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: int,
    comment_data: models.CommentCreate,
    current_user: CurrentUser,
    db: DbSession
):
    """Create a new comment on a post."""
    comment = await service.create_comment(
        session=db,
        post_id=post_id,
        user_id=current_user.id,
        content=comment_data.content
    )
    # Map comment to response with username and profile picture
    profile_pic_url = None
    if comment.user.profile_picture_url:
        try:
            profile_pic_url = get_profile_picture_url(comment.user.profile_picture_url)
        except Exception as e:
            # If we can't get the URL, just continue without it
            pass
    
    return {
        "id": comment.id,
        "content": comment.content,
        "post_id": comment.post_id,
        "user_id": comment.user_id,
        "username": comment.user.username if comment.user else f"user_{comment.user_id}",
        "profile_picture_url": profile_pic_url,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at
    }


@router.get("/posts/{post_id}", response_model=List[models.CommentResponse])
async def get_comments_by_post(
    post_id: int,
    db: DbSession
):
    """Get all comments for a post."""
    comments = await service.get_comments_by_post(db, post_id)
    # Map comments to response with username and profile picture URLs
    result = []
    for comment in comments:
        profile_pic_url = None
        if comment.user.profile_picture_url:
            try:
                profile_pic_url = get_profile_picture_url(comment.user.profile_picture_url)
            except Exception:
                pass
        
        result.append({
            "id": comment.id,
            "content": comment.content,
            "post_id": comment.post_id,
            "user_id": comment.user_id,
            "username": comment.user.username if comment.user else f"user_{comment.user_id}",
            "profile_picture_url": profile_pic_url,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at
        })
    return result


@router.put("/{comment_id}", response_model=models.CommentResponse)
async def update_comment(
    comment_id: int,
    comment_data: models.CommentUpdate,
    current_user: CurrentUser,
    db: DbSession
):
    """Update a comment."""
    comment = await service.update_comment(
        session=db,
        comment_id=comment_id,
        user_id=current_user.id,
        content=comment_data.content
    )
    # Map comment to response
    profile_pic_url = None
    if comment.user.profile_picture_url:
        try:
            profile_pic_url = get_profile_picture_url(comment.user.profile_picture_url)
        except Exception:
            pass
    
    return {
        "id": comment.id,
        "content": comment.content,
        "post_id": comment.post_id,
        "user_id": comment.user_id,
        "username": comment.user.username if comment.user else f"user_{comment.user_id}",
        "profile_picture_url": profile_pic_url,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at
    }


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user: CurrentUser,
    db: DbSession
):
    """Delete a comment."""
    await service.delete_comment(
        session=db,
        comment_id=comment_id,
        user_id=current_user.id
    )
    return None

