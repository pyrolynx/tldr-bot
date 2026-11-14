import secrets
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from tldr_bot.repository import Repository
from tldr_bot.settings import Settings
from tldr_bot.logger import get_logger

logger = get_logger("tldr_bot.handlers.activation")
activation_router = Router()


@activation_router.message(Command("generate_token"))
async def handle_generate_token(
    message: Message, repository: Repository, settings: Settings
):
    chat = message.chat
    sender = message.from_user
    username = (sender.username or "").strip().lstrip("@").lower() if sender else ""
    expected_admin = settings.admin_username.strip().lstrip("@").lower()

    if chat.type != "private":
        logger.warning(
            "Rejected /generate_token in non-private chat",
            chat_id=chat.id,
            username=username,
            chat_type=chat.type,
        )
        await message.reply(
            "⚠️ Token generation is only permitted in direct messages with the bot."
        )
        return

    if not username or username != expected_admin:
        logger.warning(
            "Unauthorized /generate_token attempt",
            username=username,
            expected_admin=expected_admin,
            user_id=sender.id if sender else None,
        )
        await message.reply("⛔ You are not authorized to generate activation tokens.")
        return

    # Generate a cryptographically secure single-use token
    token = secrets.token_urlsafe(16)
    await repository.add_token(token)
    logger.info(
        "Admin generated new activation token", admin_username=username, token=token
    )

    await message.reply(
        "🔑 **New activation token generated:**\n\n"
        f"`{token}`\n\n"
        "This token is single-use. Provide it to the group chat admin to run:\n"
        f"`/activate {token}`"
    )


@activation_router.message(Command("activate"))
async def handle_activate(message: Message, repository: Repository):
    chat = message.chat
    if chat.type not in ("group", "supergroup"):
        await message.reply(
            "The `/activate` command can only be used in group or supergroup chats."
        )
        return

    # Check if already activated
    if await repository.is_chat_activated(chat.id):
        logger.info("Chat is already activated; ignoring /activate", chat_id=chat.id)
        await message.reply("This chat is already activated!")
        return

    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.reply(
            "Please provide an activation token.\nUsage: `/activate <token>`"
        )
        return

    token = parts[1].strip()
    logger.info("Chat attempting activation", chat_id=chat.id, token=token)
    consumed = await repository.consume_token(token, chat_id=chat.id)
    if not consumed:
        logger.warning(
            "Activation failed with invalid/used token", chat_id=chat.id, token=token
        )
        await message.reply(
            "❌ Invalid or already used activation token. Please request a new token from the bot admin."
        )
        return

    await repository.activate_chat(chat.id, chat.title, token)
    logger.info(
        "Chat successfully activated", chat_id=chat.id, token=token, title=chat.title
    )
    await message.reply(
        "🎉 **Chat activated successfully!**\n"
        "I will now record messages and provide summaries on demand with `/tldr <N>`."
    )
