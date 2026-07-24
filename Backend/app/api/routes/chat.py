from typing import Annotated

from fastapi import APIRouter, Depends, Header

from app.api.dependencies.ai import get_ai_service
from app.api.dependencies.auth import get_authenticated_device
from app.api.dependencies.database import DatabaseSession
from app.api.errors.models import APIError, ErrorCode
from app.api.middleware.request_context import REQUEST_ID_HEADER, request_id_context
from app.application.chat_service import ChatService
from app.application.models.chat import ChatRequest, ChatResponse
from app.application.ports.ai_service import AIService
from app.domain.identity import AuthenticatedDevice
from app.settings import Settings, get_settings
from app.infrastructure.database.chat_repository import SqlAlchemyChatRepository

router = APIRouter(prefix="/api/v1", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def create_chat_response(
    chat_request: ChatRequest,
    identity: Annotated[AuthenticatedDevice, Depends(get_authenticated_device)],
    session: DatabaseSession,
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    x_request_id: Annotated[
        str | None,
        Header(
            alias=REQUEST_ID_HEADER,
            min_length=1,
            max_length=128,
            pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$",
        ),
    ] = None,
) -> ChatResponse:
    if x_request_id is not None and x_request_id != chat_request.request_id:
        raise APIError(
            status_code=400,
            code=ErrorCode.INVALID_REQUEST,
            message="X-Request-ID must match the request body request_id.",
            retryable=False,
        )
    if x_request_id is None:
        request_id_context.set(chat_request.request_id)

    service = ChatService(
        repository=SqlAlchemyChatRepository(session),
        ai_service=ai_service,
        ai_timeout_seconds=settings.ai_request_timeout_seconds,
    )
    return await service.create_response(chat_request, identity)
