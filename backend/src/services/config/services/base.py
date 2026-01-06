"""
KRONOS - Config Service Base

Shared dependencies and initialization for config sub-services.
"""
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.services.config.repository import ConfigRepository


class BaseConfigService:
    """
    Base class for config service modules.
    
    Provides shared dependencies:
    - Database session and repository
    - Redis cache client
    - Cache utilities
    """
    
    CACHE_PREFIX = "config:"
    CACHE_TTL = 300  # 5 minutes
    
    def __init__(
        self,
        session: AsyncSession,
        redis_client: Optional[redis.Redis] = None,
    ):
        self._session = session
        self._repo = ConfigRepository(session)
        self._redis = redis_client
    
    # ═══════════════════════════════════════════════════════════════════════
    # Cache Utilities
    # ═══════════════════════════════════════════════════════════════════════
    
    async def _invalidate_cache(self, key: Optional[str] = None) -> None:
        """Invalidate cache for a specific key or all config."""
        if not self._redis:
            return
        
        try:
            if key:
                await self._redis.delete(f"{self.CACHE_PREFIX}{key}")
            else:
                # Clear all config cache
                keys = await self._redis.keys(f"{self.CACHE_PREFIX}*")
                if keys:
                    await self._redis.delete(*keys)
        except Exception:
            pass
    
    async def clear_cache(self) -> None:
        """Clear the entire Redis cache for this service."""
        await self._invalidate_cache()
    
    def _parse_value(self, value: Any, value_type: str) -> Any:
        """Convert JSONB value to Python type."""
        import json
        
        if value is None:
            return None
        
        type_map = {
            "string": str,
            "integer": int,
            "float": float,
            "boolean": lambda v: v if isinstance(v, bool) else str(v).lower() in ("true", "1", "yes"),
            "json": lambda v: v if isinstance(v, (dict, list)) else json.loads(v),
        }
        
        converter = type_map.get(value_type, lambda x: x)
        return converter(value)
