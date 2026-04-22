from typing import Optional

import redis.asyncio as redis

from app.core.config import get_settings

_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        if not settings.redis_url:
            raise RuntimeError("REDIS_URL is empty; redis is disabled for this environment.")
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
