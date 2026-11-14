import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock
from aiogram.types import Message, Chat, User
from tests.mock_db import InMemoryAsyncDatabase
from tldr_bot.repository import Repository
from tldr_bot.handlers.messages import (
    handle_incoming_text_message,
    handle_migrate_to_chat_id,
    handle_migrate_from_chat_id,
)


@pytest.fixture
def repo():
    db = InMemoryAsyncDatabase()
    return Repository(db)


@pytest.mark.asyncio
async def test_handle_incoming_text_message_with_topic(repo):
    message = MagicMock(spec=Message)
    chat = MagicMock(spec=Chat)
    chat.id = -100999
    chat.type = "supergroup"
    message.chat = chat

    user = MagicMock(spec=User)
    user.id = 1234
    user.username = "testuser"
    user.full_name = "Test User"
    message.from_user = user

    message.message_id = 555
    message.message_thread_id = 88  # Forum topic ID
    message.text = "Hello topic 88!"
    message.date = datetime.now(timezone.utc)

    await handle_incoming_text_message(message, repo)

    recent = await repo.get_recent_messages(-100999, limit=10, message_thread_id=88)
    assert len(recent) == 1
    stored = recent[0]
    assert stored["chat_id"] == -100999
    assert stored["message_thread_id"] == 88
    assert stored["message_id"] == 555
    assert stored["text"] == "Hello topic 88!"

    # Ensure other topics do not see it
    other_topic = await repo.get_recent_messages(
        -100999, limit=10, message_thread_id=99
    )
    assert len(other_topic) == 0


@pytest.mark.asyncio
async def test_handle_migrate_to_chat_id(repo):
    old_id = -4717904000
    new_id = -1004404521368
    await repo.activate_chat(old_id, "Old Group", "migratetoken")

    message = MagicMock(spec=Message)
    chat = MagicMock(spec=Chat)
    chat.id = old_id
    message.chat = chat
    message.migrate_to_chat_id = new_id

    await handle_migrate_to_chat_id(message, repo)

    assert await repo.is_chat_activated(old_id) is False
    assert await repo.is_chat_activated(new_id) is True


@pytest.mark.asyncio
async def test_handle_migrate_from_chat_id(repo):
    old_id = -4717904000
    new_id = -1004404521368
    await repo.activate_chat(old_id, "Old Group", "migratetoken")

    message = MagicMock(spec=Message)
    chat = MagicMock(spec=Chat)
    chat.id = new_id
    message.chat = chat
    message.migrate_from_chat_id = old_id

    await handle_migrate_from_chat_id(message, repo)

    assert await repo.is_chat_activated(old_id) is False
    assert await repo.is_chat_activated(new_id) is True
