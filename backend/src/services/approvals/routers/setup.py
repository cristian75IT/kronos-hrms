from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from src.core.database import get_db
from src.core.security import require_permission, TokenPayload
from src.services.approvals.services.configs import ApprovalConfigService
from src.services.approvals.schemas import (
    SetupWorkflowsPayload,
    WorkflowConfigCreate
)
from src.services.approvals.models import WorkflowConfig

router = APIRouter()

async def get_config_service(session: AsyncSession = Depends(get_db)):
    return ApprovalConfigService(session)

@router.post("/setup/workflows", response_model=dict)
async def setup_workflows(
    payload: SetupWorkflowsPayload,
    token: TokenPayload = Depends(require_permission("settings:edit")),
    service: ApprovalConfigService = Depends(get_config_service)
):
    """Bulk setup/import of Approval Workflows."""
    results = {"created": 0, "updated": 0}
    
    for workflow_data in payload.workflows:
        # Check by name and entity_type to prevent duplicates
        existing_list = await service.list_workflow_configs(entity_type=workflow_data.entity_type)
        existing = next((w for w in existing_list if w.name == workflow_data.name), None)
        
        if existing:
            # For setup, we might skip or update. Let's stick to idempotency (skip if exists)
            # or could update if needed.
            results["updated"] += 1
        else:
            # Convert SetupWorkflow to WorkflowConfigCreate
            create_data = WorkflowConfigCreate(**workflow_data.model_dump())
            await service.create_workflow_config(
                create_data,
                created_by=token.user_id
            )
            results["created"] += 1
            
    return results
