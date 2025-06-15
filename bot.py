# bot.py
import os
import sys
import asyncio
import threading
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from aiohttp import web, ClientSession
from logging_config import get_logger
from extensions import database
from models import Base
from sqlalchemy import create_engine
import traceback
from handlers import handlers_utils

logger = get_logger('bot')
load_dotenv()

bot_token = os.environ.get('BOT_TOKEN')
if not bot_token:
    logger.error("BOT_TOKEN not set in environment variables")
    exit(1)

logger.info(f"Using bot token starting with: {bot_token[:10]}...")
bot_instance = None
lock = threading.Lock()

def get_bot():
    global bot_instance
    with lock:
        if bot_instance is None:
            try:
                bot_instance = Bot(token=bot_token)
                logger.info("Bot instance created successfully")
            except Exception as e:
                logger.error(f"Error creating bot instance: {e}")
                raise
        return bot_instance

bot = get_bot()
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Initialize database
def init_database():
    try:
        database_url = os.environ.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI")
        if not database_url:
            logger.error("DATABASE_URL or SQLALCHEMY_DATABASE_URI not set in environment variables")
            raise ValueError("Database URL not provided")
        database.initialize(database_url)
        # Create tables if they don't exist
        engine = create_engine(database_url)
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        logger.info("Database initialized successfully for bot")
    except Exception as e:
        logger.critical(f"Failed to initialize database for bot: {str(e)}")
        raise SystemExit("Cannot start bot without database")

# Register available commands
async def set_commands():
    commands = [
        BotCommand(command='/start', description='شروع / بازگشت به منوی اصلی'),
        BotCommand(command='/products', description='محصولات'),
        BotCommand(command='/services', description='خدمات'),
        BotCommand(command='/education', description='محتوای آموزشی'),
        BotCommand(command='/about', description='درباره ما'),
        BotCommand(command='/contact', description='تماس با ما'),
        BotCommand(command='/help', description='راهنما'),
    ]
    await bot.set_my_commands(commands)
    logger.info("Bot commands set successfully")

async def register_handlers():
    """Register all handlers for the bot"""
    # Import main router
    from handlers import main_router

    # Include only the main router in the dispatcher
    dp.include_router(main_router)

    # Verify handlers are registered
    handlers_count = (
        len(main_router.message.handlers) +
        len(main_router.callback_query.handlers)
    )
    logger.info(f"Handlers registered successfully: {handlers_count} handlers in main router")

async def setup_webhook(app, webhook_path, webhook_host):
    async with ClientSession() as session:
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url != webhook_host + webhook_path:
            if webhook_info.url:
                await bot.delete_webhook()
                logger.info(f"Old webhook {webhook_info.url} removed")
            await bot.set_webhook(url=webhook_host + webhook_path)
            logger.info(f"Webhook set to {webhook_host + webhook_path}")
        else:
            logger.info(f"Webhook is already set to {webhook_info.url}")

        async def handle_webhook(request):
            if request.match_info.get('token') == bot_token.split(':')[1]:
                update = await request.json()
                await dp.feed_update(bot, update)
                return web.Response(status=200)
            return web.Response(status=403)

        app.router.add_post(webhook_path, handle_webhook)
    logger.info(f"Webhook handler added for path: {webhook_path}")

async def start_polling():
    async with ClientSession() as session:
        logger.info("Starting bot in polling mode")
        try:
            # Delete any existing webhook before starting polling
            webhook_info = await bot.get_webhook_info()
            if webhook_info.url:
                logger.info(f"Removing existing webhook: {webhook_info.url}")
                await bot.delete_webhook()
                logger.info("No webhook is currently set")
            else:
                logger.info("No webhook is currently set")
        except Exception as e:
            logger.error(f"Error checking webhook: {str(e)}")
            raise

        # Initialize database before registering handlers
        init_database()

        # Set commands
        await set_commands()

        # Register all handlers
        await register_handlers()

        # Log information about the router for debugging
        logger.info("Handlers have been registered and router is included in dispatcher")

        # Start polling
        try:
            await dp.start_polling(bot)
        except Exception as e:
            logger.error(f"Error in polling: {e}")
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Forcefully deleted webhook after error")
            await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        # Run the bot with polling (for development/testing)
        asyncio.run(start_polling())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Error in bot: {e}\n{traceback.format_exc()}")