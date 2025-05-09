#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
مهاجرت جدول رسانه‌های محصولات
این اسکریپت ستون local_path را به جدول product_media اضافه می‌کند
"""

import os
import sys
import logging
from sqlalchemy import text
from app import app, db

# تنظیم لاگر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_product_media_table():
    """اضافه کردن ستون local_path به جدول product_media"""
    try:
        with app.app_context():
            logger.info("بررسی جدول product_media...")
            
            # بررسی وجود ستون local_path
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'product_media'
                    AND column_name = 'local_path'
                );
            """))
            
            column_exists = result.scalar()
            
            if not column_exists:
                logger.info("اضافه کردن ستون local_path به جدول product_media...")
                
                # اضافه کردن ستون جدید
                db.session.execute(text("""
                    ALTER TABLE product_media
                    ADD COLUMN local_path VARCHAR(255);
                """))
                
                db.session.commit()
                logger.info("ستون local_path با موفقیت به جدول product_media اضافه شد.")
            else:
                logger.info("ستون local_path در حال حاضر در جدول product_media وجود دارد.")
            
            return True
    except Exception as e:
        logger.error(f"خطا در مهاجرت جدول product_media: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    if migrate_product_media_table():
        logger.info("مهاجرت با موفقیت انجام شد.")
        sys.exit(0)
    else:
        logger.error("مهاجرت با خطا مواجه شد.")
        sys.exit(1)