import pytest
from tldr_bot.settings import Settings


def test_settings_valid(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key")
    monkeypatch.setenv("ADMIN_USERNAME", "@bot_boss")
    monkeypatch.setenv("RATE_LIMIT_SECONDS", "300")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("LOG_FORMAT", "json")

    settings = Settings(_env_file=None)
    assert settings.telegram_bot_token == "123456:ABC-DEF"
    assert settings.openai_api_key == "sk-test-openai-key"
    assert settings.admin_username == "bot_boss"
    assert settings.rate_limit_seconds == 300
    assert settings.mongodb_database == "tldr_bot"
    assert settings.log_level == "DEBUG"
    assert settings.log_format == "json"


def test_settings_missing_admin_username(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key")
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)

    with pytest.raises(Exception):
        Settings(_env_file=None)
