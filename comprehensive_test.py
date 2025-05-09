#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست جامع سیستم
این اسکریپت تمام بخش‌های اصلی سیستم را تست می‌کند:
- ساختار دیتابیس (همه جداول)
- داده‌های آزمایشی
- مدل‌های SQLAlchemy
- عملکرد اصلی
"""

import os
import sys
import logging
import asyncio
from app import app, db
from sqlalchemy.exc import SQLAlchemyError
from models import User, Product, Category, Inquiry, ProductMedia, EducationalContent, StaticContent

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestResult:
    """نگهداری نتایج تست‌ها"""
    def __init__(self):
        self.passed = []
        self.failed = []
    
    def add_pass(self, test_name):
        """افزودن تست موفق"""
        self.passed.append(test_name)
        logger.info(f"✅ {test_name}: موفق")
    
    def add_fail(self, test_name, error):
        """افزودن تست ناموفق"""
        self.failed.append((test_name, error))
        logger.error(f"❌ {test_name}: ناموفق - {error}")
    
    def summary(self):
        """نمایش خلاصه نتایج"""
        total = len(self.passed) + len(self.failed)
        print(f"\n=== خلاصه نتایج ({len(self.passed)}/{total} موفق) ===")
        
        if self.passed:
            print("\nتست‌های موفق:")
            for i, test in enumerate(self.passed, 1):
                print(f"{i}. ✅ {test}")
        
        if self.failed:
            print("\nتست‌های ناموفق:")
            for i, (test, error) in enumerate(self.failed, 1):
                print(f"{i}. ❌ {test}: {error}")
        
        success_rate = len(self.passed) / total * 100 if total > 0 else 0
        print(f"\nنرخ موفقیت: {success_rate:.2f}%")

def test_database_structure():
    """تست ساختار دیتابیس"""
    result = TestResult()
    
    with app.app_context():
        # تست جدول User
        try:
            users = User.query.all()
            result.add_pass(f"جدول User ({len(users)} رکورد)")
        except SQLAlchemyError as e:
            result.add_fail("جدول User", str(e))
        
        # تست جدول Category
        try:
            categories = Category.query.all()
            parent_categories = Category.query.filter_by(parent_id=None).all()
            result.add_pass(f"جدول Category ({len(categories)} رکورد، {len(parent_categories)} دسته اصلی)")
        except SQLAlchemyError as e:
            result.add_fail("جدول Category", str(e))
        
        # تست جدول Product
        try:
            products = Product.query.all()
            products_count = Product.query.filter_by(product_type='product').count()
            services_count = Product.query.filter_by(product_type='service').count()
            result.add_pass(f"جدول Product ({products_count} محصول، {services_count} خدمت)")
        except SQLAlchemyError as e:
            result.add_fail("جدول Product", str(e))
        
        # تست جدول ProductMedia
        try:
            media = ProductMedia.query.all()
            result.add_pass(f"جدول ProductMedia ({len(media)} رکورد)")
        except SQLAlchemyError as e:
            result.add_fail("جدول ProductMedia", str(e))
        
        # تست جدول Inquiry
        try:
            inquiries = Inquiry.query.all()
            result.add_pass(f"جدول Inquiry ({len(inquiries)} رکورد)")
        except SQLAlchemyError as e:
            result.add_fail("جدول Inquiry", str(e))
        
        # تست جدول EducationalContent
        try:
            edu_content = EducationalContent.query.all()
            result.add_pass(f"جدول EducationalContent ({len(edu_content)} رکورد)")
        except SQLAlchemyError as e:
            result.add_fail("جدول EducationalContent", str(e))
        
        # تست جدول StaticContent
        try:
            static_content = StaticContent.query.all()
            result.add_pass(f"جدول StaticContent ({len(static_content)} رکورد)")
        except SQLAlchemyError as e:
            result.add_fail("جدول StaticContent", str(e))
    
    return result

def test_models():
    """تست مدل‌های SQLAlchemy"""
    result = TestResult()
    
    with app.app_context():
        # تست ارتباطات Product و Category
        try:
            product = Product.query.first()
            if product:
                category = Category.query.get(product.category_id)
                if category:
                    result.add_pass(f"ارتباط Product-Category (محصول '{product.name}' در دسته '{category.name}')")
                else:
                    result.add_fail("ارتباط Product-Category", "دسته‌بندی مرتبط یافت نشد")
            else:
                result.add_fail("ارتباط Product-Category", "محصولی در دیتابیس یافت نشد")
        except Exception as e:
            result.add_fail("ارتباط Product-Category", str(e))
        
        # تست ارتباطات Category والد-فرزند
        try:
            parent_category = Category.query.filter(Category.parent_id.is_(None)).first()
            if parent_category:
                children = Category.query.filter_by(parent_id=parent_category.id).all()
                result.add_pass(f"ارتباط Category والد-فرزند (دسته '{parent_category.name}' دارای {len(children)} زیردسته)")
            else:
                result.add_fail("ارتباط Category والد-فرزند", "دسته‌بندی اصلی یافت نشد")
        except Exception as e:
            result.add_fail("ارتباط Category والد-فرزند", str(e))
        
        # تست ارتباطات Product و ProductMedia
        try:
            product = Product.query.first()
            if product:
                media = ProductMedia.query.filter_by(product_id=product.id).all()
                result.add_pass(f"ارتباط Product-ProductMedia (محصول '{product.name}' دارای {len(media)} رسانه)")
            else:
                result.add_fail("ارتباط Product-ProductMedia", "محصولی در دیتابیس یافت نشد")
        except Exception as e:
            result.add_fail("ارتباط Product-ProductMedia", str(e))
        
        # تست ارتباطات Product و Inquiry
        try:
            product = Product.query.first()
            if product:
                inquiries = Inquiry.query.filter_by(product_id=product.id).all()
                result.add_pass(f"ارتباط Product-Inquiry (محصول '{product.name}' دارای {len(inquiries)} استعلام)")
            else:
                result.add_fail("ارتباط Product-Inquiry", "محصولی در دیتابیس یافت نشد")
        except Exception as e:
            result.add_fail("ارتباط Product-Inquiry", str(e))
    
    return result

def test_data():
    """تست داده‌های آزمایشی"""
    result = TestResult()
    
    with app.app_context():
        # بررسی وجود کاربر مدیر
        try:
            admin = User.query.filter_by(username='admin').first()
            if admin:
                result.add_pass("وجود کاربر admin")
            else:
                result.add_fail("وجود کاربر admin", "کاربر admin یافت نشد")
        except Exception as e:
            result.add_fail("وجود کاربر admin", str(e))
        
        # بررسی وجود دسته‌بندی‌های اصلی
        try:
            categories = Category.query.filter(Category.parent_id.is_(None)).all()
            if len(categories) >= 3:
                result.add_pass(f"وجود دسته‌بندی‌های اصلی ({len(categories)} دسته)")
            else:
                result.add_fail("وجود دسته‌بندی‌های اصلی", f"تعداد کافی دسته‌بندی اصلی وجود ندارد ({len(categories)})")
        except Exception as e:
            result.add_fail("وجود دسته‌بندی‌های اصلی", str(e))
        
        # بررسی وجود محصولات
        try:
            products = Product.query.filter_by(product_type='product').all()
            if len(products) >= 5:
                result.add_pass(f"وجود محصولات ({len(products)} محصول)")
            else:
                result.add_fail("وجود محصولات", f"تعداد کافی محصول وجود ندارد ({len(products)})")
        except Exception as e:
            result.add_fail("وجود محصولات", str(e))
        
        # بررسی وجود خدمات
        try:
            services = Product.query.filter_by(product_type='service').all()
            if len(services) >= 2:
                result.add_pass(f"وجود خدمات ({len(services)} خدمت)")
            else:
                result.add_fail("وجود خدمات", f"تعداد کافی خدمت وجود ندارد ({len(services)})")
        except Exception as e:
            result.add_fail("وجود خدمات", str(e))
        
        # بررسی وجود محتوای آموزشی
        try:
            edu_content = EducationalContent.query.all()
            if len(edu_content) >= 2:
                result.add_pass(f"وجود محتوای آموزشی ({len(edu_content)} مورد)")
            else:
                result.add_fail("وجود محتوای آموزشی", f"تعداد کافی محتوای آموزشی وجود ندارد ({len(edu_content)})")
        except Exception as e:
            result.add_fail("وجود محتوای آموزشی", str(e))
        
        # بررسی وجود محتوای ثابت (about, contact)
        try:
            about = StaticContent.query.filter_by(type='about').first()
            contact = StaticContent.query.filter_by(type='contact').first()
            if about and contact:
                result.add_pass("وجود محتوای ثابت (about و contact)")
            else:
                missing = []
                if not about:
                    missing.append('about')
                if not contact:
                    missing.append('contact')
                result.add_fail("وجود محتوای ثابت", f"محتوای {', '.join(missing)} یافت نشد")
        except Exception as e:
            result.add_fail("وجود محتوای ثابت", str(e))
    
    return result

def test_functionality():
    """تست عملکرد اصلی سیستم"""
    result = TestResult()
    
    # تست وجود ماژول‌های مورد نیاز
    try:
        import handlers
        import keyboards
        import bot
        result.add_pass("وجود ماژول‌های اصلی (handlers, keyboards, bot)")
    except ImportError as e:
        result.add_fail("وجود ماژول‌های اصلی", str(e))
    
    # تست وجود توابع اصلی در handlers
    try:
        from handlers import cmd_start, cmd_products, cmd_services, cmd_about, cmd_contact
        result.add_pass("وجود توابع اصلی در handlers")
    except ImportError as e:
        result.add_fail("وجود توابع اصلی در handlers", str(e))
    
    # تست وجود توابع اصلی در keyboards
    try:
        from keyboards import main_menu_keyboard, categories_keyboard, products_keyboard
        result.add_pass("وجود توابع اصلی در keyboards")
    except ImportError as e:
        result.add_fail("وجود توابع اصلی در keyboards", str(e))
    
    # تست وجود توابع اصلی در bot
    try:
        from bot import start_polling, register_handlers
        result.add_pass("وجود توابع اصلی در bot")
    except ImportError as e:
        result.add_fail("وجود توابع اصلی در bot", str(e))
    
    # تست متغیرهای محیطی
    try:
        bot_token = os.environ.get('BOT_TOKEN')
        database_url = os.environ.get('DATABASE_URL')
        
        if bot_token and database_url:
            result.add_pass("وجود متغیرهای محیطی ضروری (BOT_TOKEN, DATABASE_URL)")
        else:
            missing = []
            if not bot_token:
                missing.append('BOT_TOKEN')
            if not database_url:
                missing.append('DATABASE_URL')
            result.add_fail("وجود متغیرهای محیطی ضروری", f"متغیرهای {', '.join(missing)} تنظیم نشده‌اند")
    except Exception as e:
        result.add_fail("وجود متغیرهای محیطی ضروری", str(e))
    
    # تست بررسی وضعیت webhook
    async def check_webhook():
        try:
            from aiogram import Bot
            bot = Bot(token=os.environ.get('BOT_TOKEN'))
            webhook_info = await bot.get_webhook_info()
            await bot.session.close()
            
            if webhook_info:
                if webhook_info.url:
                    result.add_pass(f"وضعیت webhook (فعال: {webhook_info.url})")
                else:
                    result.add_pass("وضعیت webhook (غیرفعال - قابل استفاده در حالت polling)")
            else:
                result.add_fail("وضعیت webhook", "خطا در دریافت اطلاعات webhook")
        except Exception as e:
            result.add_fail("وضعیت webhook", str(e))
    
    # اجرای تست‌های ناهمگام
    asyncio.run(check_webhook())
    
    return result

def main():
    """اجرای تمام تست‌ها"""
    print("===== شروع تست جامع سیستم =====")
    
    # اجرای تست‌ها
    print("\n--- تست ساختار دیتابیس ---")
    db_result = test_database_structure()
    
    print("\n--- تست مدل‌های SQLAlchemy ---")
    model_result = test_models()
    
    print("\n--- تست داده‌های آزمایشی ---")
    data_result = test_data()
    
    print("\n--- تست عملکرد اصلی ---")
    func_result = test_functionality()
    
    # ادغام نتایج
    all_results = TestResult()
    all_results.passed = db_result.passed + model_result.passed + data_result.passed + func_result.passed
    all_results.failed = db_result.failed + model_result.failed + data_result.failed + func_result.failed
    
    # نمایش نتایج
    all_results.summary()
    
    print("\n===== پایان تست جامع سیستم =====")
    
    # خروجی
    return len(all_results.failed) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)