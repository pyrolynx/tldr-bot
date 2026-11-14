import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, Chat
from tests.mock_db import InMemoryAsyncDatabase
from tldr_bot.repository import Repository
from tldr_bot.rate_limiter import RateLimiter
from tldr_bot.summarizer import SummarizerService
from tldr_bot.handlers.tldr import handle_tldr_command


@pytest.fixture
def repo():
    db = InMemoryAsyncDatabase()
    return Repository(db)


def create_msg(chat_id: int, text: str, message_thread_id: int = None):
    msg = MagicMock(spec=Message)
    chat = MagicMock(spec=Chat)
    chat.id = chat_id
    chat.type = "supergroup"
    msg.chat = chat
    msg.message_thread_id = message_thread_id
    msg.text = text
    msg.reply = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_tldr_boundary_responses(repo):
    rate_limiter = RateLimiter(repo, cooldown_seconds=300)
    summarizer = MagicMock(spec=SummarizerService)

    # N < 50
    msg = create_msg(-100, "/tldr 20")
    await handle_tldr_command(msg, repo, rate_limiter, summarizer)
    msg.reply.assert_called_once_with("Just read it, bro")

    # N > 1000
    msg2 = create_msg(-100, "/tldr 2000")
    await handle_tldr_command(msg2, repo, rate_limiter, summarizer)
    msg2.reply.assert_called_once_with("It's too much, pay for my tokens first!")


@pytest.mark.asyncio
async def test_tldr_not_enough_messages_in_topic(repo):
    rate_limiter = RateLimiter(repo, cooldown_seconds=300)
    summarizer = MagicMock(spec=SummarizerService)

    msg = create_msg(-100, "/tldr 60", message_thread_id=42)
    await handle_tldr_command(msg, repo, rate_limiter, summarizer)
    assert "Not enough messages recorded yet in this topic" in msg.reply.call_args[0][0]


@pytest.mark.asyncio
async def test_tldr_topic_isolation(repo):
    rate_limiter = RateLimiter(repo, cooldown_seconds=300)
    summarizer = MagicMock(spec=SummarizerService)
    summarizer.summarize_messages = AsyncMock(return_value="Topic 77 summary")

    # Populate 60 messages in topic 77
    now = datetime.now(timezone.utc)
    for i in range(60):
        await repo.save_message(
            chat_id=-100,
            message_thread_id=77,
            message_id=i + 1,
            user_id=1,
            username="testuser",
            full_name="Test",
            text=f"ChatMessage {i + 1}",
            date=now,
        )

    # Topic 88 has 0 messages, should report not enough
    msg_other_topic = create_msg(-100, "/tldr 50", message_thread_id=88)
    await handle_tldr_command(msg_other_topic, repo, rate_limiter, summarizer)
    assert (
        "Not enough messages recorded yet in this topic"
        in msg_other_topic.reply.call_args[0][0]
    )

    # Topic 77 has 60 messages, should succeed
    msg_topic77 = create_msg(-100, "/tldr 55", message_thread_id=77)
    status_mock = MagicMock()
    status_mock.edit_text = AsyncMock()
    msg_topic77.reply.return_value = status_mock

    await handle_tldr_command(msg_topic77, repo, rate_limiter, summarizer)

    summarizer.summarize_messages.assert_called_once()
    status_mock.edit_text.assert_called_once()
    assert "Topic 77 summary" in status_mock.edit_text.call_args[0][0]

    # Immediate second call in topic 77 hits rate limit and returns cached summary
    msg_limited = create_msg(-100, "/tldr 55", message_thread_id=77)
    await handle_tldr_command(msg_limited, repo, rate_limiter, summarizer)
    msg_limited.reply.assert_called_once()
    assert "Rate limit reached" in msg_limited.reply.call_args[0][0]
    assert "Topic 77 summary" in msg_limited.reply.call_args[0][0]
