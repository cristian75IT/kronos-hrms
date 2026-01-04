"""add_employee_trainings_table

Revision ID: 065c843d94a9
Revises: 3af2dbb3fd4b
Create Date: 2026-01-04 14:21:38.660651+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '065c843d94a9'
down_revision: Union[str, None] = '3af2dbb3fd4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create employee_trainings table in auth schema
    op.create_table(
        'employee_trainings',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('training_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('certificate_id', sa.String(length=100), nullable=True),
        sa.Column('hours', sa.Integer(), nullable=True),
        sa.Column('provider', sa.String(length=200), nullable=True),
        sa.Column('document_path', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['auth.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='auth'
    )
    op.create_index(op.f('ix_auth_employee_trainings_user_id'), 'employee_trainings', ['user_id'], unique=False, schema='auth')


def downgrade() -> None:
    op.drop_index(op.f('ix_auth_employee_trainings_user_id'), table_name='employee_trainings', schema='auth')
    op.drop_table('employee_trainings', schema='auth')
