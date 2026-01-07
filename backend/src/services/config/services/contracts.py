"""
KRONOS - National Contracts Service

Handles Italian national contracts (CCNL), versions, levels, and type configurations.
"""
from datetime import timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundError, ConflictError
from src.shared.audit_client import get_audit_logger
from src.services.config.models import (
    NationalContract,
    NationalContractVersion,
    NationalContractTypeConfig,
    NationalContractLevel,
    ContractType,
)


class NationalContractService:
    """
    Service for Italian national contracts (CCNL) management.
    
    Handles:
    - National contracts CRUD
    - Contract versions (historical tracking)
    - Contract type configurations
    - Contract levels
    """
    
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = get_audit_logger("config-service")
        
        # Inject repositories
        from ..repository import (
            NationalContractRepository,
            NationalContractVersionRepository,
            NationalContractLevelRepository,
            NationalContractTypeConfigRepository,
            ContractTypeRepository
        )
        self._repo = NationalContractRepository(session)
        self._version_repo = NationalContractVersionRepository(session)
        self._level_repo = NationalContractLevelRepository(session)
        self._config_repo = NationalContractTypeConfigRepository(session)
        self._type_repo = ContractTypeRepository(session)
    
    # ═══════════════════════════════════════════════════════════════════════
    # National Contracts
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_national_contracts(self, active_only: bool = True) -> list:
        """Get all national contracts with eager loading."""
        return await self._repo.get_all(active_only=active_only)
    
    async def get_national_contract(self, id: UUID):
        """Get national contract by ID with eager loading."""
        contract = await self._repo.get(id)
        if not contract:
            raise NotFoundError("National contract not found", entity_type="NationalContract", entity_id=str(id))
        return contract
    
    async def create_national_contract(self, data, user_id: Optional[UUID] = None):
        """Create new national contract."""
        # Check if code exists
        existing = await self._repo.get_by_code(data.code)
        
        if existing:
            raise ConflictError(f"National contract code already exists: {data.code}")
        
        contract = await self._repo.create(**data.model_dump())
        await self._session.commit()
        await self._session.refresh(contract)
        
        await self._audit.log_action(
            user_id=user_id,
            action="CREATE",
            resource_type="NATIONAL_CONTRACT",
            resource_id=str(contract.id),
            description=f"Created national contract: {contract.name} ({contract.code})",
            request_data=data.model_dump(mode="json")
        )
        return contract
    
    async def update_national_contract(self, id: UUID, data, user_id: Optional[UUID] = None):
        """Update national contract."""
        contract = await self._repo.get(id)
        
        if not contract:
            raise NotFoundError("National contract not found", entity_type="NationalContract", entity_id=str(id))
        
        update_data = data.model_dump(exclude_unset=True)
        await self._repo.update(id, **update_data)
        
        await self._session.commit()
        await self._session.refresh(contract)
        
        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="NATIONAL_CONTRACT",
            resource_id=str(id),
            description=f"Updated national contract: {contract.name}",
            request_data=update_data
        )
        return contract
    
    async def delete_national_contract(self, id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Deactivate national contract (soft delete)."""
        contract = await self._repo.get(id)
        
        if not contract:
            raise NotFoundError("National contract not found", entity_type="NationalContract", entity_id=str(id))
        
        await self._repo.update(id, is_active=False)
        contract_name = contract.name
        await self._session.commit()
        
        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="NATIONAL_CONTRACT",
            resource_id=str(id),
            description=f"Deactivated national contract: {contract_name}"
        )
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # Contract Versions
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_contract_versions(self, contract_id: UUID) -> list:
        """Get all versions for a national contract."""
        return await self._version_repo.get_by_contract(contract_id)
    
    async def get_contract_version(self, version_id: UUID):
        """Get a specific version by ID."""
        version = await self._version_repo.get(version_id)
        if not version:
            raise NotFoundError("Contract version not found", entity_type="NationalContractVersion", entity_id=str(version_id))
        return version
    
    async def get_contract_version_at_date(self, contract_id: UUID, reference_date):
        """Get the version valid at a specific date.
        
        This is the core method for historical calculations.
        Returns the version where valid_from <= reference_date AND (valid_to is NULL OR valid_to >= reference_date).
        """
        version = await self._version_repo.get_valid_at_date(contract_id, reference_date)
        
        if not version:
            raise NotFoundError(
                f"No contract version found for date {reference_date}", 
                entity_type="NationalContractVersion", 
                entity_id=str(contract_id)
            )
        return version
    
    async def create_contract_version(self, data, created_by: UUID = None):
        """Create new version for a national contract.
        
        Automatically updates the valid_to of the previous version.
        """
        # Verify contract exists
        contract = await self._repo.get(data.national_contract_id)
        
        if not contract:
            raise NotFoundError("National contract not found", entity_type="NationalContract", entity_id=str(data.national_contract_id))
        
        # Find the previous version that is still valid (valid_to is NULL)
        previous_version = await self._version_repo.get_previous_valid(data.national_contract_id, data.valid_from)
        
        # Update the previous version's valid_to to day before new version starts
        if previous_version:
            await self._version_repo.update(previous_version.id, valid_to=data.valid_from - timedelta(days=1))
        
        # Create new version
        version_data = data.model_dump()
        version_data['created_by'] = created_by
        version = await self._version_repo.create(**version_data)
        
        await self._session.commit()
        await self._session.refresh(version)
        
        await self._audit.log_action(
            user_id=created_by,
            action="CREATE",
            resource_type="NATIONAL_CONTRACT_VERSION",
            resource_id=str(version.id),
            description=f"Created new version for national contract {contract.name}: {version.version_name}",
            request_data=data.model_dump(mode="json")
        )
        return version
    
    async def update_contract_version(self, version_id: UUID, data, user_id: Optional[UUID] = None):
        """Update a contract version."""
        version = await self._version_repo.get(version_id)
        
        if not version:
            raise NotFoundError("Contract version not found", entity_type="NationalContractVersion", entity_id=str(version_id))
        
        update_data = data.model_dump(exclude_unset=True)
        await self._version_repo.update(version_id, **update_data)
        
        await self._session.commit()
        await self._session.refresh(version)
        
        await self._audit.log_action(
            user_id=user_id,
            action="UPDATE",
            resource_type="NATIONAL_CONTRACT_VERSION",
            resource_id=str(version_id),
            description=f"Updated national contract version: {version.version_name}",
            request_data=update_data
        )
        return version
    
    async def delete_contract_version(self, version_id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Delete a contract version (hard delete)."""
        version = await self._version_repo.get(version_id)
        
        if not version:
            raise NotFoundError("Contract version not found", entity_type="NationalContractVersion", entity_id=str(version_id))
        
        version_name = version.version_name
        await self._version_repo.delete(version_id)
        await self._session.commit()
        
        await self._audit.log_action(
            user_id=user_id,
            action="DELETE",
            resource_type="NATIONAL_CONTRACT_VERSION",
            resource_id=str(version_id),
            description=f"Deleted national contract version: {version_name}"
        )
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # Contract Types & Configurations
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_contract_types(self):
        """Get all available contract types."""
        return await self._type_repo.get_all(active_only=True)
    
    async def create_contract_type_config(self, data, actor_id: Optional[UUID] = None):
        """Create contract type parameter configuration."""
        config = await self._config_repo.create(**data.model_dump())
        await self._session.commit()
        await self._session.refresh(config)
        
        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="CONTRACT_TYPE_CONFIG",
            resource_id=str(config.id),
            description=f"Created contract type config for version {data.national_contract_version_id}",
            request_data=data.model_dump(mode="json")
        )
        return config
    
    async def update_contract_type_config(self, config_id: UUID, data, actor_id: Optional[UUID] = None):
        """Update contract type parameter configuration."""
        config = await self._config_repo.get(config_id)
        
        if not config:
            raise NotFoundError("Contract type configuration not found", entity_type="NationalContractTypeConfig", entity_id=str(config_id))
        
        update_data = data.model_dump(exclude_unset=True)
        await self._config_repo.update(config_id, **update_data)
        
        await self._session.commit()
        await self._session.refresh(config)
        
        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE",
            resource_type="CONTRACT_TYPE_CONFIG",
            resource_id=str(config_id),
            description=f"Updated contract type config",
            request_data=update_data
        )
        return config
    
    async def delete_contract_type_config(self, config_id: UUID, actor_id: Optional[UUID] = None) -> bool:
        """Delete contract type parameter configuration."""
        config = await self._config_repo.get(config_id)
        
        if not config:
            raise NotFoundError("Config not found", entity_type="NationalContractTypeConfig", entity_id=str(config_id))
        
        await self._config_repo.delete(config_id)
        await self._session.commit()
        
        await self._audit.log_action(
            user_id=actor_id,
            action="DELETE",
            resource_type="CONTRACT_TYPE_CONFIG",
            resource_id=str(config_id),
            description=f"Deleted contract type config override"
        )
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # Contract Levels
    # ═══════════════════════════════════════════════════════════════════════
    
    async def create_national_contract_level(self, data, actor_id: Optional[UUID] = None):
        """Create new level for a national contract."""
        level = await self._level_repo.create(**data.model_dump())
        await self._session.commit()
        await self._session.refresh(level)
        
        await self._audit.log_action(
            user_id=actor_id,
            action="CREATE",
            resource_type="NATIONAL_CONTRACT_LEVEL",
            resource_id=str(level.id),
            description=f"Created contract level: {level.level_name}",
            request_data=data.model_dump(mode="json")
        )
        return level
    
    async def update_national_contract_level(self, level_id: UUID, data, actor_id: Optional[UUID] = None):
        """Update a contract level."""
        level = await self._level_repo.get(level_id)
        
        if not level:
            raise NotFoundError("Contract level not found", entity_type="NationalContractLevel", entity_id=str(level_id))
        
        update_data = data.model_dump(exclude_unset=True)
        await self._level_repo.update(level_id, **update_data)
        
        await self._session.commit()
        await self._session.refresh(level)
        
        await self._audit.log_action(
            user_id=actor_id,
            action="UPDATE",
            resource_type="NATIONAL_CONTRACT_LEVEL",
            resource_id=str(level_id),
            description=f"Updated contract level: {level.level_name}",
            request_data=update_data
        )
        return level
    
    async def delete_national_contract_level(self, level_id: UUID, actor_id: Optional[UUID] = None) -> bool:
        """Delete a contract level."""
        level = await self._level_repo.get(level_id)
        
        if not level:
            raise NotFoundError("Contract level not found", entity_type="NationalContractLevel", entity_id=str(level_id))
        
        level_name = level.level_name
        await self._level_repo.delete(level_id)
        await self._session.commit()
        
        await self._audit.log_action(
            user_id=actor_id,
            action="DELETE",
            resource_type="NATIONAL_CONTRACT_LEVEL",
            resource_id=str(level_id),
            description=f"Deleted contract level: {level_name}"
        )
        return True
