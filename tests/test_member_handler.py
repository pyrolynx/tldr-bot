import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import (
    ChatMemberUpdated,
    Chat,
    ChatMemberMember,
    ChatMemberAdministrator,
)
from tldr_bot.handlers.member import handle_bot_membership_update


@pytest.mark.asyncio
async def test_bot_added_as_regular_member():
    event = MagicMock(spec=ChatMemberUpdated)
    event.chat = MagicMock(spec=Chat)
    event.chat.id = -100123
    event.chat.type = "supergroup"
    event.chat.title = "Test Group"
    event.bot = MagicMock()
    event.bot.send_message = AsyncMock()

    event.old_chat_member = MagicMock()
    event.old_chat_member.status = "left"

    new_member = MagicMock(spec=ChatMemberMember)
    new_member.status = "member"
    event.new_chat_member = new_member

    await handle_bot_membership_update(event)

    event.bot.send_message.assert_called_once()
    msg_text = event.bot.send_message.call_args.kwargs["text"]
    assert "Permission Notice" in msg_text
    assert "Promote me to **Administrator**" in msg_text


@pytest.mark.asyncio
async def test_bot_added_as_admin():
    event = MagicMock(spec=ChatMemberUpdated)
    event.chat = MagicMock(spec=Chat)
    event.chat.id = -100123
    event.chat.type = "supergroup"
    event.chat.title = "Test Group"
    event.bot = MagicMock()
    event.bot.send_message = AsyncMock()

    event.old_chat_member = MagicMock()
    event.old_chat_member.status = "left"

    new_member = MagicMock(spec=ChatMemberAdministrator)
    new_member.status = "administrator"
    event.new_chat_member = new_member

    await handle_bot_membership_update(event)

    event.bot.send_message.assert_called_once()
    msg_text = event.bot.send_message.call_args.kwargs["text"]
    assert "Administrator rights" in msg_text
