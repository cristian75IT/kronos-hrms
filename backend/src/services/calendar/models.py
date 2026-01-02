"""KRONOS Calendar Service - SQLAlchemy Models."""
from datetime import date, datetime, time
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class CalendarHoliday(Base):
    """National, regional, and local holidays.
    
    Migrated from config.holidays with enhanced functionality.
    Supports recurring holidays via RRULE patterns.
    """
    
    __tablename__ = "holidays"
    __table_args__ = {"schema": "calendar"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Date (for specific year holidays)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Scope
    scope: Mapped[str] = mapped_column(String(20), default="national")  # national, regional, local, company
    location_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))  # For local holidays
    region_code: Mapped[Optional[str]] = mapped_column(String(10))  # e.g., SAR, LOM
    
    # Recurrence (RRULE pattern for auto-generation)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(String(200))  # RRULE format
    
    # Status
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class CalendarClosure(Base):
    """Company-wide closures (collective holidays, emergencies, etc.).
    
    Migrated from config.company_closures with enhanced functionality.
    """
    
    __tablename__ = "closures"
    __table_args__ = {"schema": "calendar"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Date range
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Closure scope
    closure_type: Mapped[str] = mapped_column(String(20), default="total")  # total, partial
    affected_departments: Mapped[Optional[list]] = mapped_column(JSONB)
    affected_locations: Mapped[Optional[list]] = mapped_column(JSONB)
    
    # Policy
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True)
    consumes_leave_balance: Mapped[bool] = mapped_column(Boolean, default=False)
    leave_type_code: Mapped[Optional[str]] = mapped_column(String(10))  # e.g., FERIE if consumes balance
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class CalendarEvent(Base):
    """Generic calendar events (meetings, reminders, personal events).
    
    Extensible model for future enhancements like meetings, rooms, etc.
    """
    
    __tablename__ = "events"
    __table_args__ = {"schema": "calendar"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Date/Time
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[Optional[time]] = mapped_column(Time)
    end_time: Mapped[Optional[time]] = mapped_column(Time)
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Event Type
    event_type: Mapped[str] = mapped_column(String(30), default="generic")  # generic, meeting, reminder, training
    
    # Ownership
    user_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), index=True)  # Owner
    visibility: Mapped[str] = mapped_column(String(20), default="private")  # private, team, public
    
    # Location
    location: Mapped[Optional[str]] = mapped_column(String(200))
    is_virtual: Mapped[bool] = mapped_column(Boolean, default=False)
    meeting_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Recurrence
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(String(200))  # RRULE format
    parent_event_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calendar.events.id", ondelete="CASCADE"),
    )
    
    # Metadata
    color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    event_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="confirmed")  # tentative, confirmed, cancelled
    
    # Audit
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    # Relationships
    participants: Mapped[list["EventParticipant"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )


class EventParticipant(Base):
    """Participants in a calendar event."""
    
    __tablename__ = "event_participants"
    __table_args__ = (
        UniqueConstraint('event_id', 'user_id', name='uq_event_participant'),
        {"schema": "calendar"}
    )
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calendar.events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    
    # Response
    response_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, accepted, declined, tentative
    is_organizer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Audit
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationships
    event: Mapped["CalendarEvent"] = relationship(back_populates="participants")


class WorkingDayException(Base):
    """Exceptions to the standard working week.
    
    Allows defining days that are normally non-working as working days
    or vice versa (e.g., Saturday work recovery).
    """
    
    __tablename__ = "working_day_exceptions"
    __table_args__ = {"schema": "calendar"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Exception type
    exception_type: Mapped[str] = mapped_column(String(20), nullable=False)  # working, non_working
    reason: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Scope
    location_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))  # NULL = all locations
    department_code: Mapped[Optional[str]] = mapped_column(String(50))  # NULL = all departments
    
    # Audit
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
