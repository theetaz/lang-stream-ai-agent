from contextlib import asynccontextmanager

from api.v1.router import api_v1_router
from common.errors import AppError, app_error_handler
from common.logger import get_logger
from config.settings import get_settings
from database.db_client import close_db, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Handles database initialization on startup and cleanup on shutdown.
    """
    # Startup: Initialize database tables
    await init_db()
    logger.info("Database initialized successfully")

    yield

    # Shutdown: Close database connections
    await close_db()
    logger.info("Database connections closed")


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

# Register api v1 routers
app.include_router(api_v1_router)

# Global exception handlers
app.add_exception_handler(AppError, app_error_handler)


@app.get("/")
async def root():
    return {"message": "Welcome to the AI Agent API"}
