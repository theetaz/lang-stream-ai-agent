from config.settings import settings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

_checkpointer = None
_pool = None


async def get_async_checkpointer():
    global _checkpointer, _pool
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
        await _checkpointer.setup()
    return _checkpointer


async def close_checkpointer():
    global _pool
    if _pool:
        await _pool.close()
