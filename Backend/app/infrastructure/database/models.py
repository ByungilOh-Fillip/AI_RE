from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ProfileModel(Base):
    __tablename__ = "profiles"

    profile_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DeviceModel(Base):
    __tablename__ = "devices"
    __table_args__ = (
        UniqueConstraint("token_lookup_id", name="uq_devices_token_lookup"),
        UniqueConstraint("creation_request_id", name="uq_devices_creation_request"),
        UniqueConstraint(
            "game_registration_key",
            name="uq_devices_single_game_registration",
        ),
    )

    device_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.profile_id"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(16), index=True)
    token_lookup_id: Mapped[str] = mapped_column(String(128))
    token_hash: Mapped[str] = mapped_column(String(64))
    creation_request_id: Mapped[str] = mapped_column(String(128))
    game_registration_key: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PairingCodeModel(Base):
    __tablename__ = "pairing_codes"
    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "issue_request_id",
            name="uq_pairing_codes_profile_issue_request",
        ),
        UniqueConstraint(
            "redeemed_request_id",
            name="uq_pairing_codes_redeemed_request",
        ),
    )

    pairing_code_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.profile_id"),
        index=True,
    )
    issuing_device_id: Mapped[str] = mapped_column(
        ForeignKey("devices.device_id"),
        index=True,
    )
    code_hash: Mapped[str] = mapped_column(String(64))
    issue_request_id: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    redeemed_request_id: Mapped[str | None] = mapped_column(String(128))
    paired_device_id: Mapped[str | None] = mapped_column(
        ForeignKey("devices.device_id")
    )


class SaveSlotModel(Base):
    __tablename__ = "save_slots"

    save_slot_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.profile_id"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CompanionModel(Base):
    __tablename__ = "companions"

    companion_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.profile_id"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ConversationModel(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "save_slot_id",
            "companion_id",
            "session_id",
            "interaction_mode",
            name="uq_conversations_scope_session_mode",
        ),
    )

    conversation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.profile_id"),
        index=True,
    )
    save_slot_id: Mapped[str] = mapped_column(
        ForeignKey("save_slots.save_slot_id"),
        index=True,
    )
    companion_id: Mapped[str] = mapped_column(
        ForeignKey("companions.companion_id"),
        index=True,
    )
    session_id: Mapped[str] = mapped_column(String(128))
    interaction_mode: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MessageModel(Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "external_message_id",
            name="uq_messages_profile_external_id",
        ),
    )

    message_row_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.profile_id"),
        index=True,
    )
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.conversation_id"),
        index=True,
    )
    external_message_id: Mapped[str] = mapped_column(String(128))
    request_id: Mapped[str] = mapped_column(String(128), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ChatRequestModel(Base):
    __tablename__ = "chat_requests"
    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "request_id",
            name="uq_chat_requests_profile_request",
        ),
    )

    chat_request_row_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("profiles.profile_id"),
        index=True,
    )
    request_id: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    response_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
