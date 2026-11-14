import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, Chat
from tests.mock_db import InMemoryAsyncDatabase
from tldr_bot.repository import Repository
from tldr_bot.middlewares.activation import ActivationMiddleware


@pytest.fixture
def repo():
    db = InMemoryAsyncDatabase()
    return Repository(db)


def create_msg(chat_id: int, chat_type: str, text: str):
    msg = MagicMock(spec=Message)
    chat = MagicMock(spec=Chat)
    chat.id = chat_id
    chat.type = chat_type
    chat.title = "Test Group"
    msg.chat = chat
    msg.from_user = MagicMock()
    msg.from_user.id = 12345
    msg.message_thread_id = None
    msg.text = text
    msg.caption = None
    msg.migrate_to_chat_id = None
    msg.migrate_from_chat_id = None
    msg.reply = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_middleware_allows_private_chat(repo):
    middleware = ActivationMiddleware(repo)
    handler = AsyncMock(return_value="ok")
    msg = create_msg(1, "private", "/tldr 50")

    result = await middleware(handler, msg, {})
    assert result == "ok"
    handler.assert_called_once()


@pytest.mark.asyncio
async def test_middleware_allows_activate_in_unactivated_group(repo):
    middleware = ActivationMiddleware(repo)
    handler = AsyncMock(return_value="ok")
    msg = create_msg(-100, "group", "/activate test_token")

    result = await middleware(handler, msg, {})
    assert result == "ok"
    handler.assert_called_once()


@pytest.mark.asyncio
async def test_middleware_blocks_other_commands_in_unactivated_group(repo):
    middleware = ActivationMiddleware(repo)
    handler = AsyncMock()
    msg = create_msg(-100, "group", "/tldr 100")

    result = await middleware(handler, msg, {})
    assert result is None
    handler.assert_not_called()
    msg.reply.assert_called_once()
    assert "This chat is not activated!" in msg.reply.call_args[0][0]


@pytest.mark.asyncio
async def test_middleware_ignores_regular_messages_in_unactivated_group(repo):
    middleware = ActivationMiddleware(repo)
    handler = AsyncMock()
    msg = create_msg(-100, "group", "just normal chatting")

    result = await middleware(handler, msg, {})
    assert result is None
    handler.assert_not_called()
    msg.reply.assert_not_called()


@pytest.mark.asyncio
async def test_middleware_allows_all_in_activated_group(repo):
    await repo.activate_chat(-100, "Group", "tok")
    middleware = ActivationMiddleware(repo)
    handler = AsyncMock(return_value="handled")
    msg = create_msg(-100, "group", "/tldr 100")

    result = await middleware(handler, msg, {})
    assert result == "handled"
    handler.assert_called_once()
