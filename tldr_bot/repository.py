from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pymongo.asynchronous.database import AsyncDatabase
from tldr_bot.logger import get_logger

logger = get_logger("tldr_bot.repository")


class Repository:
    def __init__(self, db: AsyncDatabase):
        self.db = db

    # --- Token Management ---

    async def add_token(self, token: str) -> bool:
        """Add a new unused token. Returns True if added, False if duplicate."""
        try:
            await self.db.tokens.insert_one(
                {
                    "token": token,
                    "is_used": False,
                    "created_at": datetime.now(timezone.utc),
                    "used_by_chat_id": None,
                    "used_at": None,
                }
            )
            logger.info("Created new token", token=token)
            return True
        except Exception as e:
            logger.warning("Failed to add token", token=token, error=str(e))
            return False

    async def seed_tokens(self, tokens: List[str]):
        """Seed initial tokens if they do not already exist."""
        for t in tokens:
            await self.add_token(t)

    async def consume_token(self, token: str, chat_id: int) -> bool:
        """Atomically validate and mark token as used for a given chat."""
        logger.debug(
            "Attempting to consume token for chat", token=token, chat_id=chat_id
        )
        result = await self.db.tokens.update_one(
            {"token": token, "is_used": False},
            {
                "$set": {
                    "is_used": True,
                    "used_by_chat_id": chat_id,
                    "used_at": datetime.now(timezone.utc),
                }
            },
        )
        consumed = result.modified_count > 0
        if consumed:
            logger.info("Token consumed successfully", token=token, chat_id=chat_id)
        else:
            logger.warning(
                "Token consumption failed (invalid or already used)",
                token=token,
                chat_id=chat_id,
            )
        return consumed

    # --- Chat Management ---

    async def is_chat_activated(self, chat_id: int) -> bool:
        """Check if chat is activated."""
        chat = await self.db.chats.find_one({"chat_id": chat_id, "is_activated": True})
        is_active = chat is not None
        logger.debug(
            "Checked chat activation state", chat_id=chat_id, is_activated=is_active
        )
        return is_active

    async def activate_chat(
        self, chat_id: int, title: Optional[str], token: str
    ) -> bool:
        """Mark chat as activated."""
        logger.info("Activating chat", chat_id=chat_id, title=title, token=token)
        await self.db.chats.update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "chat_id": chat_id,
                    "title": title,
                    "is_activated": True,
                    "activated_at": datetime.now(timezone.utc),
                    "token_used": token,
                }
            },
            upsert=True,
        )
        return True

    async def get_chat(self, chat_id: int) -> Optional[Dict[str, Any]]:
        return await self.db.chats.find_one({"chat_id": chat_id})

    async def migrate_chat(self, old_chat_id: int, new_chat_id: int):
        """Migrate chat activation, messages, and summaries when group is upgraded to supergroup."""
        logger.info(
            "Migrating chat data for upgraded group",
            old_chat_id=old_chat_id,
            new_chat_id=new_chat_id,
        )
        # Migrate chats collection
        old_chat = await self.get_chat(old_chat_id)
        if old_chat:
            await self.db.chats.update_one(
                {"chat_id": new_chat_id},
                {
                    "$set": {
                        "chat_id": new_chat_id,
                        "title": old_chat.get("title"),
                        "is_activated": old_chat.get("is_activated", True),
                        "activated_at": old_chat.get("activated_at"),
                        "token_used": old_chat.get("token_used"),
                    }
                },
                upsert=True,
            )
            # Remove old chat record
            await self.db.chats.delete_one({"chat_id": old_chat_id})

        # Update messages
        msg_result = await self.db.messages.update_many(
            {"chat_id": old_chat_id},
            {"$set": {"chat_id": new_chat_id}},
        )

        # Update summaries
        sum_result = await self.db.summaries.update_many(
            {"chat_id": old_chat_id},
            {"$set": {"chat_id": new_chat_id}},
        )

        logger.info(
            "Chat migration complete",
            old_chat_id=old_chat_id,
            new_chat_id=new_chat_id,
            messages_migrated=msg_result.modified_count,
            summaries_migrated=sum_result.modified_count,
        )

    # --- Summary & Rate Limiting Management (Thread-Aware) ---

    async def update_last_summary(
        self,
        chat_id: int,
        message_thread_id: Optional[int],
        summary_text: str,
    ):
        """Update last generated summary and last tldr invocation timestamp for chat & thread."""
        now = datetime.now(timezone.utc)
        logger.debug(
            "Updating last summary and timestamp for thread",
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            length=len(summary_text),
        )
        await self.db.summaries.update_one(
            {"chat_id": chat_id, "message_thread_id": message_thread_id},
            {
                "$set": {
                    "chat_id": chat_id,
                    "message_thread_id": message_thread_id,
                    "summary_text": summary_text,
                    "last_tldr_at": now,
                    "created_at": now,
                }
            },
            upsert=True,
        )

    async def get_last_summary(
        self,
        chat_id: int,
        message_thread_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        return await self.db.summaries.find_one(
            {
                "chat_id": chat_id,
                "message_thread_id": message_thread_id,
            }
        )

    async def get_last_tldr_time(
        self,
        chat_id: int,
        message_thread_id: Optional[int] = None,
    ) -> Optional[datetime]:
        record = await self.db.summaries.find_one(
            {
                "chat_id": chat_id,
                "message_thread_id": message_thread_id,
            }
        )
        if record:
            return record.get("last_tldr_at")
        return None

    # --- Message Management (Thread-Aware) ---

    async def save_message(
        self,
        chat_id: int,
        message_thread_id: Optional[int],
        message_id: int,
        user_id: int,
        username: Optional[str],
        full_name: Optional[str],
        text: str,
        date: datetime,
    ):
        """Save text message with optional message_thread_id."""
        logger.debug(
            "Persisting message",
            sender=username or full_name,
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            message_id=message_id,
            user_id=user_id,
            chars=len(text),
        )
        await self.db.messages.insert_one(
            {
                "chat_id": chat_id,
                "message_thread_id": message_thread_id,
                "message_id": message_id,
                "user_id": user_id,
                "username": username,
                "full_name": full_name,
                "text": text,
                "date": date,
            }
        )

    async def get_recent_messages(
        self,
        chat_id: int,
        limit: int,
        message_thread_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve last N messages for chat & thread sorted chronologically (oldest first)."""
        logger.debug(
            "Querying recent messages",
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            limit=limit,
        )
        query: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_thread_id": message_thread_id,
        }

        cursor = self.db.messages.find(query).sort("date", -1).limit(limit)
        messages = await cursor.to_list(length=limit)
        logger.debug(
            "Retrieved messages",
            count=len(messages),
            chat_id=chat_id,
            message_thread_id=message_thread_id,
        )
        return list(reversed(messages))
