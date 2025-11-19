from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database.core import engine, Base
from .entities.user import User  # Import entities to register them
from .entities.post import Post  # Import entities to register them
from .entities.comment import Comment  # Import entities to register them
from .api import register_routes
import os

app = FastAPI(title="Linksy API", version="1.0.0")

# CORS middleware - configurable via environment variable
# Default to localhost for local development, but allow override for Docker/production
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
register_routes(app)


@app.on_event("startup")
async def startup():
    """Create database tables on startup (fallback - migrations handle this in production)."""
    # Note: In production, Alembic migrations (run via entrypoint.sh) handle schema changes.
    # This is kept as a fallback for development.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def root():
    return {"message": "Welcome to Linksy API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
