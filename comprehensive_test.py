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
from datetime import datetime
from sqlalchemy import inspect, text
from app import app, db
from models import User, Category, Product, ProductMedia, Inquiry, EducationalContent, StaticContent

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestResult:
    """نگهداری نتایج تست‌ها"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.failures = []
    
    def add_pass(self, test_name):
        """افزودن تست موفق"""
        self.total += 1
        self.passed += 1
        logger.info(f"✓ {test_name}")
    
    def add_fail(self, test_name, error):
        """افزودن تست ناموفق"""
        self.total += 1
        self.failed += 1
        self.failures.append(f"{test_name}: {error}")
        logger.error(f"✗ {test_name}: {error}")
    
    def summary(self):
        """نمایش خلاصه نتایج"""
        success_rate = (self.passed / self.total) * 100 if self.total > 0 else 0
        logger.info(f"\n===== نتایج تست =====")
        logger.info(f"تعداد کل تست‌ها: {self.total}")
        logger.info(f"تست‌های موفق: {self.passed}")
        logger.info(f"تست‌های ناموفق: {self.failed}")
        logger.info(f"نرخ موفقیت: {success_rate:.2f}%")
        
        if self.failed > 0:
            logger.error("لیست خطاها:")
            for i, failure in enumerate(self.failures, 1):
                logger.error(f"{i}. {failure}")
        
        logger.info("======================")
        
        return self.failed == 0

def test_database_structure():
    """تست ساختار دیتابیس"""
    results = TestResult()
    
    with app.app_context():
        # تست وجود جداول
        inspector = inspect(db.engine)
        tables = ['users', 'categories', 'products', 'product_media', 'inquiries', 'educational_content', 'static_content']
        
        for table in tables:
            try:
                columns = inspector.get_columns(table)
                if columns:
                    results.add_pass(f"جدول {table} وجود دارد")
                else:
                    results.add_fail(f"جدول {table}", "جدول خالی است")
            except Exception as e:
                results.add_fail(f"جدول {table}", str(e))
        
        # تست ساختار ستون‌های جدول محتوای آموزشی
        try:
            columns = {col['name'] for col in inspector.get_columns('educational_content')}
            required_columns = {'id', 'title', 'content', 'category', 'type', 'content_type', 'created_at'}
            missing = required_columns - columns
            
            if not missing:
                results.add_pass("ساختار جدول educational_content صحیح است")
            else:
                results.add_fail("ساختار جدول educational_content", f"ستون‌های زیر وجود ندارند: {missing}")
        except Exception as e:
            results.add_fail("ساختار جدول educational_content", str(e))
        
        # تست ساختار ستون‌های جدول محتوای ثابت
        try:
            columns = {col['name'] for col in inspector.get_columns('static_content')}
            required_columns = {'id', 'type', 'content', 'content_type', 'updated_at'}
            missing = required_columns - columns
            
            if not missing:
                results.add_pass("ساختار جدول static_content صحیح است")
            else:
                results.add_fail("ساختار جدول static_content", f"ستون‌های زیر وجود ندارند: {missing}")
        except Exception as e:
            results.add_fail("ساختار جدول static_content", str(e))
        
        # تست محدودیت‌های جدول static_content
        try:
            constraints = db.session.execute(text("""
                SELECT con.conname, con.contype, pg_get_constraintdef(con.oid)
                FROM pg_constraint con
                INNER JOIN pg_class rel ON rel.oid = con.conrelid
                INNER JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
                WHERE rel.relname = 'static_content';
            """)).fetchall()
            
            # بررسی وجود محدودیت unique برای ستون type
            has_type_unique = any('type' in constraint[2] and constraint[1] == 'u' for constraint in constraints)
            
            if has_type_unique:
                results.add_pass("محدودیت unique برای ستون type در جدول static_content وجود دارد")
            else:
                results.add_fail("محدودیت unique برای ستون type", "محدودیت وجود ندارد")
        except Exception as e:
            results.add_fail("بررسی محدودیت‌های جدول static_content", str(e))
    
    return results

def test_models():
    """تست مدل‌های SQLAlchemy"""
    results = TestResult()
    
    with app.app_context():
        # تست مدل User
        try:
            user = User(
                username="test_user",
                email="test@example.com",
                is_admin=False,
                telegram_id=123456789,
                telegram_username="test_tg_user",
                first_name="Test",
                last_name="User"
            )
            user.set_password("password123")
            
            db.session.add(user)
            db.session.flush()
            
            results.add_pass("مدل User به درستی کار می‌کند")
            
            # پاکسازی
            db.session.rollback()
        except Exception as e:
            results.add_fail("مدل User", str(e))
            db.session.rollback()
        
        # تست مدل StaticContent
        try:
            # آزمایش ایجاد دو رکورد با مقادیر متفاوت برای type
            static1 = StaticContent(
                type="test_type_1",
                content="Test Content 1",
                content_type="test_content_type_1"
            )
            
            static2 = StaticContent(
                type="test_type_2",
                content="Test Content 2",
                content_type="test_content_type_2"
            )
            
            db.session.add_all([static1, static2])
            db.session.flush()
            
            results.add_pass("مدل StaticContent به درستی کار می‌کند")
            
            # پاکسازی
            db.session.rollback()
        except Exception as e:
            results.add_fail("مدل StaticContent", str(e))
            db.session.rollback()
        
        # تست مدل EducationalContent
        try:
            edu_content = EducationalContent(
                title="Test Education",
                content="This is a test content",
                category="Test Category",
                type="general",
                content_type="text"
            )
            
            db.session.add(edu_content)
            db.session.flush()
            
            results.add_pass("مدل EducationalContent به درستی کار می‌کند")
            
            # پاکسازی
            db.session.rollback()
        except Exception as e:
            results.add_fail("مدل EducationalContent", str(e))
            db.session.rollback()
    
    return results

def test_data():
    """تست داده‌های آزمایشی"""
    results = TestResult()
    
    with app.app_context():
        # تست وجود داده در همه جداول
        try:
            if User.query.count() > 0:
                results.add_pass("جدول users دارای داده است")
            else:
                results.add_fail("جدول users", "هیچ داده‌ای وجود ندارد")
            
            if Category.query.count() > 0:
                results.add_pass("جدول categories دارای داده است")
            else:
                results.add_fail("جدول categories", "هیچ داده‌ای وجود ندارد")
            
            if Product.query.filter_by(product_type="product").count() > 0:
                results.add_pass("جدول products (محصولات) دارای داده است")
            else:
                results.add_fail("جدول products (محصولات)", "هیچ داده‌ای وجود ندارد")
            
            if Product.query.filter_by(product_type="service").count() > 0:
                results.add_pass("جدول products (خدمات) دارای داده است")
            else:
                results.add_fail("جدول products (خدمات)", "هیچ داده‌ای وجود ندارد")
            
            if ProductMedia.query.count() > 0:
                results.add_pass("جدول product_media دارای داده است")
            else:
                results.add_fail("جدول product_media", "هیچ داده‌ای وجود ندارد")
            
            if Inquiry.query.count() > 0:
                results.add_pass("جدول inquiries دارای داده است")
            else:
                results.add_fail("جدول inquiries", "هیچ داده‌ای وجود ندارد")
            
            if EducationalContent.query.count() > 0:
                results.add_pass("جدول educational_content دارای داده است")
            else:
                results.add_fail("جدول educational_content", "هیچ داده‌ای وجود ندارد")
            
            if StaticContent.query.count() > 0:
                results.add_pass("جدول static_content دارای داده است")
            else:
                results.add_fail("جدول static_content", "هیچ داده‌ای وجود ندارد")
        except Exception as e:
            results.add_fail("بررسی داده‌های آزمایشی", str(e))
    
    return results

def test_functionality():
    """تست عملکرد اصلی سیستم"""
    results = TestResult()
    
    with app.app_context():
        # تست فرایند احراز هویت کاربر
        try:
            # ایجاد کاربر آزمایشی
            username = f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            user = User(
                username=username,
                email=f"{username}@example.com",
                is_admin=False
            )
            user.set_password("test_password")
            
            db.session.add(user)
            db.session.commit()
            
            # تست احراز هویت
            found_user = User.query.filter_by(username=username).first()
            if found_user and found_user.check_password("test_password"):
                results.add_pass("فرایند احراز هویت کاربر به درستی کار می‌کند")
            else:
                results.add_fail("فرایند احراز هویت کاربر", "احراز هویت ناموفق بود")
            
            # پاکسازی
            User.query.filter_by(username=username).delete()
            db.session.commit()
        except Exception as e:
            results.add_fail("فرایند احراز هویت کاربر", str(e))
            db.session.rollback()
        
        # تست جستجوی محصولات
        try:
            # ایجاد محصول آزمایشی
            category = Category.query.first()
            if not category:
                category = Category(name="Test Category", cat_type="product")
                db.session.add(category)
                db.session.flush()
            
            product_name = f"Test Product {datetime.now().strftime('%Y%m%d%H%M%S')}"
            product = Product(
                name=product_name,
                price=10000,
                description="This is a test product",
                category_id=category.id,
                product_type="product",
                tags="test,search",
                brand="Test Brand"
            )
            
            db.session.add(product)
            db.session.flush()
            
            # تست جستجو با روش search
            results_by_name = Product.search(product_name)
            results_by_tag = Product.search(query="", tags="test")
            results_by_brand = Product.search(query="", brand="Test Brand")
            
            if results_by_name.count() > 0 and results_by_tag.count() > 0 and results_by_brand.count() > 0:
                results.add_pass("جستجوی محصولات به درستی کار می‌کند")
            else:
                results.add_fail("جستجوی محصولات", "جستجو نتایج مورد انتظار را برنگرداند")
            
            # پاکسازی
            db.session.rollback()
        except Exception as e:
            results.add_fail("جستجوی محصولات", str(e))
            db.session.rollback()
        
        # تست عملکرد محتوای ثابت
        try:
            # بررسی وجود داده‌های محتوای ثابت
            about_content = StaticContent.query.filter_by(content_type="about").first()
            contact_content = StaticContent.query.filter_by(content_type="contact").first()
            
            if about_content and contact_content:
                # بررسی امکان به‌روزرسانی محتوا
                old_content = about_content.content
                about_content.content = "Updated test content"
                about_content.updated_at = datetime.utcnow()
                db.session.commit()
                
                # بررسی به‌روزرسانی موفق
                refreshed_content = StaticContent.query.filter_by(content_type="about").first()
                if refreshed_content.content == "Updated test content":
                    results.add_pass("عملکرد محتوای ثابت به درستی کار می‌کند")
                else:
                    results.add_fail("عملکرد محتوای ثابت", "به‌روزرسانی محتوا موفق نبود")
                
                # بازگرداندن به حالت اولیه
                about_content.content = old_content
                db.session.commit()
            else:
                results.add_fail("عملکرد محتوای ثابت", "رکوردهای محتوای ثابت یافت نشدند")
        except Exception as e:
            results.add_fail("عملکرد محتوای ثابت", str(e))
            db.session.rollback()
    
    return results

def main():
    """اجرای تمام تست‌ها"""
    logger.info("شروع تست‌های جامع سیستم")
    
    # اجرای تست‌ها و جمع‌آوری نتایج
    structure_results = test_database_structure()
    models_results = test_models()
    data_results = test_data()
    functionality_results = test_functionality()
    
    # نمایش نتایج
    logger.info("\n----- نتایج تست ساختار دیتابیس -----")
    structure_success = structure_results.summary()
    
    logger.info("\n----- نتایج تست مدل‌ها -----")
    models_success = models_results.summary()
    
    logger.info("\n----- نتایج تست داده‌ها -----")
    data_success = data_results.summary()
    
    logger.info("\n----- نتایج تست عملکرد -----")
    functionality_success = functionality_results.summary()
    
    # نتیجه کلی
    logger.info("\n===== نتیجه کلی =====")
    total_results = TestResult()
    total_results.total = structure_results.total + models_results.total + data_results.total + functionality_results.total
    total_results.passed = structure_results.passed + models_results.passed + data_results.passed + functionality_results.passed
    total_results.failed = structure_results.failed + models_results.failed + data_results.failed + functionality_results.failed
    total_results.failures = structure_results.failures + models_results.failures + data_results.failures + functionality_results.failures
    
    success = total_results.summary()
    
    if success:
        logger.info("تمام تست‌ها با موفقیت انجام شدند. سیستم آماده استفاده است.")
        return 0
    else:
        logger.error("برخی از تست‌ها ناموفق بودند. لطفاً مشکلات را برطرف کنید.")
        return 1

if __name__ == "__main__":
    sys.exit(main())