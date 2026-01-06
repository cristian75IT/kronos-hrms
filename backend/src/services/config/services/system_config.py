"""
KRONOS - System Configuration Service

Handles system configuration (key-value settings).
"""
import json
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ConflictError
from src.shared.audit_client import get_audit_logger
from src.services.config.repository import SystemConfigRepository
from src.services.config.schemas import SystemConfigCreate


class SystemConfigService:
    """
    Service for system configuration with Redis cache.
    
    Handles:
    - Get/set configuration values
    - Cache management
    - Config creation
    """
    
    CACHE_PREFIX = "config:"
    CACHE_TTL = 300  # 5 minutes
    
    def __init__(
        self,
        session: AsyncSession,
        redis_client: Optional[redis.Redis] = None,
    ) -> None:
        self._session = session
        self._config_repo = SystemConfigRepository(session)
        self._redis = redis_client
        self._audit = get_audit_logger("config-service")
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get config value with cache.
        
        Args:
            key: Config key (e.g., 'leave.min_notice_days.rol')
            default: Fallback value if not found
            
        Returns:
            Config value (automatically typed based on value_type)
        """
        # Try cache first
        if self._redis:
            cache_key = f"{self.CACHE_PREFIX}{key}"
            cached = await self._redis.get(cache_key)
            if cached is not None:
                return json.loads(cached)
        
        # Query database
        config = await self._config_repo.get_by_key(key)
        if config is None:
            return default
        
        # Parse value
        value = self._parse_value(config.value, config.value_type)
        
        # Cache result
        if self._redis:
            await self._redis.setex(
                cache_key,
                self.CACHE_TTL,
                json.dumps(value),
            )
        
        return value
    
    async def set(self, key: str, value: Any, user_id: Optional[UUID] = None) -> None:
        """Update config value and invalidate cache."""
        config = await self._config_repo.get_by_key(key)
        if not config:
            raise NotFoundError(f"Config key not found: {key}")
        
        await self._config_repo.update(key, value=value)
        await self._invalidate_cache(key)
        
        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="SYSTEM_CONFIG",
            resource_id=key,
            description=f"Updated system config: {key}",
            request_data={"value": value}
        )
    
    async def get_by_category(self, category: str) -> dict[str, Any]:
        """Get all configs in a category."""
        configs = await self._config_repo.get_by_category(category)
        return {
            c.key: self._parse_value(c.value, c.value_type)
            for c in configs
        }
    
    async def get_all(self) -> list:
        """Get all configs with parsed values."""
        configs = await self._config_repo.get_all()
        for config in configs:
            config.value = self._parse_value(config.value, config.value_type)
        return configs
    
    async def create_config(self, data: SystemConfigCreate, user_id: Optional[UUID] = None):
        """Create new config entry."""
        existing = await self._config_repo.get_by_key(data.key)
        if existing:
            raise ConflictError(f"Config key already exists: {data.key}")
        
        config = await self._config_repo.create(
            key=data.key,
            value=data.value,
            value_type=data.value_type,
            category=data.category,
            description=data.description,
            is_sensitive=data.is_sensitive,
        )
        
        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="SYSTEM_CONFIG",
            resource_id=data.key,
            description=f"Created system config: {data.key}",
            request_data=data.model_dump(mode="json")
        )
        
        return config
    
    def _parse_value(self, value: Any, value_type: str) -> Any:
        """Convert JSONB value to Python type."""
        if value is None:
            return None
            
        try:
            if value_type == "integer":
                return int(value)
            elif value_type in ["float", "decimal"]:
                return float(value)
            elif value_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes")
                return bool(value)
            elif value_type == "json":
                if isinstance(value, str):
                    return json.loads(value)
                return value
            else:
                return str(value)
        except (ValueError, TypeError, json.JSONDecodeError):
            return value
    
    async def _invalidate_cache(self, key: Optional[str] = None) -> None:
        """Invalidate cache for a specific key or all config."""
        if not self._redis:
            return
        
        if key:
            await self._redis.delete(f"{self.CACHE_PREFIX}{key}")
        else:
            # Use SCAN to find all config keys (safer than KEYS)
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(
                    cursor,
                    match=f"{self.CACHE_PREFIX}*",
                    count=100,
                )
                if keys:
                    await self._redis.delete(*keys)
                if cursor == 0:
                    break
    
    async def clear_cache(self) -> None:
        """Clear the entire Redis cache for this service."""
        if not self._redis:
            return
        await self._redis.flushdb()
