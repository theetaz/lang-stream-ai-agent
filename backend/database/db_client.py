from typing import AsyncGenerator

from config.settings import settings
from models.base import Base
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

# Async database setup (default)
async_engine = create_async_engine(
    settings.async_database_url,
    echo=settings.ENVIRONMENT == "development",
    pool_size=5,  # Number of connections to maintain
    max_overflow=10,  # Maximum number of connections beyond pool_size
    pool_pre_ping=True,  # Verify connections are alive before using
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync database setup (available if needed)
sync_engine = create_engine(
    settings.database_url,
    echo=settings.ENVIRONMENT == "development",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    future=True,
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables based on SQLAlchemy models.
    This should be called on application startup.

    All models are automatically imported via models/__init__.py
    """
    # Import models package to ensure all models are registered with Base
    import models  # noqa: F401

    async with async_engine.begin() as conn:
        # Create all tables defined in Base.metadata
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close all database connections and dispose of connection pools.
    This should be called on application shutdown for graceful cleanup.
    """
    await async_engine.dispose()
    sync_engine.dispose()
