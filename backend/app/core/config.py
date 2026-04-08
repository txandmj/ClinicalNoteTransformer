from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
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
    # Anthropic Messages API: cache_control on static blocks (vendor prompt-prefix billing), not our LRU.
    anthropic_api_prompt_prefix_cache: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "ANTHROPIC_API_PROMPT_PREFIX_CACHE",
            "ANTHROPIC_PROMPT_CACHE",
        ),
    )

    # Cost control: cap note text sent to the model (~4 chars per token heuristic).
    generate_max_input_tokens_per_section: int = 1500
    # LRU cache of full /generate JSON (skips LLM). Distinct from anthropic_api_prompt_prefix_cache.
    generate_response_cache_enabled: bool = True
    generate_response_cache_max_entries: int = 256
    # 0 = no limit
    generate_rate_limit_per_minute: int = 30

    @field_validator("anthropic_api_key", "clinical_api_key", mode="before")
    @classmethod
    def strip_secrets(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().strip('"').strip("'")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
