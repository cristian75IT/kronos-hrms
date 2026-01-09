"""Signature Service Schemas.

Enterprise-grade Pydantic models for:
- Request validation with enhanced constraints
- Response serialization with pagination
- Type safety across the API boundary
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
import re


class SignatureCreate(BaseModel):
    """Payload for signing a document with MFA OTP verification."""
    
    document_type: str = Field(
        ..., 
        min_length=1,
        max_length=50,
        description="Type of document (e.g., SW_AGREEMENT, CONTRACT)",
        examples=["SW_AGREEMENT"]
    )
    document_id: str = Field(
        ..., 
        min_length=1,
        max_length=50,
        description="Unique identifier of the document entity",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    document_content: Optional[str] = Field(
        None, 
        max_length=100000,
        description="Document content to hash. Either this or document_hash must be provided."
    )
    document_hash: Optional[str] = Field(
        None, 
        min_length=64,
        max_length=64,
        description="Pre-calculated SHA-256 hash (64 hex characters)"
    )
    
    otp_code: str = Field(
        ..., 
        min_length=6,
        max_length=6,
        description="6-digit TOTP code from authenticator app",
        examples=["123456"]
    )
    
    # Optional metadata overrides (usually inferred from request)
    user_agent: Optional[str] = Field(None, max_length=500)
    ip_address: Optional[str] = Field(None, max_length=45)

    @field_validator('otp_code')
    @classmethod
    def validate_otp_code(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError('OTP code must contain only digits')
        return v

    @field_validator('document_hash')
    @classmethod
    def validate_document_hash(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r'^[a-fA-F0-9]{64}$', v):
            raise ValueError('document_hash must be a valid SHA-256 hash (64 hex characters)')
        return v.lower() if v else v

    @field_validator('document_type')
    @classmethod
    def validate_document_type(cls, v: str) -> str:
        # Normalize to uppercase
        return v.upper().strip()


class SignatureResponse(BaseModel):
    """Response after successful signature creation."""
    
    id: UUID = Field(..., description="Unique signature transaction ID")
    signed_at: datetime = Field(..., description="Timestamp when signature was applied")
    document_hash: str = Field(..., description="SHA-256 hash of the signed document")
    signature_method: str = Field(..., description="Method used for signing (e.g., MFA_TOTP)")
    status: str = Field(default="SIGNED", description="Signature status")

    model_config = {"from_attributes": True}


class SignatureVerificationResponse(BaseModel):
    """Detailed signature information for verification purposes."""
    
    id: UUID = Field(..., description="Unique signature transaction ID")
    user_id: UUID = Field(..., description="ID of the user who signed")
    document_type: str = Field(..., description="Type of signed document")
    document_id: str = Field(..., description="ID of the signed document")
    document_hash: str = Field(..., description="SHA-256 hash for integrity verification")
    signed_at: datetime = Field(..., description="Timestamp when signature was applied")
    signature_method: str = Field(..., description="Signing method used")
    is_valid: bool = Field(..., description="Whether the signature is currently valid")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional forensic metadata (IP, User-Agent)"
    )

    model_config = {"from_attributes": True}


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""
    
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class SignatureListResponse(BaseModel):
    """Paginated response for signature lists."""
    
    data: List[SignatureVerificationResponse] = Field(
        ..., 
        description="List of signature records"
    )
    meta: PaginationMeta = Field(..., description="Pagination information")
