"""added api logs schema

Revision ID: b17ed40e558a
Revises: 3a2daa85a323
Create Date: 2025-05-18 16:14:59.748282

"""

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b17ed40e558a"
down_revision: Union[str, None] = "3a2daa85a323"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

http_methods = [("GET",), ("POST",), ("PUT",), ("DELETE",), ("PATCH",), ("OPTIONS",), ("HEAD",)]

status_codes = [
    (200, "OK"),
    (201, "Created"),
    (204, "No Content"),
    (400, "Bad Request"),
    (401, "Unauthorized"),
    (403, "Forbidden"),
    (404, "Not Found"),
    (500, "Internal Server Error"),
]


def upgrade() -> None:
    """Upgrade schema."""
    schema_name = "services"

    op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

    op.create_table(
        "method",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(10), nullable=False),
        schema=schema_name,
    )

    op.create_table(
        "status",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(50), nullable=False),
        schema=schema_name,
    )

    op.create_table(
        "response",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("response", sa.Text()),
        schema=schema_name,
    )

    op.create_table(
        "parameter",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("value", sa.Text()),
        schema=schema_name,
    )

    op.create_table(
        "log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("user_agent", sa.Text()),
        sa.Column("execution_time", sa.Float(), nullable=False),
        sa.Column("request_path", sa.String(255), nullable=False),
        sa.Column("method_id", sa.String(36), nullable=False),
        sa.Column("status_id", sa.String(36), nullable=False),
        sa.Column("response_id", sa.String(36), nullable=True),
        sa.ForeignKeyConstraint(["method_id"], [f"{schema_name}.method.id"]),
        sa.ForeignKeyConstraint(["status_id"], [f"{schema_name}.status.id"]),
        sa.ForeignKeyConstraint(["response_id"], [f"{schema_name}.response.id"]),
        schema=schema_name,
    )

    op.create_table(
        "request",
        sa.Column("log_id", sa.String(36), nullable=False),
        sa.Column("parameter_id", sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(["log_id"], [f"{schema_name}.log.id"]),
        sa.ForeignKeyConstraint(["parameter_id"], [f"{schema_name}.parameter.id"]),
        sa.PrimaryKeyConstraint("log_id", "parameter_id"),
        schema=schema_name,
    )

    op.create_index("idx_log_timestamp", "log", ["timestamp"], schema=schema_name)
    op.create_index("idx_log_method", "log", ["method_id"], schema=schema_name)
    op.create_index("idx_log_status", "log", ["status_id"], schema=schema_name)
    op.create_index("idx_request_log", "request", ["log_id"], schema=schema_name)

    method_table = sa.table("method", sa.column("id", sa.String), sa.column("name", sa.String), schema=schema_name)

    for method in http_methods:
        op.execute(method_table.insert().values({"id": str(uuid.uuid4()), "name": method[0]}))

    status_table = sa.table(
        "status",
        sa.column("id", sa.String),
        sa.column("code", sa.Integer),
        sa.column("description", sa.String),
        schema=schema_name,
    )

    for status in status_codes:
        op.execute(status_table.insert().values({"id": str(uuid.uuid4()), "code": status[0], "description": status[1]}))


def downgrade() -> None:
    """Downgrade schema."""
    schema_name = "services"

    op.drop_index("idx_request_log", table_name="request", schema=schema_name)
    op.drop_index("idx_log_status", table_name="log", schema=schema_name)
    op.drop_index("idx_log_method", table_name="log", schema=schema_name)
    op.drop_index("idx_log_timestamp", table_name="log", schema=schema_name)
    op.drop_table("request", schema=schema_name)
    op.drop_table("log", schema=schema_name)
    op.drop_table("parameter", schema=schema_name)
    op.drop_table("response", schema=schema_name)
    op.drop_table("status", schema=schema_name)
    op.drop_table("method", schema=schema_name)

    op.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
