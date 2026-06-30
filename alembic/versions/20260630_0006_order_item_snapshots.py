"""Snapshot catalog ids and display fields on order line items.

Revision ID: 20260630_0006
Revises: 20260629_0005
"""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20260630_0006"
down_revision = "20260629_0005"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in {col["name"] for col in inspect(bind).get_columns(table)}


def upgrade() -> None:
    for column, col_type in (
        ("product_int_id", sa.BigInteger()),
        ("variant_int_id", sa.BigInteger()),
        ("brand_name", sa.String(160)),
        ("image_url", sa.String(500)),
    ):
        if not _column_exists("order_items", column):
            op.add_column("order_items", sa.Column(column, col_type, nullable=True))


def downgrade() -> None:
    for column in ("image_url", "brand_name", "variant_int_id", "product_int_id"):
        if _column_exists("order_items", column):
            op.drop_column("order_items", column)
