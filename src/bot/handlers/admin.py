"""Admin command handlers."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    await message.answer(
        "🤖 *TGuard 群组验证机器人*\n\n"
        "🛡️ *自动验证新成员身份，防止机器人和恶意用户进入群组*\n\n"
        "*功能：*\n"
        "• 新成员申请加群时自动发送验证链接\n"
        "• 通过人机验证后自动批准加群\n"
        "• 支持多种验证码服务\\(hCaptcha、Cap\\.js\\)\n\n"
        "使用 `/help` 查看更多信息",
        parse_mode="MarkdownV2"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    await message.answer(
        "🤖 *TGuard 群组验证机器人*\n\n"
        "🛡️ *自动验证新成员身份，防止机器人和恶意用户进入群组*\n\n"
        "*使用说明：*\n"
        "如何使用请见 [README](https://github.com/SideCloudGroup/TGuard/blob/main/README.md)\n\n"
        "*技术支持：*\n"
        "由 [TGuard](https://github.com/SideCloudGroup/TGuard) 提供技术支持",
        parse_mode="MarkdownV2",
        disable_web_page_preview=True
    )


def setup_admin_handlers(dp):
    """Setup admin handlers."""
    dp.include_router(router)
