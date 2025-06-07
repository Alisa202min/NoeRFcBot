#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
مهاجرت جدول محتوای ثابت
این اسکریپت ستون updated_at را به جدول static_content اضافه می‌کند
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
    """اضافه کردن ستون updated_at به جدول static_content"""
    try:
        with app.app_context():
            logger.info("بررسی جدول static_content...")
            
            # بررسی وجود ستون updated_at
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'static_content'
                    AND column_name = 'updated_at'
                );
            """))
            
            column_exists = result.scalar()
            
            if not column_exists:
                logger.info("اضافه کردن ستون updated_at به جدول static_content...")
                
                # اضافه کردن ستون جدید
                db.session.execute(text("""
                    ALTER TABLE static_content
                    ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                """))
                
                db.session.commit()
                logger.info("ستون updated_at با موفقیت به جدول static_content اضافه شد.")
            else:
                logger.info("ستون updated_at در حال حاضر در جدول static_content وجود دارد.")
            
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