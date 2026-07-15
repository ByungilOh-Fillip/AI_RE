from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.errors import (
    DuplicateRequestError,
    IdentityScopeMismatchError,
)
from app.application.models.chat import ChatRequest, ChatResponse
from app.domain.identity import AuthenticatedDevice
from app.infrastructure.database.models import (
    ChatRequestModel,
    CompanionModel,
    ConversationModel,
    MessageModel,
    ProfileModel,
    SaveSlotModel,
)


class SqlAlchemyChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_response(
        self,
        profile_id: str,
        request_id: str,
        request_hash: str,
    ) -> ChatResponse | None:
        existing = await self._find_existing(profile_id, request_id)
        if existing is None:
            return None
        return self._resolve_duplicate(existing, request_hash)

    async def save_response(
        self,
        *,
        request: ChatRequest,
        response: ChatResponse,
        identity: AuthenticatedDevice,
        request_hash: str,
    ) -> ChatResponse:
        now = datetime.now(timezone.utc)
        conversation = await self._find_conversation(request, identity.profile_id)
        if await self._session.get(ProfileModel, identity.profile_id) is None:
            self._session.add(ProfileModel(profile_id=identity.profile_id, created_at=now))
        save_slot = await self._session.get(SaveSlotModel, request.save_slot_id)
        if save_slot is None:
            self._session.add(
                SaveSlotModel(
                    save_slot_id=request.save_slot_id,
                    profile_id=identity.profile_id,
                    created_at=now,
                )
            )
        elif save_slot.profile_id != identity.profile_id:
            raise IdentityScopeMismatchError
        companion = await self._session.get(CompanionModel, request.companion_id)
        if companion is None:
            self._session.add(
                CompanionModel(
                    companion_id=request.companion_id,
                    profile_id=identity.profile_id,
                    created_at=now,
                )
            )
        elif companion.profile_id != identity.profile_id:
            raise IdentityScopeMismatchError

        if conversation is None:
            conversation = ConversationModel(
                conversation_id=f"conversation-{uuid4()}",
                profile_id=identity.profile_id,
                save_slot_id=request.save_slot_id,
                companion_id=request.companion_id,
                session_id=request.session_id,
                interaction_mode=request.interaction_mode.value,
                created_at=now,
            )
            self._session.add(conversation)

        occurred_at = (
            request.time_context.observed_at
            if request.time_context.source == "RealWorld"
            else now
        )
        self._session.add_all(
            [
                MessageModel(
                    message_row_id=f"message-row-{uuid4()}",
                    profile_id=identity.profile_id,
                    conversation_id=conversation.conversation_id,
                    external_message_id=request.message_id,
                    request_id=request.request_id,
                    role="User",
                    content=request.user_message,
                    occurred_at=occurred_at,
                    created_at=now,
                ),
                MessageModel(
                    message_row_id=f"message-row-{uuid4()}",
                    profile_id=identity.profile_id,
                    conversation_id=conversation.conversation_id,
                    external_message_id=response.response_id,
                    request_id=request.request_id,
                    role="Companion",
                    content=response.display_text,
                    occurred_at=now,
                    created_at=now,
                ),
                ChatRequestModel(
                    chat_request_row_id=f"chat-request-row-{uuid4()}",
                    profile_id=identity.profile_id,
                    request_id=request.request_id,
                    request_hash=request_hash,
                    response_payload=response.model_dump(mode="json"),
                    created_at=now,
                ),
            ]
        )
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            existing = await self._find_existing(identity.profile_id, request.request_id)
            if existing is not None:
                return self._resolve_duplicate(existing, request_hash)
            raise DuplicateRequestError
        return response

    async def _find_existing(
        self,
        profile_id: str,
        request_id: str,
    ) -> ChatRequestModel | None:
        result = await self._session.execute(
            select(ChatRequestModel).where(
                ChatRequestModel.profile_id == profile_id,
                ChatRequestModel.request_id == request_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _resolve_duplicate(
        existing: ChatRequestModel,
        request_hash: str,
    ) -> ChatResponse:
        if existing.request_hash != request_hash:
            raise DuplicateRequestError
        return ChatResponse.model_validate(existing.response_payload)

    async def _find_conversation(
        self,
        request: ChatRequest,
        profile_id: str,
    ) -> ConversationModel | None:
        result = await self._session.execute(
            select(ConversationModel).where(
                ConversationModel.profile_id == profile_id,
                ConversationModel.save_slot_id == request.save_slot_id,
                ConversationModel.companion_id == request.companion_id,
                ConversationModel.session_id == request.session_id,
                ConversationModel.interaction_mode == request.interaction_mode.value,
            )
        )
        return result.scalar_one_or_none()
