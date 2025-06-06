#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
مهاجرت جدول استعلام‌های قیمت
این اسکریپت ستون status را به جدول inquiries اضافه می‌کند
"""

import os
import sys
import logging
from sqlalchemy import text
from app import app, db

# تنظیم لاگر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_inquiry_table():
    """اضافه کردن ستون status به جدول inquiries"""
    try:
        with app.app_context():
            logger.info("بررسی جدول inquiries...")
            
            # بررسی وجود ستون status
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'inquiries'
                    AND column_name = 'status'
                );
            """))
            
            column_exists = result.scalar()
            
            if not column_exists:
                logger.info("اضافه کردن ستون status به جدول inquiries...")
                
                # اضافه کردن ستون جدید
                db.session.execute(text("""
                    ALTER TABLE inquiries
                    ADD COLUMN status VARCHAR(20) DEFAULT 'new';
                """))
                
                db.session.commit()
                logger.info("ستون status با موفقیت به جدول inquiries اضافه شد.")
            else:
                logger.info("ستون status در حال حاضر در جدول inquiries وجود دارد.")
            
            return True
    except Exception as e:
        logger.error(f"خطا در مهاجرت جدول inquiries: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    if migrate_inquiry_table():
        logger.info("مهاجرت با موفقیت انجام شد.")
        sys.exit(0)
    else:
        logger.error("مهاجرت با خطا مواجه شد.")
        sys.exit(1)