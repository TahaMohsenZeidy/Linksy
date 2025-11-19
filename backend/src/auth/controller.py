from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
import logging

from ..database.core import DbSession
from ..entities.user import User
from . import models
from .service import create_access_token, authenticate_user, get_password_hash

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    register_user_request: models.RegisterUserRequest,
    db: DbSession
):
    """Register a new user in Keycloak and database."""
    import os
    USE_KEYCLOAK = os.getenv("USE_KEYCLOAK", "true").lower() == "true"
    
    # Generate username from first_name and last_name
    # Format: firstname.lastname (lowercase, replace spaces with dots)
    base_username = f"{register_user_request.first_name.lower().replace(' ', '.')}.{register_user_request.last_name.lower().replace(' ', '.')}"
    username = base_username
    
    # Check if username already exists, if so append a number
    counter = 1
    while True:
        result = await db.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()
        if not existing_user:
            break
        username = f"{base_username}{counter}"
        counter += 1
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == register_user_request.email))
    existing_email = result.scalar_one_or_none()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    if USE_KEYCLOAK:
        # Create user in Keycloak (synchronous call wrapped in async)
        from .keycloak_client import create_user_in_keycloak
        import asyncio
        try:
            # Format date_of_birth as string if provided
            date_of_birth_str = None
            if register_user_request.date_of_birth:
                date_of_birth_str = register_user_request.date_of_birth.isoformat()
            
            keycloak_user_id = await asyncio.to_thread(
                create_user_in_keycloak,
                username,
                register_user_request.email,
                register_user_request.password,
                register_user_request.first_name,
                register_user_request.last_name,
                date_of_birth_str,
                register_user_request.phone_number
            )
            
            # Option 4: Federated Identity Pattern
            # Create user in database with Keycloak user ID reference
            from datetime import datetime
            create_user_model = User(
                email=register_user_request.email,
                username=username,  # Generated username
                password="",  # No password stored, Keycloak handles auth
                keycloak_user_id=keycloak_user_id,  # Store Keycloak UUID
                last_synced_at=datetime.utcnow()  # Mark as synced
            )
            db.add(create_user_model)
            await db.commit()
            await db.refresh(create_user_model)
            
            return {
                "message": "User created successfully in Keycloak",
                "user_id": create_user_model.id,
                "keycloak_user_id": keycloak_user_id
            }
        except Exception as e:
            logging.error(f"Failed to create user in Keycloak: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )
    else:
        # Legacy registration (database only)
        hashed_password = get_password_hash(register_user_request.password)
        
        create_user_model = User(
            email=register_user_request.email,
            username=username,  # Generated username
            password=hashed_password,
        )
        
        db.add(create_user_model)
        await db.commit()
        await db.refresh(create_user_model)
        
        return {"message": "User created successfully", "user_id": create_user_model.id}


@router.post("/token", response_model=models.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession
):
    """Login and get access token from Keycloak or legacy JWT."""
    import os
    USE_KEYCLOAK = os.getenv("USE_KEYCLOAK", "true").lower() == "true"
    
    if USE_KEYCLOAK:
        # Authenticate with Keycloak (synchronous call wrapped in async)
        from .keycloak_client import authenticate_with_keycloak
        import asyncio
        try:
            token_data = await asyncio.to_thread(
                authenticate_with_keycloak,
                form_data.username,
                form_data.password
            )
            return {
                "access_token": token_data["access_token"],
                "token_type": token_data["token_type"]
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
    else:
        # Legacy JWT authentication
        user = await authenticate_user(form_data.username, form_data.password, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        token = create_access_token(user.username, user.id, timedelta(minutes=30))
        return {"access_token": token, "token_type": "bearer"}
