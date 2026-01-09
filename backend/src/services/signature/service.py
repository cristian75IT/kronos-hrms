"""Signature Service.

Enterprise-grade business logic layer with:
- MFA OTP verification via Auth Service
- Document hash calculation (SHA-256)
- Immutable signature transaction creation
- Audit trail integration
- Pagination support
"""
import hashlib
from uuid import UUID
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from src.core.exceptions import ConflictError, AuthorizationError
from src.services.signature.models import SignatureTransaction
from src.services.signature.repository import SignatureRepository, PaginatedResult
from src.services.signature.schemas import SignatureCreate

from src.services.auth.service import UserService
from src.services.audit.service import AuditService
from src.services.audit.schemas import AuditLogCreate

# Note: In a stricter microservice architecture, we would use an HTTP Client to call Auth Service.
# Since this is a modular monolith, we import the service class directly but treat it as a library.


class SignatureService:
    """
    Core business logic for digital signatures.
    
    Handles the complete signing workflow:
    1. OTP verification
    2. Hash calculation/validation
    3. Transaction persistence
    4. Audit trail creation
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._repo = SignatureRepository(session)
        self._user_service = UserService(session)
        self._audit_service = AuditService(session)

    async def _log_audit(
        self, 
        actor_id: UUID, 
        event_type: str, 
        resource_type: str,
        resource_id: str,
        description: str
    ):
        """Helper to log audit events."""
        await self._audit_service.log_action(AuditLogCreate(
            user_id=actor_id,
            action=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            service_name="signature-service"
        ))

    async def sign_document(
        self, 
        user_id: UUID, 
        data: SignatureCreate, 
        request: Request = None
    ) -> SignatureTransaction:
        """
        Execute a legally binding digital signature.
        
        Process:
        1. Verify OTP using Auth Service (Keycloak TOTP)
        2. Calculate document hash if not provided
        3. Extract forensic metadata (IP, User-Agent)
        4. Persist immutable transaction
        5. Create audit trail record
        
        Args:
            user_id: ID of the user performing the signature
            data: Signature request payload
            request: FastAPI request object for metadata extraction
            
        Returns:
            The created SignatureTransaction
            
        Raises:
            PermissionDeniedError: If OTP verification fails
            ConflictError: If neither hash nor content is provided
        """
        # 1. Verify OTP
        is_valid = await self._user_service.verify_user_otp(user_id, data.otp_code)
        if not is_valid:
            # Log failed attempt for security monitoring
            await self._log_audit(
                actor_id=user_id,
                event_type="SIGNATURE_OTP_FAILED",
                resource_type="signature",
                resource_id=data.document_id,
                description=f"OTP verification failed for {data.document_type}"
            )
            raise AuthorizationError("Codice OTP non valido o scaduto")

        # 2. Calculate or validate document hash
        document_hash = data.document_hash
        if not document_hash:
            if not data.document_content:
                raise ConflictError("Must provide either document_hash or document_content")
            document_hash = hashlib.sha256(data.document_content.encode('utf-8')).hexdigest()
            
        # 3. Extract forensic metadata
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        # Allow override from payload (for internal service calls)
        if data.ip_address:
            ip_address = data.ip_address
        if data.user_agent:
            user_agent = data.user_agent

        # 4. Create immutable transaction
        transaction = SignatureTransaction(
            user_id=user_id,
            document_type=data.document_type,
            document_id=data.document_id,
            document_hash=document_hash,
            signature_method="MFA_TOTP",
            provider="KEYCLOAK",
            otp_verified=True,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=self._parse_user_agent(user_agent) if user_agent else {}
        )
        
        created = await self._repo.create(transaction)
        
        # 5. Create audit trail record
        await self._log_audit(
            actor_id=user_id,
            event_type="SIGNATURE_CREATED",
            resource_type="signature",
            resource_id=str(created.id),
            description=f"Signed {data.document_type} document {data.document_id}"
        )
        
        return created

    async def get_transaction(self, id: UUID) -> Optional[SignatureTransaction]:
        """Get a signature transaction by ID."""
        return await self._repo.get(id)

    async def get_history(self, document_type: str, document_id: str):
        """Get all signatures for a specific document."""
        return await self._repo.get_by_document(document_type, document_id)

    async def get_my_signatures(self, user_id: UUID):
        """Get all signatures for a user (no pagination)."""
        return await self._repo.get_by_user(user_id)

    async def get_my_signatures_paginated(
        self, 
        user_id: UUID,
        page: int = 1,
        page_size: int = 25
    ) -> PaginatedResult:
        """
        Get signatures for a user with pagination.
        
        Args:
            user_id: The user's UUID
            page: Page number (1-indexed)
            page_size: Items per page
            
        Returns:
            PaginatedResult with items and total count
        """
        offset = (page - 1) * page_size
        return await self._repo.get_by_user_paginated(
            user_id=user_id,
            offset=offset,
            limit=page_size
        )

    def _parse_user_agent(self, user_agent: str) -> Dict[str, Any]:
        """
        Parse User-Agent string to extract device info.
        
        This is a simplified parser. In production, consider using
        a library like `user-agents` for comprehensive parsing.
        """
        info: Dict[str, Any] = {"raw": user_agent[:200]}  # Truncate for storage
        
        # Simple heuristics
        ua_lower = user_agent.lower()
        if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
            info["device_type"] = "mobile"
        elif "tablet" in ua_lower or "ipad" in ua_lower:
            info["device_type"] = "tablet"
        else:
            info["device_type"] = "desktop"
            
        if "chrome" in ua_lower:
            info["browser"] = "Chrome"
        elif "firefox" in ua_lower:
            info["browser"] = "Firefox"
        elif "safari" in ua_lower:
            info["browser"] = "Safari"
        elif "edge" in ua_lower:
            info["browser"] = "Edge"
            
        return info
