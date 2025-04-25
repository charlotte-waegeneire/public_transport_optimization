"""added indexes

Revision ID: 185a77c98a35
Revises: e0deb01a69ec
Create Date: 2025-03-30 17:57:43.423380

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "185a77c98a35"
down_revision: Union[str, None] = "e0deb01a69ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Upgrade schema."""
    op.create_index("ix_transport_station_id", "station", ["id"], schema="transport")

    op.create_index(
        "ix_transport_time_bin_timestamps",
        "time_bin",
        ["start_timestamp", "end_timestamp"],
        schema="transport",
    )

    op.create_index("ix_transport_traffic_station_id", "traffic", ["station_id"], schema="transport")
    op.create_index(
        "ix_transport_traffic_time_bin_id",
        "traffic",
        ["time_bin_id"],
        schema="transport",
    )

    op.create_index(
        "uix_transport_traffic_station_time_bin",
        "traffic",
        ["station_id", "time_bin_id"],
        unique=True,
        schema="transport",
    )


def downgrade():
    """Downgrade schema."""
    op.drop_index("ix_transport_station_id", table_name="station", schema="transport")
    op.drop_index("ix_transport_time_bin_timestamps", table_name="time_bin", schema="transport")
    op.drop_index("ix_transport_traffic_station_id", table_name="traffic", schema="transport")
    op.drop_index("ix_transport_traffic_time_bin_id", table_name="traffic", schema="transport")
    op.drop_index(
        "uix_transport_traffic_station_time_bin",
        table_name="traffic",
        schema="transport",
    )
