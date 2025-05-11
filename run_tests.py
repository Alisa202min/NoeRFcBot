#!/usr/bin/env python3
"""
اسکریپت اجرای خودکار تست‌های RFCBot
این اسکریپت تست‌های مختلف را به ترتیب اجرا می‌کند و نتایج را گزارش می‌دهد.
"""

import sys
import os
import time
import datetime
import logging
import subprocess
from typing import List, Tuple, Optional

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("test_results.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def print_and_log(message):
    """چاپ پیام در خروجی استاندارد و ثبت آن در لاگ"""
    logger.info(message)

def run_command(command, description, timeout=300):
    """اجرای یک دستور و بازگرداندن نتیجه"""
    print_and_log(f"در حال اجرای {description}...")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        elapsed_time = time.time() - start_time
        success = result.returncode == 0
        
        if success:
            print_and_log(f"✅ {description} با موفقیت اجرا شد (زمان: {elapsed_time:.2f} ثانیه)")
        else:
            print_and_log(f"❌ خطا در اجرای {description}")
            print_and_log(f"خروجی استاندارد:\n{result.stdout}")
            print_and_log(f"خروجی خطا:\n{result.stderr}")
        
        return success, result.stdout, result.stderr, elapsed_time
    except subprocess.TimeoutExpired:
        print_and_log(f"⏱️ تایم‌اوت در اجرای {description} (بیش از {timeout} ثانیه)")
        return False, "", f"Timeout after {timeout} seconds", timeout
    except Exception as e:
        print_and_log(f"❌ خطای غیرمنتظره در اجرای {description}: {str(e)}")
        return False, "", str(e), time.time() - start_time

def check_test_database():
    """بررسی وجود دیتابیس تست"""
    if not os.environ.get("DATABASE_URL"):
        print_and_log("❌ متغیر محیطی DATABASE_URL تنظیم نشده است")
        return False
    
    # بررسی اتصال به دیتابیس
    result, stdout, stderr, _ = run_command(
        "python -c \"from database import Database; db = Database(); print('دیتابیس متصل شد')\"",
        "بررسی اتصال به دیتابیس"
    )
    
    if not result:
        print_and_log("❌ اتصال به دیتابیس ناموفق بود")
        return False
    
    return True

def run_tests():
    """اجرای تمام تست‌ها و گزارش نتایج"""
    print_and_log("=" * 60)
    print_and_log(f"شروع اجرای تست‌ها در {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_and_log("=" * 60)
    
    # بررسی پیش‌نیازها
    if not check_test_database():
        print_and_log("❌ پایان اجرا به دلیل مشکل در دیتابیس")
        return False
    
    test_results = []
    total_time = 0
    
    # لیست تست‌ها برای اجرا
    tests = [
        ("pytest tests/test_db.py -v", "تست‌های پایگاه داده"),
        ("pytest tests/test_bot.py -v", "تست‌های پایه بات"),
        ("pytest tests/test_flows.py -v", "تست‌های جریان مکالمه"),
        ("pytest tests/test_admin.py -v", "تست‌های پنل مدیریت")
    ]
    
    # اجرای تک تک تست‌ها
    for command, description in tests:
        success, stdout, stderr, elapsed_time = run_command(command, description)
        test_results.append((description, success, elapsed_time))
        total_time += elapsed_time
        
        # فاصله بین تست‌ها
        print_and_log("-" * 40)
    
    # نمایش نتایج نهایی
    print_and_log("\n" + "=" * 60)
    print_and_log("نتایج نهایی تست‌ها:")
    print_and_log("=" * 60)
    
    success_count = sum(1 for _, success, _ in test_results if success)
    
    for description, success, elapsed_time in test_results:
        status = "✅ موفق" if success else "❌ ناموفق"
        print_and_log(f"{status} - {description} (زمان: {elapsed_time:.2f} ثانیه)")
    
    print_and_log("-" * 60)
    print_and_log(f"نتیجه کلی: {success_count} موفق از {len(tests)} تست")
    print_and_log(f"زمان کل اجرا: {total_time:.2f} ثانیه")
    print_and_log("=" * 60)
    
    return success_count == len(tests)

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)