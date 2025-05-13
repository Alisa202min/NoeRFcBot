"""
اضافه کردن ستون‌های جدید به جدول services
"""

import logging
from src.web.app import app, db
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_service_table():
    """اضافه کردن ستون‌های featured و available به جدول services"""
    logger.info("شروع مهاجرت جدول services...")
    
    try:
        # بررسی وجود ستون featured
        query_check_featured = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='services' AND column_name='featured'
        """)
        
        # بررسی وجود ستون available
        query_check_available = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='services' AND column_name='available'
        """)
        
        result_featured = db.session.execute(query_check_featured).fetchone()
        result_available = db.session.execute(query_check_available).fetchone()
        
        # اضافه کردن ستون featured اگر وجود نداشت
        if not result_featured:
            logger.info("اضافه کردن ستون featured به جدول services...")
            query_add_featured = text("""
                ALTER TABLE services ADD COLUMN featured BOOLEAN DEFAULT FALSE
            """)
            db.session.execute(query_add_featured)
            logger.info("ستون featured با موفقیت اضافه شد")
        else:
            logger.info("ستون featured از قبل وجود دارد")
        
        # اضافه کردن ستون available اگر وجود نداشت
        if not result_available:
            logger.info("اضافه کردن ستون available به جدول services...")
            query_add_available = text("""
                ALTER TABLE services ADD COLUMN available BOOLEAN DEFAULT TRUE
            """)
            db.session.execute(query_add_available)
            logger.info("ستون available با موفقیت اضافه شد")
        else:
            logger.info("ستون available از قبل وجود دارد")
        
        db.session.commit()
        logger.info("مهاجرت جدول services با موفقیت انجام شد")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"خطا در مهاجرت جدول services: {str(e)}")
        raise

if __name__ == "__main__":
    with app.app_context():
        migrate_service_table()
