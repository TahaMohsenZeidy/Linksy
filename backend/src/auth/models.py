from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    phone_number: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

