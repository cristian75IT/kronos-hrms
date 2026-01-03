"""Create HR Reporting schema and tables

Revision ID: 030_hr_reporting
Revises: 20260102_2300
Create Date: 2026-01-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '030_hr_reporting'
down_revision = '20260102_2300_seed_generic_tmpl'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create schema
    op.execute("CREATE SCHEMA IF NOT EXISTS hr_reporting")
    
    # ═══════════════════════════════════════════════════════════
    # Generated Reports Table
    # ═══════════════════════════════════════════════════════════
    op.create_table(
        'generated_reports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('report_type', sa.String(50), nullable=False, index=True),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('department_id', UUID(as_uuid=True), nullable=True),
        sa.Column('team_id', UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('report_data', JSONB, nullable=True),
        sa.Column('summary', JSONB, nullable=True),
        sa.Column('generated_by', UUID(as_uuid=True), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pdf_path', sa.String(500), nullable=True),
        sa.Column('excel_path', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        schema='hr_reporting'
    )
    
    op.create_index(
        'ix_generated_reports_period',
        'generated_reports',
        ['report_type', 'period_start', 'department_id'],
        unique=False,
        schema='hr_reporting'
    )
    
    # ═══════════════════════════════════════════════════════════
    # Daily Snapshots Table
    # ═══════════════════════════════════════════════════════════
    op.create_table(
        'daily_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('snapshot_date', sa.Date(), nullable=False, unique=True, index=True),
        sa.Column('total_employees', sa.Integer(), server_default='0'),
        sa.Column('employees_on_leave', sa.Integer(), server_default='0'),
        sa.Column('employees_on_trip', sa.Integer(), server_default='0'),
        sa.Column('employees_sick', sa.Integer(), server_default='0'),
        sa.Column('absence_rate', sa.Numeric(5, 2), server_default='0'),
        sa.Column('pending_leave_requests', sa.Integer(), server_default='0'),
        sa.Column('approved_leave_today', sa.Integer(), server_default='0'),
        sa.Column('pending_expense_reports', sa.Integer(), server_default='0'),
        sa.Column('total_expenses_submitted', sa.Numeric(12, 2), server_default='0'),
        sa.Column('details', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema='hr_reporting'
    )
    
    # ═══════════════════════════════════════════════════════════
    # HR Alerts Table
    # ═══════════════════════════════════════════════════════════
    op.create_table(
        'hr_alerts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('alert_type', sa.String(50), nullable=False, index=True),
        sa.Column('severity', sa.String(20), server_default='info'),
        sa.Column('employee_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('department_id', UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('related_entity_type', sa.String(50), nullable=True),
        sa.Column('related_entity_id', UUID(as_uuid=True), nullable=True),
        sa.Column('action_required', sa.Boolean(), server_default='false'),
        sa.Column('action_deadline', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', index=True),
        sa.Column('acknowledged_by', UUID(as_uuid=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extra_data', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema='hr_reporting'
    )
    
    op.create_index(
        'ix_hr_alerts_active_severity',
        'hr_alerts',
        ['is_active', 'severity', 'created_at'],
        unique=False,
        schema='hr_reporting'
    )
    
    # ═══════════════════════════════════════════════════════════
    # Employee Monthly Stats Table
    # ═══════════════════════════════════════════════════════════
    op.create_table(
        'employee_monthly_stats',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('employee_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        # Leave metrics
        sa.Column('vacation_days_taken', sa.Numeric(5, 2), server_default='0'),
        sa.Column('vacation_hours_taken', sa.Numeric(6, 2), server_default='0'),
        sa.Column('rol_days_taken', sa.Numeric(5, 2), server_default='0'),
        sa.Column('rol_hours_taken', sa.Numeric(6, 2), server_default='0'),
        sa.Column('permit_hours_taken', sa.Numeric(6, 2), server_default='0'),
        sa.Column('sick_days', sa.Numeric(5, 2), server_default='0'),
        sa.Column('sick_hours', sa.Numeric(6, 2), server_default='0'),
        sa.Column('other_absence_days', sa.Numeric(5, 2), server_default='0'),
        # Balances
        sa.Column('vacation_balance_ap', sa.Numeric(5, 2), server_default='0'),
        sa.Column('vacation_balance_ac', sa.Numeric(5, 2), server_default='0'),
        sa.Column('rol_balance', sa.Numeric(6, 2), server_default='0'),
        sa.Column('permit_balance', sa.Numeric(6, 2), server_default='0'),
        # Expense metrics
        sa.Column('trips_count', sa.Integer(), server_default='0'),
        sa.Column('trips_total_days', sa.Integer(), server_default='0'),
        sa.Column('expenses_total', sa.Numeric(12, 2), server_default='0'),
        sa.Column('allowances_total', sa.Numeric(12, 2), server_default='0'),
        # Payroll
        sa.Column('payroll_codes', JSONB, nullable=True),
        sa.Column('details', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        schema='hr_reporting'
    )
    
    op.create_index(
        'ix_employee_monthly_stats_period',
        'employee_monthly_stats',
        ['employee_id', 'year', 'month'],
        unique=True,
        schema='hr_reporting'
    )
    
    # Grant permissions
    op.execute("GRANT ALL ON SCHEMA hr_reporting TO kronos")
    op.execute("GRANT ALL ON ALL TABLES IN SCHEMA hr_reporting TO kronos")


def downgrade() -> None:
    op.drop_table('employee_monthly_stats', schema='hr_reporting')
    op.drop_table('hr_alerts', schema='hr_reporting')
    op.drop_table('daily_snapshots', schema='hr_reporting')
    op.drop_table('generated_reports', schema='hr_reporting')
    op.execute("DROP SCHEMA IF EXISTS hr_reporting CASCADE")
