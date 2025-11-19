from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from ..entities.like import Like
from ..entities.post import Post
from ..exceptions import PostNotFoundError
import logging


async def toggle_like(
    session: AsyncSession,
    post_id: int,
    user_id: int
) -> tuple[bool, int]:  # Returns (is_liked, like_count)
    """Toggle like on a post. Returns (is_liked, like_count)."""
    try:
        # Verify post exists
        result = await session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        if not post:
            raise PostNotFoundError(post_id)
        
        # Check if like already exists
        result = await session.execute(
            select(Like).where(
                Like.post_id == post_id,
                Like.user_id == user_id
            )
        )
        existing_like = result.scalar_one_or_none()
        
        if existing_like:
            # Unlike: delete the like
            await session.execute(
                delete(Like).where(
                    Like.post_id == post_id,
                    Like.user_id == user_id
                )
            )
            is_liked = False
            logging.info(f"User {user_id} unliked post {post_id}")
        else:
            # Like: create new like
            like = Like(
                post_id=post_id,
                user_id=user_id
            )
            session.add(like)
            is_liked = True
            logging.info(f"User {user_id} liked post {post_id}")
        
        await session.commit()
        
        # Get updated like count
        result = await session.execute(
            select(func.count(Like.id))
            .where(Like.post_id == post_id)
        )
        like_count = result.scalar_one() or 0
        
        return (is_liked, like_count)
    except PostNotFoundError:
        raise
    except Exception as e:
        logging.error(f"Failed to toggle like for post {post_id} by user {user_id}. Error: {str(e)}")
        await session.rollback()
        raise


async def get_like_count(session: AsyncSession, post_id: int) -> int:
    """Get the count of likes for a post."""
    result = await session.execute(
        select(func.count(Like.id))
        .where(Like.post_id == post_id)
    )
    count = result.scalar_one() or 0
    return count


async def is_post_liked_by_user(
    session: AsyncSession,
    post_id: int,
    user_id: int
) -> bool:
    """Check if a post is liked by a user."""
    result = await session.execute(
        select(Like).where(
            Like.post_id == post_id,
            Like.user_id == user_id
        )
    )
    like = result.scalar_one_or_none()
    return like is not None


async def get_likes_for_posts(
    session: AsyncSession,
    post_ids: List[int],
    user_id: int
) -> dict[int, bool]:
    """Get like status for multiple posts by a user. Returns dict[post_id, is_liked]."""
    if not post_ids:
        return {}
    
    result = await session.execute(
        select(Like.post_id)
        .where(
            Like.post_id.in_(post_ids),
            Like.user_id == user_id
        )
    )
    liked_post_ids = {row[0] for row in result.all()}
    
    return {post_id: post_id in liked_post_ids for post_id in post_ids}

