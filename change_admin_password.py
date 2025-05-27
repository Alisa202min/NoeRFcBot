#!/usr/bin/env python3
"""
اسکریپت تغییر رمز عبور ادمین - مستقل و امن
این فایل هیچ تغییری در کد اصلی برنامه نمیدهد
"""
import os
import sys
import getpass
from dotenv import load_dotenv

def change_admin_password():
    """تغییر امن رمز عبور ادمین"""
    try:
        # بارگذاری متغیرهای محیطی
        load_dotenv()
        
        # وارد کردن ماژول‌های برنامه
        from app import app, db
        from models import User
        
        print("🔐 تغییر رمز عبور ادمین")
        print("=" * 30)
        
        with app.app_context():
            # دریافت نام کاربری ادمین
            username = input("نام کاربری ادمین: ").strip()
            if not username:
                print("❌ نام کاربری نمی‌تواند خالی باشد")
                return
            
            # پیدا کردن کاربر
            admin = User.query.filter_by(username=username, is_admin=True).first()
            if not admin:
                print("❌ کاربر ادمین یافت نشد")
                return
            
            # دریافت رمز عبور جدید
            new_password = getpass.getpass("رمز عبور جدید: ")
            if len(new_password) < 4:
                print("❌ رمز عبور باید حداقل 4 کاراکتر باشد")
                return
            
            confirm_password = getpass.getpass("تأیید رمز عبور جدید: ")
            if new_password != confirm_password:
                print("❌ رمزهای عبور مطابقت ندارند")
                return
            
            # تغییر رمز عبور
            admin.set_password(new_password)
            db.session.commit()
            
            print("✅ رمز عبور ادمین با موفقیت تغییر یافت")
            
    except ImportError as e:
        print(f"❌ خطا در وارد کردن ماژول‌ها: {e}")
        print("مطمئن شوید در مسیر اصلی پروژه هستید")
    except Exception as e:
        print(f"❌ خطا: {e}")

if __name__ == "__main__":
    change_admin_password()