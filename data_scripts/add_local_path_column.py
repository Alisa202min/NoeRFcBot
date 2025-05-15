#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
این اسکریپت ستون local_path را به جدول service_media اضافه می‌کند
"""

import os
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# بارگذاری متغیرهای محیطی
load_dotenv()

# اتصال به دیتابیس
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    logger.error("DATABASE_URL محیطی تنظیم نشده است")
    exit(1)

engine = create_engine(db_url)

def add_column_if_not_exists():
    """
    اضافه کردن ستون local_path به جدول service_media اگر وجود ندارد
    """
    try:
        # چک کردن وجود ستون
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'service_media' AND column_name = 'local_path'
        """)
        
        with engine.connect() as connection:
            result = connection.execute(check_query)
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                # اضافه کردن ستون
                add_column_query = text("""
                    ALTER TABLE service_media 
                    ADD COLUMN local_path TEXT
                """)
                
                connection.execute(add_column_query)
                connection.commit()
                logger.info("ستون local_path با موفقیت به جدول service_media اضافه شد")
            else:
                logger.info("ستون local_path از قبل در جدول service_media وجود دارد")
                
    except Exception as e:
        logger.error(f"خطا در اضافه کردن ستون: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        logger.info("شروع فرآیند اضافه کردن ستون local_path")
        add_column_if_not_exists()
        logger.info("فرآیند اضافه کردن ستون با موفقیت به پایان رسید")
    except Exception as e:
        logger.error(f"خطای کلی: {str(e)}")