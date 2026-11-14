import pytest
from unittest.mock import AsyncMock, MagicMock
from tests.mock_db import InMemoryAsyncDatabase
from tldr_bot.repository import Repository
from tldr_bot.settings import Settings
from tldr_bot.handlers.activation import handle_activate, handle_generate_token


@pytest.fixture
def repo():
    db = InMemoryAsyncDatabase()
    return Repository(db)


@pytest.fixture
def settings():
    return Settings(
        telegram_bot_token="test_tok",
        openai_api_key="sk-test",
        admin_username="super_admin",
    )


def create_mock_message(chat_id: int, chat_type: str, text: str, username: str = None):
    message = MagicMock()
    message.chat.id = chat_id
    message.chat.type = chat_type
    message.chat.title = "Test Group"
    message.text = text
    message.from_user = MagicMock()
    message.from_user.username = username
    message.reply = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_generate_token_in_group_rejected(repo, settings):
    msg = create_mock_message(
        chat_id=-100, chat_type="group", text="/generate_token", username="super_admin"
    )
    await handle_generate_token(msg, repo, settings)
    msg.reply.assert_called_once()
    assert "only permitted in direct messages" in msg.reply.call_args[0][0]


@pytest.mark.asyncio
async def test_generate_token_unauthorized_user(repo, settings):
    msg = create_mock_message(
        chat_id=1, chat_type="private", text="/generate_token", username="intruder"
    )
    await handle_generate_token(msg, repo, settings)
    msg.reply.assert_called_once()
    assert "not authorized" in msg.reply.call_args[0][0]


@pytest.mark.asyncio
async def test_generate_token_admin_success(repo, settings):
    msg = create_mock_message(
        chat_id=1, chat_type="private", text="/generate_token", username="super_admin"
    )
    await handle_generate_token(msg, repo, settings)
    msg.reply.assert_called_once()
    reply_text = msg.reply.call_args[0][0]
    assert "New activation token generated:" in reply_text

    # Verify token is in repository and can be used to activate a group chat
    token = reply_text.split("`")[1]
    consumed = await repo.consume_token(token, chat_id=-100)
    assert consumed is True


@pytest.mark.asyncio
async def test_activate_not_in_group(repo):
    msg = create_mock_message(chat_id=1, chat_type="private", text="/activate secret")
    await handle_activate(msg, repo)
    msg.reply.assert_called_once()
    assert "only be used in group" in msg.reply.call_args[0][0]


@pytest.mark.asyncio
async def test_activate_missing_token(repo):
    msg = create_mock_message(chat_id=-100, chat_type="group", text="/activate")
    await handle_activate(msg, repo)
    msg.reply.assert_called_once()
    assert "Please provide an activation token" in msg.reply.call_args[0][0]


@pytest.mark.asyncio
async def test_activate_invalid_token(repo):
    msg = create_mock_message(
        chat_id=-100, chat_type="group", text="/activate invalid_tok"
    )
    await handle_activate(msg, repo)
    msg.reply.assert_called_once()
    assert "Invalid or already used" in msg.reply.call_args[0][0]


@pytest.mark.asyncio
async def test_activate_success_and_reuse(repo):
    await repo.add_token("valid_token")

    msg = create_mock_message(
        chat_id=-100, chat_type="supergroup", text="/activate valid_token"
    )
    await handle_activate(msg, repo)
    assert "Chat activated successfully!" in msg.reply.call_args[0][0]
    assert await repo.is_chat_activated(-100) is True

    # Try activating same chat again
    msg2 = create_mock_message(
        chat_id=-100, chat_type="supergroup", text="/activate valid_token"
    )
    await handle_activate(msg2, repo)
    assert "already activated" in msg2.reply.call_args[0][0]

    # Try using same token in another chat
    msg3 = create_mock_message(
        chat_id=-200, chat_type="supergroup", text="/activate valid_token"
    )
    await handle_activate(msg3, repo)
    assert "Invalid or already used" in msg3.reply.call_args[0][0]
