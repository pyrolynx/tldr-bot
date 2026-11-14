from aiogram import Router, F
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMemberUpdated, ChatMemberAdministrator
from tldr_bot.logger import get_logger

logger = get_logger("tldr_bot.handlers.member")
member_router = Router()


@member_router.my_chat_member(F.chat.type.in_({"group", "supergroup"}))
async def handle_bot_membership_update(event: ChatMemberUpdated):
    # Only act if status transitioned to a member or admin (e.g. added or rights updated)
    old_status = event.old_chat_member.status
    new_member = event.new_chat_member
    new_status = new_member.status
    chat_title = event.chat.title

    logger.info(
        "Bot membership updated in chat",
        chat_id=event.chat.id,
        old_status=old_status,
        new_status=new_status,
        chat_title=chat_title,
    )

    if new_status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR):
        # Check if the bot was promoted or just added
        is_admin = (
            isinstance(new_member, ChatMemberAdministrator)
            or new_status == "administrator"
        )

        if not is_admin:
            logger.warning(
                "Bot joined chat as regular member without admin rights",
                chat_id=event.chat.id,
            )
            await event.bot.send_message(
                chat_id=event.chat.id,
                text=(
                    "👋 **Hello! Thanks for adding me.**\n\n"
                    "⚠️ **Permission Notice**:\n"
                    "To monitor chat messages and generate summaries with `/tldr`, I need permission to read messages.\n"
                    "Please either:\n"
                    "1. Promote me to **Administrator** in this group, OR\n"
                    "2. Disable **Group Privacy** in @BotFather (`/setprivacy` -> Select this bot -> Disable).\n\n"
                    "Remember to activate this chat using `/activate <token>`."
                ),
            )
        elif old_status not in ("administrator",):
            logger.info("Bot promoted to administrator", chat_id=event.chat.id)
            await event.bot.send_message(
                chat_id=event.chat.id,
                text=(
                    "👋 **Hello! Thanks for adding me with Administrator rights.**\n\n"
                    "I have full message reading access. Remember to activate this chat using:\n"
                    "`/activate <token>`"
                ),
            )
