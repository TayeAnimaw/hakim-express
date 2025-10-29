"""empty message

Revision ID: cc8029520b6e
Revises: 2ecc558982f9, add_boa_integration
Create Date: 2025-10-21 20:24:04.792392

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc8029520b6e'
down_revision: Union[str, None] = ('2ecc558982f9', 'add_boa_integration')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
