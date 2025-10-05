"""add_hackernews_item_model

Revision ID: ccfea43d8070
Revises:
Create Date: 2025-10-05 10:27:43.945239

T001: Create HackerNewsItem table for 48h cache of HN content
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'ccfea43d8070'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create hackernews_items table"""
    op.create_table(
        'hackernews_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('hn_id', sa.String(20), nullable=False),
        sa.Column('hn_type', sa.String(20), nullable=False),
        sa.Column('author', sa.String(50), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('url', sa.String(2048), nullable=True),
        sa.Column('hn_url', sa.String(2048), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('comment_count', sa.Integer(), nullable=False),
        sa.Column('created_utc', sa.TIMESTAMP(), nullable=False),
        sa.Column('fetched_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hn_id', name='uq_hackernews_items_hn_id'),
        sa.CheckConstraint('points >= 0', name='check_points_positive'),
        sa.CheckConstraint('comment_count >= 0', name='check_comments_positive')
    )

    # Create indexes
    op.create_index('ix_hackernews_items_hn_id', 'hackernews_items', ['hn_id'], unique=False)
    op.create_index('ix_hackernews_items_expires_at', 'hackernews_items', ['expires_at'], unique=False)
    op.create_index('ix_hackernews_items_created_utc', 'hackernews_items', ['created_utc'], unique=False)


def downgrade() -> None:
    """Drop hackernews_items table and indexes"""
    op.drop_index('ix_hackernews_items_created_utc', table_name='hackernews_items')
    op.drop_index('ix_hackernews_items_expires_at', table_name='hackernews_items')
    op.drop_index('ix_hackernews_items_hn_id', table_name='hackernews_items')
    op.drop_table('hackernews_items')
