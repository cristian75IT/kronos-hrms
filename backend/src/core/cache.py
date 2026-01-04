"""KRONOS Backend - Redis Caching Utility."""
import json
from typing import Any, Optional, Union

import redis.asyncio as redis
from src.core.config import settings

# Global Redis client
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or initialize the global async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url, 
            encoding="utf-8", 
            decode_responses=True
        )
    return _redis_client


async def cache_set(key: str, value: Any, expire_seconds: int = 300) -> None:
    """Set a value in Redis with expiration."""
    client = get_redis_client()
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    await client.set(key, value, ex=expire_seconds)


async def cache_get(key: str, as_json: bool = False) -> Optional[Union[str, Any]]:
    """Get a value from Redis."""
    client = get_redis_client()
    value = await client.get(key)
    if value and as_json:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


async def cache_delete(key: str) -> None:
    """Delete a key from Redis."""
    client = get_redis_client()
    await client.delete(key)
