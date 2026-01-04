"""
KRONOS Approval Service - Configuration Router.

Admin endpoints for managing workflow configurations.
"""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import require_permission, TokenPayload

from ..service import ApprovalService
from ..schemas import (
    WorkflowConfigCreate,
    WorkflowConfigUpdate,
    WorkflowConfigResponse,
    EntityTypeInfo,
    ApprovalModeInfo,
    ExpirationActionInfo,
    ENTITY_TYPES,
    APPROVAL_MODES,
    EXPIRATION_ACTIONS,
)

router = APIRouter(prefix="/config", tags=["Approval Configuration"])


def get_service(session: AsyncSession = Depends(get_db)) -> ApprovalService:
    return ApprovalService(session)


# ═══════════════════════════════════════════════════════════
# Workflow Configurations
# ═══════════════════════════════════════════════════════════

@router.get("/workflows", response_model=List[WorkflowConfigResponse])
async def list_workflow_configs(
    entity_type: Optional[str] = Query(default=None),
    active_only: bool = Query(default=True),
    current_user: TokenPayload = Depends(require_permission("approvals:config")),
    service: ApprovalService = Depends(get_service),
):
    """List all workflow configurations."""
    configs = await service.list_workflow_configs(
        entity_type=entity_type,
        active_only=active_only,
    )
    return configs


@router.get("/workflows/{config_id}", response_model=WorkflowConfigResponse)
async def get_workflow_config(
    config_id: UUID,
    current_user: TokenPayload = Depends(require_permission("approvals:config")),
    service: ApprovalService = Depends(get_service),
):
    """Get workflow configuration by ID."""
    config = await service.get_workflow_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Workflow configuration not found")
    return config


@router.post("/workflows", response_model=WorkflowConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_config(
    data: WorkflowConfigCreate,
    current_user: TokenPayload = Depends(require_permission("approvals:config")),
    service: ApprovalService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workflow configuration."""
    if data.entity_type not in ENTITY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity type. Must be one of: {ENTITY_TYPES}"
        )
    
    if data.approval_mode not in APPROVAL_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid approval mode. Must be one of: {APPROVAL_MODES}"
        )
    
    if data.expiration_action not in EXPIRATION_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid expiration action. Must be one of: {EXPIRATION_ACTIONS}"
        )
    
    config = await service.create_workflow_config(data, current_user.sub)
    await db.commit()
    return config


@router.put("/workflows/{config_id}", response_model=WorkflowConfigResponse)
async def update_workflow_config(
    config_id: UUID,
    data: WorkflowConfigUpdate,
    current_user: TokenPayload = Depends(require_permission("approvals:config")),
    service: ApprovalService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Update workflow configuration."""
    # Validate entity_type if provided
    if data.entity_type and data.entity_type not in ENTITY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity type. Must be one of: {ENTITY_TYPES}"
        )
    
    config = await service.update_workflow_config(config_id, data)
    if not config:
        raise HTTPException(status_code=404, detail="Workflow configuration not found")
    
    await db.commit()
    return config


@router.delete("/workflows/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow_config(
    config_id: UUID,
    current_user: TokenPayload = Depends(require_permission("approvals:config")),
    service: ApprovalService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate workflow configuration."""
    success = await service.delete_workflow_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow configuration not found")
    
    await db.commit()


# ═══════════════════════════════════════════════════════════
# Reference Data
# ═══════════════════════════════════════════════════════════

@router.get("/entity-types", response_model=List[EntityTypeInfo])
async def get_entity_types(
    current_user: TokenPayload = Depends(require_permission("approvals:config")),
):
    """Get available entity types for workflows."""
    return [
        EntityTypeInfo(code="LEAVE", name="Ferie/Permessi", description="Richieste di ferie e permessi"),
        EntityTypeInfo(code="TRIP", name="Trasferte", description="Richieste di trasferta"),
        EntityTypeInfo(code="EXPENSE", name="Note Spese", description="Rimborsi spese"),
        EntityTypeInfo(code="DOCUMENT", name="Documenti", description="Approvazione documenti"),
        EntityTypeInfo(code="CONTRACT", name="Contratti", description="Modifiche contrattuali"),
        EntityTypeInfo(code="OVERTIME", name="Straordinari", description="Richieste straordinario"),
    ]


@router.get("/approval-modes", response_model=List[ApprovalModeInfo])
async def get_approval_modes(
    current_user: TokenPayload = Depends(require_permission("approvals:config")),
):
    """Get available approval modes."""
    return [
        ApprovalModeInfo(
            code="ANY",
            name="Prima Approvazione",
            description="La prima approvazione ricevuta approva la richiesta"
        ),
        ApprovalModeInfo(
            code="ALL",
            name="Tutti",
            description="Tutti gli approvatori devono approvare"
        ),
        ApprovalModeInfo(
            code="SEQUENTIAL",
            name="Sequenziale",
            description="Approvazione in ordine, si ferma al primo rifiuto"
        ),
        ApprovalModeInfo(
            code="MAJORITY",
            name="Maggioranza",
            description="Approva se la maggioranza è favorevole"
        ),
    ]


@router.get("/expiration-actions", response_model=List[ExpirationActionInfo])
async def get_expiration_actions(
    current_user: TokenPayload = Depends(require_permission("approvals:config")),
):
    """Get available expiration actions."""
    return [
        ExpirationActionInfo(
            code="REJECT",
            name="Rifiuta Automaticamente",
            description="La richiesta viene rifiutata automaticamente alla scadenza"
        ),
        ExpirationActionInfo(
            code="ESCALATE",
            name="Scala al Superiore",
            description="La richiesta viene inoltrata al ruolo di escalation"
        ),
        ExpirationActionInfo(
            code="AUTO_APPROVE",
            name="Approva Automaticamente",
            description="La richiesta viene approvata automaticamente alla scadenza"
        ),
        ExpirationActionInfo(
            code="NOTIFY_ONLY",
            name="Solo Notifica",
            description="Invia un promemoria ma mantiene la richiesta in sospeso"
        ),
    ]
