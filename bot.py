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

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger(__name__)


# Note: We already configured logging at the top of the file, so we don't need to do it again
# Just use the existing logger

# Initialize bot and dispatcher
bot_token = os.environ.get('BOT_TOKEN')
if not bot_token:
    logger.error("BOT_TOKEN not set in environment variables")
    exit(1)

logger.info(f"Using bot token starting with: {bot_token[:5]}...")

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

async def register_handlers(dp):
    from handlers import register_all_handlers
    register_all_handlers(dp)
    logger.info("All handlers registered successfully")

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
                return web.Response()
            return web.Response(status=403)

        app.router.add_post(webhook_path, handle_webhook)

async def start_polling():
    async with ClientSession() as session:
        try:
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

        await set_commands()
        await register_handlers(dp)
        logger.info("Starting polling...")
        try:
            await dp.start_polling(bot)
        except Exception as e:
            logger.error(f"Polling error: {str(e)}")
            raise
        finally:
            logger.info("Polling stopped")

if __name__ == "__main__":
    asyncio.run(start_polling())