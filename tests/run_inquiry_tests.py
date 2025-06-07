#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
اسکریپت اجرای تست‌های مربوط به قابلیت استعلام قیمت

این اسکریپت تمامی تست‌های مربوط به قابلیت استعلام قیمت را در هر دو 
محیط ربات تلگرام و پنل مدیریت اجرا می‌کند.
"""

import os
import sys
import unittest
import logging
import argparse
from datetime import datetime

# تنظیم فرمت لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

def run_tests(test_types=None, verbose=False):
    """
    اجرای تست‌های مشخص شده
    
    پارامترها:
        test_types (list): لیست انواع تست‌ها برای اجرا (all, telegram, admin)
        verbose (bool): نمایش جزئیات بیشتر
    """
    if test_types is None or 'all' in test_types:
        test_types = ['telegram', 'admin']
    
    # تنظیم سطح لاگ بر اساس verbose
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # ایجاد دایرکتوری برای ذخیره گزارش‌ها
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_results')
    os.makedirs(report_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = os.path.join(report_dir, f'inquiry_tests_{timestamp}.log')
    
    with open(result_file, 'w', encoding='utf-8') as log_file:
        log_file.write(f"=== آغاز تست‌های استعلام قیمت - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
        
        total_tests = 0
        total_errors = 0
        total_failures = 0
        
        # اجرای تست‌های ربات تلگرام
        if 'telegram' in test_types:
            log_file.write("== اجرای تست‌های استعلام قیمت ربات تلگرام ==\n")
            print("\n=== اجرای تست‌های استعلام قیمت ربات تلگرام ===")
            
            try:
                # ایمپورت فایل تست تلگرام
                from test_telegram_inquiry import run_test
                
                # مسیر فایل تمپ برای نتایج تست
                tmp_result_file = os.path.join(report_dir, f'telegram_tmp_{timestamp}.log')
                
                # اجرای تست‌ها با خروجی به فایل تمپ
                original_stdout = sys.stdout
                with open(tmp_result_file, 'w', encoding='utf-8') as f:
                    sys.stdout = f
                    telegram_result = unittest.main(module='test_telegram_inquiry', exit=False)
                    sys.stdout = original_stdout
                
                # خواندن نتایج از فایل تمپ و اضافه کردن به فایل نتایج اصلی
                with open(tmp_result_file, 'r', encoding='utf-8') as f:
                    result_content = f.read()
                    log_file.write(result_content)
                    log_file.write("\n")
                
                # حذف فایل تمپ
                if os.path.exists(tmp_result_file):
                    os.remove(tmp_result_file)
                
                # جمع‌آوری آمار
                total_tests += telegram_result.result.testsRun
                total_errors += len(telegram_result.result.errors)
                total_failures += len(telegram_result.result.failures)
                
                print(f"تعداد تست‌ها: {telegram_result.result.testsRun}")
                print(f"خطاها: {len(telegram_result.result.errors)}")
                print(f"شکست‌ها: {len(telegram_result.result.failures)}")
                
            except Exception as e:
                error_msg = f"خطا در اجرای تست‌های ربات تلگرام: {str(e)}"
                log_file.write(f"{error_msg}\n")
                print(error_msg)
        
        # اجرای تست‌های پنل ادمین
        if 'admin' in test_types:
            log_file.write("\n== اجرای تست‌های استعلام قیمت پنل ادمین ==\n")
            print("\n=== اجرای تست‌های استعلام قیمت پنل ادمین ===")
            
            try:
                # ایمپورت تست پنل ادمین
                import test_admin_inquiry
                
                # مسیر فایل تمپ برای نتایج تست
                tmp_result_file = os.path.join(report_dir, f'admin_tmp_{timestamp}.log')
                
                # اجرای تست‌ها با خروجی به فایل تمپ
                original_stdout = sys.stdout
                with open(tmp_result_file, 'w', encoding='utf-8') as f:
                    sys.stdout = f
                    admin_result = unittest.main(module='test_admin_inquiry', exit=False)
                    sys.stdout = original_stdout
                
                # خواندن نتایج از فایل تمپ و اضافه کردن به فایل نتایج اصلی
                with open(tmp_result_file, 'r', encoding='utf-8') as f:
                    result_content = f.read()
                    log_file.write(result_content)
                    log_file.write("\n")
                
                # حذف فایل تمپ
                if os.path.exists(tmp_result_file):
                    os.remove(tmp_result_file)
                
                # جمع‌آوری آمار
                total_tests += admin_result.result.testsRun
                total_errors += len(admin_result.result.errors)
                total_failures += len(admin_result.result.failures)
                
                print(f"تعداد تست‌ها: {admin_result.result.testsRun}")
                print(f"خطاها: {len(admin_result.result.errors)}")
                print(f"شکست‌ها: {len(admin_result.result.failures)}")
                
            except Exception as e:
                error_msg = f"خطا در اجرای تست‌های پنل ادمین: {str(e)}"
                log_file.write(f"{error_msg}\n")
                print(error_msg)
        
        # نوشتن خلاصه نتایج
        log_file.write("\n=== خلاصه نتایج ===\n")
        log_file.write(f"کل تست‌ها: {total_tests}\n")
        log_file.write(f"تعداد خطاها: {total_errors}\n")
        log_file.write(f"تعداد شکست‌ها: {total_failures}\n")
        log_file.write(f"نتیجه کلی: {'موفق' if total_errors == 0 and total_failures == 0 else 'ناموفق'}\n")
        log_file.write(f"\n=== پایان تست‌ها - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    
    # نمایش مسیر فایل گزارش
    print(f"\n=== خلاصه نتایج ===")
    print(f"کل تست‌ها: {total_tests}")
    print(f"تعداد خطاها: {total_errors}")
    print(f"تعداد شکست‌ها: {total_failures}")
    print(f"نتیجه کلی: {'موفق' if total_errors == 0 and total_failures == 0 else 'ناموفق'}")
    print(f"\nنتایج کامل در فایل زیر ذخیره شده است:")
    print(f"{result_file}")
    
    return total_errors == 0 and total_failures == 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='اجرای تست‌های قابلیت استعلام قیمت')
    parser.add_argument(
        '--type', 
        choices=['all', 'telegram', 'admin'], 
        default='all',
        help='نوع تست‌ها برای اجرا (all, telegram, admin)'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='نمایش جزئیات بیشتر در خروجی'
    )
    
    args = parser.parse_args()
    
    test_types = [args.type]
    success = run_tests(test_types, args.verbose)
    
    # تنظیم کد خروجی بر اساس نتیجه تست‌ها
    sys.exit(0 if success else 1)