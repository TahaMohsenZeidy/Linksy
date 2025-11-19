from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List
from ..entities.post import Post
from ..exceptions import PostNotFoundError, ForbiddenException
import logging


class PostService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_post(self, user_id: int, title: str, content: str, image_url: str | None = None) -> Post:
        """Create a new post."""
        try:
            post = Post(title=title, content=content, user_id=user_id, image_url=image_url)
            self.session.add(post)
            await self.session.commit()
            await self.session.refresh(post, ["user"])  # Eager load user relationship
            logging.info(f"Created new post '{title}' for user: {user_id}")
            return post
        except Exception as e:
            logging.error(f"Failed to create post for user {user_id}. Error: {str(e)}")
            raise
    
    async def get_post(self, post_id: int) -> Post:
        """Get a post by ID."""
        result = await self.session.execute(
            select(Post)
            .options(selectinload(Post.user))
            .where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        if not post:
            logging.warning(f"Post {post_id} not found")
            raise PostNotFoundError(post_id)
        return post

    async def get_post_by_title(self, title: str) -> Post:
        """Get a post by title."""
        result = await self.session.execute(select(Post).where(Post.title == title))
        post = result.scalar_one_or_none()
        if not post:
            logging.warning(f"Post '{title}' not found")
            raise PostNotFoundError(title)
        return post
    
    async def get_user_posts(self, user_id: int) -> List[Post]:
        """Get all posts for a user."""
        result = await self.session.execute(
            select(Post)
            .options(selectinload(Post.user))
            .where(Post.user_id == user_id)
        )
        posts = result.scalars().all()
        logging.info(f"Retrieved {len(posts)} posts for user: {user_id}")
        return list(posts)
    
    async def get_all_posts(self) -> List[Post]:
        """Get all posts with user information."""
        result = await self.session.execute(
            select(Post)
            .options(selectinload(Post.user))
            .order_by(Post.created_at.desc())
        )
        posts = result.scalars().all()
        return list(posts)
    
    async def delete_post(self, post_id: int, user_id: int) -> None:
        """Delete a post."""
        try:
            result = await self.session.execute(select(Post).where(Post.id == post_id))
            post = result.scalar_one_or_none()
            if not post:
                raise PostNotFoundError(post_id)
            if post.user_id != user_id:
                logging.warning(f"User {user_id} attempted to delete post {post_id} owned by user {post.user_id}")
                raise ForbiddenException("You can only delete your own posts")
            
            # Use delete statement for async SQLAlchemy
            await self.session.execute(delete(Post).where(Post.id == post_id))
            await self.session.commit()
            logging.info(f"Post {post_id} deleted by user {user_id}")
        except (PostNotFoundError, ForbiddenException):
            raise
        except Exception as e:
            logging.error(f"Error deleting post {post_id}: {str(e)}")
            await self.session.rollback()
            raise

    async def delete_post_by_title(self, title: str, user_id: int) -> None:
        """Delete a post by title."""
        result = await self.session.execute(select(Post).where(Post.title == title))
        post = result.scalar_one_or_none()
        if not post:
            logging.warning(f"Post '{title}' not found")
            raise PostNotFoundError(title)
        if post.user_id != user_id:
            logging.warning(f"User {user_id} attempted to delete post '{title}' owned by user {post.user_id}")
            raise ForbiddenException("You can only delete your own posts")
        self.session.delete(post)
        await self.session.commit()
        logging.info(f"Post '{title}' deleted by user {user_id}")
    
    async def update_post(self, post_id: int, title: str, content: str, user_id: int) -> Post:
        """Update a post."""
        result = await self.session.execute(
            select(Post)
            .options(selectinload(Post.user))
            .where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        if not post:
            raise PostNotFoundError(post_id)
        if post.user_id != user_id:
            logging.warning(f"User {user_id} attempted to update post {post_id} owned by user {post.user_id}")
            raise ForbiddenException("You can only update your own posts")
        post.title = title
        post.content = content
        await self.session.commit()
        await self.session.refresh(post, ["user"])  # Eager load user relationship
        logging.info(f"Post {post_id} updated by user {user_id}")
        return post
