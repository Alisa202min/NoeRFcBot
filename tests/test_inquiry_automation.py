#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
اسکریپت اتوماتیک اجرای تست‌های استعلام قیمت و گزارش‌گیری

این اسکریپت تمام تست‌های مربوط به استعلام قیمت (هم ربات تلگرام و هم پنل ادمین) را اجرا 
کرده و نتایج را به صورت خودکار گزارش می‌دهد.
"""

import os
import sys
import asyncio
import unittest
import importlib
import logging
import argparse
import traceback
from datetime import datetime

# اضافه کردن مسیر فعلی به پایتون پث
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ایمپورت ماژول‌های مورد نیاز
from test_logger import TestLogger

# تنظیم لاگر
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

class InquiryTestAutomation:
    """کلاس اتوماسیون تست‌های استعلام قیمت"""
    
    def __init__(self, components=None, verbose=False, html_report=True):
        """مقداردهی اولیه
        
        پارامترها:
            components (list): لیست کامپوننت‌هایی که باید تست شوند
            verbose (bool): نمایش جزئیات بیشتر
            html_report (bool): تولید گزارش HTML
        """
        self.components = components or ['telegram', 'admin']
        self.verbose = verbose
        self.html_report = html_report
        
        # تنظیم سطح لاگ
        if self.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # ساختار نگهداری نتایج تست‌ها
        self.results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'components': {},
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'error_tests': 0,
            'report_files': []
        }
    
    async def run_telegram_tests(self):
        """اجرای تست‌های مربوط به ربات تلگرام"""
        logger.info("=== اجرای تست‌های استعلام قیمت ربات تلگرام ===")
        
        test_logger = TestLogger("استعلام قیمت ربات تلگرام", "telegram")
        
        try:
            # ایمپورت ماژول تست تلگرام
            telegram_tests = importlib.import_module('test_telegram_inquiry')
            
            # لیست تمام تست‌های تلگرام
            test_cases = []
            for attr in dir(telegram_tests.TestTelegramInquiry):
                if attr.startswith('test_'):
                    test_case = getattr(telegram_tests.TestTelegramInquiry, attr)
                    test_cases.append((attr, test_case))
            
            # اجرای هر تست
            for test_name, test_case in test_cases:
                logger.info(f"در حال اجرای تست: {test_name}")
                
                try:
                    # ایجاد نمونه تست
                    test_instance = telegram_tests.TestTelegramInquiry()
                    
                    # ایجاد یک لوپ جدید برای هر تست
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        # اجرای تست با تایم‌اوت
                        loop.run_until_complete(asyncio.wait_for(test_case(test_instance), timeout=30))
                        
                        # ثبت نتیجه موفق
                        test_logger.log_test_case(test_name, "pass")
                    except asyncio.TimeoutError:
                        # ثبت خطای تایم‌اوت
                        test_logger.log_test_case(test_name, "error", "تست به دلیل تایم‌اوت متوقف شد (احتمالاً به دلیل انتظار برای پاسخ API تلگرام)")
                    finally:
                        # بستن لوپ
                        loop.close()
                    
                except AssertionError as e:
                    # ثبت شکست تست
                    test_logger.log_test_case(test_name, "fail", str(e))
                    
                except Exception as e:
                    # ثبت خطای تست
                    error_details = traceback.format_exc()
                    test_logger.log_test_case(test_name, "error", str(e), {"traceback": error_details})
            
            # تکمیل تست‌ها و تولید گزارش
            results = test_logger.finish()
            
            if self.html_report:
                html_report = test_logger.create_html_report()
                self.results['report_files'].append(html_report)
            
            # اضافه کردن نتایج به گزارش کلی
            self.results['components']['telegram'] = results
            self.results['total_tests'] += results['total_tests']
            self.results['passed_tests'] += results['passed_tests']
            self.results['failed_tests'] += results['failed_tests']
            self.results['error_tests'] += results['error_tests']
            
            return True
            
        except Exception as e:
            logger.error(f"خطا در اجرای تست‌های تلگرام: {str(e)}")
            logger.error(traceback.format_exc())
            
            # ثبت خطای کلی
            test_logger.log_test_case("telegram_tests_setup", "error", str(e))
            test_logger.finish()
            
            if self.html_report:
                html_report = test_logger.create_html_report()
                self.results['report_files'].append(html_report)
            
            return False
    
    def run_admin_tests(self):
        """اجرای تست‌های مربوط به پنل ادمین"""
        logger.info("=== اجرای تست‌های استعلام قیمت پنل ادمین ===")
        
        test_logger = TestLogger("استعلام قیمت پنل ادمین", "admin")
        
        try:
            # ایجاد لودر تست
            loader = unittest.TestLoader()
            
            # بارگذاری تست‌های پنل ادمین
            test_suite = loader.loadTestsFromName('test_admin_inquiry')
            
            # ایجاد TestResult سفارشی برای ذخیره نتایج
            class CustomTestResult(unittest.TestResult):
                def __init__(self, test_logger):
                    super().__init__()
                    self.test_logger = test_logger
                
                def addSuccess(self, test):
                    super().addSuccess(test)
                    test_name = test._testMethodName
                    self.test_logger.log_test_case(test_name, "pass")
                
                def addFailure(self, test, err):
                    super().addFailure(test, err)
                    test_name = test._testMethodName
                    error_message = str(err[1])
                    self.test_logger.log_test_case(test_name, "fail", error_message)
                
                def addError(self, test, err):
                    super().addError(test, err)
                    test_name = test._testMethodName
                    error_message = str(err[1])
                    error_traceback = traceback.format_exception(*err)
                    self.test_logger.log_test_case(test_name, "error", error_message, {"traceback": error_traceback})
            
            # اجرای تست‌ها
            test_result = CustomTestResult(test_logger)
            test_suite.run(test_result)
            
            # تکمیل تست‌ها و تولید گزارش
            results = test_logger.finish()
            
            if self.html_report:
                html_report = test_logger.create_html_report()
                self.results['report_files'].append(html_report)
            
            # اضافه کردن نتایج به گزارش کلی
            self.results['components']['admin'] = results
            self.results['total_tests'] += results['total_tests']
            self.results['passed_tests'] += results['passed_tests']
            self.results['failed_tests'] += results['failed_tests']
            self.results['error_tests'] += results['error_tests']
            
            return True
            
        except Exception as e:
            logger.error(f"خطا در اجرای تست‌های پنل ادمین: {str(e)}")
            logger.error(traceback.format_exc())
            
            # ثبت خطای کلی
            test_logger.log_test_case("admin_tests_setup", "error", str(e))
            test_logger.finish()
            
            if self.html_report:
                html_report = test_logger.create_html_report()
                self.results['report_files'].append(html_report)
            
            return False
    
    async def run_all_tests(self):
        """اجرای تمامی تست‌ها"""
        logger.info("=== شروع اجرای خودکار تست‌های استعلام قیمت ===")
        
        # اجرای تست‌های ربات تلگرام
        if 'telegram' in self.components:
            await self.run_telegram_tests()
        
        # اجرای تست‌های پنل ادمین
        if 'admin' in self.components:
            self.run_admin_tests()
        
        # نمایش خلاصه نتایج
        self.show_summary()
        
        return self.results
    
    def show_summary(self):
        """نمایش خلاصه نتایج تست‌ها"""
        logger.info("\n=== خلاصه نتایج تست‌های استعلام قیمت ===")
        logger.info(f"تعداد کل تست‌ها: {self.results['total_tests']}")
        logger.info(f"تست‌های موفق: {self.results['passed_tests']}")
        logger.info(f"تست‌های ناموفق: {self.results['failed_tests']}")
        logger.info(f"تست‌های با خطا: {self.results['error_tests']}")
        
        success_rate = 0
        if self.results['total_tests'] > 0:
            success_rate = (self.results['passed_tests'] / self.results['total_tests']) * 100
        
        logger.info(f"نرخ موفقیت: {success_rate:.2f}%")
        logger.info(f"نتیجه کلی: {'موفق' if self.results['failed_tests'] == 0 and self.results['error_tests'] == 0 else 'ناموفق'}")
        
        if self.html_report and self.results['report_files']:
            logger.info("\nگزارش‌های HTML:")
            for report_file in self.results['report_files']:
                logger.info(f"- {report_file}")


# اجرای اسکریپت
async def main():
    parser = argparse.ArgumentParser(description='اسکریپت اتوماتیک اجرای تست‌های استعلام قیمت')
    parser.add_argument(
        '--components', 
        nargs='+',
        choices=['all', 'telegram', 'admin'], 
        default=['all'],
        help='کامپوننت‌هایی که باید تست شوند'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='نمایش جزئیات بیشتر در خروجی'
    )
    parser.add_argument(
        '--no-html', 
        action='store_true',
        help='عدم تولید گزارش HTML'
    )
    
    args = parser.parse_args()
    
    # تعیین کامپوننت‌های تست
    if 'all' in args.components:
        components = ['telegram', 'admin']
    else:
        components = args.components
    
    # اجرای تست‌ها
    automation = InquiryTestAutomation(
        components=components,
        verbose=args.verbose,
        html_report=not args.no_html
    )
    
    results = await automation.run_all_tests()
    
    # تنظیم کد خروجی بر اساس نتیجه تست‌ها
    if results['failed_tests'] > 0 or results['error_tests'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())