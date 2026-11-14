import json
import logging
from tldr_bot.logger import setup_logging, get_logger


def test_logging_plain_with_kwargs(capsys):
    setup_logging(log_level="DEBUG", log_format="plain")
    logger = get_logger("test_plain")

    logger.info(
        "Processed items for user", count=42, user="alice", chat_id=123, status="ok"
    )

    captured = capsys.readouterr().out
    assert "Processed items for user" in captured
    assert "chat_id=123" in captured
    assert "count=42" in captured
    assert "user='alice'" in captured or "user=alice" in captured


def test_logging_json_with_kwargs(capsys):
    setup_logging(log_level="DEBUG", log_format="json")
    logger = get_logger("test_json")

    logger.debug(
        "Testing rate limit calculation",
        scope="rate_limit",
        remaining_seconds=50,
        chat_id=-999,
    )

    captured = capsys.readouterr().out.strip()
    log_data = json.loads(captured)

    assert log_data["event"] == "Testing rate limit calculation"
    assert log_data["level"] == "debug"
    assert log_data["scope"] == "rate_limit"
    assert log_data["remaining_seconds"] == 50
    assert log_data["chat_id"] == -999
    assert "timestamp" in log_data


def test_aiogram_logger_integration(capsys):
    setup_logging(log_level="INFO", log_format="json")
    aiogram_logger = logging.getLogger("aiogram.dispatcher")
    aiogram_logger.info("Aiogram dispatcher update received")

    captured = capsys.readouterr().out.strip()
    log_data = json.loads(captured)
    assert log_data["event"] == "Aiogram dispatcher update received"
    assert log_data["level"] == "info"
