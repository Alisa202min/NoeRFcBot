"""
این اسکریپت وبهوک تلگرام را حذف می‌کند.
"""

import os
import asyncio
import logging
from aiogram import Bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def delete_webhook():
    """حذف وبهوک فعال در ربات تلگرام"""
    try:
        bot_token = os.environ.get('BOT_TOKEN')
        if not bot_token:
            logger.error("BOT_TOKEN یافت نشد. لطفا مطمئن شوید که متغیر محیطی BOT_TOKEN تنظیم شده است.")
            return False
            
        bot = Bot(token=bot_token)
        
        # بررسی وضعیت فعلی وبهوک
        webhook_info = await bot.get_webhook_info()
        
        if webhook_info.url:
            logger.info(f"وبهوک فعلی: {webhook_info.url}")
            
            # حذف وبهوک
            await bot.delete_webhook()
            logger.info("وبهوک با موفقیت حذف شد.")
            
            # بررسی مجدد
            webhook_info = await bot.get_webhook_info()
            logger.info(f"وضعیت وبهوک پس از حذف: {webhook_info.url or 'حذف شده'}")
            
            return True
        else:
            logger.info("وبهوکی برای حذف وجود ندارد.")
            return True
            
    except Exception as e:
        logger.error(f"خطا در حذف وبهوک: {e}")
        return False
    finally:
        # بستن جلسه بات
        if 'bot' in locals():
            await bot.session.close()

async def main():
    """تابع اصلی برای اجرای مستقیم اسکریپت"""
    success = await delete_webhook()
    if success:
        logger.info("عملیات حذف وبهوک با موفقیت انجام شد.")
    else:
        logger.error("خطا در حذف وبهوک.")

if __name__ == "__main__":
    # اجرای اسکریپت به صورت مستقیم
    asyncio.run(main())