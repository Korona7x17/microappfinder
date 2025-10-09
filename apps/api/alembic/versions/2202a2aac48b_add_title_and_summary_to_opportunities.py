"""add title and summary to opportunities

Revision ID: 2202a2aac48b
Revises: e6d296fa314d
Create Date: 2025-10-08 18:32:16.338075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2202a2aac48b'
down_revision: Union[str, Sequence[str], None] = 'e6d296fa314d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add title and summary columns to opportunities table
    op.add_column('opportunities', sa.Column('title', sa.String(100), nullable=False, comment='Opportunity title (max 100 chars)'))
    op.add_column('opportunities', sa.Column('summary', sa.String(500), nullable=False, comment='Opportunity summary (max 500 chars)'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove title and summary columns
    op.drop_column('opportunities', 'summary')
    op.drop_column('opportunities', 'title')
