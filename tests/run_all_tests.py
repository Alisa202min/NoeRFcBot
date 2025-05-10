#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اجرای تمام تست‌های سیستم به صورت یک‌جا
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime

# تنظیم لاگر
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_results.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_test(test_script, description):
    """اجرای یک اسکریپت تست و نمایش نتیجه"""
    start_time = time.time()
    logger.info(f"=== شروع تست: {description} ===")
    
    try:
        result = subprocess.run(
            [sys.executable, test_script],
            check=False,
            capture_output=True,
            text=True,
            timeout=60  # حداکثر زمان اجرا: 60 ثانیه
        )
        
        # نمایش خروجی
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                logger.info(f"[خروجی] {line}")
        
        # نمایش خطاها
        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                logger.error(f"[خطا] {line}")
        
        success = result.returncode == 0
        status = "موفق" if success else "ناموفق"
        logger.info(f"=== پایان تست: {description} - وضعیت: {status} (کد خروج: {result.returncode}) ===")
        
        elapsed_time = time.time() - start_time
        logger.info(f"زمان اجرا: {elapsed_time:.2f} ثانیه\n")
        
        return {
            "name": description,
            "script": test_script,
            "success": success,
            "return_code": result.returncode,
            "elapsed_time": elapsed_time
        }
    except subprocess.TimeoutExpired:
        logger.error(f"=== تست با خطای timeout مواجه شد: {description} ===\n")
        return {
            "name": description,
            "script": test_script,
            "success": False,
            "return_code": -1,
            "elapsed_time": time.time() - start_time,
            "timeout": True
        }
    except Exception as e:
        logger.error(f"=== خطا در اجرای تست {description}: {e} ===\n")
        return {
            "name": description,
            "script": test_script,
            "success": False,
            "return_code": -1,
            "elapsed_time": time.time() - start_time,
            "error": str(e)
        }

def format_time(seconds):
    """تبدیل ثانیه به فرمت خوانا"""
    if seconds < 60:
        return f"{seconds:.2f} ثانیه"
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f"{minutes} دقیقه و {seconds:.2f} ثانیه"

def main():
    """اجرای تمام تست‌ها"""
    start_time = time.time()
    
    # لیست تست‌ها برای اجرا
    tests = [
        ("simple_bot_test.py", "تست ساده ربات تلگرام"),
        ("db_test.py", "تست دیتابیس"),
        ("simple_handlers_test.py", "تست ساده handlers"),
        ("comprehensive_test.py", "تست جامع سیستم"),
        ("test_admin_panel.py", "تست پنل ادمین"),
        ("test_system.py", "تست وب اپلیکیشن"),
        ("test_telegram_bot.py", "تست کامل ربات تلگرام"),
        ("test_inquiry_system.py", "تست سیستم استعلام قیمت"),
    ]
    
    # نتایج اجرای تست‌ها
    results = []
    
    # ایجاد دایرکتوری نتایج اگر وجود ندارد
    os.makedirs("test_results", exist_ok=True)
    
    logger.info(f"===== شروع اجرای {len(tests)} تست در {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")
    
    for test_script, description in tests:
        # اجرای تست
        result = run_test(test_script, description)
        results.append(result)
    
    # محاسبه نتایج کلی
    total_tests = len(tests)
    successful_tests = sum(1 for result in results if result["success"])
    failed_tests = total_tests - successful_tests
    
    # نمایش نتایج
    logger.info("\n===== خلاصه نتایج =====")
    logger.info(f"تعداد کل تست‌ها: {total_tests}")
    logger.info(f"تست‌های موفق: {successful_tests}")
    logger.info(f"تست‌های ناموفق: {failed_tests}")
    logger.info(f"نرخ موفقیت: {(successful_tests / total_tests * 100):.2f}%")
    
    # اگر تست ناموفق وجود دارد
    if failed_tests > 0:
        logger.info("\nتست‌های ناموفق:")
        for i, result in enumerate([r for r in results if not r["success"]], 1):
            if result.get("timeout", False):
                status = "خطای timeout"
            elif "error" in result:
                status = f"خطا: {result['error']}"
            else:
                status = f"کد خروج: {result['return_code']}"
            
            logger.info(f"{i}. {result['name']} ({status})")
    
    # نمایش زمان اجرای هر تست
    logger.info("\nزمان اجرای تست‌ها:")
    for i, result in enumerate(results, 1):
        status = "✅" if result["success"] else "❌"
        logger.info(f"{i}. {status} {result['name']}: {format_time(result['elapsed_time'])}")
    
    # زمان کل اجرا
    total_time = time.time() - start_time
    logger.info(f"\nزمان کل اجرا: {format_time(total_time)}")
    logger.info(f"===== پایان اجرای تست‌ها در {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")
    
    # خروجی
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    sys.exit(main())