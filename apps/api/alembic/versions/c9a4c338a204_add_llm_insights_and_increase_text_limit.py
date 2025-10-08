"""add_llm_insights_and_increase_text_limit

Revision ID: c9a4c338a204
Revises: fbf7e4673c45
Create Date: 2025-10-05 21:53:51.385321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c9a4c338a204'
down_revision: Union[str, Sequence[str], None] = 'fbf7e4673c45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add llm_insights column
    op.add_column(
        'pain_points',
        sa.Column('llm_insights', postgresql.JSONB(), nullable=True, comment='LLM-generated insights: problem_summary, why_good_opportunity, key_quotes, scores')
    )

    # Drop old text length constraint (500 chars)
    op.drop_constraint('check_extracted_text_length', 'pain_points', type_='check')

    # Add new text length constraint (2000 chars)
    op.create_check_constraint(
        'check_extracted_text_length',
        'pain_points',
        'char_length(extracted_text) <= 2000'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop new text length constraint (2000 chars)
    op.drop_constraint('check_extracted_text_length', 'pain_points', type_='check')

    # Restore old text length constraint (500 chars)
    op.create_check_constraint(
        'check_extracted_text_length',
        'pain_points',
        'char_length(extracted_text) <= 500'
    )

    # Drop llm_insights column
    op.drop_column('pain_points', 'llm_insights')
