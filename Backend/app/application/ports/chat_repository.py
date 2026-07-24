from typing import Protocol

from app.application.models.chat import ChatRequest, ChatResponse
from app.domain.identity import AuthenticatedDevice


class ChatRepository(Protocol):
    async def find_response(
        self,
        profile_id: str,
        request_id: str,
        request_hash: str,
    ) -> ChatResponse | None:
        ...

    async def save_response(
        self,
        *,
        request: ChatRequest,
        response: ChatResponse,
        identity: AuthenticatedDevice,
        request_hash: str,
    ) -> ChatResponse:
        ...
