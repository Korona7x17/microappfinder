"""Add Reddit Pain Point Discovery tables

Revision ID: 002
Revises: 001
Create Date: 2025-10-04 19:08:54

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email', 'users', ['email'])

    # Create topics table
    op.create_table(
        'topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('keyword', sa.String(100), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('search_count', sa.Integer(), server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_topics_keyword', 'topics', ['keyword'])

    # Create search_runs table
    op.create_table(
        'search_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('time_range', sa.String(20), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('started_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('pain_points_count', sa.Integer(), server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'failed')", name='check_status'),
        sa.CheckConstraint("time_range IN ('24h', '7days', '30days', '90days', '1year', 'all')", name='check_time_range'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_search_runs_user_id', 'search_runs', ['user_id'])
    op.create_index('idx_search_runs_status', 'search_runs', ['status'])

    # Create search_run_topics join table
    op.create_table(
        'search_run_topics',
        sa.Column('search_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['search_run_id'], ['search_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('search_run_id', 'topic_id')
    )
    op.create_index('idx_run_topics_search_run', 'search_run_topics', ['search_run_id'])
    op.create_index('idx_run_topics_topic', 'search_run_topics', ['topic_id'])

    # Create reddit_posts table (temporary cache)
    op.create_table(
        'reddit_posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('reddit_id', sa.String(20), unique=True, nullable=False),
        sa.Column('subreddit', sa.String(50), nullable=False),
        sa.Column('author', sa.String(50), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('comment_count', sa.Integer(), nullable=False),
        sa.Column('created_utc', sa.TIMESTAMP(), nullable=False),
        sa.Column('fetched_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('is_nsfw', sa.Boolean(), server_default='FALSE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reddit_posts_reddit_id', 'reddit_posts', ['reddit_id'])
    op.create_index('idx_reddit_posts_expires_at', 'reddit_posts', ['expires_at'])

    # Create pain_points table (derived aggregates)
    op.create_table(
        'pain_points',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('search_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=False),
        sa.Column('relevance_score', sa.DECIMAL(5, 4), nullable=False),
        sa.Column('sentiment_score', sa.DECIMAL(3, 2), nullable=False),
        sa.Column('source_reddit_post_ids', postgresql.JSONB(), nullable=False),
        sa.Column('source_deleted', sa.Boolean(), server_default='FALSE'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['search_run_id'], ['search_runs.id'], ondelete='CASCADE'),
        sa.CheckConstraint('char_length(extracted_text) <= 500', name='check_extracted_text_length'),
        sa.CheckConstraint('relevance_score >= 0 AND relevance_score <= 1', name='check_relevance_score_range'),
        sa.CheckConstraint('sentiment_score >= -1 AND sentiment_score <= 1', name='check_sentiment_score_range'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pain_points_search_run', 'pain_points', ['search_run_id'])
    op.create_index('idx_pain_points_score', 'pain_points', ['relevance_score'], postgresql_ops={'relevance_score': 'DESC'})


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_pain_points_score', table_name='pain_points')
    op.drop_index('idx_pain_points_search_run', table_name='pain_points')
    op.drop_table('pain_points')

    op.drop_index('idx_reddit_posts_expires_at', table_name='reddit_posts')
    op.drop_index('idx_reddit_posts_reddit_id', table_name='reddit_posts')
    op.drop_table('reddit_posts')

    op.drop_index('idx_run_topics_topic', table_name='search_run_topics')
    op.drop_index('idx_run_topics_search_run', table_name='search_run_topics')
    op.drop_table('search_run_topics')

    op.drop_index('idx_search_runs_status', table_name='search_runs')
    op.drop_index('idx_search_runs_user_id', table_name='search_runs')
    op.drop_table('search_runs')

    op.drop_index('idx_topics_keyword', table_name='topics')
    op.drop_table('topics')

    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
