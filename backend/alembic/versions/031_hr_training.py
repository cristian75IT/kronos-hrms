"""
KRONOS HR Reporting - Training and Safety Tables Migration.

Creates tables for D.Lgs. 81/08 compliance tracking:
- training_records: Employee training certifications
- medical_records: Sorveglianza sanitaria visits
- safety_compliance: Aggregated compliance status per employee
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# Revision identifiers
revision = '031_hr_training'
down_revision = '030_hr_reporting'
branch_labels = None
depends_on = None


def upgrade():
    # Create training_records table
    op.create_table(
        'training_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('training_type', sa.String(50), nullable=False),
        sa.Column('training_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('provider_name', sa.String(200), nullable=True),
        sa.Column('provider_code', sa.String(50), nullable=True),
        sa.Column('training_date', sa.Date(), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('hours', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), server_default='valido'),
        sa.Column('certificate_number', sa.String(100), nullable=True),
        sa.Column('certificate_path', sa.String(500), nullable=True),
        sa.Column('recorded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        schema='hr_reporting'
    )
    
    # Indexes for training_records
    op.create_index(
        'ix_training_records_employee_id',
        'training_records',
        ['employee_id'],
        schema='hr_reporting'
    )
    op.create_index(
        'ix_training_records_training_type',
        'training_records',
        ['training_type'],
        schema='hr_reporting'
    )
    op.create_index(
        'ix_training_records_expiry_date',
        'training_records',
        ['expiry_date'],
        schema='hr_reporting'
    )
    op.create_index(
        'ix_training_records_status',
        'training_records',
        ['status'],
        schema='hr_reporting'
    )
    
    # Create medical_records table
    op.create_table(
        'medical_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('visit_type', sa.String(50), nullable=False),
        sa.Column('visit_date', sa.Date(), nullable=False),
        sa.Column('next_visit_date', sa.Date(), nullable=True),
        sa.Column('fitness_result', sa.String(50), nullable=False),
        sa.Column('restrictions', sa.Text(), nullable=True),
        sa.Column('doctor_name', sa.String(200), nullable=True),
        sa.Column('document_path', sa.String(500), nullable=True),
        sa.Column('recorded_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        schema='hr_reporting'
    )
    
    # Indexes for medical_records
    op.create_index(
        'ix_medical_records_employee_id',
        'medical_records',
        ['employee_id'],
        schema='hr_reporting'
    )
    op.create_index(
        'ix_medical_records_next_visit_date',
        'medical_records',
        ['next_visit_date'],
        schema='hr_reporting'
    )
    
    # Create safety_compliance table
    op.create_table(
        'safety_compliance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_compliant', sa.Boolean(), server_default='true'),
        sa.Column('compliance_score', sa.Integer(), server_default='100'),
        sa.Column('has_formazione_generale', sa.Boolean(), server_default='false'),
        sa.Column('has_formazione_specifica', sa.Boolean(), server_default='false'),
        sa.Column('trainings_expiring_soon', sa.Integer(), server_default='0'),
        sa.Column('trainings_expired', sa.Integer(), server_default='0'),
        sa.Column('medical_fitness_valid', sa.Boolean(), server_default='false'),
        sa.Column('medical_next_visit', sa.Date(), nullable=True),
        sa.Column('medical_restrictions', sa.Text(), nullable=True),
        sa.Column('last_check_date', sa.Date(), nullable=True),
        sa.Column('issues', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id'),
        schema='hr_reporting'
    )
    
    # Indexes for safety_compliance
    op.create_index(
        'ix_safety_compliance_employee_id',
        'safety_compliance',
        ['employee_id'],
        schema='hr_reporting'
    )
    op.create_index(
        'ix_safety_compliance_is_compliant',
        'safety_compliance',
        ['is_compliant'],
        schema='hr_reporting'
    )


def downgrade():
    op.drop_table('safety_compliance', schema='hr_reporting')
    op.drop_table('medical_records', schema='hr_reporting')
    op.drop_table('training_records', schema='hr_reporting')
