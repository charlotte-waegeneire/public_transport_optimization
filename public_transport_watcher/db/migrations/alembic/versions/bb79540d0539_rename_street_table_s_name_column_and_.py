"""rename street table's name column and add arrondissement

Revision ID: bb79540d0539
Revises: 185a77c98a35
Create Date: 2025-04-03 21:42:03.468117

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "bb79540d0539"
down_revision: Union[str, None] = "185a77c98a35"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("street", "wording", new_column_name="name", schema="geography")

    op.add_column(
        "street",
        sa.Column("arrondissement", sa.Integer(), nullable=True),
        schema="geography",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("street", "arrondissement", schema="geography")

    op.alter_column("street", "name", new_column_name="wording", schema="geography")
