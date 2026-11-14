from datetime import datetime, timezone
from typing import Optional, Tuple
from tldr_bot.repository import Repository
from tldr_bot.logger import get_logger

logger = get_logger("tldr_bot.rate_limiter")


class RateLimiter:
    def __init__(self, repository: Repository, cooldown_seconds: int = 300):
        self.repository = repository
        self.cooldown_seconds = cooldown_seconds

    async def check_rate_limit(
        self,
        chat_id: int,
        message_thread_id: Optional[int] = None,
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if the chat and topic thread is rate-limited.
        Returns:
            (is_limited, cached_summary_text_or_none, remaining_seconds_or_none)
        """
        last_time = await self.repository.get_last_tldr_time(
            chat_id, message_thread_id=message_thread_id
        )
        if not last_time:
            logger.debug(
                "Thread has no previous TLDR record; not rate-limited",
                chat_id=chat_id,
                message_thread_id=message_thread_id,
            )
            return False, None, None

        if last_time.tzinfo is None:
            last_time = last_time.replace(tzinfo=timezone.utc)

        elapsed = (datetime.now(timezone.utc) - last_time).total_seconds()
        logger.debug(
            "Rate limit check",
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            elapsed_seconds=round(elapsed, 1),
            cooldown_seconds=self.cooldown_seconds,
        )

        if elapsed < self.cooldown_seconds:
            remaining = int(self.cooldown_seconds - elapsed)
            last_summary_data = await self.repository.get_last_summary(
                chat_id, message_thread_id=message_thread_id
            )
            cached_text = (
                last_summary_data.get("summary_text") if last_summary_data else None
            )
            return True, cached_text, remaining

        return False, None, None
