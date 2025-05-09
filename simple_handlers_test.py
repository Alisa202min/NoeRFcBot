#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست بسیار ساده برای بررسی وجود کلاس‌ها در ربات تلگرام
"""

import logging

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_imports():
    """بررسی وارد کردن ماژول‌های مورد نیاز"""
    success = True
    
    # بررسی کتابخانه‌های ضروری
    try:
        import aiogram
        from aiogram import Bot, Dispatcher
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        from aiogram.fsm.storage.memory import MemoryStorage
        
        logger.info("✅ کتابخانه aiogram به درستی نصب شده است")
    except ImportError as e:
        logger.error(f"❌ خطا در وارد کردن aiogram: {e}")
        success = False
    
    # بررسی ماژول‌های پروژه
    try:
        import app
        logger.info("✅ ماژول app با موفقیت وارد شد")
    except ImportError as e:
        logger.error(f"❌ خطا در وارد کردن app: {e}")
        success = False
    
    try:
        import models
        logger.info("✅ ماژول models با موفقیت وارد شد")
    except ImportError as e:
        logger.error(f"❌ خطا در وارد کردن models: {e}")
        success = False
    
    try:
        import handlers
        logger.info("✅ ماژول handlers با موفقیت وارد شد")
    except ImportError as e:
        logger.error(f"❌ خطا در وارد کردن handlers: {e}")
        success = False
    
    try:
        import keyboards
        logger.info("✅ ماژول keyboards با موفقیت وارد شد")
    except ImportError as e:
        logger.error(f"❌ خطا در وارد کردن keyboards: {e}")
        success = False
    
    return success

def check_user_states():
    """بررسی وجود کلاس UserStates"""
    try:
        from handlers import UserStates
        
        # بررسی حالت‌ها
        state_attrs = [
            'browse_categories', 
            'view_product', 
            'inquiry_name', 
            'inquiry_phone', 
            'inquiry_description',
            'waiting_for_confirmation'
        ]
        
        missing_attrs = []
        for attr in state_attrs:
            if not hasattr(UserStates, attr):
                missing_attrs.append(attr)
        
        if not missing_attrs:
            logger.info(f"✅ کلاس UserStates دارای تمام {len(state_attrs)} حالت مورد نیاز است")
            return True
        else:
            logger.error(f"❌ حالت‌های زیر در UserStates تعریف نشده‌اند: {', '.join(missing_attrs)}")
            return False
    except ImportError as e:
        logger.error(f"❌ خطا در وارد کردن UserStates: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ خطای نامشخص: {e}")
        return False

def check_handler_functions():
    """بررسی وجود توابع اصلی در ماژول handlers"""
    try:
        import handlers
        
        # توابع اصلی که باید بررسی شوند
        required_functions = [
            'cmd_start',
            'cmd_products',
            'cmd_services',
            'cmd_help',
            'cmd_about',
            'cmd_contact'
        ]
        
        missing_functions = []
        for func_name in required_functions:
            if not hasattr(handlers, func_name):
                missing_functions.append(func_name)
        
        if not missing_functions:
            logger.info(f"✅ ماژول handlers دارای تمام {len(required_functions)} تابع مورد نیاز است")
            return True
        else:
            logger.error(f"❌ توابع زیر در ماژول handlers تعریف نشده‌اند: {', '.join(missing_functions)}")
            return False
    except ImportError as e:
        logger.error(f"❌ خطا در وارد کردن ماژول handlers: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ خطای نامشخص: {e}")
        return False

def check_keyboard_functions():
    """بررسی وجود توابع اصلی در ماژول keyboards"""
    try:
        import keyboards
        
        # توابع اصلی کیبورد که باید بررسی شوند
        required_functions = [
            'main_menu_keyboard',
            'categories_keyboard',
            'products_keyboard',
            'product_detail_keyboard'
        ]
        
        missing_functions = []
        for func_name in required_functions:
            if not hasattr(keyboards, func_name):
                missing_functions.append(func_name)
        
        if not missing_functions:
            logger.info(f"✅ ماژول keyboards دارای تمام {len(required_functions)} تابع مورد نیاز است")
            return True
        else:
            logger.error(f"❌ توابع زیر در ماژول keyboards تعریف نشده‌اند: {', '.join(missing_functions)}")
            return False
    except ImportError as e:
        logger.error(f"❌ خطا در وارد کردن ماژول keyboards: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ خطای نامشخص: {e}")
        return False

def main():
    """تابع اصلی"""
    print("===== تست ساده ربات تلگرام =====")
    
    tests = [
        ("وارد کردن ماژول‌ها", check_imports),
        ("کلاس UserStates", check_user_states),
        ("توابع handlers", check_handler_functions),
        ("توابع keyboards", check_keyboard_functions)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n--- تست {name} ---")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"❌ خطای پیش‌بینی نشده در تست {name}: {e}")
            failed += 1
    
    print("\n===== نتایج تست‌ها =====")
    print(f"تعداد کل تست‌ها: {len(tests)}")
    print(f"تست‌های موفق: {passed}")
    print(f"تست‌های ناموفق: {failed}")
    
    print("\n===== پایان تست‌های ساده ربات تلگرام =====")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)