"""Chat member handlers for join requests."""

import html
import logging
from datetime import timedelta

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton

from src.config.settings import config
from src.database.operations import create_join_request, create_verification_session
from src.utils.crypto import generate_verification_token
from src.utils.markdown import escape_markdown_v2, format_user_mention
from src.utils.time import utcnow

logger = logging.getLogger(__name__)
router = Router()


@router.chat_join_request()
async def handle_join_request(join_request: ChatJoinRequest):
    """Handle new chat join requests."""
    try:
        user = join_request.from_user
        chat = join_request.chat

        logger.info(f"New join request from user {user.id} ({user.username}) to chat {chat.id}")

        # Generate verification token
        verification_token = generate_verification_token()

        # Create join request record (marked as telegram type)
        db_join_request = await create_join_request(
            user_id=user.id,
            chat_id=chat.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            verification_token=verification_token,
            request_type="telegram"
        )

        if not db_join_request:
            logger.error(f"Failed to create join request for user {user.id}")
            return

        # Create verification session
        expires_at = utcnow() + timedelta(seconds=config.bot.verification_timeout)
        verification_session = await create_verification_session(
            token=verification_token,
            user_id=user.id,
            chat_id=chat.id,
            expires_at=expires_at
        )

        if not verification_session:
            logger.error(f"Failed to create verification session for user {user.id}")
            return

        # Create Mini Web App URL
        web_app_url = f"{config.api.base_url}/verify?token={verification_token}"

        # Create inline keyboard with verification button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=config.bot.verification_button_text,
                web_app={"url": web_app_url}
            )]
        ])

        # Send verification message to user
        try:
            # Create personalized welcome message with group name
            chat_title = html.escape(chat.title or "群组")
            welcome_text = f"欢迎加入群组{chat_title}！请点击下方链接完成人机验证"

            await join_request.bot.send_message(
                chat_id=user.id,
                text=welcome_text,
                reply_markup=keyboard
            )
            logger.info(f"Verification message sent to user {user.id}")

        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                logger.warning(f"Cannot send message to user {user.id}: user hasn't started bot")

                # Try to send message to the group mentioning the user
                try:
                    bot_info = await join_request.bot.get_me()
                    mention = format_user_mention(user.username, user.first_name)
                    bot_mention = escape_markdown_v2(bot_info.username)
                    # web_app buttons are only allowed in private chats, so no keyboard here
                    await join_request.bot.send_message(
                        chat_id=chat.id,
                        text=f"{mention}, 请先私聊 @{bot_mention} 机器人，然后重新申请加群\\.",
                        parse_mode="MarkdownV2"
                    )
                except Exception as group_msg_error:
                    logger.error(f"Failed to send group message: {group_msg_error}")
            else:
                logger.error(f"Failed to send verification message: {e}")

    except Exception as e:
        logger.error(f"Error handling join request: {e}")


def setup_chat_member_handlers(dp):
    """Setup chat member handlers."""
    dp.include_router(router)
