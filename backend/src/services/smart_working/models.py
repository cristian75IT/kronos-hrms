"""
KRONOS - Smart Working Models
"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import String, Date, Integer, Boolean, ForeignKey, JSON, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.core.database import Base
import enum

class SWAgreementStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"
    DRAFT = "DRAFT"

class SWRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class SWAgreement(Base):
    """
    Long-term Smart Working Agreement between company and employee.
    Defines general rules like allowed days per week and which weekdays.
    
    Historization: When a new agreement is created, previous active agreements
    are automatically expired to maintain a clear audit trail.
    """
    __tablename__ = "sw_agreements"
    __table_args__ = {"schema": "smart_working"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # Note: No FK constraint to auth.users - cross-schema FKs are not supported in microservice architecture
    user_id: Mapped[UUID] = mapped_column(index=True)
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    allowed_days_per_week: Mapped[int] = mapped_column(Integer, default=2)
    
    # Weekdays allowed for smart working: 0=Monday, 1=Tuesday, ..., 4=Friday
    # If NULL, any weekday is allowed (up to allowed_days_per_week limit)
    allowed_weekdays: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(Integer), 
        nullable=True,
        comment="0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday"
    )
    
    status: Mapped[SWAgreementStatus] = mapped_column(
        Enum(SWAgreementStatus, name="sw_agreement_status", schema="smart_working"),
        default=SWAgreementStatus.DRAFT
    )
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    # Note: No FK constraint to auth.users - cross-schema FKs are not supported in microservice architecture
    created_by: Mapped[UUID] = mapped_column()

    # Relationships
    requests: Mapped[list["SWRequest"]] = relationship(back_populates="agreement")


class SWRequest(Base):
    """
    Daily Smart Working Request.
    Linked to an active agreement.
    """
    __tablename__ = "sw_requests"
    __table_args__ = {"schema": "smart_working"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # Note: No FK constraint to auth.users - cross-schema FKs are not supported in microservice architecture
    user_id: Mapped[UUID] = mapped_column(index=True)
    agreement_id: Mapped[UUID] = mapped_column(ForeignKey("smart_working.sw_agreements.id"), index=True)
    
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    status: Mapped[SWRequestStatus] = mapped_column(
        Enum(SWRequestStatus, name="sw_request_status", schema="smart_working"),
        default=SWRequestStatus.PENDING
    )
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Approval fields - No FK constraints for cross-schema references
    approval_request_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    approver_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    agreement: Mapped["SWAgreement"] = relationship(back_populates="requests")
    attendance: Mapped[Optional["SWAttendance"]] = relationship(back_populates="request", uselist=False)


class SWAttendance(Base):
    """
    Optional Check-in/Check-out for a Smart Working day.
    """
    __tablename__ = "sw_attendance"
    __table_args__ = {"schema": "smart_working"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(ForeignKey("smart_working.sw_requests.id"), unique=True)
    
    check_in: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="e.g. Home, Co-working")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    request: Mapped["SWRequest"] = relationship(back_populates="attendance")
