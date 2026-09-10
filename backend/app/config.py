from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[2] / ".env", extra="ignore")
    database_url: str = "sqlite:///./data/app.db"
    routing_quality_threshold_tokens: int = 120
    provider_max_attempts: int = 3
    retry_base_delay_ms: int = 50
    retry_jitter_enabled: bool = False
    default_max_context_tokens: int = 1024
    default_reserved_output_tokens: int = 256
    cache_ttl_seconds: int = 300
    rate_limit_capacity: int = 5
    rate_limit_refill_per_second: float = 1.0
    llm_provider_mode: Literal["mock", "openai_compatible"] = "mock"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_fast_model: str = ""
    openai_quality_model: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
