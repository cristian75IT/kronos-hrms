"""add_notification_indexes

Revision ID: e542ccc63f31
Revises: f68068de796c
Create Date: 2026-01-10 14:18:00.571789+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e542ccc63f31'
down_revision: Union[str, None] = 'f68068de796c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # op.create_index(
    #     'ix_notifications_notifications_user_id',
    #     'notifications',
    #     ['user_id'],
    #     unique=False,
    #     schema='notifications'
    # )
    op.create_index(
        'ix_notifications_notifications_status',
        'notifications',
        ['status'],
        unique=False,
        schema='notifications'
    )
    op.create_index(
        'ix_notifications_notifications_channel',
        'notifications',
        ['channel'],
        unique=False,
        schema='notifications'
    )
    op.create_index(
        'ix_notifications_notifications_read_at',
        'notifications',
        ['read_at'],
        unique=False,
        schema='notifications'
    )


def downgrade() -> None:
    op.drop_index('ix_notifications_notifications_read_at', table_name='notifications', schema='notifications')
    op.drop_index('ix_notifications_notifications_channel', table_name='notifications', schema='notifications')
    op.drop_index('ix_notifications_notifications_status', table_name='notifications', schema='notifications')
    op.drop_index('ix_notifications_notifications_user_id', table_name='notifications', schema='notifications')
