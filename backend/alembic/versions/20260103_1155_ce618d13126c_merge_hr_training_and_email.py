"""merge_hr_training_and_email

Revision ID: ce618d13126c
Revises: 031_hr_training, 20260103_1130_email_provider
Create Date: 2026-01-03 11:55:25.303916+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce618d13126c'
down_revision: Union[str, None] = ('031_hr_training', '20260103_1130_email_provider')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
