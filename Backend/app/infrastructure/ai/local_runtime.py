from typing import Protocol

import httpx
from pydantic import JsonValue, ValidationError

from app.application.errors import (
    AIServiceInvalidOutputError,
    AIServiceTimeoutError,
    AIServiceUnavailableError,
)
from app.application.models.ai import AIServiceRequest, AIServiceResult


class LocalRuntimeTransport(Protocol):
    async def generate_chat(
        self,
        payload: dict[str, JsonValue],
    ) -> object:
        ...


class HttpLocalRuntimeTransport:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        http_transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._url = f"{base_url.rstrip('/')}/v1/generate-chat"
        self._timeout_seconds = timeout_seconds
        self._http_transport = http_transport

    async def generate_chat(
        self,
        payload: dict[str, JsonValue],
    ) -> object:
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
                transport=self._http_transport,
            ) as client:
                response = await client.post(self._url, json=payload)
        except httpx.TimeoutException as error:
            raise AIServiceTimeoutError from error
        except httpx.RequestError as error:
            raise AIServiceUnavailableError from error

        if response.status_code in {408, 504}:
            raise AIServiceTimeoutError
        if response.is_error:
            raise AIServiceUnavailableError

        try:
            return response.json()
        except ValueError as error:
            raise AIServiceInvalidOutputError from error


class LocalRuntimeAIService:
    def __init__(
        self,
        *,
        model_name: str,
        prompt_version: str,
        transport: LocalRuntimeTransport,
    ) -> None:
        self._model_name = model_name
        self._prompt_version = prompt_version
        self._transport = transport

    async def generate_chat(self, request: AIServiceRequest) -> AIServiceResult:
        payload: dict[str, JsonValue] = {
            "model": self._model_name,
            "prompt_version": self._prompt_version,
            "input": request.model_dump(mode="json"),
        }
        raw_result = await self._transport.generate_chat(payload)
        try:
            return AIServiceResult.model_validate(raw_result)
        except (TypeError, ValidationError) as error:
            raise AIServiceInvalidOutputError from error
