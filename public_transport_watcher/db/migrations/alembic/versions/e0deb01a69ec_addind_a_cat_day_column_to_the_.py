"""adding a cat_day column to the transport time_bin table

Revision ID: e0deb01a69ec
Revises: 58cdd1caec62
Create Date: 2025-03-30 12:40:18.315283

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from public_transport_watcher.db.models.enums import DayCategoryEnum

# revision identifiers, used by Alembic.
revision: str = "e0deb01a69ec"
down_revision: Union[str, None] = "58cdd1caec62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    enum_values = [e.value for e in DayCategoryEnum]
    enum_name = "cat_day"
    enum_schema = "transport"

    op.execute(f"CREATE TYPE {enum_schema}.{enum_name} AS ENUM ({', '.join(repr(v) for v in enum_values)})")

    op.add_column("time_bin", sa.Column("cat_day", sa.String(), nullable=True), schema="transport")
    op.execute(
        """
        ALTER TABLE transport.time_bin 
        ALTER COLUMN cat_day TYPE transport.cat_day 
        USING cat_day::text::transport.cat_day
    """
    )

    op.drop_column("station", "wording", schema="weather")
    op.drop_column("station", "wording", schema="pollution")
    op.drop_column("station", "wording", schema="transport")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("station", sa.Column("wording", sa.String(), nullable=True), schema="weather")
    op.add_column("station", sa.Column("wording", sa.String(), nullable=True), schema="pollution")
    op.add_column("station", sa.Column("wording", sa.String(), nullable=True), schema="transport")

    op.execute(
        """
        ALTER TABLE transport.time_bin 
        ALTER COLUMN cat_day TYPE VARCHAR 
        USING cat_day::text
    """
    )

    op.drop_column("time_bin", "cat_day", schema="transport")
    op.execute("DROP TYPE IF EXISTS transport.cat_day")
