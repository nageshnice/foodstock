"""App settings and content pages for email, push, and legal content.

Revision ID: 20260630_0007
Revises: 20260630_0006
"""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20260630_0007"
down_revision = "20260630_0006"
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    return table in inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if not _table_exists("app_settings"):
        op.create_table(
            "app_settings",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("int_id", sa.BigInteger(), nullable=True),
            sa.Column("setting_key", sa.String(80), nullable=False),
            sa.Column("group", sa.String(20), nullable=False),
            sa.Column("label", sa.String(160), nullable=False),
            sa.Column("description", sa.String(500), nullable=True),
            sa.Column("value", sa.Text(), nullable=True),
            sa.Column("value_type", sa.String(20), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_secret", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("setting_key", name="uq_app_settings_key"),
        )
        op.create_index("ix_app_settings_int_id", "app_settings", ["int_id"], unique=True)
        op.create_index("ix_app_settings_group", "app_settings", ["group"])

    if not _table_exists("content_pages"):
        op.create_table(
            "content_pages",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("slug", sa.String(80), nullable=False),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("contact_email", sa.String(320), nullable=True),
            sa.Column("contact_phone", sa.String(40), nullable=True),
            sa.Column("contact_address", sa.Text(), nullable=True),
            sa.Column("support_hours", sa.String(200), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("slug", name="uq_content_pages_slug"),
        )
        op.create_index("ix_content_pages_slug", "content_pages", ["slug"], unique=True)

    bind = op.get_bind()
    if bind.dialect.name == "mysql":
        settings_seed = [
            ("email_enabled", "email", "Enable email notifications", "Send transactional emails when enabled", "false", "boolean", 1, 0),
            ("email_smtp_host", "email", "SMTP host", "e.g. smtp.gmail.com", "", "string", 1, 0),
            ("email_smtp_port", "email", "SMTP port", "Usually 587 for TLS", "587", "number", 1, 0),
            ("email_smtp_user", "email", "SMTP username", "Login email or API user", "", "string", 1, 0),
            ("email_smtp_password", "email", "SMTP password", "App password or API key", "", "string", 1, 1),
            ("email_from_address", "email", "From email", "Sender address shown to customers", "", "string", 1, 0),
            ("email_from_name", "email", "From name", "Sender display name", "Food Stock", "string", 1, 0),
            ("push_enabled", "push", "Enable push notifications", "Send mobile push when enabled", "false", "boolean", 1, 0),
            ("push_fcm_server_key", "push", "FCM server key", "Firebase Cloud Messaging server key", "", "string", 1, 1),
            ("push_fcm_sender_id", "push", "FCM sender ID", "Firebase project sender ID", "", "string", 1, 0),
        ]
        for key, group, label, desc, value, vtype, active, secret in settings_seed:
            bind.execute(
                sa.text(
                    """
                    INSERT IGNORE INTO app_settings
                    (id, setting_key, `group`, label, description, value, value_type, is_active, is_secret)
                    VALUES (UUID(), :key, :grp, :label, :desc, :value, :vtype, :active, :secret)
                    """
                ),
                {"key": key, "grp": group, "label": label, "desc": desc, "value": value, "vtype": vtype, "active": active, "secret": secret},
            )

        pages_seed = [
            (
                "terms-and-conditions",
                "Terms & Conditions",
                "<p>Update your terms and conditions content from Admin → Settings.</p>",
            ),
            (
                "privacy-policy",
                "Privacy Policy",
                "<p>Update your privacy policy content from Admin → Settings.</p>",
            ),
            (
                "contact-us",
                "Contact Us",
                "<p>Reach out to our support team for order and account help.</p>",
            ),
        ]
        for slug, title, body in pages_seed:
            bind.execute(
                sa.text(
                    """
                    INSERT IGNORE INTO content_pages (id, slug, title, body, is_active)
                    VALUES (UUID(), :slug, :title, :body, 1)
                    """
                ),
                {"slug": slug, "title": title, "body": body},
            )


def downgrade() -> None:
    if _table_exists("content_pages"):
        op.drop_table("content_pages")
    if _table_exists("app_settings"):
        op.drop_table("app_settings")
