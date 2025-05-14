#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
مهاجرت جدول محتوای ثابت
این اسکریپت ستون content_type را به جدول static_content اضافه می‌کند
"""

import os
import sys
import logging
from sqlalchemy import text
from app import app, db

# تنظیم لاگر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_static_content_table():
    """اضافه کردن ستون content_type به جدول static_content"""
    try:
        with app.app_context():
            logger.info("بررسی جدول static_content...")
            
            # بررسی وجود جدول static_content
            table_exists = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'static_content'
                );
            """)).scalar()
            
            if not table_exists:
                logger.info("جدول static_content وجود ندارد. ایجاد جدول...")
                
                # ایجاد جدول جدید
                db.session.execute(text("""
                    CREATE TABLE static_content (
                        id SERIAL PRIMARY KEY,
                        content_type VARCHAR(20) NOT NULL UNIQUE,
                        content TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                db.session.commit()
                logger.info("جدول static_content با موفقیت ایجاد شد.")
            else:
                # بررسی وجود ستون content_type
                column_exists = db.session.execute(text("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'static_content'
                        AND column_name = 'content_type'
                    );
                """)).scalar()
                
                if not column_exists:
                    logger.info("اضافه کردن ستون content_type به جدول static_content...")
                    
                    # اضافه کردن ستون جدید با مقدار پیش‌فرض
                    db.session.execute(text("""
                        ALTER TABLE static_content
                        ADD COLUMN content_type VARCHAR(20) DEFAULT 'generic';
                    """))
                    
                    # به‌روزرسانی مقادیر content_type بر اساس داده‌های موجود
                    db.session.execute(text("""
                        UPDATE static_content
                        SET content_type = 
                            CASE
                                WHEN content LIKE '%درباره ما%' THEN 'about'
                                WHEN content LIKE '%تماس با ما%' THEN 'contact'
                                ELSE 'generic'
                            END;
                    """))
                    
                    # تنظیم NOT NULL constraint
                    db.session.execute(text("""
                        ALTER TABLE static_content
                        ALTER COLUMN content_type SET NOT NULL;
                    """))
                    
                    db.session.commit()
                    logger.info("ستون content_type با موفقیت به جدول static_content اضافه شد.")
                else:
                    logger.info("ستون content_type در حال حاضر در جدول static_content وجود دارد.")
            
            return True
    except Exception as e:
        logger.error(f"خطا در مهاجرت جدول static_content: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    if migrate_static_content_table():
        logger.info("مهاجرت با موفقیت انجام شد.")
        sys.exit(0)
    else:
        logger.error("مهاجرت با خطا مواجه شد.")
        sys.exit(1)