#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست ساده ربات تلگرام - بررسی وضعیت webhook و polling
"""

import os
import sys
import logging
import asyncio
from aiogram import Bot
import dotenv

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_webhook_status():
    """بررسی وضعیت webhook ربات"""
    try:
        # بارگذاری متغیرهای محیطی
        dotenv.load_dotenv()
        
        # دریافت توکن ربات
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            logger.error("❌ BOT_TOKEN در متغیرهای محیطی یافت نشد")
            return False
        
        # ایجاد نمونه ربات
        bot = Bot(token=bot_token)
        
        # دریافت اطلاعات webhook
        webhook_info = await bot.get_webhook_info()
        
        # بررسی وضعیت webhook
        if webhook_info.url:
            logger.info(f"✅ Webhook فعال است: {webhook_info.url}")
            logger.info(f"✅ Pending updates: {webhook_info.pending_update_count}")
            return True
        else:
            logger.info("ℹ️ هیچ webhook فعالی تنظیم نشده است - ربات می‌تواند در حالت polling اجرا شود")
            return True
    except Exception as e:
        logger.error(f"❌ خطا در بررسی وضعیت webhook: {e}")
        return False
    finally:
        if 'bot' in locals():
            await bot.session.close()

def main():
    """تابع اصلی"""
    print("===== تست وضعیت ربات تلگرام =====")
    
    # اجرای تست‌ها
    success = asyncio.run(check_webhook_status())
    
    print("\n===== نتایج تست‌ها =====")
    if success:
        print("✅ تست با موفقیت انجام شد")
    else:
        print("❌ تست ناموفق بود")
        
    print("\n===== پایان تست وضعیت ربات تلگرام =====")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)