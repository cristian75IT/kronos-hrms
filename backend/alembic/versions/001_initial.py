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

    # ═══════════════════════════════════════════════════════════════════
    # CONFIG SCHEMA
    # ═══════════════════════════════════════════════════════════════════
    
    # System parameters
    op.create_table(
        'system_parameters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('category', sa.String(100), nullable=False, index=True),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('value_type', sa.String(20), default='string', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_editable', sa.Boolean(), default=True, nullable=False),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='config'
    )
    op.create_index('ix_config_system_parameters_category_key', 'system_parameters', ['category', 'key'], unique=True, schema='config')
    
    # Leave types
    op.create_table(
        'leave_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), default='#3B82F6', nullable=False),
        sa.Column('is_paid', sa.Boolean(), default=True, nullable=False),
        sa.Column('affects_balance', sa.Boolean(), default=True, nullable=False),
        sa.Column('requires_approval', sa.Boolean(), default=True, nullable=False),
        sa.Column('requires_attachment', sa.Boolean(), default=False, nullable=False),
        sa.Column('max_consecutive_days', sa.Integer(), nullable=True),
        sa.Column('min_advance_days', sa.Integer(), default=0, nullable=False),
        sa.Column('accrual_type', sa.String(20), nullable=True),
        sa.Column('carry_over_allowed', sa.Boolean(), default=False, nullable=False),
        sa.Column('carry_over_limit', sa.Numeric(5, 2), nullable=True),
        sa.Column('carry_over_expiry_months', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='config'
    )
    
    # Holidays
    op.create_table(
        'holidays',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False, index=True),
        sa.Column('is_national', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_recurring', sa.Boolean(), default=False, nullable=False),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='config'
    )
    op.create_index('ix_config_holidays_date_location', 'holidays', ['date', 'location'], unique=True, schema='config')
    
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
        sa.Column('destination_type', sa.String(20), nullable=False),
        sa.Column('full_day_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('half_day_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('breakfast_deduction', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('lunch_deduction', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('dinner_deduction', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('overnight_bonus', sa.Numeric(10, 2), default=0, nullable=False),
        sa.Column('tax_free_limit', sa.Numeric(10, 2), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='config'
    )
    op.create_index('ix_config_daily_allowance_rules_type_date', 'daily_allowance_rules', ['destination_type', 'valid_from'], schema='config')

    # ═══════════════════════════════════════════════════════════════════
    # LEAVES SCHEMA
    # ═══════════════════════════════════════════════════════════════════
    
    # Leave balances
    op.create_table(
        'leave_balances',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('year', sa.Integer(), nullable=False, index=True),
        sa.Column('vacation_total_ap', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('vacation_used_ap', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('vacation_total_ac', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('vacation_used_ac', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('rol_total', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('rol_used', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('permits_total', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('permits_used', sa.Numeric(5, 2), default=0, nullable=False),
        sa.Column('ap_expiry_date', sa.Date(), nullable=True),
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
        sa.Column('employee_notes', sa.Text(), nullable=True),
        sa.Column('approver_notes', sa.Text(), nullable=True),
        sa.Column('approver_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('condition_type', sa.String(20), nullable=True),
        sa.Column('condition_details', sa.Text(), nullable=True),
        sa.Column('condition_accepted', sa.Boolean(), nullable=True),
        sa.Column('condition_accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('recalled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recall_reason', sa.Text(), nullable=True),
        sa.Column('actual_return_date', sa.Date(), nullable=True),
        sa.Column('compensation_days', sa.Numeric(5, 2), nullable=True),
        sa.Column('deduction_details', postgresql.JSONB(), nullable=True),
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
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        # sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
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
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('destination', sa.String(200), nullable=False),
        sa.Column('destination_type', sa.String(20), default='national', nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(20), default='draft', nullable=False, index=True),
        sa.Column('project_code', sa.String(50), nullable=True),
        sa.Column('cost_center', sa.String(50), nullable=True),
        sa.Column('estimated_budget', sa.Numeric(10, 2), nullable=True),
        sa.Column('approver_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approver_notes', sa.Text(), nullable=True),
        sa.Column('employee_notes', sa.Text(), nullable=True),
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
        sa.Column('trip_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('expenses.business_trips.id', ondelete='SET NULL'), nullable=True),
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
        sa.Column('notification_type', sa.String(50), nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('channel', sa.String(20), default='in_app', nullable=False),
        sa.Column('is_read', sa.Boolean(), default=False, nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', sa.String(50), nullable=True),
        sa.Column('action_url', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(20), default='normal', nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payload', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='notifications'
    )
    op.create_index('ix_notifications_notifications_user_read', 'notifications', ['user_id', 'is_read'], schema='notifications')
    
    # Email templates
    op.create_table(
        'email_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('notification_type', sa.String(50), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('subject', sa.String(200), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('brevo_template_id', sa.Integer(), nullable=True),
        sa.Column('variables', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='notifications'
    )
    
    # User notification preferences
    op.create_table(
        'user_notification_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('in_app_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('email_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        schema='notifications'
    )
    op.create_index('ix_notifications_preferences_user_type', 'user_notification_preferences', ['user_id', 'notification_type'], unique=True, schema='notifications')

    # ═══════════════════════════════════════════════════════════════════
    # AUDIT SCHEMA
    # ═══════════════════════════════════════════════════════════════════
    
    # Audit logs
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('action', sa.String(50), nullable=False, index=True),
        sa.Column('resource_type', sa.String(50), nullable=False, index=True),
        sa.Column('resource_id', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('request_method', sa.String(10), nullable=True),
        sa.Column('request_path', sa.String(500), nullable=True),
        sa.Column('request_body', postgresql.JSONB(), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('service_name', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), default='success', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        schema='audit'
    )
    
    # Audit trails
    op.create_table(
        'audit_trails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', sa.String(50), nullable=False, index=True),
        sa.Column('entity_id', sa.String(50), nullable=False, index=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('operation', sa.String(20), nullable=False),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('before_state', postgresql.JSONB(), nullable=True),
        sa.Column('after_state', postgresql.JSONB(), nullable=True),
        sa.Column('changes', postgresql.JSONB(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        schema='audit'
    )
    op.create_index('ix_audit_audit_trails_entity', 'audit_trails', ['entity_type', 'entity_id', 'version'], unique=True, schema='audit')


def downgrade() -> None:
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
    op.drop_table('holidays', schema='config')
    op.drop_table('leave_types', schema='config')
    op.drop_table('system_parameters', schema='config')
    
    # Auth schema
    op.drop_table('user_roles', schema='auth')
    op.drop_table('user_profiles', schema='auth')
    op.drop_table('users', schema='auth')
