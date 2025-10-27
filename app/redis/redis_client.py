import os

import redis
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    decode_responses=True,
)


def set_cache(key: str, value: str, ttl: int = 3600):
    redis_client.setex(key, ttl, value)


def get_cache(key: str) -> str:
    return redis_client.get(key)
