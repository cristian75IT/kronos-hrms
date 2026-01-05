"""KRONOS Auth Service - Pydantic Schemas."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from src.shared.schemas import BaseSchema, IDMixin, TimestampMixin, DataTableRequest, DataTableResponse


# ═══════════════════════════════════════════════════════════
# User Schemas
# ═══════════════════════════════════════════════════════════

class UserBase(BaseModel):
    """Base user schema."""
    
    email: str  # Using str instead of EmailStr to allow .local domains
    username: str = Field(..., max_length=100)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    badge_number: Optional[str] = Field(None, max_length=50)
    fiscal_code: Optional[str] = Field(None, max_length=16)
    hire_date: Optional[date] = None
    termination_date: Optional[date] = None


class UserCreate(UserBase):
    """Schema for creating user from Keycloak sync."""
    
    keycloak_id: str
    is_admin: bool = False
    is_manager: bool = False
    is_approver: bool = False

    is_hr: bool = False
    is_employee: bool = True


class UserUpdate(BaseModel):
    """Schema for updating user."""
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    badge_number: Optional[str] = None
    fiscal_code: Optional[str] = None
    hire_date: Optional[date] = None
    termination_date: Optional[date] = None
    contract_type_id: Optional[UUID] = None
    work_schedule_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_manager: Optional[bool] = None
    is_approver: Optional[bool] = None

    is_hr: Optional[bool] = None
    is_employee: Optional[bool] = None
    
    # Organization
    department_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    executive_level_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None # Explicitly ensuring it is here as well if needed explicitly


class UserProfileBase(BaseModel):
    """Base user profile schema."""
    
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    employee_number: Optional[str] = None
    avatar_url: Optional[str] = None
    hire_date: Optional[date] = None
    contract_type: Optional[str] = None
    weekly_hours: float = 40.0
    location: Optional[str] = None


class UserProfileResponse(UserProfileBase, IDMixin, BaseSchema):
    """Response schema for user profile."""
    pass


class UserResponse(UserBase, IDMixin, BaseSchema):
    """Response schema for user."""
    
    keycloak_id: str
    is_admin: bool
    is_manager: bool
    is_approver: bool

    is_hr: bool
    is_employee: bool
    is_active: bool
    full_name: str
    contract_type_id: Optional[UUID] = None
    work_schedule_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    last_sync_at: Optional[datetime] = None
    profile: Optional[UserProfileResponse] = None
    permissions: list[str] = []
    created_at: datetime
    updated_at: datetime
    
    # Organization
    department_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    executive_level_id: Optional[UUID] = None
    department: Optional[str] = None # Flattened name for convenience? Or relying on profile.department
    service: Optional[str] = None
    executive_level: Optional[str] = None


class UserListItem(BaseModel):
    """Simplified user for lists."""
    
    id: UUID
    email: str
    full_name: str
    badge_number: Optional[str] = None
    is_active: bool
    is_admin: bool
    is_manager: bool
    is_approver: bool = False

    is_hr: bool = False
    is_employee: bool = True
    
    department_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    executive_level_id: Optional[UUID] = None
    
    model_config = {"from_attributes": True}


class UserDataTableResponse(DataTableResponse[UserListItem]):
    """DataTable response for users."""
    pass


class CurrentUserResponse(BaseModel):
    """Response for current authenticated user."""
    
    id: UUID
    keycloak_id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    roles: list[str]
    is_admin: bool
    is_manager: bool
    is_approver: bool

    is_hr: bool
    is_employee: bool
    permissions: list[str] = []
    location: Optional[str] = None
    manager: Optional[str] = None


# ═══════════════════════════════════════════════════════════
# Area Schemas
# ═══════════════════════════════════════════════════════════

class AreaBase(BaseModel):
    """Base area schema."""
    
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None


class AreaCreate(AreaBase):
    """Schema for creating area."""
    pass


class AreaUpdate(BaseModel):
    """Schema for updating area."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class AreaResponse(AreaBase, IDMixin, BaseSchema):
    """Response schema for area."""
    
    is_active: bool


class AreaWithUsersResponse(AreaResponse):
    """Area response with users."""
    
    users: list[UserListItem] = []


