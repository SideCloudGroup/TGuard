"""Bot handlers setup."""

from aiogram import Dispatcher
from .chat_member import setup_chat_member_handlers
from .admin import setup_admin_handlers


def setup_handlers(dp: Dispatcher):
    """Setup all bot handlers."""
    setup_chat_member_handlers(dp)
    setup_admin_handlers(dp)
