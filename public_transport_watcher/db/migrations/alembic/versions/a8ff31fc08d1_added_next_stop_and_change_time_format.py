"""added_next_stop_and_change_time_format

Revision ID: a8ff31fc08d1
Revises: bb79540d0539
Create Date: 2025-04-25 22:50:01.746836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a8ff31fc08d1'
down_revision: Union[str, None] = 'bb79540d0539'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

transport_schema = "transport"


def upgrade():
    op.add_column(
        'schedule',
        sa.Column('next_station_id', sa.Integer(), nullable=True),
        schema=transport_schema
    )


    op.create_foreign_key(
        'fk_schedule_next_station',
        'schedule', 'station',
        ['next_station_id'], ['id'],
        source_schema=transport_schema,
        referent_schema=transport_schema
    )

    op.add_column(
        'schedule',
        sa.Column('time_only', sa.Time(), nullable=True),
        schema=transport_schema
    )

    op.execute(f"""
        UPDATE {transport_schema}.schedule
        SET time_only = timestamp::time
    """)


    op.drop_column('schedule', 'timestamp', schema=transport_schema)


    op.alter_column(
        'schedule', 'time_only',
        new_column_name='timestamp',
        nullable=False,
        schema=transport_schema
    )


def downgrade():

    op.add_column(
        'schedule',
        sa.Column('full_timestamp', sa.DateTime(), nullable=True),
        schema=transport_schema
    )


    op.execute(f"""
        UPDATE {transport_schema}.schedule
        SET full_timestamp = (CURRENT_DATE + timestamp)
    """)


    op.drop_column('schedule', 'timestamp', schema=transport_schema)

    op.alter_column(
        'schedule', 'full_timestamp',
        new_column_name='timestamp',
        nullable=False,
        schema=transport_schema
    )

    op.drop_constraint(
        'fk_schedule_next_station',
        'schedule',
        schema=transport_schema
    )

    op.drop_column('schedule', 'next_station_id', schema=transport_schema)