# ═══════════════════════════════════════════════════════════
# Location Schemas
# ═══════════════════════════════════════════════════════════

class LocationBase(BaseModel):
    """Base location schema."""
    
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=2)
    patron_saint_name: Optional[str] = None
    patron_saint_date: Optional[date] = None


class LocationCreate(LocationBase):
    """Schema for creating location."""
    pass


class LocationUpdate(BaseModel):
    """Schema for updating location."""
    
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    patron_saint_name: Optional[str] = None
    patron_saint_date: Optional[date] = None
    is_active: Optional[bool] = None


class LocationResponse(LocationBase, IDMixin, BaseSchema):
    """Response schema for location."""
    
    is_active: bool


# ═══════════════════════════════════════════════════════════
# Contract Type Schemas
# ═══════════════════════════════════════════════════════════

class ContractTypeBase(BaseModel):
    """Base contract type schema."""
    
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    is_part_time: bool = False
    part_time_percentage: int = Field(default=100, ge=0, le=100)
    annual_vacation_days: int = Field(default=26, ge=0)
    annual_rol_hours: int = Field(default=104, ge=0)
    annual_permit_hours: int = Field(default=32, ge=0)


class ContractTypeCreate(ContractTypeBase):
    """Schema for creating contract type."""
    pass


class ContractTypeUpdate(BaseModel):
    """Schema for updating contract type."""
    
    name: Optional[str] = Field(None, max_length=100)
    is_part_time: Optional[bool] = None
    part_time_percentage: Optional[int] = Field(None, ge=0, le=100)
    annual_vacation_days: Optional[int] = Field(None, ge=0)
    annual_rol_hours: Optional[int] = Field(None, ge=0)
    annual_permit_hours: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ContractTypeResponse(ContractTypeBase, IDMixin, BaseSchema):
    """Response schema for contract type."""
    
    is_active: bool


# ═══════════════════════════════════════════════════════════
# Work Schedule Schemas
# ═══════════════════════════════════════════════════════════

class WorkScheduleBase(BaseModel):
    """Base work schedule schema."""
    
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    monday_hours: int = Field(default=8, ge=0, le=24)
    tuesday_hours: int = Field(default=8, ge=0, le=24)
    wednesday_hours: int = Field(default=8, ge=0, le=24)
    thursday_hours: int = Field(default=8, ge=0, le=24)
    friday_hours: int = Field(default=8, ge=0, le=24)
    saturday_hours: int = Field(default=0, ge=0, le=24)
    sunday_hours: int = Field(default=0, ge=0, le=24)


class WorkScheduleCreate(WorkScheduleBase):
    """Schema for creating work schedule."""
    pass


class WorkScheduleResponse(WorkScheduleBase, IDMixin, BaseSchema):
    """Response schema for work schedule."""
    
    is_active: bool
    weekly_hours: int


# ═══════════════════════════════════════════════════════════
# Employee Contract Schemas
# ═══════════════════════════════════════════════════════════

class EmployeeContractBase(BaseModel):
    """Base employee contract schema."""
    
    contract_type_id: UUID
    national_contract_id: Optional[UUID] = None
    level_id: Optional[UUID] = None
    start_date: date
    end_date: Optional[date] = None
    weekly_hours: Optional[int] = Field(None, ge=0)
    job_title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    document_path: Optional[str] = None


class EmployeeContractCreate(EmployeeContractBase):
    """Schema for creating employee contract."""
    pass


class EmployeeContractUpdate(BaseModel):
    """Schema for updating employee contract."""
    
    contract_type_id: Optional[UUID] = None
    national_contract_id: Optional[UUID] = None
    level_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    weekly_hours: Optional[int] = Field(None, ge=0)
    job_title: Optional[str] = None
    department: Optional[str] = None
    document_path: Optional[str] = None


class EmployeeContractResponse(EmployeeContractBase, IDMixin, BaseSchema):
    """Response schema for employee contract."""
    
    user_id: UUID
    contract_type: Optional[ContractTypeResponse] = None # Include full type info if joined


# ═══════════════════════════════════════════════════════════
# Keycloak Sync
# ═══════════════════════════════════════════════════════════

class KeycloakSyncRequest(BaseModel):
    """Request to sync users from Keycloak."""
    
    force_full_sync: bool = False


