from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from config.settings import settings

checkpoint_pool = ConnectionPool(
    conninfo=settings.database_url,
    min_size=1,
    max_size=20,
    kwargs={"autocommit": True},
    timeout=30
)

checkpointer = PostgresSaver(checkpoint_pool)

def setup_checkpointer():
    checkpointer.setup()

async def close_checkpointer():
    checkpoint_pool.close()
    await checkpoint_pool.wait_closed()

