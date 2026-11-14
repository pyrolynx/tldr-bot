import pytest
from datetime import datetime, timezone, timedelta
from tests.mock_db import InMemoryAsyncDatabase
from tldr_bot.repository import Repository
from tldr_bot.rate_limiter import RateLimiter


@pytest.fixture
def repo():
    db = InMemoryAsyncDatabase()
    return Repository(db)


@pytest.mark.asyncio
async def test_rate_limiter_not_limited_initially(repo):
    limiter = RateLimiter(repo, cooldown_seconds=300)
    is_limited, cached, remaining = await limiter.check_rate_limit(12345)
    assert is_limited is False
    assert cached is None
    assert remaining is None


@pytest.mark.asyncio
async def test_rate_limiter_throttled_with_cached_summary_per_topic(repo):
    limiter = RateLimiter(repo, cooldown_seconds=300)
    chat_id = 12345
    thread_id = 99

    await repo.update_last_summary(
        chat_id, message_thread_id=thread_id, summary_text="Summary for topic 99"
    )

    # Topic 99 is limited
    is_limited, cached, remaining = await limiter.check_rate_limit(
        chat_id, message_thread_id=thread_id
    )
    assert is_limited is True
    assert cached == "Summary for topic 99"
    assert remaining is not None
    assert remaining > 0 and remaining <= 300

    # Topic 100 in the same chat is NOT limited
    is_limited_other, cached_other, _ = await limiter.check_rate_limit(
        chat_id, message_thread_id=100
    )
    assert is_limited_other is False
    assert cached_other is None


@pytest.mark.asyncio
async def test_rate_limiter_cooldown_expired(repo):
    limiter = RateLimiter(repo, cooldown_seconds=300)
    chat_id = 12345
    thread_id = None

    # Set last tldr 6 minutes ago
    six_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=6)
    await repo.db.summaries.update_one(
        {"chat_id": chat_id, "message_thread_id": thread_id},
        {
            "$set": {
                "last_tldr_at": six_mins_ago,
                "summary_text": "Old summary",
                "created_at": six_mins_ago,
            }
        },
        upsert=True,
    )

    is_limited, cached, remaining = await limiter.check_rate_limit(
        chat_id, message_thread_id=thread_id
    )
    assert is_limited is False
    assert cached is None


@pytest.mark.asyncio
async def test_rate_limiter_chat_without_topics_vs_chat_with_topics(repo):
    limiter = RateLimiter(repo, cooldown_seconds=300)
    chat_id = 99999

    # Limit non-topic group (message_thread_id=None)
    await repo.update_last_summary(
        chat_id, message_thread_id=None, summary_text="Non-topic summary"
    )

    # Calling check_rate_limit without message_thread_id or message_thread_id=None is throttled
    is_limited, cached, _ = await limiter.check_rate_limit(chat_id)
    assert is_limited is True
    assert cached == "Non-topic summary"

    is_limited_none, cached_none, _ = await limiter.check_rate_limit(
        chat_id, message_thread_id=None
    )
    assert is_limited_none is True
    assert cached_none == "Non-topic summary"

    # But calling in a topic (e.g. topic 10) in that same chat is isolated and not throttled
    is_limited_topic, cached_topic, _ = await limiter.check_rate_limit(
        chat_id, message_thread_id=10
    )
    assert is_limited_topic is False
    assert cached_topic is None
