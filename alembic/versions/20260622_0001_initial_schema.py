"""Create the first-phase commerce schema.

Revision ID: 20260622_0001
Revises: None
"""

import app.models  # noqa: F401
from alembic import op
from app.database.base import Base

revision = "20260622_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
