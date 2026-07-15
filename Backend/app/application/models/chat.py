from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from app.application.models.ai import (
    AIMetadata,
    CommandCandidate,
    InteractionMode,
    MemoryCandidate,
    StrictModel,
    TimeContext,
)

StableId = Annotated[
    str,
    Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$",
    ),
]


class ChatRequest(StrictModel):
    schema_version: Literal[1] = 1
    request_id: StableId
    profile_id: StableId | None = None
    save_slot_id: StableId
    companion_id: StableId
    device_id: StableId | None = None
    session_id: StableId
    interaction_mode: InteractionMode
    message_id: StableId
    user_message: str = Field(min_length=1, max_length=2000)
    time_context: TimeContext
    recent_event_ids: list[StableId] = Field(
        default_factory=list,
        max_length=32,
    )

    @model_validator(mode="after")
    def validate_time_source(self) -> Self:
        if (
            self.interaction_mode is InteractionMode.IN_GAME
            and self.time_context.source != "GameWorld"
        ):
            raise ValueError("InGame requests require GameWorld time.")
        if (
            self.interaction_mode is InteractionMode.OFFLINE
            and self.time_context.source != "RealWorld"
        ):
            raise ValueError("Offline requests require RealWorld time.")
        return self


class ChatResponse(StrictModel):
    schema_version: Literal[1] = 1
    request_id: StableId
    profile_id: StableId | None = None
    save_slot_id: StableId
    companion_id: StableId
    device_id: StableId | None = None
    session_id: StableId
    interaction_mode: InteractionMode
    response_id: StableId
    display_text: str = Field(min_length=1, max_length=4000)
    command_candidates: list[CommandCandidate] = Field(
        default_factory=list,
        max_length=4,
    )
    memory_candidates: list[MemoryCandidate] = Field(
        default_factory=list,
        max_length=8,
    )
    ai_metadata: AIMetadata
