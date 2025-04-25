"""Initial migration

Revision ID: 58cdd1caec62
Revises:
Create Date: 2025-03-23 21:48:48.133958

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "58cdd1caec62"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute("CREATE SCHEMA IF NOT EXISTS transport")
    op.execute("CREATE SCHEMA IF NOT EXISTS pollution")
    op.execute("CREATE SCHEMA IF NOT EXISTS geography")
    op.execute("CREATE SCHEMA IF NOT EXISTS weather")

    op.create_table(
        "categ",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="transport",
    )

    op.create_table(
        "station",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("wording", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="transport",
    )

    op.create_table(
        "time_bin",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("start_timestamp", sa.DateTime(), nullable=False),
        sa.Column("end_timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="transport",
    )

    op.create_table(
        "transport",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["type_id"],
            ["transport.categ.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="transport",
    )

    op.create_table(
        "schedule",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("transport_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["transport.station.id"],
        ),
        sa.ForeignKeyConstraint(
            ["transport_id"],
            ["transport.transport.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="transport",
    )

    op.create_table(
        "traffic",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("time_bin_id", sa.Integer(), nullable=False),
        sa.Column("validations", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["transport.station.id"],
        ),
        sa.ForeignKeyConstraint(
            ["time_bin_id"],
            ["transport.time_bin.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="transport",
    )

    op.create_table(
        "station",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("wording", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="pollution",
    )

    op.create_table(
        "time_bin",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("start_timestamp", sa.DateTime(), nullable=False),
        sa.Column("end_timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="pollution",
    )

    op.create_table(
        "unity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="pollution",
    )

    op.create_table(
        "measure",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("time_bin_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["pollution.station.id"],
        ),
        sa.ForeignKeyConstraint(
            ["time_bin_id"],
            ["pollution.time_bin.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="pollution",
    )

    op.create_table(
        "sensor",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("measure_id", sa.Integer(), nullable=False),
        sa.Column("unity_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["measure_id"],
            ["pollution.measure.id"],
        ),
        sa.ForeignKeyConstraint(
            ["unity_id"],
            ["pollution.unity.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="pollution",
    )

    op.create_table(
        "street",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("wording", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="geography",
    )

    op.create_table(
        "address",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("street_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["street_id"],
            ["geography.street.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="geography",
    )

    op.create_table(
        "monument",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["address_id"],
            ["geography.address.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="geography",
    )

    op.create_table(
        "parking",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("floor_amount", sa.Integer(), nullable=True),
        sa.Column("places_amount", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["address_id"],
            ["geography.address.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="geography",
    )

    op.create_table(
        "station",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("wording", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="weather",
    )

    op.create_table(
        "time_bin",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("start_timestamp", sa.DateTime(), nullable=False),
        sa.Column("end_timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="weather",
    )

    op.create_table(
        "weather_measure",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("time_bin_id", sa.Integer(), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["weather.station.id"],
        ),
        sa.ForeignKeyConstraint(
            ["time_bin_id"],
            ["weather.time_bin.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="weather",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("weather_measure", schema="weather")
    op.drop_table("time_bin", schema="weather")
    op.drop_table("station", schema="weather")

    op.drop_table("parking", schema="geography")
    op.drop_table("monument", schema="geography")
    op.drop_table("address", schema="geography")
    op.drop_table("street", schema="geography")

    op.drop_table("sensor", schema="pollution")
    op.drop_table("measure", schema="pollution")
    op.drop_table("unity", schema="pollution")
    op.drop_table("time_bin", schema="pollution")
    op.drop_table("station", schema="pollution")

    op.drop_table("traffic", schema="transport")
    op.drop_table("schedule", schema="transport")
    op.drop_table("transport", schema="transport")
    op.drop_table("time_bin", schema="transport")
    op.drop_table("station", schema="transport")
    op.drop_table("categ", schema="transport")
