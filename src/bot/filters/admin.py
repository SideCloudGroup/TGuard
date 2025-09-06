"""Admin permission filters."""

from aiogram.filters import BaseFilter
from aiogram.types import Message

from src.config.settings import config


class AdminFilter(BaseFilter):
    """Filter to check if user is admin."""
    
    async def __call__(self, message: Message) -> bool:
        """Check if message sender is admin."""
        if not message.from_user:
            return False
        
        return message.from_user.id in config.bot.admin_ids
