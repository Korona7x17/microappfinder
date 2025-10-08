"""update_time_range_constraint

Revision ID: 3809f4caae0d
Revises: c9a4c338a204
Create Date: 2025-10-07 12:31:40.280786

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3809f4caae0d'
down_revision: Union[str, Sequence[str], None] = 'c9a4c338a204'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Update time_range constraint to support new values."""
    # Drop old constraint
    op.execute("ALTER TABLE search_runs DROP CONSTRAINT IF EXISTS check_time_range")

    # Add new constraint with updated values: 1month, 3months, 6months, 1year, all
    op.execute(
        "ALTER TABLE search_runs ADD CONSTRAINT check_time_range "
        "CHECK (time_range IN ('1month', '3months', '6months', '1year', 'all'))"
    )


def downgrade() -> None:
    """Downgrade schema - Restore old time_range constraint."""
    # Drop new constraint
    op.execute("ALTER TABLE search_runs DROP CONSTRAINT IF EXISTS check_time_range")

    # Restore old constraint with original values: 24h, 7days, 30days, 90days, 1year, all
    op.execute(
        "ALTER TABLE search_runs ADD CONSTRAINT check_time_range "
        "CHECK (time_range IN ('24h', '7days', '30days', '90days', '1year', 'all'))"
    )
