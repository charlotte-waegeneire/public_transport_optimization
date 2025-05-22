"""added_lines_names

Revision ID: 558246d31130
Revises: b17ed40e558a
Create Date: 2025-05-22 11:58:31.803421

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "558246d31130"
down_revision: Union[str, None] = "b17ed40e558a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("transport", sa.Column("name", sa.String(100), nullable=True), schema="transport")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("transport", "name", schema="transport")
