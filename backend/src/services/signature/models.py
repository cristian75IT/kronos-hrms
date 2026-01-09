"""Signature Service Models."""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, func, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from src.core.database import Base

class SignatureTransaction(Base):
    """
    Immutable records of digital signatures.
    Represents a specific act of signing a document version by a user.
    """
    __tablename__ = "signature_transactions"
    __table_args__ = {"schema": "signature"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Actor
    user_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    actor_id: Mapped[Optional[UUID]] = mapped_column(nullable=True) # If signed on behalf (e.g. assisted) or admin override

    # Document Context
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # e.g. 'SW_AGREEMENT'
    document_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)   # External ID
    document_hash: Mapped[str] = mapped_column(String(64), nullable=False) # SHA-256
    document_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Signature Details
    signature_method: Mapped[str] = mapped_column(String(20), default="MFA_TOTP")
    provider: Mapped[str] = mapped_column(String(20), default="KEYCLOAK")
    otp_verified: Mapped[bool] = mapped_column(Boolean, default=True)

    # Forensic Metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    device_info: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
