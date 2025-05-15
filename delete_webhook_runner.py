"""
اسکریپتی برای اجرای حذف وبهوک تلگرام
"""

import asyncio
from src.utils.delete_webhook import delete_webhook

if __name__ == "__main__":
    # اجرای غیرهمزمان برای حذف وبهوک
    asyncio.run(delete_webhook())