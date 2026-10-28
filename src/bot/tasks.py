"""Background tasks for the bot (e.g. periodic cleanup)."""

import asyncio
import logging

from src.api.services.approval import dismiss_join_request
from src.config.settings import config
from src.database.operations import cleanup_expired_sessions, purge_stale_records

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL_SECONDS = 60
PURGE_INTERVAL_SECONDS = 24 * 60 * 60


async def cleanup_and_dismiss_expired_requests() -> None:
    """Run cleanup of expired sessions and dismiss corresponding Telegram join requests."""
    try:
        to_dismiss = await cleanup_expired_sessions()
        for chat_id, user_id in to_dismiss:
            try:
                await dismiss_join_request(chat_id=chat_id, user_id=user_id)
            except Exception as e:
                logger.warning(
                    "Skip dismiss for user %s (chat %s): %s",
                    user_id, chat_id, e,
                    exc_info=False
                )
    except Exception as e:
        logger.exception("Error in cleanup_and_dismiss_expired_requests: %s", e)


async def purge_old_records() -> None:
    """Delete sessions and join requests past the retention window."""
    try:
        await purge_stale_records(config.cleanup.retention_days)
    except Exception as e:
        logger.exception("Error in purge_old_records: %s", e)


async def run_cleanup_loop(interval_seconds: int = CLEANUP_INTERVAL_SECONDS) -> None:
    """Run expiry cleanup frequently and stale-data purge once per day."""
    retention_days = config.cleanup.retention_days
    logger.info(
        "Cleanup loop started (interval=%ds, retention=%dd)",
        interval_seconds,
        retention_days,
    )
    elapsed_since_purge = PURGE_INTERVAL_SECONDS
    while True:
        try:
            await cleanup_and_dismiss_expired_requests()
            if elapsed_since_purge >= PURGE_INTERVAL_SECONDS:
                await purge_old_records()
                elapsed_since_purge = 0
        except Exception as e:
            logger.exception("Cleanup loop iteration failed: %s", e)
        await asyncio.sleep(interval_seconds)
        elapsed_since_purge += interval_seconds
