from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from typing import List, Optional

from ..database.core import DbSession
from ..auth.service import CurrentUser, OptionalCurrentUser
from . import models
from .service import PostService
from ..comments import service as comment_service
from ..likes import service as like_service
from ..storage import upload_post_image, delete_post_image, get_post_image_url
import logging

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=models.PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    current_user: CurrentUser,
    db: DbSession,
    title: str = Form(...),
    content: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    """Create a new post with optional image."""
    service = PostService(db)
    image_url = None
    
    # Create post first (without image)
    post = await service.create_post(current_user.id, title, content, None)
    
    # Upload image if provided (after post is created so we have post_id)
    if image:
        try:
            image_url = await upload_post_image(image, post.id, current_user.id)
            # Update post with image_url
            post.image_url = image_url
            await db.commit()
            await db.refresh(post, ["user"])
        except Exception as e:
            logging.error(f"Failed to upload post image: {e}")
            # If image upload fails, delete the post
            await service.delete_post(post.id, current_user.id)
            raise
    
    # Get comment count (will be 0 for new post)
    comment_count = await comment_service.get_comment_count(db, post.id)
    # Get like count (will be 0 for new post)
    like_count = await like_service.get_like_count(db, post.id)
    # Map post to response with username, profile picture, and counts
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "user_id": post.user_id,
        "username": post.user.username if post.user else f"user_{post.user_id}",
        "profile_picture_url": post.user.profile_picture_url if post.user else None,
        "image_url": post.image_url,
        "comment_count": comment_count,
        "like_count": like_count,
        "is_liked": False,  # New post, not liked yet
        "created_at": post.created_at,
        "updated_at": post.updated_at
    }


@router.get("/", response_model=List[models.PostResponse])
async def get_all_posts(
    db: DbSession,
    current_user: OptionalCurrentUser = None
):
    """Get all posts."""
    service = PostService(db)
    posts = await service.get_all_posts()
    # Map posts to response with username, profile picture, and counts
    result = []
    post_ids = [post.id for post in posts]
    
    # Get like counts for all posts
    like_counts = {}
    for post_id in post_ids:
        like_counts[post_id] = await like_service.get_like_count(db, post_id)
    
    # Get like status for current user if authenticated
    is_liked_map = {}
    if current_user:
        is_liked_map = await like_service.get_likes_for_posts(db, post_ids, current_user.id)
    
    for post in posts:
        comment_count = await comment_service.get_comment_count(db, post.id)
        result.append({
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "user_id": post.user_id,
            "username": post.user.username if post.user else f"user_{post.user_id}",
            "profile_picture_url": post.user.profile_picture_url if post.user else None,
            "image_url": post.image_url,
            "comment_count": comment_count,
            "like_count": like_counts.get(post.id, 0),
            "is_liked": is_liked_map.get(post.id, False),
            "created_at": post.created_at,
            "updated_at": post.updated_at
        })
    return result


@router.get("/me", response_model=List[models.PostResponse])
async def get_my_posts(
    current_user: CurrentUser,
    db: DbSession
):
    """Get current user's posts."""
    service = PostService(db)
    posts = await service.get_user_posts(current_user.id)
    # Map posts to response with username, profile picture, and counts
    result = []
    post_ids = [post.id for post in posts]
    
    # Get like counts for all posts
    like_counts = {}
    for post_id in post_ids:
        like_counts[post_id] = await like_service.get_like_count(db, post_id)
    
    # Get like status for current user
    is_liked_map = await like_service.get_likes_for_posts(db, post_ids, current_user.id)
    
    for post in posts:
        comment_count = await comment_service.get_comment_count(db, post.id)
        result.append({
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "user_id": post.user_id,
            "username": post.user.username if post.user else f"user_{post.user_id}",
            "profile_picture_url": post.user.profile_picture_url if post.user else None,
            "image_url": post.image_url,
            "comment_count": comment_count,
            "like_count": like_counts.get(post.id, 0),
            "is_liked": is_liked_map.get(post.id, False),
            "created_at": post.created_at,
            "updated_at": post.updated_at
        })
    return result


@router.get("/{post_id}/image-url")
async def get_post_image_url_endpoint(
    post_id: int,
    db: DbSession
):
    """Get a presigned URL for a post's image."""
    service = PostService(db)
    post = await service.get_post(post_id)
    
    if not post.image_url:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post image not found"
        )
    
    try:
        url = get_post_image_url(post.image_url)
        return {"url": url, "object_name": post.image_url}
    except Exception as e:
        error_detail = str(e)
        logging.error(f"Error generating post image URL for post {post_id}: {error_detail}")
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.get("/{post_id}", response_model=models.PostResponse)
async def get_post(
    post_id: int,
    db: DbSession,
    current_user: CurrentUser
):
    """Get a specific post."""
    service = PostService(db)
    post = await service.get_post(post_id)
    # Get comment count
    comment_count = await comment_service.get_comment_count(db, post.id)
    # Get like count
    like_count = await like_service.get_like_count(db, post.id)
    # Get like status for current user
    is_liked = await like_service.is_post_liked_by_user(db, post_id, current_user.id)
    # Map post to response with username, profile picture, and counts
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "user_id": post.user_id,
        "username": post.user.username if post.user else f"user_{post.user_id}",
        "profile_picture_url": post.user.profile_picture_url if post.user else None,
        "image_url": post.image_url,
        "comment_count": comment_count,
        "like_count": like_count,
        "is_liked": is_liked,
        "created_at": post.created_at,
        "updated_at": post.updated_at
    }

# NOTE: Get by title route conflicts with get by id - removed to avoid routing conflicts
# If you need get by title, use a different path like: /posts/by-title/{title}


@router.put("/{post_id}", response_model=models.PostResponse)
async def update_post(
    post_id: int,
    post_data: models.PostUpdate,
    current_user: CurrentUser,
    db: DbSession
):
    """Update a post."""
    service = PostService(db)
    post = await service.update_post(post_id, post_data.title, post_data.content, current_user.id)
    # Refresh to load user relationship
    await db.refresh(post, ["user"])
    # Get comment count
    comment_count = await comment_service.get_comment_count(db, post.id)
    # Get like count
    like_count = await like_service.get_like_count(db, post.id)
    # Get like status for current user
    is_liked = await like_service.is_post_liked_by_user(db, post_id, current_user.id)
    # Map post to response with username, profile picture, and counts
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "user_id": post.user_id,
        "username": post.user.username if post.user else f"user_{post.user_id}",
        "profile_picture_url": post.user.profile_picture_url if post.user else None,
        "image_url": post.image_url,
        "comment_count": comment_count,
        "like_count": like_count,
        "is_liked": is_liked,
        "created_at": post.created_at,
        "updated_at": post.updated_at
    }


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: CurrentUser,
    db: DbSession
):
    """Delete a post."""
    service = PostService(db)
    try:
        # Get post first to check for image
        post = await service.get_post(post_id)
        
        # Delete image from MinIO if exists
        if post.image_url:
            try:
                delete_post_image(post.image_url)
            except Exception as e:
                logging.warning(f"Failed to delete post image for post {post_id}: {e}")
        
        await service.delete_post(post_id, current_user.id)
        return None
    except Exception as e:
        logging.error(f"Error in delete_post controller: {str(e)}")
        raise

# NOTE: Delete by title route conflicts with delete by id - removed to avoid routing conflicts
# If you need delete by title, use a different path like: /posts/by-title/{title}