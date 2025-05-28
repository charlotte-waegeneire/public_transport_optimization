"""move parameter id to the log table

Revision ID: c9974f4b191b
Revises: 558246d31130
Create Date: 2025-05-27 15:26:54.164530

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c9974f4b191b"
down_revision: Union[str, None] = "558246d31130"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    schema_name = "services"

    op.add_column("log", sa.Column("response", sa.Text(), nullable=True), schema=schema_name)

    op.execute(
        f"""
        UPDATE {schema_name}.log 
        SET response = r.response 
        FROM {schema_name}.response r 
        WHERE {schema_name}.log.response_id = r.id
    """
    )

    op.drop_constraint(
        "log_response_id_fkey",
        "log",
        type_="foreignkey",
        schema=schema_name,
    )

    op.drop_column("log", "response_id", schema=schema_name)

    op.drop_table("response", schema=schema_name)


def downgrade() -> None:
    """Downgrade schema."""
    schema_name = "services"

    op.create_table(
        "response",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("response", sa.Text()),
        schema=schema_name,
    )

    op.add_column("log", sa.Column("response_id", sa.String(36), nullable=True), schema=schema_name)

    op.execute(
        f"""
        WITH response_inserts AS (
            INSERT INTO {schema_name}.response (id, response)
            SELECT gen_random_uuid()::text, response
            FROM {schema_name}.log
            WHERE response IS NOT NULL
            RETURNING id, response
        )
        UPDATE {schema_name}.log
        SET response_id = ri.id
        FROM response_inserts ri
        WHERE {schema_name}.log.response = ri.response
    """
    )

    op.create_foreign_key(
        "log_response_id_fkey",
        "log",
        "response",
        ["response_id"],
        ["id"],
        source_schema=schema_name,
        referent_schema=schema_name,
    )

    op.drop_column("log", "response", schema=schema_name)
