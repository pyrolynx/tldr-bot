import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from tldr_bot.database import Database


@pytest.mark.asyncio
async def test_database_init_indexes():
    with patch("tldr_bot.database.AsyncMongoClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        mock_db.messages.create_index = AsyncMock()
        mock_db.tokens.create_index = AsyncMock()
        mock_db.chats.create_index = AsyncMock()
        mock_db.summaries.create_index = AsyncMock()
        mock_client.close = AsyncMock()
        mock_client_cls.return_value = mock_client

        db = Database("mongodb://localhost:27017", "test_db")
        await db.connect()

        assert db.client is not None
        assert db.db is not None
        assert mock_db.messages.create_index.call_count == 2
        assert mock_db.tokens.create_index.call_count == 1
        assert mock_db.chats.create_index.call_count == 1
        assert mock_db.summaries.create_index.call_count == 1

        await db.close()
        mock_client.close.assert_called_once()
        assert db.client is None
