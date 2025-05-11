#!/usr/bin/env python3
"""
اسکریپت اجرای خودکار تست‌های RFCBot
این اسکریپت تست‌های مختلف را به ترتیب اجرا می‌کند و نتایج را گزارش می‌دهد.
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime

# تنظیمات logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='test_results.log'
)

logger = logging.getLogger('RFCBot Tests')

def print_and_log(message):
    """چاپ پیام در خروجی استاندارد و ثبت آن در لاگ"""
    print(message)
    logger.info(message)

def run_command(command, description, timeout=300):
    """اجرای یک دستور و بازگرداندن نتیجه"""
    print_and_log(f"در حال اجرای {description}...")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout
        )
        if result.returncode == 0:
            print_and_log(f"{description} با موفقیت اجرا شد.")
            return True, result.stdout
        else:
            print_and_log(f"خطا در اجرای {description}:")
            print_and_log(result.stderr)
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print_and_log(f"تایم‌اوت در اجرای {description}")
        return False, "Timeout"
    except Exception as e:
        print_and_log(f"خطای غیرمنتظره در اجرای {description}: {e}")
        return False, str(e)

def check_test_database():
    """بررسی وجود دیتابیس تست"""
    print_and_log("بررسی دیتابیس تست...")
    
    if 'DATABASE_URL' not in os.environ:
        print_and_log("متغیر محیطی DATABASE_URL تنظیم نشده است.")
        return False
    
    # دریافت نام دیتابیس از DATABASE_URL
    db_url = os.environ['DATABASE_URL']
    if 'postgresql' not in db_url.lower():
        print_and_log("DATABASE_URL باید به یک دیتابیس PostgreSQL اشاره کند.")
        return False
    
    return True

def run_tests():
    """اجرای تمام تست‌ها و گزارش نتایج"""
    start_time = time.time()
    test_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print_and_log(f"شروع اجرای تست‌ها در {test_date}")
    
    # بررسی پیش‌نیازها
    if not check_test_database():
        print_and_log("خطا در پیش‌نیازها. تست‌ها اجرا نمی‌شوند.")
        return False
    
    # لیست تمام تست‌ها
    tests = [
        {
            "name": "تست‌های بات",
            "command": ["pytest", "-v", "tests/test_bot.py"],
        },
        {
            "name": "تست‌های جریان‌های مکالمه",
            "command": ["pytest", "-v", "tests/test_flows.py"],
        },
        {
            "name": "تست‌های پایگاه داده",
            "command": ["pytest", "-v", "tests/test_db.py"],
        },
        {
            "name": "تست‌های پنل مدیریت",
            "command": ["pytest", "-v", "tests/test_admin.py"],
        }
    ]
    
    # اجرای هر تست
    results = []
    for test in tests:
        success, output = run_command(test["command"], test["name"])
        results.append({
            "name": test["name"],
            "success": success,
            "output": output
        })
        
        # کمی تأخیر بین تست‌ها
        time.sleep(1)
    
    # گزارش کلی
    print_and_log("\n--- گزارش نتایج تست‌ها ---")
    all_passed = True
    for result in results:
        status = "موفق" if result["success"] else "ناموفق"
        print_and_log(f"{result['name']}: {status}")
        if not result["success"]:
            all_passed = False
    
    # زمان اجرا
    elapsed_time = time.time() - start_time
    print_and_log(f"زمان کل اجرا: {elapsed_time:.2f} ثانیه")
    
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)