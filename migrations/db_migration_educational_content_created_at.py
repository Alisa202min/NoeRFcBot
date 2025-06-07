#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
مهاجرت جدول محتوای آموزشی
این اسکریپت ستون created_at را به جدول educational_content اضافه می‌کند
"""

import os
import sys
import logging
from sqlalchemy import text
from app import app, db

# تنظیم لاگر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_educational_content_table():
    """اضافه کردن ستون created_at به جدول educational_content"""
    try:
        with app.app_context():
            logger.info("بررسی جدول educational_content...")
            
            # بررسی وجود ستون created_at
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'educational_content'
                    AND column_name = 'created_at'
                );
            """))
            
            column_exists = result.scalar()
            
            if not column_exists:
                logger.info("اضافه کردن ستون created_at به جدول educational_content...")
                
                # اضافه کردن ستون جدید
                db.session.execute(text("""
                    ALTER TABLE educational_content
                    ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                """))
                
                db.session.commit()
                logger.info("ستون created_at با موفقیت به جدول educational_content اضافه شد.")
            else:
                logger.info("ستون created_at در حال حاضر در جدول educational_content وجود دارد.")
            
            return True
    except Exception as e:
        logger.error(f"خطا در مهاجرت جدول educational_content: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    if migrate_educational_content_table():
        logger.info("مهاجرت با موفقیت انجام شد.")
        sys.exit(0)
    else:
        logger.error("مهاجرت با خطا مواجه شد.")
        sys.exit(1)