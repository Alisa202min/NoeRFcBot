#!/usr/bin/env python3
"""
اسکریپت راه‌اندازی RFCBot
این اسکریپت برنامه فلسک و بات تلگرام را راه‌اندازی می‌کند.
"""

import logging
import os
from src.web import app
from src.bot import bot, dp, register_handlers, start_polling

# تنظیم لاگ‌ها
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # ثبت هندلرهای بات
    register_handlers(dp)
    
    # راه‌اندازی برنامه فلسک
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)