from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from tldr_bot.repository import Repository
from tldr_bot.rate_limiter import RateLimiter
from tldr_bot.summarizer import SummarizerService
from tldr_bot.utils import parse_and_validate_n
from tldr_bot.logger import get_logger

logger = get_logger("tldr_bot.handlers.tldr")
tldr_router = Router()


@tldr_router.message(Command("tldr"))
async def handle_tldr_command(
    message: Message,
    repository: Repository,
    rate_limiter: RateLimiter,
    summarizer: SummarizerService,
):
    chat = message.chat
    thread_id = message.message_thread_id

    if chat.type not in ("group", "supergroup"):
        logger.info(
            "Command /tldr invoked outside group chat",
            chat_id=chat.id,
            chat_type=chat.type,
        )
        await message.reply("The `/tldr` command is only available in group chats.")
        return

    # Check parameter bounds
    n, boundary_response = parse_and_validate_n(message.text or "")
    if boundary_response:
        logger.info(
            "Parameter N validation failed for /tldr",
            chat_id=chat.id,
            message_thread_id=thread_id,
            raw_text=message.text,
            response=boundary_response,
        )
        await message.reply(boundary_response)
        return

    # Check rate limit per (chat_id, thread_id)
    is_limited, cached_summary, remaining = await rate_limiter.check_rate_limit(
        chat_id=chat.id,
        message_thread_id=thread_id,
    )
    if is_limited:
        remaining_mins = max(1, (remaining or 0) // 60)
        logger.warning(
            "Rate limit triggered",
            chat_id=chat.id,
            message_thread_id=thread_id,
            remaining_seconds=remaining,
            has_cached_summary=bool(cached_summary),
        )
        if cached_summary:
            await message.reply(
                f"⏳ **Rate limit reached** (max 1 summary per 5 minutes).\n"
                f"Cooldown remaining: ~{remaining_mins} min.\n\n"
                f"Here is the last generated summary:\n\n{cached_summary}",
            )
        else:
            await message.reply(
                f"⏳ **Rate limit reached** (max 1 summary per 5 minutes).\n"
                f"Please wait ~{remaining_mins} min before requesting again.",
            )
        return

    # Fetch last N messages from repository for this topic
    logger.info(
        "Fetching messages for summary",
        limit=n,
        chat_id=chat.id,
        message_thread_id=thread_id,
    )
    messages = await repository.get_recent_messages(
        chat.id, limit=n, message_thread_id=thread_id
    )
    if len(messages) < 50:
        logger.info(
            "Insufficient messages for summary",
            chat_id=chat.id,
            message_thread_id=thread_id,
            found_count=len(messages),
            required_count=50,
        )
        scope_name = "in this topic" if thread_id else "in this chat"
        await message.reply(
            f"ℹ️ Not enough messages recorded yet {scope_name} to generate a summary (found {len(messages)}, need at least 50).",
        )
        return

    # Send typing/progress notification in the topic
    status_msg = await message.reply(
        f"🤖 Analyzing the last {len(messages)} messages, please wait...",
    )

    try:
        logger.info(
            "Requesting OpenAI summary",
            chat_id=chat.id,
            message_thread_id=thread_id,
            message_count=len(messages),
        )
        summary = await summarizer.summarize_messages(messages)
        # Update cached last summary and rate limiter timestamp for this thread
        await repository.update_last_summary(chat.id, thread_id, summary)

        logger.info(
            "Summary successfully generated and saved",
            chat_id=chat.id,
            message_thread_id=thread_id,
            summary_length=len(summary),
        )
        await status_msg.edit_text(
            f"📋 **TLDR Summary (last {len(messages)} messages):**\n\n{summary}"
        )
    except Exception as e:
        logger.error(
            "Failed to generate summary",
            chat_id=chat.id,
            message_thread_id=thread_id,
            error=str(e),
            exc_info=True,
        )
        await status_msg.edit_text(f"❌ Failed to generate summary: {str(e)}")
