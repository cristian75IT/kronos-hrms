"""KRONOS Auth Service - SQLAlchemy Models."""
from datetime import datetime
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
    Table,
    Column,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


# Association table: User <-> Area (Many-to-Many)
user_areas = Table(
    "user_areas",
    Base.metadata,
    Column("user_id", PG_UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True),
    Column("area_id", PG_UUID(as_uuid=True), ForeignKey("auth.areas.id", ondelete="CASCADE"), primary_key=True),
    schema="auth",
)


class User(Base):
    """User model synchronized from Keycloak.
    
    This is a local copy of user data from Keycloak.
    The source of truth for authentication is Keycloak.
    """
    
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Keycloak sync
    keycloak_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Basic info
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Employment info
    badge_number: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    fiscal_code: Mapped[Optional[str]] = mapped_column(String(16), unique=True)
    hire_date: Mapped[Optional[datetime]] = mapped_column(Date)
    termination_date: Mapped[Optional[datetime]] = mapped_column(Date)
    
    # Work configuration
    contract_type_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.contract_types.id"),
    )
    work_schedule_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.work_schedules.id"),
    )
    location_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.locations.id"),
    )
    
    # Manager relationship
    manager_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.users.id"),
    )
    
    # Roles (cached from Keycloak)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_manager: Mapped[bool] = mapped_column(Boolean, default=False)
    is_approver: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
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
    contract_type: Mapped[Optional["ContractType"]] = relationship(back_populates="users")
    work_schedule: Mapped[Optional["WorkSchedule"]] = relationship(back_populates="users")
    location: Mapped[Optional["Location"]] = relationship(back_populates="users")
    manager: Mapped[Optional["User"]] = relationship(
        remote_side=[id],
        back_populates="subordinates",
    )
    subordinates: Mapped[list["User"]] = relationship(back_populates="manager")
    areas: Mapped[list["Area"]] = relationship(
        secondary=user_areas,
        back_populates="users",
    )
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"


class Area(Base):
    """Organizational area/department."""
    
    __tablename__ = "areas"
    __table_args__ = {"schema": "auth"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.areas.id"),
    )
    manager_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.users.id"),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationships
    parent: Mapped[Optional["Area"]] = relationship(
        remote_side=[id],
        back_populates="children",
    )
    children: Mapped[list["Area"]] = relationship(back_populates="parent")
    users: Mapped[list["User"]] = relationship(
        secondary=user_areas,
        back_populates="areas",
    )


class Location(Base):
    """Work location/office."""
    
    __tablename__ = "locations"
    __table_args__ = {"schema": "auth"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    province: Mapped[Optional[str]] = mapped_column(String(2))
    
    # Santo Patrono for local holiday
    patron_saint_name: Mapped[Optional[str]] = mapped_column(String(100))
    patron_saint_date: Mapped[Optional[datetime]] = mapped_column(Date)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="location")


class ContractType(Base):
    """Employment contract type."""
    
    __tablename__ = "contract_types"
    __table_args__ = {"schema": "auth"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Part-time configuration
    is_part_time: Mapped[bool] = mapped_column(Boolean, default=False)
    part_time_percentage: Mapped[int] = mapped_column(Integer, default=100)  # 50%, 75%, etc.
    
    # Leave accrual
    annual_vacation_days: Mapped[int] = mapped_column(Integer, default=26)
    annual_rol_hours: Mapped[int] = mapped_column(Integer, default=104)
    annual_permit_hours: Mapped[int] = mapped_column(Integer, default=32)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="contract_type")


class WorkSchedule(Base):
    """Work schedule profile."""
    
    __tablename__ = "work_schedules"
    __table_args__ = {"schema": "auth"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Weekly hours per day (0 = not working)
    monday_hours: Mapped[int] = mapped_column(Integer, default=8)
    tuesday_hours: Mapped[int] = mapped_column(Integer, default=8)
    wednesday_hours: Mapped[int] = mapped_column(Integer, default=8)
    thursday_hours: Mapped[int] = mapped_column(Integer, default=8)
    friday_hours: Mapped[int] = mapped_column(Integer, default=8)
    saturday_hours: Mapped[int] = mapped_column(Integer, default=0)
    sunday_hours: Mapped[int] = mapped_column(Integer, default=0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    
    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="work_schedule")
    
    @property
    def weekly_hours(self) -> int:
        """Calculate total weekly hours."""
        return (
            self.monday_hours +
            self.tuesday_hours +
            self.wednesday_hours +
            self.thursday_hours +
            self.friday_hours +
            self.saturday_hours +
            self.sunday_hours
        )
