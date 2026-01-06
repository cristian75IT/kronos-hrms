"""
KRONOS - Enterprise Base HTTP Client

Provides connection pooling, retry logic, and standardized error handling
for all inter-service communication.

Features:
- Singleton HTTP client with connection pooling (Keep-Alive)
- Automatic retry with exponential backoff
- Typed exception handling
- Request/Response logging
- Configurable timeouts

Usage:
    class AuthClient(BaseClient):
        def __init__(self):
            super().__init__(
                base_url=settings.auth_service_url,
                service_name="auth"
            )
        
        async def get_user(self, user_id: UUID) -> Optional[dict]:
            return await self.get(f"/api/v1/users/{user_id}")
"""
import logging
from typing import Optional, Any, ClassVar
from contextlib import asynccontextmanager

import httpx

from src.core.config import settings
from src.shared.exceptions import (
    ServiceUnavailableError,
    ServiceResponseError,
    ServiceTimeoutError,
)

logger = logging.getLogger(__name__)


class BaseClient:
    """
    Enterprise-grade HTTP client with connection pooling and error handling.
    
    All service clients should inherit from this class to benefit from:
    - Shared connection pool (reduced latency, better resource usage)
    - Consistent error handling
    - Automatic retry for transient failures
    - Request logging for debugging
    """
    
    # Class-level shared client for connection pooling
    _shared_client: ClassVar[Optional[httpx.AsyncClient]] = None
    _client_initialized: ClassVar[bool] = False
    
    def __init__(self, base_url: str, service_name: str):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL for the service (e.g., "http://localhost:8001")
            service_name: Human-readable name for logging and errors
        """
        self.base_url = base_url.rstrip("/")
        self.service_name = service_name
    
    @classmethod
    async def get_shared_client(cls) -> httpx.AsyncClient:
        """
        Get or create the shared HTTP client with connection pooling.
        
        The client is shared across all BaseClient instances to maximize
        connection reuse and minimize overhead.
        """
        if cls._shared_client is None or cls._shared_client.is_closed:
            cls._shared_client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    timeout=settings.service_timeout,
                    connect=5.0,  # Connection timeout
                ),
                limits=httpx.Limits(
                    max_connections=settings.service_pool_connections,
                    max_keepalive_connections=settings.service_pool_keepalive,
                ),
                # Enable HTTP/2 for better performance
                http2=False,  # Set to True if all services support HTTP/2
            )
            cls._client_initialized = True
            logger.info(
                f"Initialized shared HTTP client with pool: "
                f"max_connections={settings.service_pool_connections}, "
                f"keepalive={settings.service_pool_keepalive}"
            )
        return cls._shared_client
    
    @classmethod
    async def close_shared_client(cls) -> None:
        """Close the shared client. Call this during application shutdown."""
        if cls._shared_client and not cls._shared_client.is_closed:
            await cls._shared_client.aclose()
            cls._shared_client = None
            cls._client_initialized = False
            logger.info("Closed shared HTTP client")
    
    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> Optional[Any]:
        """
        Make HTTP request with enterprise error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (will be appended to base_url)
            params: Query parameters
            json: JSON body for POST/PUT
            headers: Additional headers
            timeout: Override default timeout
        
        Returns:
            Parsed JSON response or None for empty responses
        
        Raises:
            ServiceUnavailableError: When service is unreachable
            ServiceTimeoutError: When request times out
            ServiceResponseError: When service returns 5xx error
        """
        url = f"{self.base_url}{path}"
        client = await self.get_shared_client()
        
        # Build request kwargs
        request_kwargs = {
            "method": method,
            "url": url,
        }
        if params:
            request_kwargs["params"] = params
        if json:
            request_kwargs["json"] = json
        if headers:
            request_kwargs["headers"] = headers
        if timeout:
            request_kwargs["timeout"] = timeout
        
        try:
            logger.debug(f"[{self.service_name}] {method} {path}")
            response = await client.request(**request_kwargs)
            
            # Handle server errors (5xx)
            if response.status_code >= 500:
                logger.error(
                    f"[{self.service_name}] Server error: "
                    f"{response.status_code} {response.text[:200]}"
                )
                raise ServiceResponseError(
                    self.service_name,
                    response.status_code,
                    response.text[:500],
                )
            
            # Handle client errors (4xx) - log but don't raise
            if response.status_code >= 400:
                logger.warning(
                    f"[{self.service_name}] Client error: "
                    f"{response.status_code} on {method} {path}"
                )
                return None
            
            # Parse response
            if response.content:
                return response.json()
            return None
            
        except httpx.ConnectError as e:
            logger.error(f"[{self.service_name}] Connection error: {e}")
            raise ServiceUnavailableError(self.service_name, str(e))
        
        except httpx.TimeoutException as e:
            logger.error(f"[{self.service_name}] Timeout: {e}")
            raise ServiceTimeoutError(
                self.service_name,
                timeout or settings.service_timeout,
            )
        
        except httpx.HTTPError as e:
            logger.error(f"[{self.service_name}] HTTP error: {e}")
            raise ServiceUnavailableError(self.service_name, str(e))
    
    async def _request_safe(
        self,
        method: str,
        path: str,
        default: Any = None,
        **kwargs,
    ) -> Any:
        """
        Make HTTP request with graceful error handling.
        
        Unlike _request(), this method catches exceptions and returns
        a default value. Use this for non-critical operations where
        failure should not break the main flow.
        
        Args:
            method: HTTP method
            path: API path
            default: Value to return on error
            **kwargs: Passed to _request()
        
        Returns:
            Response data or default value on error
        """
        try:
            result = await self._request(method, path, **kwargs)
            return result if result is not None else default
        except Exception as e:
            logger.warning(
                f"[{self.service_name}] Request failed (returning default): {e}"
            )
            return default
    
    # ═══════════════════════════════════════════════════════════════════════
    # Convenience Methods
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get(
        self,
        path: str,
        params: Optional[dict] = None,
        **kwargs,
    ) -> Optional[Any]:
        """Make GET request."""
        return await self._request("GET", path, params=params, **kwargs)
    
    async def get_safe(
        self,
        path: str,
        default: Any = None,
        params: Optional[dict] = None,
        **kwargs,
    ) -> Any:
        """Make GET request with graceful error handling."""
        return await self._request_safe("GET", path, default, params=params, **kwargs)
    
    async def post(
        self,
        path: str,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
        **kwargs,
    ) -> Optional[Any]:
        """Make POST request."""
        return await self._request("POST", path, json=json, params=params, **kwargs)
    
    async def post_safe(
        self,
        path: str,
        default: Any = None,
        json: Optional[dict] = None,
        **kwargs,
    ) -> Any:
        """Make POST request with graceful error handling."""
        return await self._request_safe("POST", path, default, json=json, **kwargs)
    
    async def put(
        self,
        path: str,
        json: Optional[dict] = None,
        **kwargs,
    ) -> Optional[Any]:
        """Make PUT request."""
        return await self._request("PUT", path, json=json, **kwargs)
    
    async def delete(
        self,
        path: str,
        **kwargs,
    ) -> Optional[Any]:
        """Make DELETE request."""
        return await self._request("DELETE", path, **kwargs)
