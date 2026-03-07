"""Background tasks for the bot (e.g. periodic cleanup)."""

import asyncio
import logging

from src.api.services.approval import dismiss_join_request
from src.database.operations import cleanup_expired_sessions

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL_SECONDS = 60


async def cleanup_and_dismiss_expired_requests() -> None:
    """Run cleanup of expired sessions and dismiss corresponding Telegram join requests."""
    try:
        to_dismiss = await cleanup_expired_sessions()
        for chat_id, user_id in to_dismiss:
            await dismiss_join_request(chat_id=chat_id, user_id=user_id)
    except Exception as e:
        logger.exception("Error in cleanup_and_dismiss_expired_requests: %s", e)


async def run_cleanup_loop(interval_seconds: int = CLEANUP_INTERVAL_SECONDS) -> None:
    """Run the cleanup+dismiss task periodically."""
    logger.info("Cleanup loop started (interval=%ds)", interval_seconds)
    while True:
        try:
            await cleanup_and_dismiss_expired_requests()
        except Exception as e:
            logger.exception("Cleanup loop iteration failed: %s", e)
        await asyncio.sleep(interval_seconds)
