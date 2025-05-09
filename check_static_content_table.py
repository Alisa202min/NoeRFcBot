#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بررسی ساختار جدول static_content
"""

import os
import sys
import logging
from sqlalchemy import text
from app import app, db

# تنظیم لاگر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_static_content_table():
    """بررسی ساختار جدول static_content"""
    try:
        with app.app_context():
            logger.info("بررسی جدول static_content...")
            
            # دریافت اطلاعات ستون‌های جدول
            result = db.session.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'static_content'
                ORDER BY ordinal_position;
            """))
            
            print("Column Name | Data Type | Nullable")
            print("-" * 50)
            for row in result:
                print(f"{row[0]} | {row[1]} | {row[2]}")
            
            return True
    except Exception as e:
        logger.error(f"خطا در بررسی جدول static_content: {e}")
        return False

if __name__ == "__main__":
    if check_static_content_table():
        sys.exit(0)
    else:
        sys.exit(1)