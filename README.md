# TL;DR Bad Bot

An asynchronous Telegram bot that records group chat messages and generates smart, concise AI conversation summaries on demand via OpenAI.

Built with Python 3.13, [aiogram 3.x](https://docs.aiogram.dev/), native asynchronous [PyMongo 4.9+](https://pymongo.readthedocs.io/), and structured logging via [structlog](https://www.structlog.org/).

---

## Features

- **Continuous Message Ingestion**: Records incoming text messages in activated group chats into MongoDB with a **30-day automated TTL expiration** (`expireAfterSeconds: 2592000`).
- **Telegram Forum Topics / Threads**: Fully isolates message ingestion, rate limiting, and `/tldr` summaries per topic thread (`message_thread_id`). Replies always stay within the originating topic.
- **Group Migration Resilience**: Detects Telegram group-to-supergroup conversion events (`migrate_to_chat_id` / `migrate_from_chat_id`) and seamlessly migrates activation state, message history, and cached summaries to the new chat ID.
- **Language Preservation**: Generates summaries in the same language as the conversation messages. For multilingual chats, summaries are generated in the predominant language.
- **Timestamped Context**: Formats message history with UTC timestamps (`[YYYY-MM-DD HH:MM UTC] [Sender]: Text`) so the LLM understands conversation chronology and timing intervals.
- **Token-Based Activation**: Protects OpenAI token usage. Only the configured administrator can generate single-use activation tokens in private DMs with `/generate_token`. Groups must activate with `/activate <token>` before any features or recording begin.
- **Per-Chat / Per-Topic Rate Limiting**: Enforces a 5-minute cooldown per thread on `/tldr` requests. If called during cooldown, it provides remaining cooldown time and returns the previously cached summary.
- **Structured Observability**: Configurable logging (`plain` or `json`) via `structlog`, with aiogram loggers routed through structlog.
- **Containerized**: Production-ready multi-stage `Dockerfile` and `docker-compose.yml` for quick deployment.

---

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended package manager) or standard `pip`
- MongoDB 7.0+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- OpenAI API Key

---

## Configuration

Configuration is loaded from environment variables or a `.env` file in the root directory:

| Variable | Type | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | String | *Required* | Telegram Bot API token from @BotFather |
| `OPENAI_API_KEY` | String | *Required* | OpenAI API Key |
| `ADMIN_USERNAME` | String | *Required* | Telegram username of bot admin allowed to run `/generate_token` (without `@`) |
| `MONGODB_URI` | String | `mongodb://localhost:27017` | MongoDB connection URI |
| `MONGODB_DATABASE` | String | `tldr_bot` | MongoDB database name |
| `OPENAI_MODEL` | String | `gpt-4o-mini` | OpenAI model used for summarization |
| `RATE_LIMIT_SECONDS`| Integer | `300` | Cooldown duration per chat/topic in seconds (5 minutes) |
| `LOG_LEVEL` | String | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | String | `plain` | Log format: `plain` or `json` |

Example `.env`:
```dotenv
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz
OPENAI_API_KEY=sk-proj-...
ADMIN_USERNAME=your_telegram_username
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=tldr_bot
OPENAI_MODEL=gpt-4o-mini
RATE_LIMIT_SECONDS=300
LOG_LEVEL=INFO
LOG_FORMAT=plain
```

---

## Quickstart

### 1. Local Development (with `uv`)

1. Clone repository and install dependencies:
   ```bash
   uv sync
   ```

2. Make sure MongoDB is running locally:
   ```bash
   docker run -d --name mongodb -p 27017:27017 mongo:7-jammy
   ```

3. Create `.env` file with your configuration.

4. Run the bot:
   ```bash
   uv run python -m tldr_bot.main
   ```

### 2. Run with Docker Compose

```bash
# Build and start bot & mongodb
docker compose up -d --build

# View logs
docker compose logs -f bot
```

---

## Bot Commands & Usage Flow

### 1. Admin Token Generation (Private Chat)
In a direct message with the bot, the administrator runs:
```
/generate_token
```
*The bot returns a single-use token (e.g. `167QXSz8rDD22ByeXxU-6w`). Non-admin users are rejected.*

### 2. Add Bot to Group & Permissions
1. Add the bot to your Telegram group or forum supergroup.
2. Ensure the bot has **permission to read messages**:
   - Promote the bot to **Administrator**, OR
   - Disable **Group Privacy** in [@BotFather](https://t.me/BotFather) (`/setprivacy` → select bot → `Disable`).

### 3. Activate Group Chat
In the group chat, run:
```
/activate <token>
```
*The token is validated and consumed. The bot will now begin recording incoming messages in that group.*

### 4. Generate Summaries (`/tldr`)
In the group or within a specific forum topic, run:
```
/tldr [N]
```
- `N`: Number of recent messages to summarize (default: `100`, min: `50`, max: `1000`).
- Validations:
  - If $N < 50$: Replies *"Just read it, bro"*.
  - If $N > 1000$: Replies *"It's too much, pay for my tokens first!"*.
  - If fewer than 50 messages recorded: Informs users that not enough messages are stored yet.
- Rate Limiter: If invoked within the 5-minute cooldown, returns the cooldown remaining time and the last generated summary for that thread.

---

## Running Tests

Run test suite via `pytest`:
```bash
uv run pytest
```
All 42 tests cover token activation, rate limiting, OpenAI summarization prompts, structured logging, topic thread isolation, and chat migration.
