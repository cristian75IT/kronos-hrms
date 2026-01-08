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
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.services.config.models import ContractType, NationalContract, NationalContractLevel


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
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    
    # Employment info
    badge_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    fiscal_code: Mapped[Optional[str]] = mapped_column(String(16), unique=True)
    hire_date: Mapped[Optional[datetime]] = mapped_column(Date)
    termination_date: Mapped[Optional[datetime]] = mapped_column(Date)
    
    # Work configuration
    contract_type_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("config.contract_types.id"),
    )
    work_schedule_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.work_schedules.id"),
    )
    location_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.locations.id"),
    )

    # Organizational Assignment
    department_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.departments.id"),
    )
    service_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.organizational_services.id"),
    )
    executive_level_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.executive_levels.id"),
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

    is_hr: Mapped[bool] = mapped_column(Boolean, default=False)
    is_employee: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_synced: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
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
    contract_type: Mapped[Optional["ContractType"]] = relationship()
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
    profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="UserProfile.user_id",
    )
    contracts: Mapped[list["EmployeeContract"]] = relationship(
        back_populates="user",
        order_by="desc(EmployeeContract.start_date)",
        cascade="all, delete-orphan",
    )
    trainings: Mapped[list["EmployeeTraining"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    # Organization Relationships
    department_entity: Mapped[Optional["Department"]] = relationship(
        foreign_keys=[department_id],
        back_populates="users",
    )
    service_entity: Mapped[Optional["OrganizationalService"]] = relationship(
        foreign_keys=[service_id],
        back_populates="users",
    )
    executive_level: Mapped[Optional["ExecutiveLevel"]] = relationship(
        back_populates="users",
    )
    
    # Management Roles
    managed_departments: Mapped[list["Department"]] = relationship(
        foreign_keys="Department.manager_id",
        back_populates="manager",
    )
    deputy_managed_departments: Mapped[list["Department"]] = relationship(
        foreign_keys="Department.deputy_manager_id",
        back_populates="deputy_manager",
    )
    coordinated_services: Mapped[list["OrganizationalService"]] = relationship(
        foreign_keys="OrganizationalService.coordinator_id",
        back_populates="coordinator",
    )
    deputy_coordinated_services: Mapped[list["OrganizationalService"]] = relationship(
        foreign_keys="OrganizationalService.deputy_coordinator_id",
        back_populates="deputy_coordinator",
    )
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"


class UserProfile(Base):
    """Extended user profile."""
    
    __tablename__ = "user_profiles"
    __table_args__ = {"schema": "auth"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    
    # Contact & Work Info
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    department: Mapped[Optional[str]] = mapped_column(String(100))
    position: Mapped[Optional[str]] = mapped_column(String(100))
    employee_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    
    # Legacy fields (kept for compatibility with existing DB structure if any)
    hire_date: Mapped[Optional[datetime]] = mapped_column(Date)
    contract_type: Mapped[Optional[str]] = mapped_column(String(50))
    weekly_hours: Mapped[Optional[float]] = mapped_column(
        postgresql.NUMERIC(4, 1), # Use numeric for precision if needed, but float is mapped here
        default=40.0
    )
    location: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Manager link (redundant with User.manager_id but present in schema)
    manager_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="SET NULL"),
    )
    
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
    user: Mapped["User"] = relationship(back_populates="profile", foreign_keys=[user_id])


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


class EmployeeContract(Base):
    """Employee contract history (storicizzazione contratti)."""
    
    __tablename__ = "employee_contracts"
    __table_args__ = {"schema": "auth"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    contract_type_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("config.contract_types.id"),
        nullable=False
    )
    national_contract_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("config.national_contracts.id"),
        nullable=True
    )
    level_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("config.national_contract_levels.id"),
        nullable=True
    )
    
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(Date)
    
    # Contract details
    weekly_hours: Mapped[Optional[int]] = mapped_column(Integer, comment="Ore settimanali effettive")
    job_title: Mapped[Optional[str]] = mapped_column(String(100))
    department: Mapped[Optional[str]] = mapped_column(String(100))
    
    wage_data: Mapped[Optional[dict]] = mapped_column(
        Text, 
    )
    document_path: Mapped[Optional[str]] = mapped_column(Text)
    
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
    user: Mapped["User"] = relationship(back_populates="contracts")
    contract_type: Mapped["ContractType"] = relationship()
    national_contract: Mapped["NationalContract"] = relationship()
    level: Mapped["NationalContractLevel"] = relationship()


