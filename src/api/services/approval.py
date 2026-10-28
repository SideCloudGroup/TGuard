"""Auto-approval service for verified users."""

import logging
from typing import NamedTuple, Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from src.config.settings import config
from src.database.operations import get_join_request_by_token, approve_join_request
from src.utils.markdown import escape_markdown_v2

logger = logging.getLogger(__name__)

# Known Telegram error fragments mapped to user-facing messages
TELEGRAM_ERRORS = {
    "user_not_found": "用户不存在",
    "chat_not_found": "群组不存在",
    "request_not_found": "加群申请在Telegram中不存在",
    "bot_not_member": "机器人不是群组成员",
    "not_enough_rights": "机器人权限不足",
    "deactivated": "用户已注销",
}

_bot: Optional[Bot] = None


class ApprovalResult(NamedTuple):
    """Result of auto-approval attempt."""
    success: bool
    error: str = None


def get_bot() -> Bot:
    """Get the shared Bot client used for Telegram API calls outside the polling loop."""
    global _bot
    if _bot is None:
        _bot = Bot(token=config.bot.token)
    return _bot


async def close_bot() -> None:
    """Close the shared Bot client session."""
    global _bot
    if _bot is not None:
        await _bot.session.close()
        _bot = None


def _describe_telegram_error(error: Exception) -> Optional[str]:
    """Map a Telegram error to a known user-facing message, if recognised."""
    error_msg = str(error).lower()
    for fragment, message in TELEGRAM_ERRORS.items():
        if fragment in error_msg:
            return message
    return None


async def dismiss_join_request(chat_id: int, user_id: int) -> bool:
    """Decline (dismiss) a chat join request via Telegram API. Returns True on success."""
    try:
        await get_bot().decline_chat_join_request(chat_id=chat_id, user_id=user_id)
        logger.info(f"Dismissed join request: user {user_id} for chat {chat_id}")
        return True
    except TelegramBadRequest as e:
        reason = _describe_telegram_error(e) or "Telegram API错误"
        logger.warning(f"Skip dismiss for user {user_id} (chat {chat_id}): {reason} ({e})")
        return False


async def _send_welcome_message(bot: Bot, chat_id: int, user_id: int) -> None:
    """Notify the user that they have joined; failures are non-fatal."""
    try:
        chat_info = await bot.get_chat(chat_id)
        escaped_title = escape_markdown_v2(chat_info.title or "群组")
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 *验证成功\\!*\n\n您已成功加入 *{escaped_title}*，欢迎\\!",
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logger.warning(f"Could not send welcome message to {user_id}: {e}")


async def auto_approve_user(verification_token: str) -> ApprovalResult:
    """Automatically approve user after successful verification."""
    try:
        join_request = await get_join_request_by_token(verification_token)
        if not join_request:
            logger.error(f"Join request not found for token: {verification_token[:8]}...")
            return ApprovalResult(False, "加群申请不存在")

        if join_request.status != "pending":
            logger.warning(f"Join request already processed: {join_request.status}")
            return ApprovalResult(False, f"申请已处理：{join_request.status}")

        if join_request.chat_id == 0:
            logger.warning("Cannot approve request with chat_id=0 (API request without chat)")
            return ApprovalResult(False, "无效的群组ID")

        bot = get_bot()
        try:
            await bot.approve_chat_join_request(
                chat_id=join_request.chat_id,
                user_id=join_request.user_id
            )
        except TelegramBadRequest as e:
            reason = _describe_telegram_error(e)
            logger.warning(
                f"Telegram rejected approval of user {join_request.user_id} "
                f"for chat {join_request.chat_id}: {e}"
            )
            return ApprovalResult(False, reason or f"Telegram API错误：{e}")

        if not await approve_join_request(verification_token):
            logger.error(f"Failed to update database for token: {verification_token[:8]}...")
            return ApprovalResult(False, "数据库更新失败")

        logger.info(
            f"Successfully auto-approved user {join_request.user_id} "
            f"for chat {join_request.chat_id}"
        )

        if join_request.request_type == "telegram":
            await _send_welcome_message(bot, join_request.chat_id, join_request.user_id)

        return ApprovalResult(True)

    except Exception as e:
        logger.error(f"Unexpected error during auto-approval: {e}")
        return ApprovalResult(False, f"自动审批失败：{e}")
