#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست ساده برای handlers ربات تلگرام بدون نیاز به اتصال به API تلگرام
"""

import sys
import logging
from app import app
from handlers import UserStates

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_user_states():
    """تست حالت‌های کاربر در FSM"""
    try:
        # بررسی تعریف حالت‌ها
        states = [
            UserStates.browse_categories,
            UserStates.view_product,
            UserStates.view_category,
            UserStates.view_educational_content,
            UserStates.inquiry_name,
            UserStates.inquiry_phone,
            UserStates.inquiry_description,
            UserStates.waiting_for_confirmation
        ]
        
        # بررسی نام‌های حالت‌ها
        for state in states:
            logger.info(f"✅ حالت: {state.state}")
        
        logger.info(f"✅ تمام {len(states)} حالت با موفقیت بررسی شدند")
        return True
    except Exception as e:
        logger.error(f"❌ خطا در تست حالت‌های کاربر: {e}")
        return False

def test_handlers_import():
    """تست وارد کردن توابع handlers"""
    try:
        import handlers
        
        # بررسی وجود روتر
        router = getattr(handlers, 'router', None)
        assert router is not None, "روتر در ماژول handlers تعریف نشده است"
        logger.info("✅ روتر ربات به درستی تعریف شده است")
        
        # بررسی توابع اصلی
        assert hasattr(handlers, 'cmd_start'), "تابع cmd_start تعریف نشده است"
        assert hasattr(handlers, 'cmd_products'), "تابع cmd_products تعریف نشده است"
        assert hasattr(handlers, 'cmd_services'), "تابع cmd_services تعریف نشده است"
        
        logger.info("✅ توابع اصلی handlers به درستی تعریف شده‌اند")
        return True
    except Exception as e:
        logger.error(f"❌ خطا در تست وارد کردن handlers: {e}")
        return False

def test_keyboards_import():
    """تست وارد کردن کیبوردها"""
    try:
        import keyboards
        
        # بررسی توابع اصلی کیبورد
        assert hasattr(keyboards, 'get_main_keyboard'), "تابع get_main_keyboard تعریف نشده است"
        assert hasattr(keyboards, 'get_back_button'), "تابع get_back_button تعریف نشده است"
        
        # ایجاد و بررسی کیبورد اصلی
        main_kb = keyboards.get_main_keyboard()
        assert main_kb is not None, "کیبورد اصلی ایجاد نشد"
        
        logger.info("✅ کیبوردها به درستی تعریف شده‌اند")
        return True
    except Exception as e:
        logger.error(f"❌ خطا در تست وارد کردن کیبوردها: {e}")
        return False

def test_bot_config():
    """تست پیکربندی ربات"""
    try:
        import os
        import dotenv
        
        # بارگذاری متغیرهای محیطی
        dotenv.load_dotenv()
        
        # بررسی توکن ربات
        bot_token = os.getenv('BOT_TOKEN')
        assert bot_token, "BOT_TOKEN در متغیرهای محیطی تعریف نشده است"
        
        # بررسی پارامترهای مسیر Webhook (در صورت استفاده)
        webhook_host = os.getenv('WEBHOOK_HOST')
        if webhook_host:
            logger.info(f"✅ WEBHOOK_HOST: {webhook_host}")
            
            webhook_path = os.getenv('WEBHOOK_PATH')
            if webhook_path:
                logger.info(f"✅ WEBHOOK_PATH: {webhook_path}")
        else:
            logger.info("ℹ️ حالت webhook تنظیم نشده است - ربات احتمالاً در حالت polling اجرا می‌شود")
        
        logger.info("✅ پیکربندی ربات به درستی انجام شده است")
        return True
    except Exception as e:
        logger.error(f"❌ خطا در تست پیکربندی ربات: {e}")
        return False

def run_all_tests():
    """اجرای تمام تست‌ها و نمایش نتایج"""
    print("===== شروع تست‌های handlers =====")
    
    with app.app_context():
        tests = {
            "حالت‌های کاربر": test_user_states,
            "وارد کردن handlers": test_handlers_import,
            "وارد کردن کیبوردها": test_keyboards_import,
            "پیکربندی ربات": test_bot_config
        }
        
        results = {}
        for name, test_func in tests.items():
            print(f"\n--- تست {name} ---")
            try:
                result = test_func()
                results[name] = result
            except Exception as e:
                logger.error(f"❌ خطای پیش‌بینی نشده در تست {name}: {e}")
                results[name] = False
        
        # نمایش نتایج
        print("\n===== نتایج تست‌ها =====")
        passed = sum(1 for result in results.values() if result)
        failed = len(results) - passed
        
        print(f"تعداد کل تست‌ها: {len(results)}")
        print(f"تست‌های موفق: {passed}")
        print(f"تست‌های ناموفق: {failed}")
        
        if failed > 0:
            print("\nتست‌های ناموفق:")
            for name, result in results.items():
                if not result:
                    print(f"❌ {name}")
        
        print("\n===== پایان تست‌های handlers =====")
        return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)