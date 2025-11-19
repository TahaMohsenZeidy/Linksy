from fastapi import FastAPI
from .auth.controller import router as auth_router
from .posts.controller import router as posts_router
from .users.controller import router as users_router
from .comments.controller import router as comments_router
from .likes.controller import router as likes_router


def register_routes(app: FastAPI):
    """Register all API routes."""
    app.include_router(auth_router)
    app.include_router(posts_router)
    app.include_router(users_router)
    app.include_router(comments_router)
    app.include_router(likes_router)

