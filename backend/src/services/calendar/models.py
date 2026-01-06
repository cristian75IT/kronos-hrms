"""KRONOS Calendar Service - Enterprise Models."""
from datetime import date, datetime, time
from typing import Optional
from uuid import UUID, uuid4
import enum
from decimal import Decimal

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
    Enum as SQLEnum,
    CheckConstraint,
    Numeric
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class CalendarType(str, enum.Enum):
    """Type of calendar."""
    SYSTEM = "SYSTEM"       # Read-only global calendars (e.g. National Holidays)
    LOCATION = "LOCATION"   # Location-specific calendars (auto-assigned)
    PERSONAL = "PERSONAL"   # Created by users
    TEAM = "TEAM"           # Shared team calendars


class CalendarPermission(str, enum.Enum):
    """Permission level for shared calendars."""
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"


class Calendar(Base):
    """
    Unified Calendar Entity.
    
    Serves as the container for events, holidays (if system), and rules.
    """
    __tablename__ = "calendars"
    __table_args__ = {"schema": "calendar"}

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Classification
    type: Mapped[CalendarType] = mapped_column(SQLEnum(CalendarType, native_enum=False), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[str] = mapped_column(String(7), default="#4F46E5")
    visibility: Mapped[str] = mapped_column(String(20), default="private")
    
    # Ownership (System calendars have no owner)
    owner_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), index=True)
    
    # System flags
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Relationships
    events: Mapped[list["CalendarEvent"]] = relationship(
        back_populates="calendar", 
        cascade="all, delete-orphan"
    )
    shares: Mapped[list["CalendarShare"]] = relationship(
        back_populates="calendar", 
        cascade="all, delete-orphan"
    )
    
    # Link to Profile (if it's a holiday calendar)
    holiday_profile: Mapped[Optional["HolidayProfile"]] = relationship(back_populates="calendar")


class CalendarShare(Base):
    """
    Unified Sharing Model.
    
    Defines who can access which calendar and with what permissions.
    """
    __tablename__ = "calendar_shares"
    __table_args__ = (
        UniqueConstraint('calendar_id', 'user_id', name='uq_calendar_share_user'),
        {"schema": "calendar"}
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    calendar_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("calendar.calendars.id", ondelete="CASCADE"), 
        nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    
    # Permission
    permission: Mapped[CalendarPermission] = mapped_column(
        SQLEnum(CalendarPermission, native_enum=False),
        default=CalendarPermission.READ
    )
    
    # Mandatory shares cannot be removed by users (for System/Location calendars)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    calendar: Mapped["Calendar"] = relationship(back_populates="shares")


class WorkWeekProfile(Base):
    """
    Dynamic Work Week Configuration.
    
    Defines working days and hours separate from code logic.
    """
    __tablename__ = "work_week_profiles"
    __table_args__ = {"schema": "calendar"}

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # e.g., STANDARD_5
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Weekly Config (JSONB)
    # {
    #   "monday": {"is_working": true, "hours": 8.0},
    #   "saturday": {"is_working": false}
    # }
    weekly_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    total_weekly_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=40.0)
    
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )


class HolidayProfile(Base):
    """
    Groups holidays for easier assignment (e.g. Italy National, Milan Local).
    """
    __tablename__ = "holiday_profiles"
    __table_args__ = {"schema": "calendar"}

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    calendar_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calendar.calendars.id", ondelete="CASCADE"),
        unique=True
    )
    
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    country_code: Mapped[Optional[str]] = mapped_column(String(2))
    region_code: Mapped[Optional[str]] = mapped_column(String(10))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    calendar: Mapped["Calendar"] = relationship(back_populates="holiday_profile")
    holidays: Mapped[list["CalendarHoliday"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan"
    )


class LocationCalendar(Base):
    """
    Links a Location to its Time Rules (Work Week + Holiday Profiles).
    """
    __tablename__ = "location_calendars"
    __table_args__ = (
        UniqueConstraint('location_id', name='uq_location_calendar'),
        {"schema": "calendar"}
    )
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    
    work_week_profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calendar.work_week_profiles.id")
    )
    work_week_profile: Mapped["WorkWeekProfile"] = relationship()
    
    # Timezone
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Rome")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Relationships
    subscriptions: Mapped[list["LocationSubscription"]] = relationship(
        back_populates="location_config",
        cascade="all, delete-orphan"
    )

