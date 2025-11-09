from contextlib import asynccontextmanager

from api.v1.router import api_v1_router
from common.errors import AppError, app_error_handler
from common.logger import get_logger
from common.response import error_response
from config.settings import get_settings
from database.checkpoint_pool import close_checkpointer, get_async_checkpointer
from database.db_client import close_db, init_db
from database.store_pool import close_store, get_async_store
from fastapi import FastAPI, Request, status
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

    # Initialize LangGraph checkpointer and store at startup
    # Note: Checkpointer setup may fail if run inside a transaction (CREATE INDEX CONCURRENTLY)
    # It will be retried on first use when no transaction is active
    try:
        await get_async_checkpointer()
        logger.info("LangGraph checkpointer initialized")
    except Exception as e:
        error_msg = str(e)
        if "CREATE INDEX CONCURRENTLY" in error_msg:
            logger.info(
                "Checkpointer setup deferred (will initialize on first use to avoid transaction conflict)"
            )
        else:
            logger.warning(
                f"Failed to initialize checkpointer (will retry on first use): {e}"
            )

    try:
        await get_async_store()
        logger.info("LangGraph store initialized")
    except ValueError as e:
        # API key validation error - this is critical but we allow app to start
        # Store will fail on first use if API key is not set
        logger.error(f"Failed to initialize store (API key issue): {e}")
    except Exception as e:
        error_msg = str(e)
        if "CREATE INDEX CONCURRENTLY" in error_msg:
            logger.info(
                "Store setup deferred (will initialize on first use to avoid transaction conflict)"
            )
        else:
            logger.warning(f"Failed to initialize store (will retry on first use): {e}")

    yield

    # Shutdown: Close database connections and pools
    await close_checkpointer()
    await close_store()
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

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=response.model_dump()
    )


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
