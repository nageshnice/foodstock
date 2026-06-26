"""Add int_id, image_url to users, subtitle to regions (MySQL-compatible).

Revision ID: 20260622_0002
Revises: 20260622_0001
"""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20260622_0002"
down_revision = "20260622_0001"
branch_labels = None
depends_on = None

_TABLES = [
    "users",
    "regions",
    "categories",
    "brands",
    "vendors",
    "products",
    "product_variants",
    "carts",
    "cart_items",
    "addresses",
    "orders",
]


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    return any(col["name"] == column for col in inspector.get_columns(table))


def upgrade() -> None:
    conn = op.get_bind()

    for table in _TABLES:
        if _column_exists(table, "int_id"):
            continue
        op.add_column(table, sa.Column("int_id", sa.BigInteger(), nullable=True))
        conn.execute(
            sa.text(f"""
                UPDATE {table} AS target
                INNER JOIN (
                    SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) AS rn
                    FROM {table}
                ) AS ranked ON target.id = ranked.id
                SET target.int_id = ranked.rn
            """)
        )
        op.alter_column(table, "int_id", nullable=False)
        op.create_unique_constraint(f"uq_{table}_int_id", table, ["int_id"])
        op.create_index(f"ix_{table}_int_id", table, ["int_id"])

    if not _column_exists("users", "image_url"):
        op.add_column("users", sa.Column("image_url", sa.String(500), nullable=True))
    if not _column_exists("regions", "subtitle"):
        op.add_column("regions", sa.Column("subtitle", sa.String(200), nullable=True))


def downgrade() -> None:
    if _column_exists("users", "image_url"):
        op.drop_column("users", "image_url")
    if _column_exists("regions", "subtitle"):
        op.drop_column("regions", "subtitle")

    for table in _TABLES:
        if not _column_exists(table, "int_id"):
            continue
        op.drop_index(f"ix_{table}_int_id", table_name=table)
        op.drop_constraint(f"uq_{table}_int_id", table, type_="unique")
        op.drop_column(table, "int_id")
