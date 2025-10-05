"""add_source_tracking_to_search_runs

Revision ID: fbf7e4673c45
Revises: 567b524c9df9
Create Date: 2025-10-05 10:29:13.304902

T003: Add source tracking metadata to SearchRun model
- Add sources_queried JSONB to track which sources were queried
- Add hn_items_fetched to track HN-specific fetch count
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'fbf7e4673c45'
down_revision: Union[str, Sequence[str], None] = '567b524c9df9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add source tracking to search_runs table"""
    # Add sources_queried JSONB column with default ["reddit"] for existing rows
    op.add_column('search_runs', sa.Column('sources_queried', postgresql.JSONB(), server_default='["reddit"]', nullable=False))

    # Add hn_items_fetched column (nullable)
    op.add_column('search_runs', sa.Column('hn_items_fetched', sa.Integer(), nullable=True))

    # Add check constraint for hn_items_fetched
    op.create_check_constraint('check_hn_items_positive', 'search_runs', 'hn_items_fetched >= 0 OR hn_items_fetched IS NULL')


def downgrade() -> None:
    """Revert search_runs source tracking changes"""
    # Drop check constraint
    op.drop_constraint('check_hn_items_positive', 'search_runs', type_='check')

    # Drop columns
    op.drop_column('search_runs', 'hn_items_fetched')
    op.drop_column('search_runs', 'sources_queried')