class LocationSubscription(Base):
    """
    Links a Location to a Calendar (e.g. National Holidays).
    """
    __tablename__ = "location_subscriptions"
    __table_args__ = (
        UniqueConstraint('location_id', 'calendar_id', name='uq_location_subscription'),
        {"schema": "calendar"}
    )
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # We link to LocationCalendar (config) AND store the raw location_id for query speed/integrity
    location_calendar_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calendar.location_calendars.id", ondelete="CASCADE"),
        nullable=False
    )
    
    location_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    
    calendar_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calendar.calendars.id", ondelete="CASCADE"),
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    location_config: Mapped["LocationCalendar"] = relationship(back_populates="subscriptions")
    calendar: Mapped["Calendar"] = relationship()



class CalendarHoliday(Base):
    """
    Specific holiday definition.
    Linked to a profile for reuse.
    """
    __tablename__ = "holidays"
    __table_args__ = {"schema": "calendar"}
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Link to Profile (Enterprise)
    profile_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calendar.holiday_profiles.id", ondelete="CASCADE"),
        index=True
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    date: Mapped[Optional[date]] = mapped_column(Date, index=True) # Specific date (legacy/fixed)
    
    # Recurrence (Enterprise)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[Optional[dict]] = mapped_column(JSONB) # {"month": 1, "day": 1} or {"type": "easter", "offset": 1}
    
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Relationships
    profile: Mapped[Optional["HolidayProfile"]] = relationship(back_populates="holidays")


class CalendarEvent(Base):
    """
    Generic calendar event.
    Refactored to use unified Calendar.
    """
    __tablename__ = "events"
    __table_args__ = {"schema": "calendar"}
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Link to Unified Calendar
    calendar_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calendar.calendars.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[Optional[time]] = mapped_column(Time)
    end_time: Mapped[Optional[time]] = mapped_column(Time)
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=True)
    
    event_type: Mapped[str] = mapped_column(String(30), default="generic")
    visibility: Mapped[str] = mapped_column(String(20), default="private")
    
    # Additional fields from DB schema
    color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    status: Mapped[str] = mapped_column(String(20), default="confirmed")
    location: Mapped[Optional[str]] = mapped_column(String(200))
    is_virtual: Mapped[bool] = mapped_column(Boolean, default=False)
    meeting_url: Mapped[Optional[str]] = mapped_column(String(500))
    event_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    alert_before_minutes: Mapped[Optional[int]] = mapped_column(Integer, default=2880)
    user_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    # Recurrence
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(String(200))
    parent_event_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calendar.events.id", ondelete="CASCADE"),
    )
    
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    calendar: Mapped["Calendar"] = relationship(back_populates="events")
    participants: Mapped[list["EventParticipant"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )


class EventParticipant(Base):
    """Participant in a calendar event."""
    __tablename__ = "event_participants"
    __table_args__ = (
        UniqueConstraint('event_id', 'user_id', name='uq_event_participant'),
        {"schema": "calendar"}
    )
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("calendar.events.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    
    response_status: Mapped[str] = mapped_column(String(20), default="pending")
    is_organizer: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    event: Mapped["CalendarEvent"] = relationship(back_populates="participants")


class WorkingDayException(Base):
    """Manual exception to working rules."""
    __tablename__ = "working_day_exceptions"
    __table_args__ = {"schema": "calendar"}
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    exception_type: Mapped[str] = mapped_column(String(20), nullable=False) # working, non_working
    reason: Mapped[Optional[str]] = mapped_column(String(200))
    
    location_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CalendarClosure(Base):
    """Company closure."""
    __tablename__ = "closures"
    __table_args__ = {"schema": "calendar"}
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
