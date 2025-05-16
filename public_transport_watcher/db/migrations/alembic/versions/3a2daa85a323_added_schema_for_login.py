"""added schema for login

Revision ID: 3a2daa85a323
Revises: 79463770f866
Create Date: 2025-05-13 13:12:26.786293

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "3a2daa85a323"
down_revision: Union[str, None] = "79463770f866"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
        schema="application",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("users")
