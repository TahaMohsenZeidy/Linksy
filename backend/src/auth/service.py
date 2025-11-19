from datetime import timedelta, datetime, timezone
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database.core import get_db
from ..entities.user import User
from .models import TokenData
from .keycloak_client import authenticate_with_keycloak, verify_keycloak_token, create_user_in_keycloak
import os
import logging

# Legacy JWT config (for backward compatibility during migration)
SECRET_KEY = os.getenv("SECRET_KEY", "197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Keycloak configuration
USE_KEYCLOAK = os.getenv("USE_KEYCLOAK", "true").lower() == "true"

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
oauth2_bearer_optional = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


def create_access_token(username: str, user_id: int, expires_delta: timedelta) -> str:
    encode = {"sub": username, "id": user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed_password.decode('utf-8')


async def authenticate_user(username: str, password: str, db: AsyncSession) -> Optional[User]:
    """Authenticate a user by username and password."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        logging.warning(f"Failed authentication attempt for username: {username}")
        return None
    if not verify_password(password, user.password):
        logging.warning(f"Failed authentication attempt for username: {username}")
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user from Keycloak or JWT token."""
    try:
        if USE_KEYCLOAK:
            # Verify token with Keycloak (synchronous call)
            import asyncio
            from datetime import datetime
            token_info = await asyncio.to_thread(verify_keycloak_token, token)
            if not token_info.get("active"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token is not active."
                )
            
            keycloak_user_id = token_info.get("keycloak_user_id")
            username = token_info.get("preferred_username")
            email = token_info.get("email")
            
            if not username or not keycloak_user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate user."
                )
            
            # Option 4: Federated Identity Pattern
            # Try to find user by keycloak_user_id first (most reliable)
            result = await db.execute(select(User).where(User.keycloak_user_id == keycloak_user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                # Try to find by username (for backward compatibility)
                result = await db.execute(select(User).where(User.username == username))
                user = result.scalar_one_or_none()
            
            if not user:
                # Create new user in database (first login from Keycloak)
                user = User(
                    username=username,
                    email=email or f"{username}@keycloak.local",
                    password="",  # No password needed, Keycloak handles auth
                    keycloak_user_id=keycloak_user_id,
                    last_synced_at=datetime.utcnow()
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                logging.info(f"Created user {username} in database from Keycloak (ID: {keycloak_user_id})")
            else:
                # User exists - sync data from Keycloak
                # Update keycloak_user_id if missing (migration scenario)
                if not user.keycloak_user_id:
                    user.keycloak_user_id = keycloak_user_id
                    logging.info(f"Updated user {user.id} with Keycloak ID: {keycloak_user_id}")
                
                # Update cached data if stale (sync every 24 hours or if data differs)
                should_sync = (
                    not user.last_synced_at or
                    (datetime.utcnow() - user.last_synced_at).total_seconds() > 86400 or  # 24 hours
                    user.username != username or
                    user.email != email
                )
                
                if should_sync:
                    user.username = username
                    user.email = email or user.email
                    user.last_synced_at = datetime.utcnow()
                    await db.commit()
                    await db.refresh(user)
                    logging.debug(f"Synced user {user.id} data from Keycloak")
            
            return user
        else:
            # Legacy JWT validation
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            user_id: int = payload.get("id")
            if username is None or user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate user."
                )
            
            # Fetch user from database
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found."
                )
            return user
    except (JWTError, Exception) as e:
        logging.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user."
        )


CurrentUser = Annotated[User, Depends(get_current_user)]


# Make oauth2_bearer optional for endpoints that don't require auth
oauth2_bearer_optional = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)

async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_bearer_optional),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get the current authenticated user if token is provided, otherwise return None."""
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        # If token is invalid, return None instead of raising
        return None


OptionalCurrentUser = Annotated[Optional[User], Depends(get_current_user_optional)]
