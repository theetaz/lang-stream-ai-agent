"""
Async database connection and session management for PostgreSQL.
Uses asyncpg driver with SQLAlchemy async engine.
"""
import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)

# Use Base from models.base instead of creating a new one
from models.base import Base

# Load environment variables
load_dotenv()

# Database configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "lang_ai_agent")

# Async database URL using asyncpg driver
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Create async engine
# echo=True enables SQL query logging (useful for development)
# pool_pre_ping=True ensures connections are alive before using them
async_engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    pool_size=5,  # Number of connections to maintain
    max_overflow=10,  # Maximum number of connections to create beyond pool_size
    pool_pre_ping=True,  # Verify connections before using
)

# Create async session factory
# expire_on_commit=False prevents SQLAlchemy from expiring objects after commit
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function for FastAPI to get async database session.

    Usage in FastAPI routes:
    ```python
    @router.get("/users")
    async def get_users(db: AsyncSession = Depends(get_async_db)):
        result = await db.execute(select(User))
        return result.scalars().all()
    ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.
    This should be called on application startup.
    """
    # Import all models here to ensure they're registered
    from models.user import User
    from models.session import Session
    from models.base import Base

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close all database connections.
    This should be called on application shutdown.
    """
    await async_engine.dispose()
