"""
ماژول اصلی بات تلگرام
این ماژول رابط اتصال به API تلگرام و تنظیمات بات را فراهم می‌کند.
"""

import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from aiohttp import web

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def set_commands():
    """Set bot commands in the menu"""
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

async def register_handlers(dp):
    """Register all handlers for the bot"""
    from src.bot.handlers import register_all_handlers
    register_all_handlers(dp)

async def setup_webhook(app, webhook_path, webhook_host):
    """Set up webhook handling for the bot with aiohttp app"""
    # Get webhook info
    webhook_info = await bot.get_webhook_info()
    
    # If URL is different from the one we want, set new URL
    if webhook_info.url != webhook_host + webhook_path:
        # If we already have a webhook, remove it
        if webhook_info.url:
            await bot.delete_webhook()
            logger.info(f"Old webhook {webhook_info.url} removed")
        
        # Set webhook with the proper URL
        await bot.set_webhook(url=webhook_host + webhook_path)
        logger.info(f"Webhook set to {webhook_host + webhook_path}")
    else:
        logger.info(f"Webhook is already set to {webhook_info.url}")
    
    # Function to process updates from Telegram
    async def handle_webhook(request):
        """Process webhook updates from Telegram"""
        if request.match_info.get('token') == BOT_TOKEN.split(':')[1]:
            update = await request.json()
            await dp.feed_update(bot, update)
            return web.Response()
        return web.Response(status=403)
    
    # Map the handler to our app at the proper route
    app.router.add_post(webhook_path, handle_webhook)

async def start_polling():
    """Start the bot in polling mode (for testing)"""
    # Delete webhook if exists
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url:
        logger.info(f"Removing existing webhook: {webhook_info.url}")
        await bot.delete_webhook()
        logger.info("No webhook is currently set")
    else:
        logger.info("No webhook is currently set")
    
    # Set commands
    await set_commands()
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_polling())