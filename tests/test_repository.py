import pytest
from datetime import datetime, timezone
from tldr_bot.repository import Repository
from tests.mock_db import InMemoryAsyncDatabase


@pytest.fixture
def repo():
    db = InMemoryAsyncDatabase()
    return Repository(db)


@pytest.mark.asyncio
async def test_token_lifecycle(repo):
    token = "secret123"
    assert await repo.add_token(token) is True
    assert await repo.add_token(token) is False

    assert await repo.is_chat_activated(100) is False

    # Consume token
    success = await repo.consume_token(token, chat_id=100)
    assert success is True

    # Try consuming again
    retry = await repo.consume_token(token, chat_id=100)
    assert retry is False

    # Activate chat
    await repo.activate_chat(100, "Test Group", token)
    assert await repo.is_chat_activated(100) is True


@pytest.mark.asyncio
async def test_messages_persistence_with_topics(repo):
    chat_id = 200
    now = datetime.now(timezone.utc)

    # Insert messages in topic 42
    for i in range(5):
        await repo.save_message(
            chat_id=chat_id,
            message_thread_id=42,
            message_id=i + 1,
            user_id=1,
            username="alice",
            full_name="Alice",
            text=f"topic42 msg {i + 1}",
            date=datetime.fromtimestamp(now.timestamp() + i, tz=timezone.utc),
        )

    # Insert messages in topic 99
    for i in range(3):
        await repo.save_message(
            chat_id=chat_id,
            message_thread_id=99,
            message_id=i + 10,
            user_id=2,
            username="bob",
            full_name="Bob",
            text=f"topic99 msg {i + 1}",
            date=datetime.fromtimestamp(now.timestamp() + i, tz=timezone.utc),
        )

    # Retrieve topic 42
    topic42_msgs = await repo.get_recent_messages(
        chat_id, limit=3, message_thread_id=42
    )
    assert len(topic42_msgs) == 3
    assert topic42_msgs[0]["text"] == "topic42 msg 3"
    assert topic42_msgs[2]["text"] == "topic42 msg 5"

    # Retrieve topic 99
    topic99_msgs = await repo.get_recent_messages(
        chat_id, limit=10, message_thread_id=99
    )
    assert len(topic99_msgs) == 3
    assert topic99_msgs[0]["text"] == "topic99 msg 1"


@pytest.mark.asyncio
async def test_last_summary_and_tldr_time_per_topic(repo):
    chat_id = 300
    assert await repo.get_last_summary(chat_id, message_thread_id=10) is None
    assert await repo.get_last_tldr_time(chat_id, message_thread_id=10) is None

    await repo.update_last_summary(
        chat_id, message_thread_id=10, summary_text="Topic 10 Summary"
    )
    await repo.update_last_summary(
        chat_id, message_thread_id=20, summary_text="Topic 20 Summary"
    )

    summary10 = await repo.get_last_summary(chat_id, message_thread_id=10)
    assert summary10 is not None
    assert summary10["summary_text"] == "Topic 10 Summary"

    summary20 = await repo.get_last_summary(chat_id, message_thread_id=20)
    assert summary20 is not None
    assert summary20["summary_text"] == "Topic 20 Summary"


@pytest.mark.asyncio
async def test_migrate_chat(repo):
    old_id = -4717904000
    new_id = -1004404521368
    token = "migratetoken"

    # Setup old chat, messages, summaries
    await repo.activate_chat(old_id, "Old Group", token)
    assert await repo.is_chat_activated(old_id) is True

    await repo.save_message(
        chat_id=old_id,
        message_thread_id=None,
        message_id=1,
        user_id=10,
        username="user1",
        full_name="User One",
        text="Hello old group",
        date=datetime.now(timezone.utc),
    )
    await repo.update_last_summary(
        old_id, message_thread_id=None, summary_text="Old group summary"
    )

    # Perform migration
    await repo.migrate_chat(old_chat_id=old_id, new_chat_id=new_id)

    # Verify old chat deactivated/removed, new chat activated
    assert await repo.is_chat_activated(old_id) is False
    assert await repo.is_chat_activated(new_id) is True

    new_chat = await repo.get_chat(new_id)
    assert new_chat["title"] == "Old Group"
    assert new_chat["token_used"] == token

    # Verify messages migrated
    msgs = await repo.get_recent_messages(new_id, limit=5, message_thread_id=None)
    assert len(msgs) == 1
    assert msgs[0]["text"] == "Hello old group"

    old_msgs = await repo.get_recent_messages(old_id, limit=5, message_thread_id=None)
    assert len(old_msgs) == 0

    # Verify summaries migrated
    summary = await repo.get_last_summary(new_id, message_thread_id=None)
    assert summary is not None
    assert summary["summary_text"] == "Old group summary"
