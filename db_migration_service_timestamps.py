"""
اسکریپت اضافه کردن فیلدهای created_at و updated_at به جدول services
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import text

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# اضافه کردن مسیر پروژه به sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# وارد کردن ماژول‌های مورد نیاز
from src.web.app import app, db

def add_timestamp_columns():
    """اضافه کردن فیلدهای created_at و updated_at به جدول services"""
    try:
        # بررسی وجود ستون‌ها
        connection = db.engine.connect()
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('services')]
        
        # افزودن created_at اگر وجود ندارد
        if 'created_at' not in columns:
            logger.info("Adding created_at column to services table")
            connection.execute(text("ALTER TABLE services ADD COLUMN created_at TIMESTAMP DEFAULT NOW()"))
        
        # افزودن updated_at اگر وجود ندارد
        if 'updated_at' not in columns:
            logger.info("Adding updated_at column to services table")
            connection.execute(text("ALTER TABLE services ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()"))
        
        connection.commit()
        logger.info("Timestamp columns added successfully")
        
    except Exception as e:
        logger.error(f"Error adding timestamp columns: {str(e)}")
        raise

def main():
    """تابع اصلی"""
    logger.info("Starting service timestamps migration")
    
    try:
        add_timestamp_columns()
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    with app.app_context():
        main()