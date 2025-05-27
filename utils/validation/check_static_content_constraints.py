#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بررسی محدودیت‌های جدول static_content
"""

import os
import sys
import logging
from sqlalchemy import text
from app import app, db

# تنظیم لاگر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_static_content_constraints():
    """بررسی محدودیت‌های جدول static_content"""
    try:
        with app.app_context():
            logger.info("بررسی محدودیت‌های جدول static_content...")
            
            # دریافت اطلاعات شاخص‌های جدول
            result = db.session.execute(text("""
                SELECT con.conname, con.contype, pg_get_constraintdef(con.oid)
                FROM pg_constraint con
                INNER JOIN pg_class rel ON rel.oid = con.conrelid
                INNER JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
                WHERE rel.relname = 'static_content';
            """))
            
            print("Constraint Name | Type | Definition")
            print("-" * 60)
            for row in result:
                print(f"{row[0]} | {row[1]} | {row[2]}")
            
            return True
    except Exception as e:
        logger.error(f"خطا در بررسی محدودیت‌های جدول static_content: {e}")
        return False

if __name__ == "__main__":
    if check_static_content_constraints():
        sys.exit(0)
    else:
        sys.exit(1)