from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock, MagicMock
from tldr_bot.summarizer import SummarizerService


@pytest.mark.asyncio
async def test_format_chat_history():
    service = SummarizerService(api_key="mock_key")
    msgs = [
        {
            "username": "alice",
            "full_name": "Alice A",
            "text": "Hello world",
            "date": datetime(2026, 11, 14, 15, 30, tzinfo=timezone.utc),
        },
        {"username": None, "full_name": "Bob B", "text": "Line 1\nLine 2"},
    ]
    formatted = service.format_chat_history(msgs)
    assert "[2026-11-14 15:30 UTC] [alice]: Hello world" in formatted
    assert "[Bob B]: Line 1 Line 2" in formatted


@pytest.mark.asyncio
async def test_summarize_messages_mocked():
    service = SummarizerService(api_key="mock_key", model="gpt-4o-mini")

    mock_choice = MagicMock()
    mock_choice.message.content = "Here is the summary of the chat."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    service.client.chat.completions.create = AsyncMock(return_value=mock_response)

    msgs = [{"username": "alice", "text": "Fixing the bug now."}]
    summary = await service.summarize_messages(msgs)

    assert summary == "Here is the summary of the chat."
    service.client.chat.completions.create.assert_called_once()
    call_args = service.client.chat.completions.create.call_args[1]
    system_prompt = call_args["messages"][0]["content"]
    assert "same language as the conversation messages" in system_prompt
    assert "in the one that was used the most" in system_prompt
