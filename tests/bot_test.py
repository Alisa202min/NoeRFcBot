#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست ساده ربات تلگرام - کاملاً مستقل از API تلگرام
"""

import os
import sys
import unittest
import logging
from datetime import datetime
from app import app

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestTelegramBot(unittest.TestCase):
    """تست‌های ساده ربات تلگرام"""
    
    def setUp(self):
        """آماده‌سازی تست"""
        self.app_context = app.app_context()
        self.app_context.push()
        self.test_passed = []
        self.test_failed = []
    
    def tearDown(self):
        """پاکسازی بعد از اتمام تست"""
        self.app_context.pop()
    
    def test_environment_variables(self):
        """تست متغیرهای محیطی مورد نیاز"""
        print("\n=== تست متغیرهای محیطی ===")
        
        # تست وجود توکن ربات تلگرام
        bot_token = os.environ.get('BOT_TOKEN')
        self.assertIsNotNone(bot_token, "BOT_TOKEN باید در متغیرهای محیطی تنظیم شده باشد")
        self.assertGreater(len(bot_token), 20, "طول BOT_TOKEN باید بیشتر از 20 کاراکتر باشد")
        print(f"✅ BOT_TOKEN موجود است: {bot_token[:5]}...{bot_token[-5:]}")
        self.test_passed.append("تست وجود BOT_TOKEN")
        
        # تست وجود DATABASE_URL
        database_url = os.environ.get('DATABASE_URL')
        self.assertIsNotNone(database_url, "DATABASE_URL باید در متغیرهای محیطی تنظیم شده باشد")
        self.assertIn('postgresql', database_url, "DATABASE_URL باید به یک دیتابیس PostgreSQL اشاره کند")
        print(f"✅ DATABASE_URL موجود است و به PostgreSQL اشاره می‌کند")
        self.test_passed.append("تست وجود DATABASE_URL")

    def test_bot_module_imports(self):
        """تست وارد کردن ماژول‌های مورد نیاز ربات"""
        print("\n=== تست ماژول‌های ربات ===")
        
        try:
            from aiogram import Bot, Dispatcher
            print("✅ ماژول aiogram با موفقیت وارد شد")
            self.test_passed.append("تست وارد کردن aiogram")
        except ImportError as e:
            print(f"❌ خطا در وارد کردن aiogram: {e}")
            self.test_failed.append(f"تست وارد کردن aiogram: {e}")
            self.fail(f"خطا در وارد کردن aiogram: {e}")
        
        try:
            import handlers
            print("✅ ماژول handlers با موفقیت وارد شد")
            self.test_passed.append("تست وارد کردن handlers")
        except ImportError as e:
            print(f"❌ خطا در وارد کردن handlers: {e}")
            self.test_failed.append(f"تست وارد کردن handlers: {e}")
            self.fail(f"خطا در وارد کردن handlers: {e}")
        
        try:
            import keyboards
            print("✅ ماژول keyboards با موفقیت وارد شد")
            self.test_passed.append("تست وارد کردن keyboards")
        except ImportError as e:
            print(f"❌ خطا در وارد کردن keyboards: {e}")
            self.test_failed.append(f"تست وارد کردن keyboards: {e}")
            self.fail(f"خطا در وارد کردن keyboards: {e}")

    def test_database_models(self):
        """تست مدل‌های دیتابیس"""
        print("\n=== تست مدل‌های دیتابیس ===")

        try:
            from models import User, Product, Category, Inquiry, ProductMedia
            
            # تست مدل User
            users = User.query.all()
            print(f"✅ تعداد کاربران: {len(users)}")
            self.test_passed.append("تست مدل User")
            
            # تست مدل Category
            categories = Category.query.all()
            print(f"✅ تعداد دسته‌بندی‌ها: {len(categories)}")
            self.test_passed.append("تست مدل Category")
            
            # تست مدل Product
            products = Product.query.all()
            print(f"✅ تعداد محصولات: {len(products)}")
            self.test_passed.append("تست مدل Product")
            
            # تست مدل ProductMedia
            medias = ProductMedia.query.all()
            print(f"✅ تعداد رسانه‌ها: {len(medias)}")
            self.test_passed.append("تست مدل ProductMedia")
            
            # تست مدل Inquiry
            inquiries = Inquiry.query.all()
            print(f"✅ تعداد استعلام‌ها: {len(inquiries)}")
            self.test_passed.append("تست مدل Inquiry")
            
        except Exception as e:
            print(f"❌ خطا در تست مدل‌های دیتابیس: {e}")
            self.test_failed.append(f"تست مدل‌های دیتابیس: {e}")
            self.fail(f"خطا در تست مدل‌های دیتابیس: {e}")

    def test_handler_utils(self):
        """تست ابزارهای کمکی handlers"""
        print("\n=== تست ابزارهای handlers ===")
        
        try:
           
            
            # تست کلاس UserStates
            self.assertIsNotNone(UserStates.browse_categories, "حالت browse_categories باید تعریف شده باشد")
            self.assertIsNotNone(UserStates.view_product, "حالت view_product باید تعریف شده باشد")
            self.assertIsNotNone(UserStates.inquiry_name, "حالت inquiry_name باید تعریف شده باشد")
            print("✅ حالت‌های FSM به درستی تعریف شده‌اند")
            self.test_passed.append("تست حالت‌های FSM")
            
            # تست وجود روتر
            self.assertIsNotNone(handlers.router, "روتر ربات باید تعریف شده باشد")
            print("✅ روتر ربات به درستی تعریف شده است")
            self.test_passed.append("تست روتر ربات")
            
        except Exception as e:
            print(f"❌ خطا در تست ابزارهای handlers: {e}")
            self.test_failed.append(f"تست ابزارهای handlers: {e}")
            self.fail(f"خطا در تست ابزارهای handlers: {e}")
            
    def test_keyboard_utils(self):
        """تست ابزارهای کمکی keyboards"""
        print("\n=== تست ابزارهای keyboards ===")
        
        try:
            import keyboards
            
            # تست تابع ایجاد کیبورد اصلی
            main_kb = keyboards.get_main_keyboard()
            self.assertIsNotNone(main_kb, "کیبورد اصلی باید ایجاد شود")
            print("✅ کیبورد اصلی به درستی ایجاد می‌شود")
            self.test_passed.append("تست کیبورد اصلی")
            
        except Exception as e:
            print(f"❌ خطا در تست ابزارهای keyboards: {e}")
            self.test_failed.append(f"تست ابزارهای keyboards: {e}")
            self.fail(f"خطا در تست ابزارهای keyboards: {e}")
    
    def print_summary(self):
        """نمایش خلاصه نتایج تست‌ها"""
        print("\n===== خلاصه نتایج تست‌ها =====")
        print(f"تعداد تست‌های موفق: {len(self.test_passed)}")
        print(f"تعداد تست‌های ناموفق: {len(self.test_failed)}")
        
        if self.test_passed:
            print("\nتست‌های موفق:")
            for i, test in enumerate(self.test_passed, 1):
                print(f"{i}. ✅ {test}")
        
        if self.test_failed:
            print("\nتست‌های ناموفق:")
            for i, test in enumerate(self.test_failed, 1):
                print(f"{i}. ❌ {test}")
        
        success_rate = len(self.test_passed) / (len(self.test_passed) + len(self.test_failed)) * 100 if (len(self.test_passed) + len(self.test_failed)) > 0 else 0
        print(f"\nنرخ موفقیت: {success_rate:.2f}%")

def run_tests():
    """اجرای تست‌ها با خروجی سفارشی"""
    test_suite = unittest.TestSuite()
    test_suite.addTest(TestTelegramBot('test_environment_variables'))
    test_suite.addTest(TestTelegramBot('test_bot_module_imports'))
    test_suite.addTest(TestTelegramBot('test_database_models'))
    test_suite.addTest(TestTelegramBot('test_handler_utils'))
    test_suite.addTest(TestTelegramBot('test_keyboard_utils'))
    
    # اجرای تست‌ها
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # نمایش خلاصه نتایج
    test_bot = TestTelegramBot()
    test_bot.test_passed = [str(test).split()[0] for test in result.successes] if hasattr(result, 'successes') else []
    test_bot.test_failed = [str(test[0]).split()[0] for test in result.failures]
    test_bot.print_summary()
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("===== شروع تست‌های ربات تلگرام =====")
    success = run_tests()
    print("\n===== پایان تست‌های ربات تلگرام =====")
    sys.exit(0 if success else 1)