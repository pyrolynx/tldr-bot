# Tasks

## 1. Project Setup and Environment

- [x] 1.1 Configure project dependencies in `pyproject.toml` (`aiogram`, `pymongo`, `openai`, `pydantic-settings`, `pytest`, `pytest-asyncio`) and verify installation succeeds via `uv sync`
- [x] 1.2 Update application configuration schemas (`settings.py`) using Pydantic for `admin_username` instead of initial tokens, verified with unit tests for config parsing
- [x] 1.3 Add `structlog` to `pyproject.toml` and configure `log_format` and `log_level` in `settings.py`, verified with unit tests
- [x] 1.4 Implement logging setup module in `tldr_bot/logger.py` supporting JSON/plain formats with positional and keyword arguments, verified with unit tests

## 2. Database Layer and Retention

- [x] 2.1 Implement MongoDB client connection and collection initializers in `database.py` with automatic index creation (including 30-day TTL index on messages timestamp) and verify with integration tests
- [x] 2.2 Implement repository helpers for chats, single-use activation tokens, and message persistence, verified with repository tests
- [x] 2.3 Update database compound index and repository helpers to support `message_thread_id` for forum topics and per-thread summary caching, verified with unit tests

## 3. Bot Middleware and Chat Activation

- [x] 3.1 Implement activation logic and the `/activate <token>` command handler, verifying single-use token consumption and chat state transitions with tests
- [x] 3.2 Implement `ActivationMiddleware` to intercept commands from unactivated chats, verify that unactivated chats receive the activation reminder, and verify that regular messages are ignored before activation
- [x] 3.3 Implement `/generate_token` command in DM for configured administrator and verify with unit tests
- [x] 3.4 Implement repository helper to migrate chat data (chats, messages, summaries) from old_chat_id to new_chat_id, verified with unit tests
- [x] 3.5 Implement chat migration handler for `migrate_to_chat_id` and `migrate_from_chat_id` message events, verified with unit tests

## 4. Message Ingestion and Privacy Check

- [x] 4.1 Implement `my_chat_member` handler to detect when the bot is added to a group chat and send a warning if it lacks administrator rights or if privacy mode restricts reading
- [x] 4.2 Implement message recording handler for incoming text messages in activated group chats, verifying messages are correctly persisted into MongoDB
- [x] 4.3 Update message ingestion handler to record `message_thread_id` for incoming messages, verified with unit tests

## 5. Rate Limiter and TLDR Summarization

- [x] 5.1 Implement per-chat rate limiter enforcing a 5-minute cooldown and retrieving the cached last summary if throttled, verified with unit tests
- [x] 5.2 Implement `/tldr [N]` command parameter validation ($N < 50$ replying "Just read it, bro", $N > 1000$ replying "It's too much, pay for my tokens first!"), verified with unit tests
- [x] 5.3 Implement OpenAI summarization service (`openai_client.py`) formatting message history into prompt transcripts, verified with mocked OpenAI test responses
- [x] 5.4 Connect `/tldr` handler to the summarizer, update cached summary on success, and verify end-to-end command response flow
- [x] 5.5 Update `/tldr` handler and rate limiter to isolate queries, summaries, and cooldowns by `message_thread_id` and ensure replies stay in the topic thread, verified with unit tests
- [x] 5.6 Update summarizer system prompt to enforce output in the predominant language of the input messages, verified with unit tests
- [x] 5.7 Update message transcript formatting in SummarizerService to include message timestamps in transcripts, verified with unit tests
- [x] 5.8 Verify and test RateLimiter edge cases for chat vs (chat, topic) cooldown isolation

## 6. Observability Instrumentation and Containerization

- [x] 6.1 Instrument all handlers, middlewares, database operations, and summarizer service with verbose structured logging calls
- [x] 6.2 Create multi-stage `Dockerfile` with Python 3.13 and `uv` to build the bot service image and verify local docker build succeeds
- [x] 6.3 Create `docker-compose.yml` defining the bot service and MongoDB with volume persistence and verify services start cleanly
