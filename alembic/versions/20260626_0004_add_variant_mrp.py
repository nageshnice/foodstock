"""Add mrp column to product_variants for offer pricing.

Revision ID: 20260626_0004
Revises: 20260626_0003
"""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20260626_0004"
down_revision = "20260626_0003"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in {col["name"] for col in inspect(bind).get_columns(table)}


def upgrade() -> None:
    if not _column_exists("product_variants", "mrp"):
        op.add_column(
            "product_variants",
            sa.Column("mrp", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        )
        op.execute(
            "UPDATE product_variants SET mrp = CASE "
            "WHEN price > 0 THEN ROUND(price / 0.87, 2) ELSE price END"
        )


def downgrade() -> None:
    if _column_exists("product_variants", "mrp"):
        op.drop_column("product_variants", "mrp")
