"""create signature schema

Revision ID: 0cf3c087d0ff
Revises: 1be86edca46d
Create Date: 2026-01-09 08:12:25.946001+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0cf3c087d0ff'
down_revision: Union[str, None] = '1be86edca46d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure schema exists
    op.execute("CREATE SCHEMA IF NOT EXISTS signature")

    # Create table
    op.create_table(
        'signature_transactions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('document_id', sa.String(length=50), nullable=False),
        sa.Column('document_hash', sa.String(length=64), nullable=False),
        sa.Column('document_version', sa.String(length=20), nullable=True),
        sa.Column('signature_method', sa.String(length=20), server_default="MFA_TOTP", nullable=False),
        sa.Column('provider', sa.String(length=20), server_default="KEYCLOAK", nullable=False),
        sa.Column('otp_verified', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('device_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('signed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='signature'
    )

    # Create indexes
    op.create_index(op.f('ix_signature_signature_transactions_user_id'), 'signature_transactions', ['user_id'], unique=False, schema='signature')
    op.create_index(op.f('ix_signature_signature_transactions_document_type'), 'signature_transactions', ['document_type'], unique=False, schema='signature')
    op.create_index(op.f('ix_signature_signature_transactions_document_id'), 'signature_transactions', ['document_id'], unique=False, schema='signature')


def downgrade() -> None:
    # We don't drop the schema in downgrade usually to avoid side effects if shared, but here it is specific.
    # Safe to drop table.
    op.drop_table('signature_transactions', schema='signature')
