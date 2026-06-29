"""Link brands to regions for region-scoped catalog filtering.

Revision ID: 20260629_0005
Revises: 20260626_0004
"""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20260629_0005"
down_revision = "20260626_0004"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in {col["name"] for col in inspect(bind).get_columns(table)}


def _index_exists(table: str, index_name: str) -> bool:
    bind = op.get_bind()
    return index_name in {idx["name"] for idx in inspect(bind).get_indexes(table)}


def _unique_exists(table: str, name: str) -> bool:
    bind = op.get_bind()
    return name in {uc["name"] for uc in inspect(bind).get_unique_constraints(table)}


def _drop_brand_name_unique() -> None:
    bind = op.get_bind()
    for uc in inspect(bind).get_unique_constraints("brands"):
        if uc["column_names"] == ["name"]:
            op.drop_constraint(uc["name"], "brands", type_="unique")
            return
    for idx in inspect(bind).get_indexes("brands"):
        if idx.get("unique") and idx["column_names"] == ["name"]:
            op.drop_index(idx["name"], table_name="brands")
            return


def upgrade() -> None:
    if not _column_exists("brands", "region_id"):
        op.add_column("brands", sa.Column("region_id", sa.String(length=36), nullable=True))
        op.create_index("ix_brands_region_id", "brands", ["region_id"])
        op.create_foreign_key(
            "fk_brands_region_id",
            "brands",
            "regions",
            ["region_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        """
        UPDATE brands b
        INNER JOIN (
            SELECT p.brand_id, MIN(p.region_id) AS region_id
            FROM products p
            WHERE p.brand_id IS NOT NULL AND p.region_id IS NOT NULL
            GROUP BY p.brand_id
        ) src ON b.id = src.brand_id
        SET b.region_id = src.region_id
        WHERE b.region_id IS NULL
        """
    )

    _drop_brand_name_unique()

    if not _unique_exists("brands", "uq_brands_region_name"):
        op.create_unique_constraint("uq_brands_region_name", "brands", ["region_id", "name"])


def downgrade() -> None:
    if _unique_exists("brands", "uq_brands_region_name"):
        op.drop_constraint("uq_brands_region_name", "brands", type_="unique")

    if _column_exists("brands", "region_id"):
        op.drop_constraint("fk_brands_region_id", "brands", type_="foreignkey")
        op.drop_index("ix_brands_region_id", table_name="brands")
        op.drop_column("brands", "region_id")

    if not _unique_exists("brands", "name"):
        op.create_unique_constraint("name", "brands", ["name"])
