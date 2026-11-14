from unittest.mock import AsyncMock, MagicMock


class InMemoryAsyncDatabase:
    """Lightweight in-memory test double for pymongo.AsyncDatabase"""

    def __init__(self):
        self.tokens_data = {}
        self.chats_data = {}
        self.summaries_data = {}
        self.messages_data = []

        self.tokens = MagicMock()
        self.chats = MagicMock()
        self.summaries = MagicMock()
        self.messages = MagicMock()

        self._setup_mocks()

    def _setup_mocks(self):
        # Tokens
        async def mock_token_insert_one(doc):
            tok = doc["token"]
            if tok in self.tokens_data:
                raise Exception("Duplicate key")
            self.tokens_data[tok] = dict(doc)
            return MagicMock()

        async def mock_token_update_one(query, update):
            tok = query.get("token")
            is_used = query.get("is_used")
            if tok in self.tokens_data:
                entry = self.tokens_data[tok]
                if is_used is None or entry.get("is_used") == is_used:
                    if "$set" in update:
                        entry.update(update["$set"])
                    res = MagicMock()
                    res.modified_count = 1
                    return res
            res = MagicMock()
            res.modified_count = 0
            return res

        self.tokens.insert_one = AsyncMock(side_effect=mock_token_insert_one)
        self.tokens.update_one = AsyncMock(side_effect=mock_token_update_one)
        self.tokens.create_index = AsyncMock()

        # Chats
        async def mock_chat_find_one(query):
            cid = query.get("chat_id")
            chat = self.chats_data.get(cid)
            if not chat:
                return None
            if (
                "is_activated" in query
                and chat.get("is_activated") != query["is_activated"]
            ):
                return None
            return dict(chat)

        async def mock_chat_update_one(query, update, upsert=False):
            cid = query.get("chat_id")
            if cid not in self.chats_data:
                if upsert:
                    self.chats_data[cid] = {"chat_id": cid}
                else:
                    res = MagicMock()
                    res.modified_count = 0
                    return res
            if "$set" in update:
                self.chats_data[cid].update(update["$set"])
            res = MagicMock()
            res.modified_count = 1
            return res

        self.chats.find_one = AsyncMock(side_effect=mock_chat_find_one)
        self.chats.update_one = AsyncMock(side_effect=mock_chat_update_one)

        async def mock_chat_delete_one(query):
            cid = query.get("chat_id")
            if cid in self.chats_data:
                del self.chats_data[cid]
                res = MagicMock()
                res.deleted_count = 1
                return res
            res = MagicMock()
            res.deleted_count = 0
            return res

        self.chats.delete_one = AsyncMock(side_effect=mock_chat_delete_one)
        self.chats.create_index = AsyncMock()

        # Summaries
        async def mock_summary_find_one(query):
            key = (query.get("chat_id"), query.get("message_thread_id"))
            record = self.summaries_data.get(key)
            return dict(record) if record else None

        async def mock_summary_update_one(query, update, upsert=False):
            key = (query.get("chat_id"), query.get("message_thread_id"))
            if key not in self.summaries_data:
                if upsert:
                    self.summaries_data[key] = {
                        "chat_id": query.get("chat_id"),
                        "message_thread_id": query.get("message_thread_id"),
                    }
                else:
                    res = MagicMock()
                    res.modified_count = 0
                    return res
            if "$set" in update:
                self.summaries_data[key].update(update["$set"])
            res = MagicMock()
            res.modified_count = 1
            return res

        async def mock_summary_update_many(query, update):
            cid = query.get("chat_id")
            count = 0
            new_data = {}
            for (c, t), val in list(self.summaries_data.items()):
                if c == cid:
                    if "$set" in update:
                        val.update(update["$set"])
                    new_chat_id = val.get("chat_id")
                    new_data[(new_chat_id, t)] = val
                    count += 1
                else:
                    new_data[(c, t)] = val
            self.summaries_data = new_data
            res = MagicMock()
            res.modified_count = count
            return res

        self.summaries.find_one = AsyncMock(side_effect=mock_summary_find_one)
        self.summaries.update_one = AsyncMock(side_effect=mock_summary_update_one)
        self.summaries.update_many = AsyncMock(side_effect=mock_summary_update_many)
        self.summaries.create_index = AsyncMock()

        # Messages
        async def mock_msg_insert_one(doc):
            self.messages_data.append(dict(doc))
            return MagicMock()

        async def mock_msg_update_many(query, update):
            cid = query.get("chat_id")
            count = 0
            for m in self.messages_data:
                if m.get("chat_id") == cid:
                    if "$set" in update:
                        m.update(update["$set"])
                    count += 1
            res = MagicMock()
            res.modified_count = count
            return res

        def mock_msg_find(query):
            cid = query.get("chat_id")
            thread_id = query.get("message_thread_id")
            matched = [
                m
                for m in self.messages_data
                if m.get("chat_id") == cid and m.get("message_thread_id") == thread_id
            ]

            cursor = MagicMock()

            def sort_fn(field, direction):
                reverse = direction == -1
                matched.sort(key=lambda x: x.get(field), reverse=reverse)
                return cursor

            def limit_fn(n):
                sub_cursor = MagicMock()

                async def to_list(length=None):
                    limit_count = length if length is not None else n
                    return matched[:limit_count]

                sub_cursor.to_list = AsyncMock(side_effect=to_list)
                return sub_cursor

            cursor.sort = MagicMock(side_effect=sort_fn)
            cursor.limit = MagicMock(side_effect=limit_fn)
            return cursor

        self.messages.insert_one = AsyncMock(side_effect=mock_msg_insert_one)
        self.messages.update_many = AsyncMock(side_effect=mock_msg_update_many)
        self.messages.find = MagicMock(side_effect=mock_msg_find)
        self.messages.create_index = AsyncMock()
