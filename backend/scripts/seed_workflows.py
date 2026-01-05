#!/usr/bin/env python3
"""
KRONOS - Seed Default Approval Workflows.

Seeds the database with default workflow configurations.
"""
import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.core.database import engine as async_engine, async_session_factory as AsyncSessionLocal


DEFAULT_WORKFLOWS = [
    # Leave workflows
    {
        "entity_type": "LEAVE",
        "name": "Approvazione Ferie Standard",
        "description": "Flusso standard per richieste ferie e permessi",
        "min_approvers": 1,
        "max_approvers": 1,
        "approval_mode": "ANY",
        "auto_assign_approvers": True,
        "allow_self_approval": False,
        "expiration_hours": 72,
        "expiration_action": "NOTIFY_ONLY",
        "reminder_hours_before": 24,
        "send_reminders": True,
        "priority": 100,
        "is_active": True,
        "is_default": True,
    },
    {
        "entity_type": "LEAVE",
        "name": "Approvazione Ferie Estese",
        "description": "Per ferie superiori a 5 giorni - richiede doppia approvazione",
        "min_approvers": 2,
        "max_approvers": 2,
        "approval_mode": "ALL",
        "auto_assign_approvers": True,
        "allow_self_approval": False,
        "expiration_hours": 120,
        "expiration_action": "ESCALATE",
        "reminder_hours_before": 48,
        "send_reminders": True,
        "conditions": {"min_days": 5},
        "priority": 50,
        "is_active": True,
        "is_default": False,
    },
    {
        "entity_type": "LEAVE",
        "name": "Approvazione Ferie Manager",
        "description": "Richiede approvazione del Responsabile Dipartimento",
        "min_approvers": 1,
        "max_approvers": 1,
        "approval_mode": "ANY",
        "auto_assign_approvers": True,
        "allow_self_approval": False,
        "expiration_hours": 72,
        "expiration_action": "ESCALATE",
        "reminder_hours_before": 24,
        "send_reminders": True,
        "priority": 90,
        "is_active": True,
        "is_default": False,
        "approver_role_ids": ["DYNAMIC:DEPARTMENT_MANAGER"]
    },
    # Trip workflows
    {
        "entity_type": "TRIP",
        "name": "Approvazione Trasferta Standard",
        "description": "Flusso standard per richieste trasferta",
        "min_approvers": 1,
        "max_approvers": 1,
        "approval_mode": "ANY",
        "auto_assign_approvers": True,
        "allow_self_approval": False,
        "expiration_hours": 48,
        "expiration_action": "NOTIFY_ONLY",
        "reminder_hours_before": 12,
        "send_reminders": True,
        "priority": 100,
        "is_active": True,
        "is_default": True,
    },
    # Expense workflows
    {
        "entity_type": "EXPENSE",
        "name": "Approvazione Nota Spese Standard",
        "description": "Per note spese fino a 500 euro",
        "min_approvers": 1,
        "max_approvers": 1,
        "approval_mode": "ANY",
        "auto_assign_approvers": True,
        "allow_self_approval": False,
        "expiration_hours": 96,
        "expiration_action": "NOTIFY_ONLY",
        "reminder_hours_before": 24,
        "send_reminders": True,
        "conditions": {"max_amount": 500},
        "priority": 100,
        "is_active": True,
        "is_default": True,
    },
    {
        "entity_type": "EXPENSE",
        "name": "Approvazione Nota Spese Alta",
        "description": "Per note spese oltre 500 euro - approvazione sequenziale",
        "min_approvers": 2,
        "max_approvers": 3,
        "approval_mode": "SEQUENTIAL",
        "auto_assign_approvers": True,
        "allow_self_approval": False,
        "expiration_hours": 168,
        "expiration_action": "ESCALATE",
        "reminder_hours_before": 48,
        "send_reminders": True,
        "conditions": {"min_amount": 500},
        "priority": 50,
        "is_active": True,
        "is_default": False,
    },
]


async def seed_workflows():
    """Seed default workflow configurations."""
    print("=" * 60)
    print("KRONOS - Seeding Default Approval Workflows")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # Check if schema exists
        result = await session.execute(text(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'approvals'"
        ))
        if not result.scalar():
            print("\n⚠️  Schema 'approvals' does not exist. Run migrations first:")
            print("   cd /app && alembic upgrade head")
            return
        
        # Insert workflows
        print("\nSeeding workflow configurations...")
        
        for wf in DEFAULT_WORKFLOWS:
            # Check if workflow exists by name and entity_type
            result = await session.execute(text(
                "SELECT id FROM approvals.workflow_configs WHERE name = :name AND entity_type = :entity_type"
            ), {"name": wf['name'], "entity_type": wf['entity_type']})
            existing_id = result.scalar()
            
            if existing_id:
                print(f"  ✓ Exists: {wf['entity_type']} - {wf['name']}")
                continue

            wf_id = uuid4()
            
            # Handle JSON fields properly
            conditions_val = json.dumps(wf.get('conditions', {})) if wf.get('conditions') else None
            
            sql = """
            INSERT INTO approvals.workflow_configs (
                id, entity_type, name, description, min_approvers, max_approvers,
                approval_mode, approver_role_ids, auto_assign_approvers, allow_self_approval,
                expiration_hours, expiration_action, reminder_hours_before, send_reminders,
                conditions, priority, is_active, is_default
            ) VALUES (
                :id, :entity_type, :name, :description, :min_approvers, :max_approvers,
                :approval_mode, :approver_role_ids, :auto_assign_approvers, :allow_self_approval,
                :expiration_hours, :expiration_action, :reminder_hours_before, :send_reminders,
                :conditions, :priority, :is_active, :is_default
            )
            """
            
            params = {
                "id": str(wf_id),
                "entity_type": wf['entity_type'],
                "name": wf['name'],
                "description": wf.get('description', ''),
                "min_approvers": wf['min_approvers'],
                "max_approvers": wf.get('max_approvers'),
                "approval_mode": wf['approval_mode'],
                "approver_role_ids": json.dumps(wf.get('approver_role_ids', [])),
                "auto_assign_approvers": wf['auto_assign_approvers'],
                "allow_self_approval": wf['allow_self_approval'],
                "expiration_hours": wf.get('expiration_hours'),
                "expiration_action": wf['expiration_action'],
                "reminder_hours_before": wf.get('reminder_hours_before'),
                "send_reminders": wf['send_reminders'],
                "conditions": conditions_val,
                "priority": wf['priority'],
                "is_active": wf['is_active'],
                "is_default": wf['is_default'],
            }
            
            await session.execute(text(sql), params)
            print(f"  ✓ Created: {wf['entity_type']} - {wf['name']}")
        
        await session.commit()
        print(f"\n✅ Successfully seeded {len(DEFAULT_WORKFLOWS)} workflow configurations!")


if __name__ == "__main__":
    asyncio.run(seed_workflows())
