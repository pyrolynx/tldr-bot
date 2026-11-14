# Design

## Context

See `proposal.md` for background and problem motivation. The project is a new Python 3.13 service interacting with the Telegram Bot API, MongoDB, and the OpenAI API.

## Goals / Non-Goals

**Goals:**
- Provide asynchronous Telegram bot processing using `aiogram` 3.x.
- Asynchronously persist incoming group chat text messages in MongoDB with automated 30-day TTL expiration and topic thread identification (`message_thread_id`).
- Scope `/tldr` queries and summaries strictly to the topic thread where the request was issued.
- Implement token-based chat activation to prevent unauthorized use of OpenAI API tokens, with dynamic token generation in DMs by the configured admin.
- Apply a per-thread 5-minute cooldown with cached fallback for `/tldr`.
- Implement structured logging via `structlog` with configurable JSON/plaintext output and support for positional and keyword arguments.
- Package the bot and its dependencies into a Docker container with `docker-compose` orchestration.

**Non-Goals:**
- Multimodal parsing: Images, voice messages, videos, stickers, and document attachments are ignored for summarization.
- Fine-grained per-user rate limiting (rate limiting is per chat and topic thread).
- Complex multi-tenancy or sharded databases (a single MongoDB database instance suffices).

## Decisions

### 1. Telegram Framework: `aiogram` 3.x
- **Decision**: Use `aiogram` 3.x with asyncio long-polling (or optional webhook support in configuration).
- **Rationale**: Built natively around `asyncio`, type annotations, routers, and filters. Clean handler separation.
- **Alternatives considered**: `python-telegram-bot` (heavier syntax for async dispatch), `telebot` (asyncio support is secondary).

### 2. MongoDB Driver: Native PyMongo Async API
- **Decision**: Use `pymongo.AsyncMongoClient` (`from pymongo import AsyncMongoClient`) and `pymongo.asynchronous.database.AsyncDatabase`.
- **Rationale**: PyMongo 4.9+ natively supports non-blocking asynchronous operations directly integrated with `asyncio`, eliminating the need for `motor` or external wrappers.
- **Alternatives considered**: Synchronous `pymongo` (blocks event loop), `motor` (legacy async wrapper around PyMongo, no longer needed).

### 3. Data Models & TTL Indexing (Topic-Aware)
- **Collections**:
  - `chats`: `{ chat_id, title, is_activated, activated_at, token_used }`
  - `summaries`: `{ chat_id, message_thread_id, summary_text, created_at }`
  - `tokens`: `{ token, is_used, created_at, used_by_chat_id, used_at }`
  - `messages`: `{ chat_id, message_thread_id, message_id, user_id, username, full_name, text, date }`
- **TTL Index**: A TTL index on `messages.date` with `expireAfterSeconds: 2592000` (30 days). MongoDB automatically purges expired records.
- **Compound Query Index**: `[("chat_id", ASCENDING), ("message_thread_id", ASCENDING), ("date", DESCENDING)]`.

### 4. Topic Thread Handling
- **Decision**: In Telegram, messages posted in forum topics contain `message_thread_id: Optional[int]`.
- **Storage**: Store `message_thread_id` (or `None` for main/general non-topic chat).
- **Retrieval**: When `/tldr` is called, pass `message.message_thread_id` to query only messages belonging to that thread.
- **Reply**: Send bot responses using `message_thread_id=message.message_thread_id` to ensure replies stay in the topic.
- **Rate Limiting**: Cooldown and summary cache are tracked by key `(chat_id, message_thread_id)`. Non-topic groups use `message_thread_id=None` across the group.
- **Transcript Formatting**: Messages formatted for summarization prepend the UTC timestamp: `[<YYYY-MM-DD HH:MM UTC>] [<sender>]: <text>`.

### 5. Structured Logging: `structlog`
- Configurable format via `LOG_FORMAT`: `json` or `plain`.
- Processors chain with positional arguments formatter, ISO timestamp, and error formatting.

### 6. Admin Identification & Token Generation
- Authenticate administrator by Telegram username configured in `admin_username` setting.
- Dynamic token generation in private chat with `/generate_token`.

### 7. Packaging & Deployment
- Multi-stage `Dockerfile` with Python 3.13 and `uv`.
- `docker-compose.yml` defining `bot` and `mongodb` with volume persistence.

### 8. Telegram Chat Migration Handling
- **Decision**: Handle `migrate_to_chat_id` and `migrate_from_chat_id` message service updates in `aiogram`.
- **Database updates**:
  - `chats`: update document matching `chat_id: old_chat_id` to `chat_id: new_chat_id` (or upsert).
  - `messages`: `update_many({"chat_id": old_chat_id}, {"$set": {"chat_id": new_chat_id}})`.
  - `summaries`: `update_many({"chat_id": old_chat_id}, {"$set": {"chat_id": new_chat_id}})`.
- **Logging**: Log at INFO level when a chat migration occurs with `old_chat_id` and `new_chat_id`.

## Risks / Trade-offs

- [Bot Privacy Mode enabled by default in Telegram] → When added to a chat, the bot inspects its member status; if regular member, sends a notification to chat admins to grant admin rights or disable privacy mode in BotFather.
- [Topic confusion / General topic vs Subtopics] → When `message_thread_id` is None, query messages where `message_thread_id` is None (or not present for backward compatibility).
- [Token limit or context window overrun on large N] → Even with $N=1000$, average chat messages (50-100 chars) result in ~15,000-25,000 tokens, well within the 128k context window of modern OpenAI models.
