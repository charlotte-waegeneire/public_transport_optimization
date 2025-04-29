"""added_journey_id

Revision ID: 79463770f866
Revises: a8ff31fc08d1
Create Date: 2025-04-29 15:01:36.718648

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "79463770f866"
down_revision: Union[str, None] = "a8ff31fc08d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'schedule',
        sa.Column('journey_id', sa.String(), nullable=True),
        schema='transport'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column(
        'schedule',
        'journey_id',
        schema='transport'
    )
