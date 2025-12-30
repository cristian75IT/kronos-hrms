"""KRONOS Audit Service - SQLAlchemy Models."""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class AuditLog(Base):
    """Audit log for tracking all user actions.
    
    Records: WHO did WHAT, WHEN, from WHERE, with what RESULT.
    """
    
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "audit"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # WHO
    user_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    user_email: Mapped[Optional[str]] = mapped_column(String(255))
    
    # WHAT
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATE, READ, UPDATE, DELETE, LOGIN, etc.
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # LeaveRequest, User, etc.
    resource_id: Mapped[Optional[str]] = mapped_column(String(100))  # UUID as string
    
    # DETAILS
    description: Mapped[Optional[str]] = mapped_column(Text)
    request_data: Mapped[Optional[dict]] = mapped_column(JSONB)  # Input data (sanitized)
    response_data: Mapped[Optional[dict]] = mapped_column(JSONB)  # Output data (summary)
    
    # WHERE
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    endpoint: Mapped[Optional[str]] = mapped_column(String(255))  # API endpoint
    http_method: Mapped[Optional[str]] = mapped_column(String(10))
    
    # RESULT
    status: Mapped[str] = mapped_column(String(20), default="SUCCESS")  # SUCCESS, FAILURE, ERROR
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # SERVICE
    service_name: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # WHEN
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class AuditTrail(Base):
    """Audit trail for entity versioning.
    
    Maintains complete history of entity changes with snapshots.
    """
    
    __tablename__ = "audit_trail"
    __table_args__ = {"schema": "audit"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Entity identification
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Table/model name
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)   # Primary key
    
    # Version
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Change type
    operation: Mapped[str] = mapped_column(String(10), nullable=False)  # INSERT, UPDATE, DELETE
    
    # Snapshot
    before_data: Mapped[Optional[dict]] = mapped_column(JSONB)  # State before change
    after_data: Mapped[Optional[dict]] = mapped_column(JSONB)   # State after change
    changed_fields: Mapped[Optional[list]] = mapped_column(JSONB)  # List of changed fields
    
    # Who and when
    changed_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    changed_by_email: Mapped[Optional[str]] = mapped_column(String(255))
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Context
    change_reason: Mapped[Optional[str]] = mapped_column(Text)
    service_name: Mapped[str] = mapped_column(String(50), nullable=False)
    request_id: Mapped[Optional[str]] = mapped_column(String(100))  # Correlation ID
