"""
KRONOS Approvals Service - Workflow Configuration Module.
"""
from typing import Optional, List
from uuid import UUID

from src.core.exceptions import NotFoundError, BusinessRuleError
from src.services.approvals.schemas import (
    WorkflowConfigCreate,
    WorkflowConfigUpdate,
)
from src.services.approvals.services.base import BaseApprovalService

from src.services.approvals.models import WorkflowConfig

class ApprovalConfigService(BaseApprovalService):
    """Manages Workflow Configurations."""

    async def create_workflow_config(
        self,
        data: WorkflowConfigCreate,
        created_by: Optional[UUID] = None,
    ):
        """Create a new workflow configuration."""
        # Check uniqueness
        existing_list = await self._config_repo.get_active_by_entity_type(data.entity_type)
        if existing_list:
             # Deactivate old logic? Repository returns list, assume strict mode or first
             pass
        
        # Convert schema to model
        config = WorkflowConfig(
            entity_type=data.entity_type,
            steps=data.steps, # Assuming JSON/Dict compatibility or model handling
            is_active=True,
            created_by=created_by
        )
        await self._config_repo.create(config)
        
        await self._audit.log_action(
            user_id=created_by or UUID('00000000-0000-0000-0000-000000000000'),
            action="CREATE_WORKFLOW_CONFIG",
            resource_type="WORKFLOW_CONFIG",
            resource_id=str(config.id),
            description=f"Created workflow for {data.entity_type}"
        )
        return config

    async def get_workflow_config(self, config_id: UUID):
        """Get workflow config by ID."""
        config = await self._repo.get_workflow_config(config_id)
        if not config:
            raise NotFoundError("Workflow configuration not found")
        return config

    async def list_workflow_configs(
        self,
        entity_type: Optional[str] = None,
        active_only: bool = True,
    ):
        """List workflow configurations."""
        return await self._repo.list_workflow_configs(entity_type, active_only)

    async def update_workflow_config(
        self,
        config_id: UUID,
        data: WorkflowConfigUpdate,
    ):
        """Update workflow configuration."""
        config = await self.get_workflow_config(config_id)
        return await self._repo.update_workflow_config(config, data)

    async def delete_workflow_config(self, config_id: UUID):
        """Deactivate workflow configuration."""
        config = await self.get_workflow_config(config_id)
        return await self._repo.update_workflow_config(
            config, 
            WorkflowConfigUpdate(is_active=False)
        )
