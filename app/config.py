"""Typed settings loaded from environment / .env — never hardcoded secrets."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",
                                      extra="ignore")

    app_env: str = "development"
    debug: bool = False

    # Secrets — MUST be provided via env in any non-dev environment.
    secret_key: str = Field(default="dev-only-insecure-change-me")
    database_url: str = "sqlite:///./campuscare.db"

    # LLM provider (optional — chat returns a safe fallback if unset)
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Auth
    access_token_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"

    # CORS — lock down in production to your real origins
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Rate limiting (requests per window per client)
    rate_limit_requests: int = 30
    rate_limit_window_seconds: int = 60

    # Crisis / safety
    crisis_hotline_region: str = "international"

    def assert_production_safe(self) -> list[str]:
        """Return a list of production misconfigurations (empty == safe)."""
        problems = []
        if self.app_env == "production":
            if self.secret_key == "dev-only-insecure-change-me":
                problems.append("SECRET_KEY is still the insecure default")
            if self.debug:
                problems.append("DEBUG must be false in production")
            if self.database_url.startswith("sqlite"):
                problems.append("SQLite is not recommended for production")
        return problems


@lru_cache
def get_settings() -> Settings:
    return Settings()
