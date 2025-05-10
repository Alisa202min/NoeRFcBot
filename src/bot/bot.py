import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from aiohttp import web

# Import handlers
import handlers

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
bot_token = os.environ.get('BOT_TOKEN')
if not bot_token:
    logger.error("BOT_TOKEN not set in environment variables")
    exit(1)

# Create bot instance
bot = Bot(token=bot_token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Register available commands
async def set_commands():
    commands = [
        BotCommand(command="/start", description="شروع مجدد"),
        BotCommand(command="/products", description="مشاهده محصولات"),
        BotCommand(command="/services", description="مشاهده خدمات"),
        BotCommand(command="/contact", description="تماس با ما"),
        BotCommand(command="/about", description="درباره ما"),
        BotCommand(command="/help", description="راهنما")
    ]
    await bot.set_my_commands(commands)

async def register_handlers():
    """Register all handlers for the bot"""
    # Include the router from handlers module
    dp.include_router(handlers.router)

async def setup_webhook(app, webhook_path, webhook_host):
    """Set up webhook handling for the bot with aiohttp app"""
    webhook_url = f"{webhook_host}{webhook_path}"
    logger.info(f"Setting webhook to {webhook_url}")
    
    # Set webhook
    await bot.set_webhook(webhook_url)
    
    # Process webhook
    async def handle_webhook(request):
        url = str(request.url)
        if url.startswith(webhook_url) or webhook_path in url:
            update = await request.json()
            await dp.feed_update(bot, update)
            return web.Response(status=200)
        return web.Response(status=403)
    
    app.router.add_post(webhook_path, handle_webhook)
    logger.info(f"Webhook handler added for path: {webhook_path}")

async def start_polling():
    """Start the bot in polling mode (for testing)"""
    logger.info("Starting bot in polling mode")
    
    # Set commands
    await set_commands()
    
    # Register all handlers
    await register_handlers()
    
    # Delete any existing webhook before starting polling
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url:
        logger.info(f"Deleting existing webhook: {webhook_info.url}")
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Deleted existing webhook")
    else:
        logger.info("No webhook is currently set")
    
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