class KeycloakSyncResponse(BaseModel):
    """Response from Keycloak sync."""
    
    synced: int
    created: int
    updated: int
    deactivated: int
    errors: list[str] = []


# ═══════════════════════════════════════════════════════════
# Employee Training Schemas
# ═══════════════════════════════════════════════════════════

class EmployeeTrainingBase(BaseModel):
    """Base employee training schema."""
    
    training_type: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    issue_date: date
    expiry_date: Optional[date] = None
    certificate_id: Optional[str] = Field(None, max_length=100)
    hours: Optional[int] = Field(None, ge=0)
    provider: Optional[str] = Field(None, max_length=200)
    document_path: Optional[str] = None


class EmployeeTrainingCreate(EmployeeTrainingBase):
    """Schema for creating employee training."""
    
    user_id: UUID


class EmployeeTrainingUpdate(BaseModel):
    """Schema for updating employee training."""
    
    training_type: Optional[str] = None
    description: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    certificate_id: Optional[str] = None
    hours: Optional[int] = None
    provider: Optional[str] = None
    document_path: Optional[str] = None


class EmployeeTrainingResponse(EmployeeTrainingBase, IDMixin, TimestampMixin, BaseSchema):
    """Response schema for employee training."""
    
    user_id: UUID


# ═══════════════════════════════════════════════════════════
# RBAC Schemas
# ═══════════════════════════════════════════════════════════

class PermissionRead(BaseSchema, IDMixin):
    """Schema for permission read."""
    
    code: str
    resource: str
    action: str
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class RoleRead(BaseSchema, IDMixin):
    """Schema for role read."""
    
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_system: bool
    parent_id: Optional[UUID] = None
    permissions: list[PermissionRead] = []
    
    model_config = {"from_attributes": True}


class RolePermissionUpdate(BaseModel):
    """Schema for updating role permissions."""
    
    permission_ids: list[UUID]

    permission_ids: list[UUID]


# ═══════════════════════════════════════════════════════════
# Enterprise Organization Schemas
# ═══════════════════════════════════════════════════════════

class ExecutiveLevelBase(BaseModel):
    """Base executive level schema."""
    code: str = Field(..., max_length=20)
    title: str = Field(..., max_length=100)
    hierarchy_level: int
    escalates_to_id: Optional[UUID] = None
    max_approval_amount: Optional[float] = None
    can_override_workflow: bool = False

class ExecutiveLevelCreate(ExecutiveLevelBase):
    pass

class ExecutiveLevelUpdate(BaseModel):
    title: Optional[str] = None
    hierarchy_level: Optional[int] = None
    escalates_to_id: Optional[UUID] = None
    max_approval_amount: Optional[float] = None
    can_override_workflow: Optional[bool] = None
    is_active: Optional[bool] = None

class ExecutiveLevelResponse(ExecutiveLevelBase, IDMixin, TimestampMixin, BaseSchema):
    is_active: bool


class DepartmentBase(BaseModel):
    """Base department schema."""
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    deputy_manager_id: Optional[UUID] = None
    cost_center_code: Optional[str] = Field(None, max_length=50)

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    deputy_manager_id: Optional[UUID] = None
    cost_center_code: Optional[str] = None
    is_active: Optional[bool] = None

class DepartmentResponse(DepartmentBase, IDMixin, TimestampMixin, BaseSchema):
    is_active: bool
    manager: Optional[UserListItem] = None
    deputy_manager: Optional[UserListItem] = None


class OrganizationalServiceBase(BaseModel):
    """Base organizational service schema."""
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    department_id: UUID
    coordinator_id: Optional[UUID] = None
    deputy_coordinator_id: Optional[UUID] = None

class OrganizationalServiceCreate(OrganizationalServiceBase):
    pass

class OrganizationalServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[UUID] = None
    coordinator_id: Optional[UUID] = None
    deputy_coordinator_id: Optional[UUID] = None
    is_active: Optional[bool] = None

class OrganizationalServiceResponse(OrganizationalServiceBase, IDMixin, TimestampMixin, BaseSchema):
    is_active: bool
    department_name: Optional[str] = None
    coordinator: Optional[UserListItem] = None
    deputy_coordinator: Optional[UserListItem] = None
