"""add opportunities table

Revision ID: e6d296fa314d
Revises: 3809f4caae0d
Create Date: 2025-10-08 12:10:45.999286

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e6d296fa314d'
down_revision: Union[str, Sequence[str], None] = '3809f4caae0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create opportunities table with indexes and constraints."""
    # Create opportunities table
    op.create_table(
        'opportunities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('pain_point_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Six-dimensional scores
        sa.Column('problem_severity', sa.Float(), nullable=False),
        sa.Column('market_size_indicator', sa.String(10), nullable=False),
        sa.Column('monetization_potential', sa.Float(), nullable=False),
        sa.Column('technical_complexity', sa.Float(), nullable=False),
        sa.Column('competition_level', sa.String(20), nullable=False),
        sa.Column('trend_direction', sa.String(20), nullable=False),

        # Metadata
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('trend_data', postgresql.JSONB(), nullable=True),
        sa.Column('geographic_spread', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('affected_industries', postgresql.ARRAY(sa.String()), nullable=True),

        # Timestamps
        sa.Column('analyzed_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('enrichment_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_enriched_at', sa.DateTime(), nullable=True),

        # Foreign key
        sa.ForeignKeyConstraint(['pain_point_id'], ['pain_points.id'], ondelete='SET NULL'),

        # Check constraints
        sa.CheckConstraint('problem_severity >= 0.0 AND problem_severity <= 10.0', name='check_problem_severity_range'),
        sa.CheckConstraint("market_size_indicator IN ('niche', 'mid', 'large')", name='check_market_size_indicator'),
        sa.CheckConstraint('monetization_potential >= 0.0 AND monetization_potential <= 10.0', name='check_monetization_potential_range'),
        sa.CheckConstraint('technical_complexity >= 0.0 AND technical_complexity <= 10.0', name='check_technical_complexity_range'),
        sa.CheckConstraint("competition_level IN ('low', 'medium', 'high', 'saturated')", name='check_competition_level'),
        sa.CheckConstraint("trend_direction IN ('declining', 'stable', 'growing', 'explosive')", name='check_trend_direction'),
        sa.CheckConstraint('confidence_level >= 0.0 AND confidence_level <= 1.0', name='check_confidence_level_range'),
        sa.CheckConstraint('enrichment_count >= 0', name='check_enrichment_count_nonnegative'),
    )

    # Create indexes
    op.create_index('idx_opportunity_severity', 'opportunities', [sa.text('problem_severity DESC')])
    op.create_index('idx_opportunity_analyzed_at', 'opportunities', [sa.text('analyzed_at DESC')])
    op.create_index('idx_opportunity_cursor', 'opportunities', ['id', 'analyzed_at'])
    op.create_index('idx_opportunity_pain_point', 'opportunities', ['pain_point_id'], postgresql_where=sa.text('pain_point_id IS NOT NULL'))
    op.create_index('idx_opportunity_monetization', 'opportunities', [sa.text('monetization_potential DESC')])
    op.create_index('idx_opportunity_market_size', 'opportunities', ['market_size_indicator'])


def downgrade() -> None:
    """Downgrade schema: drop opportunities table."""
    op.drop_table('opportunities')
