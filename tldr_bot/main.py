import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from tldr_bot.settings import Settings
from tldr_bot.logger import setup_logging, get_logger
from tldr_bot.database import Database
from tldr_bot.repository import Repository
from tldr_bot.rate_limiter import RateLimiter
from tldr_bot.summarizer import SummarizerService
from tldr_bot.middlewares.activation import ActivationMiddleware
from tldr_bot.handlers.activation import activation_router
from tldr_bot.handlers.member import member_router
from tldr_bot.handlers.messages import messages_router
from tldr_bot.handlers.tldr import tldr_router

logger = get_logger("tldr_bot.main")


async def main():
    settings = Settings()
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)

    logger.info(
        "Starting tldr-bad-bot service",
        log_level=settings.log_level,
        log_format=settings.log_format,
        admin_username=settings.admin_username,
        rate_limit_seconds=settings.rate_limit_seconds,
        openai_model=settings.openai_model,
    )

    # Initialize MongoDB connection and indexes
    db = Database(settings.mongodb_uri, settings.mongodb_database)
    await db.connect()
    repository = Repository(db.db)

    # Initialize services
    rate_limiter = RateLimiter(repository, cooldown_seconds=settings.rate_limit_seconds)
    summarizer = SummarizerService(
        api_key=settings.openai_api_key, model=settings.openai_model
    )

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    # Inject shared dependencies into handler contexts
    dp["settings"] = settings
    dp["repository"] = repository
    dp["rate_limiter"] = rate_limiter
    dp["summarizer"] = summarizer

    # Register middleware
    dp.message.middleware(ActivationMiddleware(repository))

    # Register routers
    dp.include_router(activation_router)
    dp.include_router(member_router)
    dp.include_router(tldr_router)
    dp.include_router(messages_router)

    logger.info("Bot initialized successfully. Starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down bot service...")
        await bot.session.close()
        await db.close()
        logger.info("Bot service shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
