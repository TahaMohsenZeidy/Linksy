from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PostCreate(BaseModel):
    title: str
    content: str


class PostUpdate(BaseModel):
    title: str
    content: str


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    user_id: int
    username: str
    profile_picture_url: str | None = None
    image_url: str | None = None  # Object path/name in MinIO bucket
    comment_count: int = 0
    like_count: int = 0
    is_liked: bool = False  # Whether the current user has liked this post
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

