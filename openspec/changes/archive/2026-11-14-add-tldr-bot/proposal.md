# Proposal

## Why

Group chats can be fast-paced and overwhelming. Members who return after being away often miss critical discussions, context, or decisions, and reading hundreds of missed messages is time-consuming. This change introduces an automated Telegram bot that records chat messages and provides AI-powered TLDR summaries on demand, protected by single-use token activation, per-chat/per-topic rate limiting, topic-aware message isolation, and verbose structured observability.

## What Changes

- Add a background message ingestion pipeline to continuously store incoming group chat text messages in MongoDB with topic thread isolation (`message_thread_id`) and a 30-day TTL data retention policy.
- Implement topic-aware `/tldr [N]` command allowing users to request a summary of the last `N` messages specifically from the topic/thread where the command was executed.
- Implement an admin token generation command (`/generate_token`) available only in direct message with the bot administrator (identified by configured Telegram username).
- Implement an activation flow requiring each group chat to submit a valid single-use access token before using bot features; any unactivated chat attempting to run commands receives a reminder to activate.
- Add permission and privacy checks when joining a chat to inform admins if the bot lacks access to read messages (e.g., Telegram Bot Privacy Mode enabled without admin rights).
- Integrate OpenAI (`AsyncOpenAI`) to generate conversational summaries from formatted chat histories.
- Implement a per-chat and per-topic rate limiter allowing at most 1 TLDR request every 5 minutes per thread, returning the last generated summary (if available) or a cooldown warning when throttled.
- Integrate `structlog` for structured and verbose logging across all components, supporting configurable JSON or plaintext output formats and positional/keyword arguments.
- Containerize the application with Docker and Docker Compose (including MongoDB).

## Capabilities

### New Capabilities
- `chat-activation`: Single-use token management, admin DM token generation, group chat activation state verification, and access restrictions for unactivated chats.
- `message-ingestion`: Message observation with forum topic tracking, text extraction, Telegram privacy warning detection, and 30-day TTL storage in MongoDB.
- `tldr-summary`: Topic-scoped `/tldr` command processing, boundary checks (N < 50, N > 1000), chat message formatting, and OpenAI-driven summary generation.
- `rate-limiter`: Per-thread 5-minute cooldown enforcement with cached summary fallback when rate-limited.
- `structured-logging`: Configurable JSON/plaintext logging with structlog, supporting positional and keyword arguments for verbose tracing across all scenarios.

### Modified Capabilities
*(None - initial implementation in a clean repository)*

## Impact

- **New Dependencies**: `aiogram` (v3), `pymongo` (v4.9+ async API), `openai`, `pydantic-settings`, `structlog`.
- **Infrastructure**: Docker container with Python 3.13 and MongoDB 7+ database with TTL indexing.
- **External APIs**: Telegram Bot API and OpenAI API.
