# bot.py
import os
import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from aiohttp import web, ClientSession
from logging_config import get_logger



# Get bot logger
logger = get_logger('bot')

# Load environment variables
load_dotenv()

# Initialize bot and dispatcher
bot_token = os.environ.get('BOT_TOKEN')
if not bot_token:
    logger.error("BOT_TOKEN not set in environment variables")
    exit(1)

logger.info(f"Using bot token starting with: {bot_token[:10]}...")

# Create bot instance
try:
    bot = Bot(token=bot_token)
    logger.info("Bot instance created successfully")
except Exception as e:
    logger.error(f"Error creating bot instance: {e}")
    raise
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

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
    # Import all necessary handlers to ensure they are initialized
    from handlers import router, cmd_start, cmd_help, cmd_products, cmd_services
    from handlers import cmd_contact, cmd_about, callback_products, callback_services
    from handlers import callback_contact, callback_about, callback_educational
    
    # Include the router from handlers module
    dp.include_router(router)
    
    # Verify handlers are registered by checking some key ones
    handlers_count = len(router.message.handlers) + len(router.callback_query.handlers)
    logger.info(f"Handlers registered successfully: {handlers_count} handlers in router")


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
            if request.match_info.get('token') == BOT_TOKEN.split(':')[1]:
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
        # Try to force delete webhook if we're still having issues
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Forcefully deleted webhook after error")
        # Try polling again
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        # Run the bot with polling (for development/testing)
        asyncio.run(start_polling())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Error in bot: {e}")