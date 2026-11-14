from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = Field(
        ..., description="Telegram Bot Token from BotFather"
    )
    mongodb_uri: str = Field(
        "mongodb://localhost:27017", description="MongoDB connection URI"
    )
    mongodb_database: str = Field("tldr_bot", description="Database name")
    openai_api_key: str = Field(..., description="OpenAI API Key")
    openai_model: str = Field("gpt-4o-mini", description="OpenAI model for summaries")

    # Administrator Telegram username (nickname) allowed to generate activation tokens in DM
    admin_username: str = Field(
        ..., description="Telegram username of the bot admin (without @)"
    )

    # Rate limit cooldown in seconds (default 5 minutes)
    rate_limit_seconds: int = Field(
        300, description="Rate limit cooldown per chat in seconds"
    )

    # Logging settings
    log_level: str = Field(
        "INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    log_format: Literal["plain", "json"] = Field(
        "plain", description="Log output format: plain or json"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("admin_username")
    @classmethod
    def clean_admin_username(cls, v: str) -> str:
        return v.strip().lstrip("@")

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, v: str) -> str:
        return v.strip().upper()
