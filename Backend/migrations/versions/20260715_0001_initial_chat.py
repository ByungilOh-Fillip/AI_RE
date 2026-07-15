"""Create the initial local chat persistence tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260715_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("profile_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("profile_id"),
    )
    op.create_table(
        "save_slots",
        sa.Column("save_slot_id", sa.String(length=128), nullable=False),
        sa.Column("profile_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.profile_id"]),
        sa.PrimaryKeyConstraint("save_slot_id"),
    )
    op.create_index("ix_save_slots_profile_id", "save_slots", ["profile_id"])
    op.create_table(
        "companions",
        sa.Column("companion_id", sa.String(length=128), nullable=False),
        sa.Column("profile_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.profile_id"]),
        sa.PrimaryKeyConstraint("companion_id"),
    )
    op.create_index("ix_companions_profile_id", "companions", ["profile_id"])
    op.create_table(
        "conversations",
        sa.Column("conversation_id", sa.String(length=128), nullable=False),
        sa.Column("profile_id", sa.String(length=128), nullable=False),
        sa.Column("save_slot_id", sa.String(length=128), nullable=False),
        sa.Column("companion_id", sa.String(length=128), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("interaction_mode", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["companion_id"], ["companions.companion_id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.profile_id"]),
        sa.ForeignKeyConstraint(["save_slot_id"], ["save_slots.save_slot_id"]),
        sa.PrimaryKeyConstraint("conversation_id"),
        sa.UniqueConstraint(
            "profile_id",
            "save_slot_id",
            "companion_id",
            "session_id",
            "interaction_mode",
            name="uq_conversations_scope_session_mode",
        ),
    )
    op.create_index("ix_conversations_profile_id", "conversations", ["profile_id"])
    op.create_index("ix_conversations_save_slot_id", "conversations", ["save_slot_id"])
    op.create_index("ix_conversations_companion_id", "conversations", ["companion_id"])
    op.create_table(
        "chat_requests",
        sa.Column("chat_request_row_id", sa.String(length=128), nullable=False),
        sa.Column("profile_id", sa.String(length=128), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.profile_id"]),
        sa.PrimaryKeyConstraint("chat_request_row_id"),
        sa.UniqueConstraint(
            "profile_id",
            "request_id",
            name="uq_chat_requests_profile_request",
        ),
    )
    op.create_index("ix_chat_requests_profile_id", "chat_requests", ["profile_id"])
    op.create_table(
        "messages",
        sa.Column("message_row_id", sa.String(length=128), nullable=False),
        sa.Column("profile_id", sa.String(length=128), nullable=False),
        sa.Column("conversation_id", sa.String(length=128), nullable=False),
        sa.Column("external_message_id", sa.String(length=128), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.conversation_id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.profile_id"]),
        sa.PrimaryKeyConstraint("message_row_id"),
        sa.UniqueConstraint(
            "profile_id",
            "external_message_id",
            name="uq_messages_profile_external_id",
        ),
    )
    op.create_index("ix_messages_profile_id", "messages", ["profile_id"])
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_request_id", "messages", ["request_id"])


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("chat_requests")
    op.drop_table("conversations")
    op.drop_table("companions")
    op.drop_table("save_slots")
    op.drop_table("profiles")
