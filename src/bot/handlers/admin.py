"""Admin command handlers."""

import logging
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.filters import AdminFilter
from src.config.settings import config
from src.database.operations import get_global_stats

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
        "• 支持多种验证码服务\\(hCaptcha、Cap\\.js、Turnstile\\)\n\n"
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


@router.message(Command("stats"), AdminFilter())
async def cmd_stats(message: Message):
    """Handle /stats command (admin only)."""
    try:
        stats = await get_global_stats()

        if not stats:
            await message.answer(
                "❌ *无法获取统计数据*\n\n"
                "请检查数据库连接状态",
                parse_mode="MarkdownV2"
            )
            return

        # Format statistics
        total_requests = stats.get('total_requests', 0)
        approved = stats.get('approved', 0)
        rejected = stats.get('rejected', 0)
        pending = stats.get('pending', 0)
        expired = stats.get('expired', 0)
        approval_rate = stats.get('approval_rate', 0)

        today_total = stats.get('today_total', 0)
        today_approved = stats.get('today_approved', 0)
        today_approval_rate = stats.get('today_approval_rate', 0)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        stats_text = (
            f"📊 *TGuard 统计信息*\n"
            f"⏰ 更新时间：`{current_time}`\n\n"
            f"📈 *总体统计*\n"
            f"• 总验证请求：`{total_requests}`\n"
            f"• 已通过：`{approved}`\n"
            f"• 已拒绝：`{rejected}`\n"
            f"• 待处理：`{pending}`\n"
            f"• 已过期：`{expired}`\n"
            f"• 通过率：`{approval_rate:.1f}%`\n\n"
            f"📅 *今日统计*\n"
            f"• 今日请求：`{today_total}`\n"
            f"• 今日通过：`{today_approved}`\n"
            f"• 今日通过率：`{today_approval_rate:.1f}%`"
        )

        await message.answer(
            stats_text,
            parse_mode="MarkdownV2"
        )

    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await message.answer(
            "❌ *获取统计数据时发生错误*\n\n"
            "请稍后重试",
            parse_mode="MarkdownV2"
        )


@router.message(Command("api"), AdminFilter())
async def cmd_api(message: Message):
    """Handle /api command (admin only, not in menu)."""
    try:
        api_config = config.api

        if api_config.enable:
            # API is enabled, show URL and KEY
            api_text = (
                "🔌 *API 状态：已启用*\n\n"
                f"🌐 *服务器地址：*\n"
                f"`{api_config.base_url}`\n\n"
                f"🔑 *API Key：*\n"
                f"`{api_config.api_key}`\n\n"
                "⚠️ *注意：请妥善保管您的 API Key*"
            )
        else:
            # API is disabled
            api_text = (
                "🔌 *API 状态：未启用*\n\n"
                "请在配置文件中设置 `api.enable = true` 来启用 API 功能"
            )

        await message.answer(
            api_text,
            parse_mode="MarkdownV2"
        )

    except Exception as e:
        logger.error(f"Error in api command: {e}")
        await message.answer(
            "❌ *获取 API 信息时发生错误*\n\n"
            "请稍后重试",
            parse_mode="MarkdownV2"
        )


def setup_admin_handlers(dp):
    """Setup admin handlers."""
    dp.include_router(router)
