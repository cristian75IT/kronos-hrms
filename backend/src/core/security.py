"""KRONOS Backend - Keycloak Security."""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from keycloak import KeycloakOpenID
from pydantic import BaseModel

from src.core.config import settings


# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.keycloak_url}realms/{settings.keycloak_realm}/protocol/openid-connect/token",
    auto_error=True,
)

# Keycloak client
keycloak_openid = KeycloakOpenID(
    server_url=settings.keycloak_url,
    client_id=settings.keycloak_client_id,
    realm_name=settings.keycloak_realm,
    client_secret_key=settings.keycloak_client_secret or None,
)


class TokenPayload(BaseModel):
    """Decoded JWT token payload with resolved internal user ID.
    
    The flow is:
    1. JWT contains Keycloak 'sub' (external identity)
    2. Auth layer resolves keycloak_id → internal_user_id (once per request)
    3. All services use internal_user_id consistently
    """
    
    sub: str  # Keycloak user ID
    email: Optional[str] = None
    name: Optional[str] = None
    preferred_username: Optional[str] = None
    realm_access: Optional[dict] = None
    
    # Internal user ID - resolved from keycloak_id
    # This is set by get_current_user dependency after DB lookup
    internal_user_id: Optional[UUID] = None
    
    # DB-based roles (merged with Keycloak roles)
    db_is_admin: bool = False
    db_is_manager: bool = False
    db_is_approver: bool = False
    db_is_hr: bool = False
    
    @property
    def keycloak_id(self) -> str:
        """Get Keycloak user ID (external identity)."""
        return self.sub
    
    @property
    def user_id(self) -> UUID:
        """Get internal user ID for database operations.
        
        This is the ID to use in all leave_balances, leave_requests, etc.
        Raises ValueError if not yet resolved (should never happen in normal flow).
        """
        if self.internal_user_id is None:
            raise ValueError(
                "Internal user ID not resolved. Use get_current_user dependency "
                "instead of get_current_token for endpoints that need user context."
            )
        return self.internal_user_id
    
    @property
    def roles(self) -> list[str]:
        """Get user roles from realm_access."""
        if self.realm_access and "roles" in self.realm_access:
            return self.realm_access["roles"]
        return []
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.has_role("admin") or self.db_is_admin
    
    @property
    def is_manager(self) -> bool:
        """Check if user is manager or admin."""
        return self.has_role("manager") or self.db_is_manager or self.is_admin
    
    @property
    def is_approver(self) -> bool:
        """Check if user has approver capability."""
        return self.has_role("approver") or self.db_is_approver or self.is_admin or self.is_hr

    @property
    def is_hr(self) -> bool:
        """Check if user is HR."""
        return self.has_role("hr") or self.db_is_hr or self.is_admin


async def decode_token(token: str) -> TokenPayload:
    """Decode and validate JWT token.
    
    Args:
        token: JWT access token.
        
    Returns:
        TokenPayload with user information.
        
    Raises:
        HTTPException: If token is invalid.
    """
    try:
        # Decode token with signature verification
        # python-keycloak 6.0 handles public key retrieval internally
        payload = keycloak_openid.decode_token(
            token,
            validate=True,
        )
        
        return TokenPayload(**payload)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_token(
    token: str = Depends(oauth2_scheme),
) -> TokenPayload:
    """Get current token payload (raw, without internal ID resolution).
    
    Use this only for simple role checks where you don't need the internal user ID.
    For most endpoints, use get_current_user instead.
    """
    return await decode_token(token)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> TokenPayload:
    """Get current user with resolved internal user ID.
    
    This is the primary dependency to use for endpoints that need user context.
    It decodes the JWT, then calls auth-service to resolve keycloak_id → internal_user_id.
    
    The internal_user_id is then accessible via token.user_id property.
    """
    import httpx
    
    payload = await decode_token(token)
    
    # Resolve keycloak_id to internal_user_id via auth service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.auth_service_url}/api/v1/users/by-keycloak/{payload.keycloak_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0,
            )
            
            if response.status_code == 200:
                user_data = response.json()
                payload.internal_user_id = UUID(user_data.get("id"))
                payload.db_is_admin = user_data.get("is_admin", False)
                payload.db_is_manager = user_data.get("is_manager", False)
                payload.db_is_approver = user_data.get("is_approver", False)
                payload.db_is_hr = user_data.get("is_hr", False)
            elif response.status_code == 404:
                # User not found in local DB - they may need to be synced
                # For now, raise an error
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found in system. Please contact administrator.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to resolve user identity",
                )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Auth service unavailable: {str(e)}",
        )
    
    return payload


async def require_admin(
    token: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Require admin role (with resolved internal ID)."""
    if not token.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return token


async def require_manager(
    token: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Require manager or admin role (with resolved internal ID)."""
    if not token.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager role required",
        )
    return token


async def require_approver(
    token: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Require approver capability (with resolved internal ID)."""
    if not token.is_approver:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approver capability required",
        )
    return token


async def require_hr(
    token: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Require HR or admin role (with resolved internal ID)."""
    if not token.is_hr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR role required",
        )
    return token
