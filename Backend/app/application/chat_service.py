import asyncio
import hashlib
import json
from uuid import uuid4

from app.application.errors import (
    AIServiceInvalidOutputError,
    AIServiceTimeoutError,
    AIServiceUnavailableError,
    DeviceRoleNotAllowedError,
    IdentityScopeMismatchError,
)
from app.application.models.ai import AIServiceRequest, InteractionMode
from app.application.models.chat import ChatRequest, ChatResponse
from app.application.ports.ai_service import AIService
from app.application.ports.chat_repository import ChatRepository
from app.domain.identity import AuthenticatedDevice, DeviceRole


class ChatService:
    def __init__(
        self,
        *,
        repository: ChatRepository,
        ai_service: AIService,
        ai_timeout_seconds: float,
    ) -> None:
        self._repository = repository
        self._ai_service = ai_service
        self._ai_timeout_seconds = ai_timeout_seconds

    async def create_response(
        self,
        request: ChatRequest,
        identity: AuthenticatedDevice,
    ) -> ChatResponse:
        self._validate_identity_and_mode(request, identity)
        request_hash = self._hash_request(request)
        existing = await self._repository.find_response(
            identity.profile_id,
            request.request_id,
            request_hash,
        )
        if existing is not None:
            return existing

        ai_request = AIServiceRequest(
            request_id=request.request_id,
            interaction_mode=request.interaction_mode,
            companion_id=request.companion_id,
            user_message=request.user_message,
            time_context=request.time_context,
        )
        try:
            async with asyncio.timeout(self._ai_timeout_seconds):
                result = await self._ai_service.generate_chat(ai_request)
        except TimeoutError as error:
            raise AIServiceTimeoutError from error

        if result.request_id != request.request_id:
            raise AIServiceInvalidOutputError

        response = ChatResponse(
            request_id=request.request_id,
            profile_id=identity.profile_id,
            save_slot_id=request.save_slot_id,
            companion_id=request.companion_id,
            device_id=identity.device_id,
            session_id=request.session_id,
            interaction_mode=request.interaction_mode,
            response_id=f"response-{uuid4()}",
            display_text=result.display_text,
            command_candidates=result.command_candidates,
            memory_candidates=result.memory_candidates,
            ai_metadata=result.metadata,
        )
        return await self._repository.save_response(
            request=request,
            response=response,
            identity=identity,
            request_hash=request_hash,
        )

    @staticmethod
    def _validate_identity_and_mode(
        request: ChatRequest,
        identity: AuthenticatedDevice,
    ) -> None:
        try:
            identity.validate_claims(request.profile_id, request.device_id)
        except ValueError as error:
            raise IdentityScopeMismatchError from error

        expected_role = (
            DeviceRole.WEB_CLIENT
            if request.interaction_mode is InteractionMode.OFFLINE
            else DeviceRole.GAME_CLIENT
        )
        if identity.role is not expected_role:
            raise DeviceRoleNotAllowedError

    @staticmethod
    def _hash_request(request: ChatRequest) -> str:
        canonical = json.dumps(
            request.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
