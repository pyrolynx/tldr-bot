from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from tldr_bot.repository import Repository
from tldr_bot.logger import get_logger

logger = get_logger("tldr_bot.middleware.activation")


class ActivationMiddleware(BaseMiddleware):
    def __init__(self, repository: Repository):
        super().__init__()
        self.repository = repository

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["repository"] = self.repository

        if not isinstance(event, Message):
            return await handler(event, data)

        chat = event.chat
        # Middleware checks apply to group and supergroup chats
        if chat.type not in ("group", "supergroup"):
            return await handler(event, data)

        # Allow group migration service messages to pass through to handlers
        if event.migrate_to_chat_id or event.migrate_from_chat_id:
            return await handler(event, data)

        text = event.text or event.caption or ""
        is_activate_command = text.strip().startswith("/activate")

        is_activated = await self.repository.is_chat_activated(chat.id)

        chat_title = chat.title
        from_user = event.from_user
        user_id = from_user.id if from_user else None

        if not is_activated:
            if is_activate_command:
                logger.info(
                    "Routing /activate command for unactivated chat",
                    chat_id=chat.id,
                    title=chat_title,
                )
                return await handler(event, data)

            if text.startswith("/"):
                cmd = text.split()[0]
                logger.warning(
                    "Blocked command in unactivated chat",
                    command=cmd,
                    chat_id=chat.id,
                    user_id=user_id,
                )
                await event.reply(
                    "⚠️ **This chat is not activated!**\n\n"
                    "Before using bot commands, an admin must activate this chat using:\n"
                    "`/activate <token>`"
                )
                return None

            logger.debug(
                "Discarding regular message in unactivated chat", chat_id=chat.id
            )
            return None

        return await handler(event, data)
