import aioredis
import json
from typing import Any

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}", decode_responses=True)

async def get_cache(key: str) -> Any:
    value = await redis.get(key)
    if value:
        return json.loads(value)
    return None

async def set_cache(key: str, value: Any, expire: int = 300):
    """expire in seconds, default 5 minutes"""
    await redis.set(key, json.dumps(value), ex=expire)
