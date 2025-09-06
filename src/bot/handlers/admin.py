"""Admin command handlers."""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, ChatMemberUpdatedFilter
from aiogram.enums import ChatMemberStatus

from src.database.operations import get_pending_requests, get_verification_stats
from src.utils.markdown import escape_markdown_v2, format_user_mention, format_code_inline

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    await message.answer(
        "🤖 *TGuard 群组验证机器人*\n\n"
        "我可以帮助管理员自动验证新成员\\.\n\n"
        "*功能：*\n"
        "• 新成员申请加群时自动发送验证链接\n"
        "• 通过人机验证后自动批准加群\n"
        "• 防止机器人和恶意用户\n\n"
        "*管理员命令：*\n"
        "/status \\- 查看验证统计\n"
        "/pending \\- 查看待处理请求\n"
        "/help \\- 显示帮助信息",
        parse_mode="MarkdownV2"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    await message.answer(
        "🆘 *TGuard 帮助*\n\n"
        "*如何使用：*\n"
        "1\\. 将机器人添加到群组\n"
        "2\\. 给予机器人管理员权限\n"
        "3\\. 开启群组的 '批准新成员' 功能\n"
        "4\\. 新成员申请时会自动发送验证链接\n\n"
        "*管理员命令：*\n"
        "• `/status` \\- 查看验证统计信息\n"
        "• `/pending` \\- 查看待处理的申请\n"
        "• `/help` \\- 显示此帮助信息\n\n"
        "*设置要求：*\n"
        "• 机器人需要管理员权限\n"
        "• 群组需要开启 '批准新成员'\n"
        "• 新成员需要先私聊机器人",
        parse_mode="MarkdownV2"
    )


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Handle /status command - show verification statistics."""
    try:
        # Check if user is admin
        chat_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            await message.answer("❌ 只有管理员可以使用此命令\\.", parse_mode="MarkdownV2")
            return
        
        stats = await get_verification_stats(message.chat.id)
        
        if not stats:
            await message.answer("📊 暂无验证统计数据\\.", parse_mode="MarkdownV2")
            return
        
        await message.answer(
            f"📊 *验证统计*\n\n"
            f"📝 总申请数：`{stats.get('total_requests', 0)}`\n"
            f"✅ 已批准：`{stats.get('approved', 0)}`\n"
            f"❌ 已拒绝：`{stats.get('rejected', 0)}`\n"
            f"⏳ 待处理：`{stats.get('pending', 0)}`\n"
            f"⏰ 已过期：`{stats.get('expired', 0)}`\n\n"
            f"📈 通过率：`{stats.get('approval_rate', 0):.1f}%`",
            parse_mode="MarkdownV2"
        )
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        await message.answer("❌ 获取统计信息时出错\\.", parse_mode="MarkdownV2")


@router.message(Command("pending"))
async def cmd_pending(message: Message):
    """Handle /pending command - show pending requests."""
    try:
        # Check if user is admin
        chat_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            await message.answer("❌ 只有管理员可以使用此命令\\.", parse_mode="MarkdownV2")
            return
        
        pending_requests = await get_pending_requests(message.chat.id)
        
        if not pending_requests:
            await message.answer("✅ 当前没有待处理的申请\\.", parse_mode="MarkdownV2")
            return
        
        response = "⏳ *待处理申请*\n\n"
        
        for req in pending_requests[:10]:  # Show max 10 requests
            name = f"{req.first_name} {req.last_name or ''}".strip()
            user_mention = format_user_mention(req.username, req.first_name)
            
            response += (
                f"👤 *{escape_markdown_v2(name)}* \\({user_mention}\\)\n"
                f"🆔 ID: {format_code_inline(str(req.user_id))}\n"
                f"🕐 申请时间: {format_code_inline(req.request_time.strftime('%Y-%m-%d %H:%M'))}\n"
                f"🔗 验证状态: {'已完成' if req.verification_completed else '未完成'}\n\n"
            )
        
        if len(pending_requests) > 10:
            response += f"{escape_markdown_v2('...')} 还有 {format_code_inline(str(len(pending_requests) - 10))} 个申请"
        
        await message.answer(response, parse_mode="MarkdownV2")
        
    except Exception as e:
        logger.error(f"Error getting pending requests: {e}")
        await message.answer("❌ 获取待处理申请时出错\\.", parse_mode="MarkdownV2")


def setup_admin_handlers(dp):
    """Setup admin handlers."""
    dp.include_router(router)
