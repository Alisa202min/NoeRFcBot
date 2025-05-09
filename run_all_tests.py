#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اسکریپت اجرای تمام تست‌ها
این اسکریپت تمام تست‌های سیستم را اجرا می‌کند و گزارش نتایج را نمایش می‌دهد
"""

import os
import sys
import unittest
import logging
from datetime import datetime

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_results.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_test_suite(test_module_name, test_description):
    """
    اجرای یک مجموعه تست و گزارش نتایج
    
    Args:
        test_module_name: نام ماژول تست
        test_description: توضیحات تست
    
    Returns:
        (success_count, total_count): تعداد تست‌های موفق و کل
    """
    logger.info(f"================================================")
    logger.info(f"شروع اجرای تست‌های {test_description}")
    logger.info(f"================================================")
    
    try:
        # بارگیری ماژول تست
        __import__(test_module_name)
        test_module = sys.modules[test_module_name]
        
        # ایجاد مجموعه تست
        suite = unittest.TestLoader().loadTestsFromModule(test_module)
        
        # اجرای تست‌ها
        result = unittest.TextTestRunner().run(suite)
        
        # گزارش نتایج
        success_count = result.testsRun - len(result.errors) - len(result.failures)
        total_count = result.testsRun
        
        logger.info(f"نتایج اجرای تست‌های {test_description}:")
        logger.info(f"  تعداد کل تست‌ها: {total_count}")
        logger.info(f"  تست‌های موفق: {success_count}")
        logger.info(f"  تست‌های ناموفق: {len(result.failures)}")
        logger.info(f"  خطاها: {len(result.errors)}")
        
        # نمایش خطاها و شکست‌ها
        if result.failures:
            logger.error("شکست‌ها:")
            for i, (test, traceback) in enumerate(result.failures):
                logger.error(f"شکست {i+1}: {test}")
                logger.error(traceback)
        
        if result.errors:
            logger.error("خطاها:")
            for i, (test, traceback) in enumerate(result.errors):
                logger.error(f"خطا {i+1}: {test}")
                logger.error(traceback)
        
        logger.info(f"================================================")
        
        return success_count, total_count
        
    except Exception as e:
        logger.error(f"خطا در اجرای تست‌های {test_description}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0, 0

def seed_database():
    """
    مقداردهی اولیه دیتابیس
    
    Returns:
        bool: نتیجه عملیات
    """
    logger.info("در حال مقداردهی اولیه دیتابیس...")
    try:
        from app import app
        from seed_admin_data import main
        
        with app.app_context():
            result = main()
            
            if result == 0:
                logger.info("مقداردهی اولیه دیتابیس با موفقیت انجام شد")
                return True
            else:
                logger.error("خطا در مقداردهی اولیه دیتابیس")
                return False
    
    except Exception as e:
        logger.error(f"خطا در مقداردهی اولیه دیتابیس: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """
    اجرای اصلی
    """
    logger.info("شروع اجرای تمام تست‌ها")
    logger.info(f"تاریخ و زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # مقداردهی اولیه دیتابیس
    if not seed_database():
        logger.error("به دلیل خطا در مقداردهی اولیه دیتابیس، اجرای تست‌ها متوقف شد")
        return 1
    
    # لیست تمام ماژول‌های تست و توضیحات آن‌ها
    test_modules = [
        ("test_admin_panel", "پنل ادمین"),
        ("test_telegram_bot", "بات تلگرام"),
        # در صورت نیاز ماژول‌های تست دیگر را اضافه کنید
    ]
    
    # شمارنده‌های کلی
    total_success = 0
    total_tests = 0
    
    # اجرای تمام ماژول‌های تست
    for module_name, description in test_modules:
        success, total = run_test_suite(module_name, description)
        total_success += success
        total_tests += total
    
    # گزارش نهایی
    logger.info("================================================")
    logger.info("گزارش نهایی اجرای تمام تست‌ها:")
    logger.info(f"  تعداد کل تست‌ها: {total_tests}")
    logger.info(f"  تست‌های موفق: {total_success}")
    logger.info(f"  تست‌های ناموفق: {total_tests - total_success}")
    
    # نمایش درصد موفقیت
    if total_tests > 0:
        success_rate = (total_success / total_tests) * 100
        logger.info(f"  درصد موفقیت: {success_rate:.2f}%")
    
    logger.info("================================================")
    
    # تولید کد بازگشت مناسب
    return 0 if total_success == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())