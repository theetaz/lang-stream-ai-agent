import asyncio
from config.settings import settings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from psycopg import AsyncConnection
from common.logger import get_logger

logger = get_logger(__name__)

_checkpointer = None
_pool = None
_setup_completed = False


async def _setup_checkpointer_with_autocommit():
    """Setup checkpointer using a connection with autocommit mode."""
    # Get a direct connection with autocommit for setup
    conn = await AsyncConnection.connect(
        conninfo=settings.psycopg_database_url,
        autocommit=True
    )
    try:
        # Create a temporary saver just for setup
        temp_saver = AsyncPostgresSaver(conn)
        await temp_saver.setup()
        logger.info("Checkpointer tables created successfully")
    finally:
        await conn.close()


async def get_async_checkpointer():
    """
    Get or create the singleton AsyncPostgresSaver instance for checkpointing.
    Ensures setup() is called successfully before returning.
    """
    global _checkpointer, _pool, _setup_completed
    
    if _checkpointer is None:
        _pool = AsyncConnectionPool(
            conninfo=settings.psycopg_database_url,
            min_size=1,
            max_size=20,
            timeout=30,
            open=False,
        )
        await _pool.open()
        _checkpointer = AsyncPostgresSaver(_pool)
    
    # Ensure setup is completed successfully
    if not _setup_completed:
        max_retries = 5
        retry_delay = 0.2
        
        for attempt in range(max_retries):
            try:
                # Try normal setup first
                await _checkpointer.setup()
                _setup_completed = True
                logger.info("Checkpointer setup completed successfully")
                break
            except Exception as e:
                error_msg = str(e)
                if "CREATE INDEX CONCURRENTLY" in error_msg or "transaction" in error_msg.lower():
                    if attempt < max_retries - 1:
                        # Wait a bit and retry
                        await asyncio.sleep(retry_delay)
                        logger.info(f"Retrying checkpointer setup (attempt {attempt + 1}/{max_retries})")
                        continue
                    else:
                        # Last attempt: use autocommit connection
                        logger.info("Using autocommit connection for checkpointer setup")
                        try:
                            await _setup_checkpointer_with_autocommit()
                            _setup_completed = True
                            logger.info("Checkpointer setup completed with autocommit")
                            break
                        except Exception as autocommit_error:
                            logger.error(f"Checkpointer setup failed even with autocommit: {autocommit_error}")
                            raise
                elif "does not exist" in error_msg.lower() or "relation" in error_msg.lower():
                    # Table doesn't exist - try autocommit setup
                    logger.info("Tables missing, using autocommit connection for setup")
                    try:
                        await _setup_checkpointer_with_autocommit()
                        _setup_completed = True
                        logger.info("Checkpointer setup completed with autocommit")
                        break
                    except Exception as autocommit_error:
                        logger.error(f"Checkpointer setup failed: {autocommit_error}")
                        raise
                else:
                    logger.error(f"Checkpointer setup failed: {e}")
                    raise
    
    return _checkpointer


async def close_checkpointer():
    global _pool
    if _pool:
        await _pool.close()
