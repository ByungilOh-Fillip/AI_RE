from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InteractionMode(StrEnum):
    IN_GAME = "InGame"
    OFFLINE = "Offline"


class CommandType(StrEnum):
    FOLLOW = "Command.Follow"
    HOLD_POSITION = "Command.HoldPosition"
    RETURN_TO_PLAYER = "Command.ReturnToPlayer"
    ENGAGE_TARGET = "Command.EngageTarget"
    DISTRACT_TARGET = "Command.DistractTarget"
    MOVE_TO_LOCATION = "Command.MoveToLocation"
    CANCEL_CURRENT = "Command.CancelCurrent"


class GameWorldTimeContext(StrictModel):
    source: Literal["GameWorld"] = "GameWorld"
    day: int = Field(ge=0)
    hour: float = Field(ge=0, lt=24)
    period: Literal["Dawn", "Morning", "Afternoon", "Evening", "Night"]


class RealWorldTimeContext(StrictModel):
    source: Literal["RealWorld"] = "RealWorld"
    observed_at: datetime
    timezone: str = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_real_world_time(self) -> Self:
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("RealWorld observed_at must include a UTC offset.")
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as error:
            raise ValueError("RealWorld timezone must be a valid IANA name.") from error
        return self


TimeContext = Annotated[
    GameWorldTimeContext | RealWorldTimeContext,
    Field(discriminator="source"),
]


class RetrievedMemory(StrictModel):
    memory_id: str = Field(min_length=1, max_length=128)
    summary: str = Field(min_length=1, max_length=512)
    source_ids: list[str] = Field(min_length=1, max_length=16)
    occurred_at: datetime


class AIServiceRequest(StrictModel):
    schema_version: Literal[1] = 1
    request_id: str = Field(min_length=1, max_length=128)
    interaction_mode: InteractionMode
    companion_id: str = Field(min_length=1, max_length=128)
    user_message: str = Field(min_length=1, max_length=2000)
    time_context: TimeContext
    game_context: dict[str, JsonValue] = Field(default_factory=dict)
    retrieved_memories: list[RetrievedMemory] = Field(
        default_factory=list,
        max_length=12,
    )
    allowed_commands: list[CommandType] = Field(default_factory=list, max_length=16)

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


class CommandCandidate(StrictModel):
    command_id: str = Field(min_length=1, max_length=128)
    request_id: str = Field(min_length=1, max_length=128)
    type: CommandType
    target_id: str | None = Field(default=None, max_length=128)
    priority: Literal["Low", "Normal", "High", "Critical"] = "Normal"
    issued_at: datetime
    expires_at: datetime
    parameters: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_expiration(self) -> Self:
        if self.expires_at <= self.issued_at:
            raise ValueError("Command expiration must be later than issue time.")
        return self


class MemoryCandidate(StrictModel):
    candidate_id: str = Field(min_length=1, max_length=128)
    type: Literal[
        "UserSharedEvent",
        "Promise",
        "Preference",
        "RelationshipMoment",
    ]
    summary: str = Field(min_length=1, max_length=512)
    source_ids: list[str] = Field(min_length=1, max_length=16)
    source_mode: InteractionMode
    occurred_at: datetime
    confidence: float = Field(ge=0, le=1)


class AIMetadata(StrictModel):
    provider: str = Field(min_length=1, max_length=64)
    model_version: str = Field(min_length=1, max_length=128)
    prompt_version: str = Field(min_length=1, max_length=128)


class AIServiceResult(StrictModel):
    schema_version: Literal[1] = 1
    request_id: str = Field(min_length=1, max_length=128)
    display_text: str = Field(min_length=1, max_length=4000)
    command_candidates: list[CommandCandidate] = Field(
        default_factory=list,
        max_length=4,
    )
    memory_candidates: list[MemoryCandidate] = Field(
        default_factory=list,
        max_length=8,
    )
    metadata: AIMetadata
