from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
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
    ai_runtime_base_url: str | None = None
    ai_model_name: str | None = None
    ai_prompt_version: str | None = None
    mock_ai_scenario: Literal[
        "normal",
        "command",
        "memory",
        "timeout",
        "unavailable",
        "invalid_output",
    ] = "normal"
    dev_game_device_token: SecretStr | None = None
    device_credential_pepper: SecretStr | None = None
    pairing_code_ttl_seconds: int = Field(default=300, ge=60, le=3600)

    @model_validator(mode="after")
    def validate_local_ai_settings(self) -> "Settings":
        if self.ai_mode == "local":
            required_values = {
                "AI_RUNTIME_BASE_URL": self.ai_runtime_base_url,
                "AI_MODEL_NAME": self.ai_model_name,
                "AI_PROMPT_VERSION": self.ai_prompt_version,
            }
            missing = [name for name, value in required_values.items() if not value]
            if missing:
                names = ", ".join(missing)
                raise ValueError(f"AI_MODE=local requires: {names}.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