class EmployeeTraining(Base):
    """Safety training records for employees (D.Lgs. 81/08)."""
    
    __tablename__ = "employee_trainings"
    __table_args__ = {"schema": "auth"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Training details
    training_type: Mapped[str] = mapped_column(String(50), nullable=False) # GENERAL, SPECIFIC_RISK, etc.
    description: Mapped[Optional[str]] = mapped_column(String(200))
    
    issue_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(Date) # Some don't expire
    
    certificate_id: Mapped[Optional[str]] = mapped_column(String(100))
    hours: Mapped[Optional[int]] = mapped_column(Integer)
    
    provider: Mapped[Optional[str]] = mapped_column(String(200))
    document_path: Mapped[Optional[str]] = mapped_column(Text)
    
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
    user: Mapped["User"] = relationship(back_populates="trainings")



class ExecutiveLevel(Base):
    """C-Suite and executive hierarchy levels."""
    __tablename__ = "executive_levels"
    __table_args__ = {"schema": "auth"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # CEO, CIO, etc.
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    hierarchy_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=CEO, 2=C-Suite
    
    # Escalation target
    escalates_to_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.executive_levels.id"),
    )
    
    # Approval authority
    max_approval_amount: Mapped[Optional[float]] = mapped_column(postgresql.NUMERIC(12, 2))
    can_override_workflow: Mapped[bool] = mapped_column(Boolean, default=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
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
    escalates_to: Mapped[Optional["ExecutiveLevel"]] = relationship(remote_side=[id])
    users: Mapped[list["User"]] = relationship(back_populates="executive_level")


class Department(Base):
    """Organizational department."""
    __tablename__ = "departments"
    __table_args__ = {"schema": "auth"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Hierarchy
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.departments.id"),
    )
    hierarchy_level: Mapped[int] = mapped_column(Integer, default=2)
    
    # Manager
    manager_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.users.id"),
    )
    deputy_manager_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.users.id"),
    )
    
    cost_center_code: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
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
    parent: Mapped[Optional["Department"]] = relationship(
        remote_side=[id],
        back_populates="children",
    )
    children: Mapped[list["Department"]] = relationship(back_populates="parent")
    manager: Mapped[Optional["User"]] = relationship(
        foreign_keys=[manager_id],
        back_populates="managed_departments",
    )
    deputy_manager: Mapped[Optional["User"]] = relationship(
        foreign_keys=[deputy_manager_id],
        back_populates="deputy_managed_departments",
    )
    services: Mapped[list["OrganizationalService"]] = relationship(back_populates="department")
    users: Mapped[list["User"]] = relationship(
        foreign_keys="User.department_id",
        back_populates="department_entity",
    )


class OrganizationalService(Base):
    """Service/Unit within a department."""
    __tablename__ = "organizational_services"
    __table_args__ = {"schema": "auth"}
    
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Parent Department
    department_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.departments.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Coordinator
    coordinator_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.users.id"),
    )
    deputy_coordinator_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth.users.id"),
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
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
    department: Mapped["Department"] = relationship(back_populates="services")
    coordinator: Mapped[Optional["User"]] = relationship(
        foreign_keys=[coordinator_id],
        back_populates="coordinated_services",
    )
    deputy_coordinator: Mapped[Optional["User"]] = relationship(
        foreign_keys=[deputy_coordinator_id],
        back_populates="deputy_coordinated_services",
    )
    users: Mapped[list["User"]] = relationship(
        foreign_keys="User.service_id",
        back_populates="service_entity",
    )


class Permission(Base):
    """RBAC Permission (Resource + Action)."""
    __tablename__ = "permissions"
    __table_args__ = {"schema": "auth"}
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False) # e.g. leaves:create
    resource: Mapped[str] = mapped_column(String, nullable=False) # LEAVES
    action: Mapped[str] = mapped_column(String, nullable=False) # CREATE
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Role(Base):
    """RBAC Role (Collection of Permissions)."""
    __tablename__ = "roles"
    __table_args__ = {"schema": "auth"}
    
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    parent_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("auth.roles.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False) # keycloak role name
    display_name: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Hierarchy
    parent: Mapped[Optional["Role"]] = relationship("Role", remote_side=[id], back_populates="children")
    children: Mapped[list["Role"]] = relationship("Role", back_populates="parent")

    permissions: Mapped[list["Permission"]] = relationship(
        secondary="auth.role_permissions",
        # lazy="selectin"  <-- Removed to let Repository handle loading explicitly
    )


class RolePermission(Base):
    """Link Table Role <-> Permission."""
    __tablename__ = "role_permissions"
    __table_args__ = {"schema": "auth"}
    
    role_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("auth.roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("auth.permissions.id", ondelete="CASCADE"), primary_key=True)
    scope: Mapped[str] = mapped_column(String, primary_key=True, default="GLOBAL") # GLOBAL, AREA, LOCATION, OWN
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

