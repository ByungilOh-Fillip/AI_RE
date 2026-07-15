from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ai_mode: Literal["mock", "local"] = "mock"
    backend_host: str = "0.0.0.0"
    backend_port: int = Field(default=8000, ge=1, le=65535)
    schema_version: int = Field(default=1, ge=1)
    database_url: str = "sqlite+aiosqlite:///./aire.db"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    max_request_body_bytes: int = Field(default=262_144, ge=1)
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    ai_request_timeout_seconds: float = Field(default=10.0, gt=0)
    mock_ai_scenario: Literal[
        "normal",
        "timeout",
        "unavailable",
        "invalid_output",
    ] = "normal"
    dev_profile_id: str = "profile-local-001"
    dev_game_device_id: str = "device-game-001"
    dev_web_device_id: str = "device-phone-001"
    dev_game_device_token: SecretStr | None = None
    dev_web_device_token: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
