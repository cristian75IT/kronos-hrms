"""KRONOS Initial Migration - All Schemas.

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-30

Creates all tables for:
- auth: Users, profiles, user-role mappings
- leaves: Leave requests, balances, transactions, history
- expenses: Business trips, daily allowances, expense reports, items
- config: System parameters, leave types, holidays, allowance rules
- notifications: Notifications, email templates, user preferences
- audit: Audit logs, audit trails
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════════════
    # AUTH SCHEMA
    # ═══════════════════════════════════════════════════════════════════
    
    # Locations
    op.create_table(
        'locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('province', sa.String(2), nullable=True),
        sa.Column('patron_saint_name', sa.String(100), nullable=True),
        sa.Column('patron_saint_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='auth'
    )

    # Work Schedules
    op.create_table(
        'work_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('monday_hours', sa.Integer(), server_default='8', nullable=False),
        sa.Column('tuesday_hours', sa.Integer(), server_default='8', nullable=False),
        sa.Column('wednesday_hours', sa.Integer(), server_default='8', nullable=False),
        sa.Column('thursday_hours', sa.Integer(), server_default='8', nullable=False),
        sa.Column('friday_hours', sa.Integer(), server_default='8', nullable=False),
        sa.Column('saturday_hours', sa.Integer(), server_default='0', nullable=False),
        sa.Column('sunday_hours', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='auth'
    )

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('keycloak_id', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_synced', sa.Boolean(), default=False, nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('badge_number', sa.String(50), nullable=True),
        sa.Column('fiscal_code', sa.String(16), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=True),
        sa.Column('termination_date', sa.Date(), nullable=True),
        sa.Column('work_schedule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auth.work_schedules.id'), nullable=True),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auth.locations.id'), nullable=True),
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_manager', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_approver', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='auth'
    )
    
    # User profiles
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auth.users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('position', sa.String(100), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=True),
        sa.Column('contract_type', sa.String(50), nullable=True),
        sa.Column('weekly_hours', sa.Numeric(4, 1), default=40, nullable=True),
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auth.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('employee_number', sa.String(50), nullable=True, unique=True),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='auth'
    )
    
    # User roles mapping
    op.create_table(
        'user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auth.users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_name', sa.String(100), nullable=False),
        sa.Column('scope', sa.String(100), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), nullable=True),
        schema='auth'
    )
    op.create_index('ix_auth_user_roles_user_role', 'user_roles', ['user_id', 'role_name'], schema='auth')

    # Areas
    op.create_table(
        'areas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auth.areas.id'), nullable=True),
        sa.Column('manager_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auth.users.id'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='auth'
    )

    # User Areas association
    op.create_table(
        'user_areas',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auth.users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('area_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auth.areas.id', ondelete='CASCADE'), primary_key=True),
        schema='auth'
    )

    # ═══════════════════════════════════════════════════════════════════
    # CONFIG SCHEMA
    # ═══════════════════════════════════════════════════════════════════
    
    # System configuration
    op.create_table(
        'system_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(100), unique=True, nullable=False),
        sa.Column('value', postgresql.JSONB(), nullable=False),
        sa.Column('value_type', sa.String(20), nullable=False),  # string, integer, boolean, float, json
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_sensitive', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='config'
    )
    op.create_index('ix_config_system_config_key', 'system_config', ['key'], unique=True, schema='config')
    
    # Leave types (Updated to match model)
    op.create_table(
        'leave_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(10), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scales_balance', sa.Boolean(), default=True, nullable=False),
        sa.Column('balance_type', sa.String(20), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), default=True, nullable=False),
        sa.Column('requires_attachment', sa.Boolean(), default=False, nullable=False),
        sa.Column('requires_protocol', sa.Boolean(), default=False, nullable=False),
        sa.Column('min_notice_days', sa.Integer(), nullable=True),
        sa.Column('max_consecutive_days', sa.Integer(), nullable=True),
        sa.Column('max_per_month', sa.Integer(), nullable=True),
        sa.Column('allow_past_dates', sa.Boolean(), default=False, nullable=False),
        sa.Column('allow_half_day', sa.Boolean(), default=True, nullable=False),
        sa.Column('allow_negative_balance', sa.Boolean(), default=False, nullable=False),
        sa.Column('color', sa.String(7), default='#3B82F6', nullable=False),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='config'
    )

    # Contract types
    op.create_table(
        'contract_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('is_part_time', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('part_time_percentage', sa.Float(), server_default='100.0', nullable=False),
        sa.Column('annual_vacation_days', sa.Integer(), server_default='26', nullable=False),
        sa.Column('annual_rol_hours', sa.Integer(), server_default='72', nullable=False),
        sa.Column('annual_permit_hours', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='config'
    )
    op.create_index('ix_config_contract_types_code', 'contract_types', ['code'], unique=True, schema='config')
    
    # Holidays
    op.create_table(
        'holidays',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_national', sa.Boolean(), default=True, nullable=False),
        sa.Column('year', sa.Integer(), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='config'
    )
    op.create_index('ix_config_holidays_date_location', 'holidays', ['date', 'location_id'], unique=True, schema='config')
    
    # Company Closures
    op.create_table(
        'company_closures',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('closure_type', sa.String(20), nullable=False, default='total'),  # total, partial
        sa.Column('affected_departments', postgresql.JSONB(), nullable=True),
        sa.Column('affected_locations', postgresql.JSONB(), nullable=True),
        sa.Column('is_paid', sa.Boolean(), default=True, nullable=False),
        sa.Column('consumes_leave_balance', sa.Boolean(), default=False, nullable=False),
        sa.Column('leave_type_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False, index=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='config'
    )
    op.create_index('ix_config_closures_dates', 'company_closures', ['start_date', 'end_date'], schema='config')
    
    # Expense types
    op.create_table(
        'expense_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('requires_receipt', sa.Boolean(), default=True, nullable=False),
        sa.Column('max_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('km_reimbursement_rate', sa.Numeric(5, 3), nullable=True),
        sa.Column('is_taxable', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='config'
    )
    
    # Daily allowance rules
    op.create_table(
        'daily_allowance_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('destination_type', sa.String(20), nullable=False),
        sa.Column('full_day_amount', sa.Numeric(8, 2), nullable=False),
        sa.Column('half_day_amount', sa.Numeric(8, 2), nullable=False),
        sa.Column('threshold_hours', sa.Integer(), default=8, nullable=False),
        sa.Column('meals_deduction', sa.Numeric(8, 2), default=0, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='config'
    )
    
    # Policy rules (Added to match model)
    op.create_table(
        'policy_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('conditions', postgresql.JSONB(), nullable=False),
        sa.Column('actions', postgresql.JSONB(), nullable=False),
        sa.Column('priority', sa.Integer(), default=0, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='config'
    )

    # ═══════════════════════════════════════════════════════════════════
    # LEAVES SCHEMA
    # ═══════════════════════════════════════════════════════════════════
    
    # Leave balances
    op.create_table(
        'leave_balances',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('year', sa.Integer(), nullable=False, index=True),
        sa.Column('vacation_previous_year', sa.Numeric(5, 2), server_default='0', nullable=False),
        sa.Column('vacation_current_year', sa.Numeric(5, 2), server_default='0', nullable=False),
        sa.Column('vacation_accrued', sa.Numeric(5, 2), server_default='0', nullable=False),
        sa.Column('vacation_used', sa.Numeric(5, 2), server_default='0', nullable=False),
        sa.Column('vacation_used_ap', sa.Numeric(5, 2), server_default='0', nullable=False),
        sa.Column('vacation_used_ac', sa.Numeric(5, 2), server_default='0', nullable=False),
        sa.Column('rol_previous_year', sa.Numeric(6, 2), server_default='0', nullable=False),
        sa.Column('rol_current_year', sa.Numeric(6, 2), server_default='0', nullable=False),
        sa.Column('rol_accrued', sa.Numeric(6, 2), server_default='0', nullable=False),
        sa.Column('rol_used', sa.Numeric(6, 2), server_default='0', nullable=False),
        sa.Column('permits_total', sa.Numeric(6, 2), server_default='0', nullable=False),
        sa.Column('permits_used', sa.Numeric(6, 2), server_default='0', nullable=False),
        sa.Column('ap_expiry_date', sa.Date(), nullable=True),
        sa.Column('last_accrual_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='leaves'
    )
    op.create_index('ix_leaves_leave_balances_user_year', 'leave_balances', ['user_id', 'year'], unique=True, schema='leaves')
    
    # Leave requests
    op.create_table(
        'leave_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('leave_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('leave_type_code', sa.String(20), nullable=False),
        sa.Column('status', sa.String(30), default='draft', nullable=False, index=True),
        sa.Column('start_date', sa.Date(), nullable=False, index=True),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('start_half_day', sa.Boolean(), default=False, nullable=False),
        sa.Column('end_half_day', sa.Boolean(), default=False, nullable=False),
        sa.Column('days_requested', sa.Numeric(5, 2), nullable=False),
        sa.Column('hours_requested', sa.Numeric(6, 2), nullable=True),
        sa.Column('employee_notes', sa.Text(), nullable=True),
        sa.Column('approver_notes', sa.Text(), nullable=True),
        sa.Column('approver_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('has_conditions', sa.Boolean(), default=False, nullable=False),
        sa.Column('condition_type', sa.String(20), nullable=True),
        sa.Column('condition_details', sa.Text(), nullable=True),
        sa.Column('condition_accepted', sa.Boolean(), nullable=True),
        sa.Column('condition_accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('recalled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recall_reason', sa.Text(), nullable=True),
        sa.Column('protocol_number', sa.String(50), nullable=True),
        sa.Column('actual_return_date', sa.Date(), nullable=True),
        sa.Column('compensation_days', sa.Numeric(5, 2), nullable=True),
        sa.Column('deduction_details', postgresql.JSONB(), nullable=True),
        sa.Column('policy_violations', postgresql.JSONB(), nullable=True),
        sa.Column('balance_deducted', sa.Boolean(), default=False, nullable=False),
        sa.Column('attachment_path', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='leaves'
    )
    
    # Balance transactions
    op.create_table(
        'balance_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('balance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leaves.leave_balances.id', ondelete='CASCADE'), nullable=False),
        sa.Column('leave_request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leaves.leave_requests.id', ondelete='SET NULL'), nullable=True),
        sa.Column('transaction_type', sa.String(20), nullable=False),
        sa.Column('balance_type', sa.String(20), nullable=False),
        sa.Column('amount', sa.Numeric(5, 2), nullable=False),
        sa.Column('balance_after', sa.Numeric(5, 2), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='leaves'
    )
    op.create_index('ix_leaves_balance_transactions_balance', 'balance_transactions', ['balance_id'], schema='leaves')
    
    # Request history
    op.create_table(
        'leave_request_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('leave_request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leaves.leave_requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_status', sa.String(30), nullable=True),
        sa.Column('to_status', sa.String(30), nullable=False),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        # sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='leaves'
    )
    op.create_index('ix_leaves_leave_request_history_request', 'leave_request_history', ['leave_request_id'], schema='leaves')

    # ═══════════════════════════════════════════════════════════════════
    # EXPENSES SCHEMA
    # ═══════════════════════════════════════════════════════════════════
    
    # Business trips
    op.create_table(
        'business_trips',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('destination', sa.String(200), nullable=False),
        sa.Column('destination_type', sa.String(20), server_default='national', nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('project_code', sa.String(50), nullable=True),
        sa.Column('client_name', sa.String(200), nullable=True),
        sa.Column('estimated_budget', sa.Numeric(10, 2), nullable=True),
        sa.Column('status', sa.String(30), server_default='draft', nullable=False, index=True),
        sa.Column('approver_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approver_notes', sa.Text(), nullable=True),
        sa.Column('attachment_path', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='expenses'
    )
    
    # Daily allowances
    op.create_table(
        'daily_allowances',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('trip_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('expenses.business_trips.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('is_full_day', sa.Boolean(), default=True, nullable=False),
        sa.Column('breakfast_provided', sa.Boolean(), default=False, nullable=False),
        sa.Column('lunch_provided', sa.Boolean(), default=False, nullable=False),
        sa.Column('dinner_provided', sa.Boolean(), default=False, nullable=False),
        sa.Column('base_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('meals_deduction', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('final_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='expenses'
    )
    op.create_index('ix_expenses_daily_allowances_trip_date', 'daily_allowances', ['trip_id', 'date'], unique=True, schema='expenses')
    
    # Expense reports
    op.create_table(
        'expense_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('trip_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('expenses.business_trips.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('report_number', sa.String(50), unique=True, nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('status', sa.String(20), default='draft', nullable=False, index=True),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('total_amount', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('approved_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('employee_notes', sa.Text(), nullable=True),
        sa.Column('approver_notes', sa.Text(), nullable=True),
        sa.Column('approver_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attachment_path', sa.String(500), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payment_reference', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='expenses'
    )
    
    # Expense items
    op.create_table(
        'expense_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('expenses.expense_reports.id', ondelete='CASCADE'), nullable=False),
        sa.Column('expense_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expense_type_code', sa.String(20), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='EUR', nullable=False),
        sa.Column('exchange_rate', sa.Numeric(10, 6), default=1, nullable=False),
        sa.Column('amount_eur', sa.Numeric(10, 2), nullable=False),
        sa.Column('km_distance', sa.Numeric(7, 2), nullable=True),
        sa.Column('km_rate', sa.Numeric(5, 3), nullable=True),
        sa.Column('merchant_name', sa.String(200), nullable=True),
        sa.Column('receipt_number', sa.String(100), nullable=True),
        sa.Column('receipt_path', sa.Text(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='expenses'
    )
    op.create_index('ix_expenses_expense_items_report', 'expense_items', ['report_id'], schema='expenses')

    # ═══════════════════════════════════════════════════════════════════
    # NOTIFICATIONS SCHEMA
    # ═══════════════════════════════════════════════════════════════════
    
    # Notifications
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('channel', sa.String(20), default='in_app', nullable=False),
        sa.Column('status', sa.String(20), default='pending', nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', sa.String(100), nullable=True),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('payload', postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='notifications'
    )
    # op.create_index('ix_notifications_notifications_user_read', 'notifications', ['user_id', 'is_read'], schema='notifications')
    
    # Email templates
    op.create_table(
        'email_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(50), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('brevo_template_id', sa.Integer(), nullable=True),
        sa.Column('subject', sa.String(200), nullable=True),
        sa.Column('html_content', sa.Text(), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('available_variables', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='notifications'
    )
    
    # User notification preferences
    op.create_table(
        'user_notification_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), unique=True, nullable=False),
        sa.Column('email_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('email_leave_updates', sa.Boolean(), default=True, nullable=False),
        sa.Column('email_expense_updates', sa.Boolean(), default=True, nullable=False),
        sa.Column('email_system_announcements', sa.Boolean(), default=True, nullable=False),
        sa.Column('email_compliance_alerts', sa.Boolean(), default=True, nullable=False),
        sa.Column('in_app_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('digest_frequency', sa.String(20), default='instant', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='notifications'
    )

    # ═══════════════════════════════════════════════════════════════════
    # AUDIT SCHEMA
    # ═══════════════════════════════════════════════════════════════════
    
    # Audit logs
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('request_data', postgresql.JSONB(), nullable=True),
        sa.Column('response_data', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('endpoint', sa.String(255), nullable=True),
        sa.Column('http_method', sa.String(10), nullable=True),
        sa.Column('status', sa.String(20), default='SUCCESS', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('service_name', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='audit'
    )
    
    # Audit trail
    op.create_table(
        'audit_trail',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('version', sa.Integer(), default=1, nullable=False),
        sa.Column('operation', sa.String(10), nullable=False),
        sa.Column('before_data', postgresql.JSONB(), nullable=True),
        sa.Column('after_data', postgresql.JSONB(), nullable=True),
        sa.Column('changed_fields', postgresql.JSONB(), nullable=True),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('changed_by_email', sa.String(255), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('service_name', sa.String(50), nullable=False),
        sa.Column('request_id', sa.String(100), nullable=True),
        schema='audit'
    )

    # ═══════════════════════════════════════════════════════════════════
    # NEW ENTITIES (Employee Contracts)
    # ═══════════════════════════════════════════════════════════════════
    
    # Employee contracts
    op.create_table(
        'employee_contracts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auth.users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('contract_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('weekly_hours', sa.Integer(), nullable=True, comment='Ore settimanali effettive'),
        sa.Column('job_title', sa.String(100), nullable=True),
        sa.Column('level', sa.String(50), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('wage_data', sa.Text(), nullable=True),
        sa.Column('document_path', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='auth'
    )
    
    # Add link to users
    # Add link to users (must be after config.contract_types is created)
    op.add_column('users', sa.Column('contract_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('config.contract_types.id'), nullable=True), schema='auth')


def downgrade() -> None:
    # New entities
    op.drop_column('users', 'contract_type_id', schema='auth')
    op.drop_table('employee_contracts', schema='auth')

    # Audit schema
    op.drop_table('audit_trails', schema='audit')
    op.drop_table('audit_logs', schema='audit')
    
    # Notifications schema
    op.drop_table('user_notification_preferences', schema='notifications')
    op.drop_table('email_templates', schema='notifications')
    op.drop_table('notifications', schema='notifications')
    
    # Expenses schema
    op.drop_table('expense_items', schema='expenses')
    op.drop_table('expense_reports', schema='expenses')
    op.drop_table('daily_allowances', schema='expenses')
    op.drop_table('business_trips', schema='expenses')
    
    # Leaves schema
    op.drop_table('leave_request_history', schema='leaves')
    op.drop_table('balance_transactions', schema='leaves')
    op.drop_table('leave_requests', schema='leaves')
    op.drop_table('leave_balances', schema='leaves')
    
    # Config schema
    op.drop_table('daily_allowance_rules', schema='config')
    op.drop_table('expense_types', schema='config')
    op.drop_index('ix_config_closures_dates', table_name='company_closures', schema='config')
    op.drop_table('company_closures', schema='config')
    op.drop_table('holidays', schema='config')
    op.drop_index('ix_config_contract_types_code', table_name='contract_types', schema='config')
    op.drop_table('contract_types', schema='config')
    op.drop_table('leave_types', schema='config')
    op.drop_table('system_config', schema='config')
    
    # Auth schema
    op.drop_table('user_roles', schema='auth')
    op.drop_table('user_areas', schema='auth')
    op.drop_table('areas', schema='auth')
    op.drop_table('user_profiles', schema='auth')
    op.drop_table('users', schema='auth')
    op.drop_table('work_schedules', schema='auth')
    op.drop_table('locations', schema='auth')
