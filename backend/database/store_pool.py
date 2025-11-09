"""
PostgreSQL Store Pool for LangGraph Long-Term Memory

This module provides a singleton AsyncPostgresStore instance for storing
user-specific memories across sessions with semantic search capabilities.
"""
import asyncio
from config.settings import settings
from langchain_openai import OpenAIEmbeddings
from langgraph.store.postgres.aio import AsyncPostgresStore
from psycopg_pool import AsyncConnectionPool
from psycopg import AsyncConnection
from common.logger import get_logger

logger = get_logger(__name__)

_store = None
_pool = None
_setup_completed = False


async def _setup_store_with_autocommit():
    """Setup store using a connection with autocommit mode."""
    # Validate API key is set
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not set. Please add your OpenAI API key to the .env file"
        )
    
    # Initialize embeddings for semantic search
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=api_key,
    )
    
    # Get a direct connection with autocommit for setup
    conn = await AsyncConnection.connect(
        conninfo=settings.psycopg_database_url,
        autocommit=True
    )
    try:
        # Create a temporary store just for setup
        temp_store = AsyncPostgresStore(
            conn,
            index={
                "embed": embeddings,
                "dims": 1536,
            }
        )
        await temp_store.setup()
        logger.info("Store tables created successfully")
    finally:
        await conn.close()


async def get_async_store():
    """
    Get or create the singleton AsyncPostgresStore instance with semantic search.
    Ensures setup() is called successfully before returning.
    
    Returns:
        AsyncPostgresStore: Configured store instance with embeddings
    """
    global _store, _pool, _setup_completed
    
    if _store is None:
        # Validate API key is set
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not set. Please add your OpenAI API key to the .env file"
            )
        
        # Create connection pool for the store
        _pool = AsyncConnectionPool(
            conninfo=settings.psycopg_database_url,
            min_size=1,
            max_size=20,
            timeout=30,
            open=False,
        )
        await _pool.open()
        
        # Initialize embeddings for semantic search with explicit API key
        # Using OpenAI embeddings matching our embedding_service configuration
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key,
        )
        
        # Create store with semantic search enabled
        _store = AsyncPostgresStore(
            _pool,
            index={
                "embed": embeddings,
                "dims": 1536,  # Matching text-embedding-3-small dimensions
            }
        )
    
    # Ensure setup is completed successfully
    if not _setup_completed:
        max_retries = 5
        retry_delay = 0.2
        
        for attempt in range(max_retries):
            try:
                # Try normal setup first
                await _store.setup()
                _setup_completed = True
                logger.info("PostgreSQL store setup completed successfully")
                break
            except Exception as e:
                error_msg = str(e)
                if "CREATE INDEX CONCURRENTLY" in error_msg or "transaction" in error_msg.lower():
                    if attempt < max_retries - 1:
                        # Wait a bit and retry
                        await asyncio.sleep(retry_delay)
                        logger.info(f"Retrying store setup (attempt {attempt + 1}/{max_retries})")
                        continue
                    else:
                        # Last attempt: use autocommit connection
                        logger.info("Using autocommit connection for store setup")
                        try:
                            await _setup_store_with_autocommit()
                            _setup_completed = True
                            logger.info("Store setup completed with autocommit")
                            break
                        except Exception as autocommit_error:
                            logger.error(f"Store setup failed even with autocommit: {autocommit_error}")
                            raise
                elif "does not exist" in error_msg.lower() or "relation" in error_msg.lower():
                    # Table doesn't exist - try autocommit setup
                    logger.info("Tables missing, using autocommit connection for setup")
                    try:
                        await _setup_store_with_autocommit()
                        _setup_completed = True
                        logger.info("Store setup completed with autocommit")
                        break
                    except Exception as autocommit_error:
                        logger.error(f"Store setup failed: {autocommit_error}")
                        raise
                else:
                    logger.error(f"Store setup failed: {e}")
                    raise
    
    return _store


async def close_store():
    """Close the store connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("PostgreSQL store connection pool closed")

