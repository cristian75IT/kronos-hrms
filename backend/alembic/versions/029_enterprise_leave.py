"""Enterprise Leave Management Tables

Revision ID: 029_enterprise_leave
Revises: 028_enterprise_audit
Create Date: 2026-01-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '029_enterprise_leave'
down_revision: str = '028_enterprise_audit'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add enterprise leave management tables."""
    
    # ═══════════════════════════════════════════════════════════════════
    # Leave Interruptions Table
    # For sickness during vacation, partial recall, emergency work
    # ═══════════════════════════════════════════════════════════════════
    
    op.create_table(
        'leave_interruptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('leave_request_id', UUID(as_uuid=True), 
                  sa.ForeignKey('leaves.leave_requests.id', ondelete='CASCADE'), 
                  nullable=False, index=True),
        
        # Interruption type
        sa.Column('interruption_type', sa.String(30), nullable=False),
        
        # Interruption period
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        
        # Specific days (for non-contiguous partial recall)
        sa.Column('specific_days', JSONB, nullable=True),
        
        # Refund tracking
        sa.Column('days_refunded', sa.Numeric(5, 2), default=0),
        
        # Sickness specific
        sa.Column('protocol_number', sa.String(50), nullable=True),
        sa.Column('attachment_path', sa.String(500), nullable=True),
        
        # Initiator
        sa.Column('initiated_by', UUID(as_uuid=True), nullable=False),
        sa.Column('initiated_by_role', sa.String(20), default='EMPLOYEE'),
        
        # Reason
        sa.Column('reason', sa.Text, nullable=True),
        
        # Status
        sa.Column('status', sa.String(20), default='ACTIVE'),
        
        # Wallet reference
        sa.Column('refund_transaction_id', UUID(as_uuid=True), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        schema='leaves'
    )
    
    # Index for finding interruptions by type
    op.create_index(
        'ix_leave_interruptions_type',
        'leave_interruptions',
        ['interruption_type', 'status'],
        schema='leaves'
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # Approval Delegations Table
    # For temporary delegation of approval authority
    # ═══════════════════════════════════════════════════════════════════
    
    op.create_table(
        'approval_delegations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        
        # Delegator and delegate
        sa.Column('delegator_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('delegate_id', UUID(as_uuid=True), nullable=False, index=True),
        
        # Period
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        
        # Type
        sa.Column('delegation_type', sa.String(20), default='FULL'),
        
        # Scope limits
        sa.Column('scope_team_ids', JSONB, nullable=True),
        sa.Column('scope_leave_types', JSONB, nullable=True),
        
        # Reason
        sa.Column('reason', sa.Text, nullable=True),
        
        # Status
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by', UUID(as_uuid=True), nullable=True),
        
        # Timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        schema='leaves'
    )
    
    # Index for finding active delegations
    op.create_index(
        'ix_approval_delegations_active',
        'approval_delegations',
        ['delegate_id', 'is_active', 'start_date', 'end_date'],
        schema='leaves'
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # Balance Reservations Table
    # For holding balance during pending approval
    # ═══════════════════════════════════════════════════════════════════
    
    op.create_table(
        'balance_reservations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        
        # Reference
        sa.Column('leave_request_id', UUID(as_uuid=True), 
                  sa.ForeignKey('leaves.leave_requests.id', ondelete='CASCADE'), 
                  nullable=False, unique=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False, index=True),
        
        # What is reserved
        sa.Column('balance_type', sa.String(30), nullable=False),
        sa.Column('amount', sa.Numeric(5, 2), nullable=False),
        sa.Column('breakdown', JSONB, nullable=True),
        
        # Status
        sa.Column('status', sa.String(20), default='PENDING'),
        
        # Resolution timestamps
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        
        # Auto-expiry
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        
        # Timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        schema='leaves'
    )
    
    # Index for finding pending reservations
    op.create_index(
        'ix_balance_reservations_pending',
        'balance_reservations',
        ['user_id', 'status'],
        schema='leaves'
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # Add rejection_reason to leave_requests (if not exists)
    # ═══════════════════════════════════════════════════════════════════
    
    # Check and add column if not exists
    try:
        op.add_column(
            'leave_requests',
            sa.Column('rejection_reason', sa.Text, nullable=True),
            schema='leaves'
        )
    except Exception:
        pass  # Column may already exist
        
    # ═══════════════════════════════════════════════════════════════════
    # Add interruptions relationship to leave_requests
    # ═══════════════════════════════════════════════════════════════════
    
    try:
        op.add_column(
            'leave_requests',
            sa.Column('has_interruptions', sa.Boolean, default=False),
            schema='leaves'
        )
    except Exception:
        pass


def downgrade() -> None:
    """Remove enterprise leave management tables."""
    
    # Drop columns
    try:
        op.drop_column('leave_requests', 'has_interruptions', schema='leaves')
    except Exception:
        pass
        
    try:
        op.drop_column('leave_requests', 'rejection_reason', schema='leaves')
    except Exception:
        pass
    
    # Drop indexes
    op.drop_index('ix_balance_reservations_pending', table_name='balance_reservations', schema='leaves')
    op.drop_index('ix_approval_delegations_active', table_name='approval_delegations', schema='leaves')
    op.drop_index('ix_leave_interruptions_type', table_name='leave_interruptions', schema='leaves')
    
    # Drop tables
    op.drop_table('balance_reservations', schema='leaves')
    op.drop_table('approval_delegations', schema='leaves')
    op.drop_table('leave_interruptions', schema='leaves')
