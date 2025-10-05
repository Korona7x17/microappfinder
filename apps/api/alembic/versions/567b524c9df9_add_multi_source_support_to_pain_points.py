"""add_multi_source_support_to_pain_points

Revision ID: 567b524c9df9
Revises: ccfea43d8070
Create Date: 2025-10-05 10:28:33.062680

T002: Add multi-source support to PainPoint model
- Add source_platform column to track origin (reddit/hackernews)
- Rename source_reddit_post_ids to source_post_ids for platform-agnostic storage
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '567b524c9df9'
down_revision: Union[str, Sequence[str], None] = 'ccfea43d8070'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add multi-source support to pain_points table"""
    # Add source_platform column with default 'reddit' for existing rows
    op.add_column('pain_points', sa.Column('source_platform', sa.String(20), server_default='reddit', nullable=False))

    # Rename source_reddit_post_ids to source_post_ids
    op.alter_column('pain_points', 'source_reddit_post_ids', new_column_name='source_post_ids')


def downgrade() -> None:
    """Revert pain_points multi-source changes"""
    # Rename back to source_reddit_post_ids
    op.alter_column('pain_points', 'source_post_ids', new_column_name='source_reddit_post_ids')

    # Drop source_platform column
    op.drop_column('pain_points', 'source_platform')
