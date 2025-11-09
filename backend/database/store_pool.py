"""
PostgreSQL Store Pool for LangGraph Long-Term Memory

This module provides a singleton AsyncPostgresStore instance for storing
user-specific memories across sessions with semantic search capabilities.
"""
from config.settings import settings
from langchain_openai import OpenAIEmbeddings
from langgraph.store.postgres.aio import AsyncPostgresStore
from psycopg_pool import AsyncConnectionPool
from common.logger import get_logger

logger = get_logger(__name__)

_store = None
_pool = None


async def get_async_store():
    """
    Get or create the singleton AsyncPostgresStore instance with semantic search.
    
    Returns:
        AsyncPostgresStore: Configured store instance with embeddings
    """
    global _store, _pool
    
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
        
        # Setup the store (creates necessary tables)
        await _store.setup()
        logger.info("PostgreSQL store initialized with semantic search")
    
    return _store


async def close_store():
    """Close the store connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("PostgreSQL store connection pool closed")

