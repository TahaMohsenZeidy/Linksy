from fastapi import APIRouter, Depends, status, HTTPException
from typing import List

from ..database.core import DbSession
from ..auth.service import CurrentUser
from . import service

router = APIRouter(prefix="/likes", tags=["likes"])


@router.post("/posts/{post_id}", status_code=status.HTTP_200_OK)
async def toggle_like_post(
    post_id: int,
    current_user: CurrentUser,
    db: DbSession
):
    """Toggle like on a post."""
    is_liked, like_count = await service.toggle_like(
        session=db,
        post_id=post_id,
        user_id=current_user.id
    )
    return {
        "is_liked": is_liked,
        "like_count": like_count
    }


@router.get("/posts/{post_id}/status")
async def get_like_status(
    post_id: int,
    current_user: CurrentUser,
    db: DbSession
):
    """Get like status for a post."""
    is_liked = await service.is_post_liked_by_user(db, post_id, current_user.id)
    like_count = await service.get_like_count(db, post_id)
    return {
        "is_liked": is_liked,
        "like_count": like_count
    }

