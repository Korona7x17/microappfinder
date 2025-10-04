"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create runs table
    op.create_table(
        'runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('topic_tags', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'DONE', 'FAILED', name='runstatus'), nullable=False),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('finished_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('counters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('cost_estimate_cents', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_runs_user_id'), 'runs', ['user_id'], unique=False)

    # Create signals table
    op.create_table(
        'signals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('source', sa.Enum('REDDIT', 'HN', 'PRODUCTHUNT', 'INDIEHACKERS', name='source'), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('audience_guess', sa.Text(), nullable=True),
        sa.Column('job_to_be_done', sa.Text(), nullable=True),
        sa.Column('pain_snippet', sa.Text(), nullable=True),
        sa.Column('frequency', sa.Enum('DAILY', 'WEEKLY', 'IRREGULAR', name='frequency'), nullable=True),
        sa.Column('evidence_pull', sa.Boolean(), nullable=True),
        sa.Column('workaround', sa.Text(), nullable=True),
        sa.Column('wtp_hint', sa.Enum('NONE', 'LOW', 'MEDIUM', 'HIGH', name='wtphint'), nullable=True),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('micro_fit', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_signals_run_id'), 'signals', ['run_id'], unique=False)

    # Create clusters table
    op.create_table(
        'clusters',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('theme', sa.Text(), nullable=False),
        sa.Column('audiences', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('signals_count', sa.Integer(), nullable=True),
        sa.Column('pain_intensity_avg', sa.Float(), nullable=True),
        sa.Column('frequency_mode', sa.String(), nullable=True),
        sa.Column('pull_evidence', sa.Text(), nullable=True),
        sa.Column('gap_summary', sa.Text(), nullable=True),
        sa.Column('score_int', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clusters_run_id'), 'clusters', ['run_id'], unique=False)

    # Create briefs table
    op.create_table(
        'briefs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('cluster_id', sa.String(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('who_hurts', sa.Text(), nullable=True),
        sa.Column('job_to_be_done', sa.Text(), nullable=True),
        sa.Column('killer_feature', sa.Text(), nullable=True),
        sa.Column('scope', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('mechanics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('success_metric', sa.Text(), nullable=True),
        sa.Column('pricing_hint', sa.Text(), nullable=True),
        sa.Column('risks', sa.Text(), nullable=True),
        sa.Column('validation_plan', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('proof_urls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_briefs_run_id'), 'briefs', ['run_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_briefs_run_id'), table_name='briefs')
    op.drop_table('briefs')
    op.drop_index(op.f('ix_clusters_run_id'), table_name='clusters')
    op.drop_table('clusters')
    op.drop_index(op.f('ix_signals_run_id'), table_name='signals')
    op.drop_table('signals')
    op.drop_index(op.f('ix_runs_user_id'), table_name='runs')
    op.drop_table('runs')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS runstatus')
    op.execute('DROP TYPE IF EXISTS source')
    op.execute('DROP TYPE IF EXISTS frequency')
    op.execute('DROP TYPE IF EXISTS wtphint')
