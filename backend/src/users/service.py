from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..entities.user import User
from ..exceptions import UserNotFoundError, InvalidPasswordError, PasswordMismatchError
from ..auth.service import verify_password, get_password_hash
import logging


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    """Get a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        logging.warning(f"User not found with ID: {user_id}")
        raise UserNotFoundError(user_id)
    logging.info(f"Successfully retrieved user with ID: {user_id}")
    return user


async def get_current_user_profile(db: AsyncSession, user_id: int) -> User:
    """Get current user's profile."""
    return await get_user_by_id(db, user_id)


async def change_password(
    db: AsyncSession,
    user_id: int,
    current_password: str,
    new_password: str,
    new_password_confirm: str
) -> None:
    """Change user password."""
    try:
        user = await get_user_by_id(db, user_id)
        
        # Verify current password
        if not verify_password(current_password, user.password):
            logging.warning(f"Invalid current password provided for user ID: {user_id}")
            raise InvalidPasswordError()
        
        # Verify new passwords match
        if new_password != new_password_confirm:
            logging.warning(f"Password mismatch during change attempt for user ID: {user_id}")
            raise PasswordMismatchError()
        
        # Update password
        user.password = get_password_hash(new_password)
        await db.commit()
        await db.refresh(user)
        logging.info(f"Successfully changed password for user ID: {user_id}")
    except (InvalidPasswordError, PasswordMismatchError, UserNotFoundError):
        raise
    except Exception as e:
        logging.error(f"Error during password change for user ID: {user_id}. Error: {str(e)}")
        raise


async def update_user(
    db: AsyncSession,
    user_id: int,
    username: str | None = None,
    email: str | None = None
) -> User:
    """Update user profile information."""
    user = await get_user_by_id(db, user_id)
    
    # Check if username already exists (if changing)
    if username and username != user.username:
        result = await db.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        user.username = username
    
    # Check if email already exists (if changing)
    if email and email != user.email:
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        user.email = email
    
    await db.commit()
    await db.refresh(user)
    logging.info(f"Successfully updated user profile for user ID: {user_id}")
    return user


async def update_profile_picture(
    db: AsyncSession,
    user_id: int,
    profile_picture_url: str
) -> User:
    """Update user's profile picture URL."""
    user = await get_user_by_id(db, user_id)
    
    # Delete old profile picture if it exists
    if user.profile_picture_url:
        from ..storage.minio_client import delete_profile_picture
        try:
            delete_profile_picture(user.profile_picture_url)
        except Exception as e:
            logging.warning(f"Failed to delete old profile picture for user {user_id}: {e}")
    
    # Update profile picture URL
    user.profile_picture_url = profile_picture_url
    await db.commit()
    await db.refresh(user)
    logging.info(f"Successfully updated profile picture for user ID: {user_id}")
    return user

