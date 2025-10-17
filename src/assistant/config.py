# src/assistant/config.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

# --- Nested Models for YAML Structure ---


class ApiEndpoints(BaseModel):
    news_api: str
    fred: str
    arxiv_qfin: str  # Add this field


class NewsApiSettings(BaseModel):
    query: str
    language: str
    sort_by: str
    page_size: int


class ArxivSettings(BaseModel):
    query: str
    max_results: int


class FetcherSettings(BaseModel):
    news_api: NewsApiSettings
    arxiv: ArxivSettings


class AnalyzerSettings(BaseModel):
    llm_model: str


class DigestSettings(BaseModel):
    benchmarks: list[str] = Field(default_factory=lambda: ["SPY", "QQQ"])


# --- Custom YAML Source Function ---


def yaml_config_source() -> Dict[str, Any]:
    """A Pydantic settings source that loads variables from a YAML file."""
    config_path = Path(__file__).parent.parent.parent / "config/base.yaml"
    if not config_path.is_file():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# --- Main Settings Class ---


OLLAMA_CHAT_PATH = "/api/chat"


class Settings(BaseSettings):
    """Main application settings, loaded from YAML, .env, and environment variables."""

    # --- Secret/Dynamic Fields (from .env or environment) ---
    OLLAMA_ENDPOINT: str = "http://localhost:11434"
    NEWS_API_KEY: str
    FRED_API_KEY: Optional[str] = None
    ALPHAVANTAGE_KEY: Optional[str] = None
    SEMANTIC_SCHOLAR_KEY: Optional[str] = None
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str
    DIGEST_TO: str
    WRDS_USERNAME: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    dry_run: bool = False

    # --- Static Fields (from YAML) ---
    api_endpoints: ApiEndpoints
    fetcher_settings: FetcherSettings
    analyzer_settings: AnalyzerSettings
    digest: DigestSettings = Field(default_factory=DigestSettings)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def DRY_RUN(self) -> bool:  # pragma: no cover - shim for legacy attribute
        return self.dry_run

    @DRY_RUN.setter
    def DRY_RUN(self, value: bool) -> None:  # pragma: no cover - shim for legacy attribute
        self.dry_run = value

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        # Set loading precedence: env vars > .env file > yaml file
        return env_settings, dotenv_settings, yaml_config_source


# --- Global Instance ---
settings = Settings()
