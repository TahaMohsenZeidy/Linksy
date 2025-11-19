from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from typing import List
from ..entities.comment import Comment
from ..entities.post import Post
from ..exceptions import PostNotFoundError, ForbiddenException, CommentNotFoundError
import logging


async def create_comment(
    session: AsyncSession,
    post_id: int,
    user_id: int,
    content: str
) -> Comment:
    """Create a new comment."""
    try:
        # Verify post exists
        result = await session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        if not post:
            raise PostNotFoundError(post_id)
        
        comment = Comment(
            content=content,
            post_id=post_id,
            user_id=user_id
        )
        session.add(comment)
        await session.commit()
        await session.refresh(comment, ["user", "post"])
        logging.info(f"Created comment {comment.id} for post {post_id} by user {user_id}")
        return comment
    except PostNotFoundError:
        raise
    except Exception as e:
        logging.error(f"Failed to create comment for post {post_id} by user {user_id}. Error: {str(e)}")
        await session.rollback()
        raise


async def get_comments_by_post(
    session: AsyncSession,
    post_id: int
) -> List[Comment]:
    """Get all comments for a post, sorted by newest first."""
    result = await session.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.desc())
    )
    comments = result.scalars().all()
    return list(comments)


async def get_comment_count(session: AsyncSession, post_id: int) -> int:
    """Get the count of comments for a post."""
    result = await session.execute(
        select(func.count(Comment.id))
        .where(Comment.post_id == post_id)
    )
    count = result.scalar_one()
    return count


async def update_comment(
    session: AsyncSession,
    comment_id: int,
    user_id: int,
    content: str
) -> Comment:
    """Update a comment."""
    result = await session.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise CommentNotFoundError(comment_id)
    
    if comment.user_id != user_id:
        logging.warning(f"User {user_id} attempted to update comment {comment_id} owned by user {comment.user_id}")
        raise ForbiddenException("You can only update your own comments")
    
    comment.content = content
    await session.commit()
    await session.refresh(comment, ["user"])
    logging.info(f"Comment {comment_id} updated by user {user_id}")
    return comment


async def delete_comment(
    session: AsyncSession,
    comment_id: int,
    user_id: int
) -> None:
    """Delete a comment."""
    result = await session.execute(
        select(Comment).where(Comment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise CommentNotFoundError(comment_id)
    
    if comment.user_id != user_id:
        logging.warning(f"User {user_id} attempted to delete comment {comment_id} owned by user {comment.user_id}")
        raise ForbiddenException("You can only delete your own comments")
    
    await session.execute(delete(Comment).where(Comment.id == comment_id))
    await session.commit()
    logging.info(f"Comment {comment_id} deleted by user {user_id}")

