from contextlib import asynccontextmanager

from api.v1.router import api_v1_router
from common.errors import AppError, app_error_handler
from common.logger import get_logger
from common.response import error_response
from config.settings import get_settings
from database.db_client import close_db, init_db
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors and return in APIResponse format"""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(f"Validation error on {request.url.path}: {errors}")

    response = error_response(message="Validation error", metadata={"errors": errors})

    return JSONResponse(status_code=422, content=response.model_dump())


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTPException and return in APIResponse format"""
    logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")

    response = error_response(
        message=exc.detail if isinstance(exc.detail, str) else "HTTP error occurred",
        metadata={"status_code": exc.status_code},
    )

    return JSONResponse(status_code=exc.status_code, content=response.model_dump())


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected exceptions"""
    # Log full error with traceback for debugging
    logger.error(f"Unexpected error on {request.url.path}: {exc}", exc_info=True)

    # Return generic error message (don't expose internal details in production)
    response = error_response(
        message=(
            "An unexpected error occurred"
            if settings.ENVIRONMENT == "production"
            else str(exc)
        ),
        metadata=(
            {"error_type": type(exc).__name__, "path": request.url.path}
            if settings.ENVIRONMENT != "production"
            else None
        ),
    )

    return JSONResponse(status_code=500, content=response.model_dump())


@app.get("/")
async def root():
    return {"message": "Welcome to the AI Agent API"}
