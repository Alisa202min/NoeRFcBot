import os
import asyncio
import logging
from aiogram import Bot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize bot
bot_token = os.environ.get('BOT_TOKEN')
if not bot_token:
    logger.error("BOT_TOKEN not set in environment variables")
    exit(1)

# Create bot instance
bot = Bot(token=bot_token)

async def delete_webhook():
    """Force delete webhook"""
    logger.info("Deleting webhook...")
    webhook_info = await bot.get_webhook_info()
    logger.info(f"Current webhook URL: {webhook_info.url}")
    
    # Delete webhook
    success = await bot.delete_webhook(drop_pending_updates=True)
    logger.info(f"Webhook deleted successfully: {success}")
    
    # Verify webhook is deleted
    webhook_info = await bot.get_webhook_info()
    logger.info(f"Webhook URL after deletion: {webhook_info.url}")
    
    if not webhook_info.url:
        logger.info("Webhook successfully removed")
    else:
        logger.error(f"Failed to remove webhook, still set to: {webhook_info.url}")

if __name__ == "__main__":
    asyncio.run(delete_webhook())