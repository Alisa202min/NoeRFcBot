"""
مهاجرت جدول استعلام‌های قیمت
این اسکریپت نوع داده ستون user_id را در جدول inquiries به BIGINT تغییر می‌دهد
"""
import os
import psycopg2
import logging
from dotenv import load_dotenv

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def migrate_inquiry_user_id():
    """تغییر نوع داده ستون user_id به BIGINT در جدول inquiries برای پشتیبانی از شناسه‌های بزرگ تلگرام"""
    load_dotenv()
    
    # اتصال به دیتابیس
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = True
        
        with conn.cursor() as cursor:
            # بررسی نوع داده فعلی
            cursor.execute("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'inquiries' AND column_name = 'user_id'
            """)
            
            current_type = cursor.fetchone()[0]
            logger.info(f"Current data type for user_id: {current_type}")
            
            # تغییر نوع داده اگر INTEGER باشد
            if current_type.lower() == 'integer':
                cursor.execute("ALTER TABLE inquiries ALTER COLUMN user_id TYPE BIGINT;")
                logger.info("Successfully altered user_id column type to BIGINT")
            else:
                logger.info(f"user_id column is already of type {current_type}, no change needed")
                
    except Exception as e:
        logger.error(f"Error in migration: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_inquiry_user_id()
    logger.info("Migration completed successfully")