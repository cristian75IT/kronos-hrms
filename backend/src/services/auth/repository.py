"""KRONOS Auth Service - Repository Layer (Aggregator)."""
from src.services.auth.repositories.user import UserRepository
from src.services.auth.repositories.org_legacy import AreaRepository, LocationRepository
from src.services.auth.repositories.org_structure import (
    ExecutiveLevelRepository,
    DepartmentRepository,
    OrganizationalServiceRepository,
)
from src.services.auth.repositories.contracts import (
    ContractTypeRepository,
    WorkScheduleRepository,
    EmployeeContractRepository,
)
from src.services.auth.repositories.training import EmployeeTrainingRepository
from src.services.auth.repositories.rbac import RoleRepository, PermissionRepository

__all__ = [
    "UserRepository",
    "AreaRepository",
    "LocationRepository",
    "ExecutiveLevelRepository",
    "DepartmentRepository",
    "OrganizationalServiceRepository",
    "ContractTypeRepository",
    "WorkScheduleRepository",
    "EmployeeContractRepository",
    "EmployeeTrainingRepository",
    "RoleRepository",
    "PermissionRepository",
]
