from contextlib import asynccontextmanager

from api.routes import router as api_router
from api.user_routes import router as user_router
from database import init_db, close_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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


app = FastAPI(title="AI Agent API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to the AI Agent API"}
