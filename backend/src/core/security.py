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
    """Decoded JWT token payload."""
    
    sub: str  # Keycloak user ID
    email: Optional[str] = None
    name: Optional[str] = None
    preferred_username: Optional[str] = None
    realm_access: Optional[dict] = None
    
    @property
    def keycloak_id(self) -> str:
        """Get Keycloak user ID."""
        return self.sub
    
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
        return self.has_role("admin")
    
    @property
    def is_manager(self) -> bool:
        """Check if user is manager or admin."""
        return self.has_role("manager") or self.is_admin
    
    @property
    def is_approver(self) -> bool:
        """Check if user has approver capability."""
        return self.has_role("approver") or self.is_admin


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
        # Get public key for verification
        public_key = (
            "-----BEGIN PUBLIC KEY-----\n"
            + keycloak_openid.public_key()
            + "\n-----END PUBLIC KEY-----"
        )
        
        # Decode token
        payload = keycloak_openid.decode_token(
            token,
            key=public_key,
            options={
                "verify_signature": True,
                "verify_aud": False,
                "verify_exp": True,
            },
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
    """Get current token payload.
    
    Use this when you only need token info, not full user object.
    """
    return await decode_token(token)


async def require_admin(
    token: TokenPayload = Depends(get_current_token),
) -> TokenPayload:
    """Require admin role."""
    if not token.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return token


async def require_manager(
    token: TokenPayload = Depends(get_current_token),
) -> TokenPayload:
    """Require manager or admin role."""
    if not token.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager role required",
        )
    return token


async def require_approver(
    token: TokenPayload = Depends(get_current_token),
) -> TokenPayload:
    """Require approver capability."""
    if not token.is_approver:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approver capability required",
        )
    return token
