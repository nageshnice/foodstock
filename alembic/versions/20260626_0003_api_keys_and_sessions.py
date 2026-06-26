"""Add user login sessions and API keys tables.

Revision ID: 20260626_0003
Revises: 20260622_0002
"""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20260626_0003"
down_revision = "20260622_0002"
branch_labels = None
depends_on = None


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def upgrade() -> None:
    if not _table_exists("user_login_sessions"):
        op.create_table(
            "user_login_sessions",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("login_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("logout_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("user_agent", sa.String(500), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        )
        op.create_index("ix_user_login_sessions_user_id", "user_login_sessions", ["user_id"])
        op.create_index("ix_user_login_sessions_login_at", "user_login_sessions", ["login_at"])
        op.create_index("ix_user_login_sessions_is_active", "user_login_sessions", ["is_active"])

    if not _table_exists("user_api_keys"):
        op.create_table(
            "user_api_keys",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column(
                "session_id",
                sa.Uuid(),
                sa.ForeignKey("user_login_sessions.id"),
                nullable=True,
            ),
            sa.Column("key_prefix", sa.String(16), nullable=False),
            sa.Column("key_hash", sa.String(255), nullable=False),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index("ix_user_api_keys_user_id", "user_api_keys", ["user_id"])
        op.create_index("ix_user_api_keys_session_id", "user_api_keys", ["session_id"])
        op.create_index("ix_user_api_keys_key_prefix", "user_api_keys", ["key_prefix"])
        op.create_index("ix_user_api_keys_is_active", "user_api_keys", ["is_active"])


def downgrade() -> None:
    if _table_exists("user_api_keys"):
        op.drop_table("user_api_keys")
    if _table_exists("user_login_sessions"):
        op.drop_table("user_login_sessions")
