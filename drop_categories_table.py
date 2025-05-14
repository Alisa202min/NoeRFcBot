"""
حذف جدول categories با برداشتن محدودیت‌های کلید خارجی
"""

import os
import sys
import logging
from sqlalchemy import text
from app import app, db
from models import Product, Service

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def drop_foreign_keys():
    """برداشتن محدودیت‌های کلید خارجی"""
    with app.app_context():
        try:
            # حذف محدودیت کلید خارجی جدول products
            db.session.execute(text("""
                ALTER TABLE products
                DROP CONSTRAINT IF EXISTS products_category_id_fkey;
            """))
            
            # حذف محدودیت کلید خارجی جدول services
            db.session.execute(text("""
                ALTER TABLE services
                DROP CONSTRAINT IF EXISTS services_category_id_fkey;
            """))
            
            # حذف محدودیت کلید خارجی برای جدول inquiries (اگر وجود دارد)
            db.session.execute(text("""
                ALTER TABLE inquiries
                DROP CONSTRAINT IF EXISTS inquiries_product_id_fkey,
                DROP CONSTRAINT IF EXISTS inquiries_service_id_fkey;
            """))

            db.session.commit()
            logger.info("محدودیت‌های کلید خارجی با موفقیت برداشته شدند")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"خطا در برداشتن محدودیت‌های کلید خارجی: {str(e)}")
            return False

def drop_categories_table():
    """حذف جدول categories"""
    with app.app_context():
        try:
            # حذف جدول با استفاده از SQL مستقیم
            db.session.execute(text("DROP TABLE IF EXISTS categories CASCADE;"))
            db.session.commit()
            logger.info("جدول categories با موفقیت حذف شد")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"خطا در حذف جدول categories: {str(e)}")
            return False

def main():
    """تابع اصلی برای حذف جدول categories"""
    logger.info("شروع فرآیند حذف جدول categories")
    
    if not drop_foreign_keys():
        logger.error("خطا در برداشتن محدودیت‌های کلید خارجی. فرآیند متوقف شد.")
        return False
    
    if not drop_categories_table():
        logger.error("خطا در حذف جدول categories. فرآیند متوقف شد.")
        return False
    
    logger.info("فرآیند حذف جدول categories با موفقیت انجام شد")
    return True

if __name__ == "__main__":
    main()