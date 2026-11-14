from typing import Optional
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
import pymongo
from tldr_bot.logger import get_logger

logger = get_logger("tldr_bot.database")


class Database:
    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name
        self.client: Optional[AsyncMongoClient] = None
        self.db: Optional[AsyncDatabase] = None

    async def connect(self):
        if not self.client:
            logger.info("Connecting to MongoDB", uri=self.uri, database=self.db_name)
            self.client = AsyncMongoClient(self.uri)
            self.db = self.client[self.db_name]
            await self.init_indexes()
            logger.info("MongoDB connected and indexes initialized")

    async def close(self):
        if self.client:
            logger.info("Closing MongoDB connection")
            await self.client.close()
            self.client = None
            self.db = None

    async def init_indexes(self):
        if self.db is None:
            return

        logger.debug("Ensuring MongoDB indexes")
        # 30-day TTL index on messages (2592000 seconds)
        await self.db.messages.create_index(
            [("date", pymongo.ASCENDING)],
            expireAfterSeconds=2592000,
            name="ttl_messages_date_30d",
        )

        # Compound index for fast querying of recent chat & topic messages in chronological order
        await self.db.messages.create_index(
            [
                ("chat_id", pymongo.ASCENDING),
                ("message_thread_id", pymongo.ASCENDING),
                ("date", pymongo.DESCENDING),
            ],
            name="chat_topic_messages_recent",
        )

        # Ensure tokens are uniquely indexed
        await self.db.tokens.create_index(
            [("token", pymongo.ASCENDING)],
            unique=True,
            name="unique_tokens",
        )

        # Ensure chats are uniquely indexed by chat_id
        await self.db.chats.create_index(
            [("chat_id", pymongo.ASCENDING)],
            unique=True,
            name="unique_chat_id",
        )

        # Index for per-thread summary lookup
        await self.db.summaries.create_index(
            [("chat_id", pymongo.ASCENDING), ("message_thread_id", pymongo.ASCENDING)],
            unique=True,
            name="unique_chat_thread_summary",
        )
