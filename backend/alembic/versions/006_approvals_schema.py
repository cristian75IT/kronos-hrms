"""Add approvals schema

Revision ID: 006
Revises: 005
Create Date: 2026-01-03

Enterprise approval workflow engine schema.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '006_approvals_schema'
down_revision = 'ce618d13126c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create approvals schema
    op.execute("CREATE SCHEMA IF NOT EXISTS approvals")
    
    # Workflow Configurations table
    op.create_table(
        'workflow_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(50), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('min_approvers', sa.Integer, nullable=False, server_default='1'),
        sa.Column('max_approvers', sa.Integer, nullable=True),
        sa.Column('approval_mode', sa.String(30), nullable=False, server_default='ANY'),
        sa.Column('approver_role_ids', postgresql.JSONB, nullable=True, server_default='[]'),
        sa.Column('auto_assign_approvers', sa.Boolean, server_default='false'),
        sa.Column('allow_self_approval', sa.Boolean, server_default='false'),
        sa.Column('expiration_hours', sa.Integer, nullable=True),
        sa.Column('expiration_action', sa.String(30), nullable=False, server_default='REJECT'),
        sa.Column('escalation_role_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reminder_hours_before', sa.Integer, nullable=True, server_default='24'),
        sa.Column('send_reminders', sa.Boolean, server_default='true'),
        sa.Column('conditions', postgresql.JSONB, nullable=True),
        sa.Column('priority', sa.Integer, nullable=False, server_default='100'),
        sa.Column('is_active', sa.Boolean, server_default='true', index=True),
        sa.Column('is_default', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint('entity_type', 'name', name='uq_workflow_entity_name'),
        schema='approvals'
    )
    
    # Approval Requests table
    op.create_table(
        'approval_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(50), nullable=False, index=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_ref', sa.String(100), nullable=True),
        sa.Column('workflow_config_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('requester_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('requester_name', sa.String(200), nullable=True),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('request_metadata', postgresql.JSONB, nullable=True),
        sa.Column('callback_url', sa.String(500), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='PENDING', index=True),
        sa.Column('required_approvals', sa.Integer, nullable=False, server_default='1'),
        sa.Column('received_approvals', sa.Integer, server_default='0'),
        sa.Column('received_rejections', sa.Integer, server_default='0'),
        sa.Column('current_level', sa.Integer, server_default='1'),
        sa.Column('max_level', sa.Integer, server_default='1'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('expired_action_taken', sa.Boolean, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        sa.Column('final_decision_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['workflow_config_id'], ['approvals.workflow_configs.id'], name='fk_request_workflow'),
        sa.UniqueConstraint('entity_type', 'entity_id', name='uq_entity_request'),
        schema='approvals'
    )
    
    # Approval Decisions table
    op.create_table(
        'approval_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('approval_request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approver_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('approver_name', sa.String(200), nullable=True),
        sa.Column('approver_role', sa.String(100), nullable=True),
        sa.Column('approval_level', sa.Integer, server_default='1'),
        sa.Column('decision', sa.String(20), nullable=True),
        sa.Column('decision_notes', sa.Text, nullable=True),
        sa.Column('delegated_to_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('delegated_to_name', sa.String(200), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['approval_request_id'], ['approvals.approval_requests.id'], ondelete='CASCADE', name='fk_decision_request'),
        sa.UniqueConstraint('approval_request_id', 'approver_id', name='uq_approver_request'),
        schema='approvals'
    )
    
    # Approval History table
    op.create_table(
        'approval_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('approval_request_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_name', sa.String(200), nullable=True),
        sa.Column('actor_type', sa.String(30), nullable=True),
        sa.Column('details', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['approval_request_id'], ['approvals.approval_requests.id'], ondelete='CASCADE', name='fk_history_request'),
        schema='approvals'
    )
    
    # Approval Reminders table
    op.create_table(
        'approval_reminders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('approval_request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approver_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reminder_type', sa.String(30), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_sent', sa.Boolean, server_default='false'),
        sa.ForeignKeyConstraint(['approval_request_id'], ['approvals.approval_requests.id'], ondelete='CASCADE', name='fk_reminder_request'),
        schema='approvals'
    )
    
    # Create indexes for performance
    op.create_index(
        'idx_approval_requests_pending_expires',
        'approval_requests',
        ['expires_at'],
        schema='approvals',
        postgresql_where=sa.text("status = 'PENDING'")
    )
    
    op.create_index(
        'idx_approval_decisions_pending',
        'approval_decisions',
        ['approval_request_id'],
        schema='approvals',
        postgresql_where=sa.text("decided_at IS NULL")
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('approval_reminders', schema='approvals')
    op.drop_table('approval_history', schema='approvals')
    op.drop_table('approval_decisions', schema='approvals')
    op.drop_table('approval_requests', schema='approvals')
    op.drop_table('workflow_configs', schema='approvals')
    
    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS approvals CASCADE")
