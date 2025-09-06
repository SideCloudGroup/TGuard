"""Main entry point for Telegram bot."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.handlers import setup_handlers
from src.config.settings import config
from src.database.connection import init_database


async def main():
    """Main bot function."""
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting TGuard bot...")

    # Initialize database
    await init_database()

    # Create bot and dispatcher
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    # Setup handlers
    setup_handlers(dp)

    # Set bot commands menu
    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="start", description="启动机器人"),
        BotCommand(command="help", description="显示帮助信息"),
    ])

    try:
        logger.info("Bot started successfully")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
