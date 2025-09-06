"""Admin command handlers."""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, ChatMemberUpdatedFilter
from aiogram.enums import ChatMemberStatus

from src.database.operations import get_pending_requests, get_verification_stats

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    await message.answer(
        "🤖 <b>TGuard 群组验证机器人</b>\n\n"
        "我可以帮助管理员自动验证新成员。\n\n"
        "<b>功能：</b>\n"
        "• 新成员申请加群时自动发送验证链接\n"
        "• 通过人机验证后自动批准加群\n"
        "• 防止机器人和恶意用户\n\n"
        "<b>管理员命令：</b>\n"
        "/status - 查看验证统计\n"
        "/pending - 查看待处理请求\n"
        "/help - 显示帮助信息"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    await message.answer(
        "🆘 <b>TGuard 帮助</b>\n\n"
        "<b>如何使用：</b>\n"
        "1. 将机器人添加到群组\n"
        "2. 给予机器人管理员权限\n"
        "3. 开启群组的 '批准新成员' 功能\n"
        "4. 新成员申请时会自动发送验证链接\n\n"
        "<b>管理员命令：</b>\n"
        "• <code>/status</code> - 查看验证统计信息\n"
        "• <code>/pending</code> - 查看待处理的申请\n"
        "• <code>/help</code> - 显示此帮助信息\n\n"
        "<b>设置要求：</b>\n"
        "• 机器人需要管理员权限\n"
        "• 群组需要开启 '批准新成员'\n"
        "• 新成员需要先私聊机器人"
    )


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Handle /status command - show verification statistics."""
    try:
        # Check if user is admin
        chat_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            await message.answer("❌ 只有管理员可以使用此命令。")
            return
        
        stats = await get_verification_stats(message.chat.id)
        
        if not stats:
            await message.answer("📊 暂无验证统计数据。")
            return
        
        await message.answer(
            f"📊 <b>验证统计</b>\n\n"
            f"📝 总申请数：{stats.get('total_requests', 0)}\n"
            f"✅ 已批准：{stats.get('approved', 0)}\n"
            f"❌ 已拒绝：{stats.get('rejected', 0)}\n"
            f"⏳ 待处理：{stats.get('pending', 0)}\n"
            f"⏰ 已过期：{stats.get('expired', 0)}\n\n"
            f"📈 通过率：{stats.get('approval_rate', 0):.1f}%"
        )
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        await message.answer("❌ 获取统计信息时出错。")


@router.message(Command("pending"))
async def cmd_pending(message: Message):
    """Handle /pending command - show pending requests."""
    try:
        # Check if user is admin
        chat_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            await message.answer("❌ 只有管理员可以使用此命令。")
            return
        
        pending_requests = await get_pending_requests(message.chat.id)
        
        if not pending_requests:
            await message.answer("✅ 当前没有待处理的申请。")
            return
        
        response = "⏳ <b>待处理申请</b>\n\n"
        
        for req in pending_requests[:10]:  # Show max 10 requests
            username = req.username or "无用户名"
            name = f"{req.first_name} {req.last_name or ''}".strip()
            time_ago = (req.request_time.replace(tzinfo=None) - req.request_time.replace(tzinfo=None)).total_seconds()
            
            response += (
                f"👤 <b>{name}</b> (@{username})\n"
                f"🆔 ID: <code>{req.user_id}</code>\n"
                f"🕐 申请时间: {req.request_time.strftime('%Y-%m-%d %H:%M')}\n"
                f"🔗 验证状态: {'已完成' if req.verification_completed else '未完成'}\n\n"
            )
        
        if len(pending_requests) > 10:
            response += f"... 还有 {len(pending_requests) - 10} 个申请"
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error getting pending requests: {e}")
        await message.answer("❌ 获取待处理申请时出错。")


def setup_admin_handlers(dp):
    """Setup admin handlers."""
    dp.include_router(router)
