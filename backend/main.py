"""
Main FastAPI application.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.db_client import init_db, close_db
from api.v1.auth.routes import router as auth_router
from api.v1.user.routes import router as user_router
from api.v1.chat.routes import router as chat_router
from common.errors import AppError, app_error_handler
from config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Handles database initialization on startup and cleanup on shutdown.
    """
    # Startup: Initialize database tables
    await init_db()
    print("✓ Database initialized successfully")

    yield

    # Shutdown: Close database connections
    await close_db()
    print("✓ Database connections closed")


app = FastAPI(title="AI Agent API", version="1.0", lifespan=lifespan)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")

# Global exception handlers
app.add_exception_handler(AppError, app_error_handler)


@app.get("/")
async def root():
    return {"message": "Welcome to the AI Agent API"}
