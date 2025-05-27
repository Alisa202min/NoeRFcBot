"""
نقطه ورود اصلی برنامه RFCBot (سیستم تلگرام و وب)
این فایل مسئول راه‌اندازی هر دو سرویس بات تلگرام و برنامه وب است.
"""

import os
import logging
import threading
import asyncio
from src.web import app
from src.bot.bot import start_polling, register_handlers

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_web_app():
    """راه‌اندازی برنامه وب Flask"""
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)

def run_telegram_bot():
    """راه‌اندازی بات تلگرام در حالت polling"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # ثبت هندلرها
    register_handlers()
    
    # راه‌اندازی بات
    loop.run_until_complete(start_polling())

if __name__ == "__main__":
    # راه‌اندازی بات تلگرام در یک ترد جداگانه
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # راه‌اندازی برنامه وب
    run_web_app()