#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
مهاجرت جدول کاربران به ساختار جدید
این اسکریپت ستون‌های جدید تلگرام را به جدول کاربران اضافه می‌کند
"""

import os
import sys
import psycopg2
from psycopg2 import sql

def migrate_user_table():
    """اضافه کردن ستون‌های تلگرام به جدول کاربران"""
    
    # اتصال به دیتابیس
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        print("خطا: متغیر DATABASE_URL تنظیم نشده است")
        return False
    
    print(f"در حال اتصال به دیتابیس...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # بررسی وجود ستون‌های جدید
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'telegram_id'
        """)
        
        if cursor.fetchone():
            print("ستون‌های تلگرام قبلاً اضافه شده‌اند")
            conn.close()
            return True
        
        print("در حال اضافه کردن ستون‌های تلگرام به جدول کاربران...")
        
        # تغییر ستون‌های موجود
        cursor.execute("""
            ALTER TABLE users 
            ALTER COLUMN email DROP NOT NULL,
            ALTER COLUMN password_hash DROP NOT NULL
        """)
        
        # اضافه کردن ستون‌های جدید
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN telegram_id BIGINT UNIQUE,
            ADD COLUMN telegram_username VARCHAR(64),
            ADD COLUMN first_name VARCHAR(64),
            ADD COLUMN last_name VARCHAR(64),
            ADD COLUMN last_seen TIMESTAMP
        """)
        
        # ثبت تغییرات
        conn.commit()
        print("✓ ستون‌های تلگرام با موفقیت اضافه شدند")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"خطا در مهاجرت جدول کاربران: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    migrate_user_table()