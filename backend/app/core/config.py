from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always load backend/.env, not CWD/.env (fixes missing key when uvicorn runs from repo root).
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = ""
    clinical_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    prompt_version: str = "v1"
    # Ephemeral prompt cache breakpoints on static system/guideline/reference blocks (Anthropic)
    anthropic_prompt_cache: bool = True

    @field_validator("anthropic_api_key", "clinical_api_key", mode="before")
    @classmethod
    def strip_secrets(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().strip('"').strip("'")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
