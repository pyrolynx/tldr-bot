from datetime import timezone
from aiogram import Router, F
from aiogram.types import Message
from tldr_bot.repository import Repository
from tldr_bot.logger import get_logger

logger = get_logger("tldr_bot.handlers.messages")
messages_router = Router()


@messages_router.message(F.migrate_to_chat_id)
async def handle_migrate_to_chat_id(message: Message, repository: Repository):
    """Handle basic group migration to supergroup (sent to the old basic group)."""
    old_chat_id = message.chat.id
    new_chat_id = message.migrate_to_chat_id
    if new_chat_id:
        logger.info(
            "Received group migration event (migrate_to_chat_id)",
            old_chat_id=old_chat_id,
            new_chat_id=new_chat_id,
        )
        await repository.migrate_chat(old_chat_id=old_chat_id, new_chat_id=new_chat_id)


@messages_router.message(F.migrate_from_chat_id)
async def handle_migrate_from_chat_id(message: Message, repository: Repository):
    """Handle supergroup created from basic group (sent to the new supergroup)."""
    old_chat_id = message.migrate_from_chat_id
    new_chat_id = message.chat.id
    if old_chat_id:
        logger.info(
            "Received supergroup migration event (migrate_from_chat_id)",
            old_chat_id=old_chat_id,
            new_chat_id=new_chat_id,
        )
        await repository.migrate_chat(old_chat_id=old_chat_id, new_chat_id=new_chat_id)


@messages_router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.text,
    ~F.text.startswith("/"),
)
async def handle_incoming_text_message(message: Message, repository: Repository):
    """Store group chat text messages in the database, preserving topic thread context."""
    # Ensure text is not empty
    text = (message.text or "").strip()
    if not text:
        return

    sender = message.from_user
    user_id = sender.id if sender else 0
    username = sender.username if sender else None
    full_name = sender.full_name if sender else "Unknown"

    # Capture topic thread ID if present in forum groups
    message_thread_id = message.message_thread_id

    # Use message date from Telegram, converted to UTC timezone
    msg_date = message.date
    if msg_date.tzinfo is None:
        msg_date = msg_date.replace(tzinfo=timezone.utc)

    logger.debug(
        "Ingesting text message",
        chat_id=message.chat.id,
        message_thread_id=message_thread_id,
        sender=username or full_name,
        message_id=message.message_id,
        char_count=len(text),
    )

    await repository.save_message(
        chat_id=message.chat.id,
        message_thread_id=message_thread_id,
        message_id=message.message_id,
        user_id=user_id,
        username=username,
        full_name=full_name,
        text=text,
        date=msg_date,
    )
