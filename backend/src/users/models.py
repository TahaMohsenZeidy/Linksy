from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    profile_picture_url: str | None = None

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    new_password_confirm: str


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None

