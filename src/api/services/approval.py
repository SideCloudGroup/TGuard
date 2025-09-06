"""Auto-approval service for verified users."""

import logging
from typing import NamedTuple
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from src.config.settings import config
from src.database.operations import get_join_request_by_token, approve_join_request

logger = logging.getLogger(__name__)


class ApprovalResult(NamedTuple):
    """Result of auto-approval attempt."""
    success: bool
    error: str = None


async def auto_approve_user(verification_token: str) -> ApprovalResult:
    """Automatically approve user after successful verification."""
    try:
        # Get join request
        join_request = await get_join_request_by_token(verification_token)
        if not join_request:
            logger.error(f"Join request not found for token: {verification_token}")
            return ApprovalResult(False, "加群申请不存在")
        
        # Check if already processed
        if join_request.status != "pending":
            logger.warning(f"Join request already processed: {join_request.status}")
            return ApprovalResult(False, f"申请已处理：{join_request.status}")
        
        # Create bot instance
        bot = Bot(token=config.bot.token)
        
        try:
            # Approve the join request via Telegram API
            await bot.approve_chat_join_request(
                chat_id=join_request.chat_id,
                user_id=join_request.user_id
            )
            
            # Update database
            success = await approve_join_request(verification_token)
            if not success:
                logger.error(f"Failed to update database for token: {verification_token}")
                return ApprovalResult(False, "数据库更新失败")
            
            logger.info(
                f"Successfully auto-approved user {join_request.user_id} "
                f"for chat {join_request.chat_id}"
            )
            
            # Send welcome message to user (optional)
            try:
                # Get chat info to include group name
                chat_info = await bot.get_chat(join_request.chat_id)
                chat_title = chat_info.title if chat_info.title else "群组"
                
                # Escape group name for MarkdownV2
                from src.utils.markdown import escape_markdown_v2
                escaped_title = escape_markdown_v2(chat_title)
                
                await bot.send_message(
                    chat_id=join_request.user_id,
                    text=f"🎉 *验证成功\\!*\n\n您已成功加入 *{escaped_title}*，欢迎\\!",
                    parse_mode="MarkdownV2"
                )
            except TelegramBadRequest as e:
                # Don't fail the approval if we can't send welcome message
                logger.warning(f"Could not send welcome message to {join_request.user_id}: {e}")
            
            return ApprovalResult(True)
            
        except TelegramBadRequest as e:
            error_msg = str(e).lower()
            
            if "user_not_found" in error_msg:
                logger.warning(f"User {join_request.user_id} not found")
                return ApprovalResult(False, "用户不存在")
            elif "chat_not_found" in error_msg:
                logger.warning(f"Chat {join_request.chat_id} not found")
                return ApprovalResult(False, "群组不存在")
            elif "request_not_found" in error_msg:
                logger.warning(f"Join request not found in Telegram")
                return ApprovalResult(False, "加群申请在Telegram中不存在")
            elif "bot_not_member" in error_msg:
                logger.error(f"Bot is not a member of chat {join_request.chat_id}")
                return ApprovalResult(False, "机器人不是群组成员")
            elif "not_enough_rights" in error_msg:
                logger.error(f"Bot lacks permissions in chat {join_request.chat_id}")
                return ApprovalResult(False, "机器人权限不足")
            else:
                logger.error(f"Telegram API error: {e}")
                return ApprovalResult(False, f"Telegram API错误：{e}")
                
        finally:
            await bot.session.close()
            
    except Exception as e:
        logger.error(f"Unexpected error during auto-approval: {e}")
        return ApprovalResult(False, f"自动审批失败：{e}")
