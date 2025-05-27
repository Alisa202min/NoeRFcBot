#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست ساده دیتابیس و مدل‌های SQLAlchemy
"""

import sys
import logging
import os

# اضافه کردن مسیر پروژه به PYTHONPATH برای دسترسی به ماژول‌های پروژه
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.web.app import app, db
from src.models.models import User, Category, Product, Service, ProductMedia, ServiceMedia, Inquiry, EducationalContent, StaticContent

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """تست اتصال به دیتابیس"""
    try:
        with app.app_context():
            # تست ساده برای بررسی اتصال
            result = db.session.execute(db.text('SELECT 1')).scalar()
            assert result == 1, "اتصال به دیتابیس ناموفق بود"
            
            logger.info("✅ اتصال به دیتابیس با موفقیت برقرار شد")
            return True
    except Exception as e:
        logger.error(f"❌ خطا در اتصال به دیتابیس: {e}")
        return False

def test_user_model():
    """تست مدل User"""
    try:
        with app.app_context():
            users = User.query.all()
            logger.info(f"✅ تعداد کاربران: {len(users)}")
            
            if users:
                logger.info(f"✅ کاربر اول: {users[0].username}")
            return True
    except Exception as e:
        logger.error(f"❌ خطا در تست مدل User: {e}")
        return False

def test_category_model():
    """تست مدل Category"""
    try:
        with app.app_context():
            categories = Category.query.all()
            logger.info(f"✅ تعداد دسته‌بندی‌ها: {len(categories)}")
            
            # تست ارتباط والد-فرزند
            parent_categories = Category.query.filter_by(parent_id=None).all()
            logger.info(f"✅ تعداد دسته‌بندی‌های اصلی: {len(parent_categories)}")
            
            if parent_categories:
                parent = parent_categories[0]
                children = Category.query.filter_by(parent_id=parent.id).all()
                logger.info(f"✅ دسته‌بندی '{parent.name}' دارای {len(children)} زیردسته است")
            return True
    except Exception as e:
        logger.error(f"❌ خطا در تست مدل Category: {e}")
        return False

def test_product_model():
    """تست مدل Product"""
    try:
        with app.app_context():
            products = Product.query.all()
            services = Service.query.all()
            logger.info(f"✅ تعداد محصولات: {len(products)}")
            logger.info(f"✅ تعداد خدمات: {len(services)}")
            
            # تست ارتباط محصول و دسته‌بندی
            if products:
                product = products[0]
                category = Category.query.get(product.category_id)
                logger.info(f"✅ محصول '{product.name}' در دسته‌بندی '{category.name if category else 'نامشخص'}' قرار دارد")
            
            # تست ارتباط خدمت و دسته‌بندی
            if services:
                service = services[0]
                category = Category.query.get(service.category_id)
                logger.info(f"✅ خدمت '{service.name}' در دسته‌بندی '{category.name if category else 'نامشخص'}' قرار دارد")
            return True
    except Exception as e:
        logger.error(f"❌ خطا در تست مدل Product و Service: {e}")
        return False

def test_media_models():
    """تست مدل‌های ProductMedia و ServiceMedia"""
    try:
        with app.app_context():
            product_media_files = ProductMedia.query.all()
            service_media_files = ServiceMedia.query.all()
            logger.info(f"✅ تعداد فایل‌های چندرسانه‌ای محصولات: {len(product_media_files)}")
            logger.info(f"✅ تعداد فایل‌های چندرسانه‌ای خدمات: {len(service_media_files)}")
            
            # تست ارتباط محصول و رسانه
            if product_media_files:
                media = product_media_files[0]
                product = Product.query.get(media.product_id)
                logger.info(f"✅ رسانه محصول با ID {media.id} مربوط به محصول '{product.name if product else 'نامشخص'}' است")
                logger.info(f"✅ نوع فایل: {media.file_type}, file_id: {media.file_id[:10] if len(media.file_id) > 10 else media.file_id}...")
            
            # تست ارتباط خدمت و رسانه
            if service_media_files:
                media = service_media_files[0]
                service = Service.query.get(media.service_id)
                logger.info(f"✅ رسانه خدمت با ID {media.id} مربوط به خدمت '{service.name if service else 'نامشخص'}' است")
                logger.info(f"✅ نوع فایل: {media.file_type}, file_id: {media.file_id[:10] if len(media.file_id) > 10 else media.file_id}...")
            return True
    except Exception as e:
        logger.error(f"❌ خطا در تست مدل‌های ProductMedia و ServiceMedia: {e}")
        return False

def test_inquiry_model():
    """تست مدل Inquiry"""
    try:
        with app.app_context():
            inquiries = Inquiry.query.all()
            logger.info(f"✅ تعداد استعلام‌های قیمت: {len(inquiries)}")
            
            # تست جزئیات استعلام‌ها
            if inquiries:
                inquiry = inquiries[0]
                
                # بررسی محصول یا خدمت مرتبط
                related_item = None
                related_name = "ندارد"
                
                if inquiry.product_id:
                    if inquiry.product_type == 'product':
                        related_item = Product.query.get(inquiry.product_id)
                    elif inquiry.product_type == 'service':
                        related_item = Service.query.get(inquiry.product_id)
                    
                    if related_item:
                        related_name = related_item.name
                
                logger.info(f"✅ استعلام با ID {inquiry.id}:")
                logger.info(f"   • نام مشتری: {inquiry.name}")
                logger.info(f"   • تلفن: {inquiry.phone}")
                logger.info(f"   • وضعیت: {inquiry.status or 'در انتظار بررسی'}")
                logger.info(f"   • نوع استعلام: {inquiry.product_type or 'عمومی'}")
                logger.info(f"   • محصول/خدمت مرتبط: {related_name}")
            return True
    except Exception as e:
        logger.error(f"❌ خطا در تست مدل Inquiry: {e}")
        return False

def test_educational_content_model():
    """تست مدل EducationalContent"""
    try:
        with app.app_context():
            contents = EducationalContent.query.all()
            logger.info(f"✅ تعداد محتوای آموزشی: {len(contents)}")
            
            # تست جزئیات محتوای آموزشی
            if contents:
                content = contents[0]
                logger.info(f"✅ محتوای آموزشی با ID {content.id}:")
                logger.info(f"   • عنوان: {content.title}")
                logger.info(f"   • دسته‌بندی: {content.category}")
                logger.info(f"   • نوع محتوا: {content.content_type}")
            return True
    except Exception as e:
        logger.error(f"❌ خطا در تست مدل EducationalContent: {e}")
        return False

def test_static_content_model():
    """تست مدل StaticContent"""
    try:
        with app.app_context():
            contents = StaticContent.query.all()
            logger.info(f"✅ تعداد محتوای استاتیک: {len(contents)}")
            
            # تست محتوای استاتیک
            for content_type in ['about', 'contact']:
                content = StaticContent.query.filter_by(type=content_type).first()
                if content:
                    logger.info(f"✅ محتوای '{content_type}' موجود است")
                    logger.info(f"   • آخرین بروزرسانی: {content.updated_at}")
                else:
                    logger.warning(f"⚠️ محتوای '{content_type}' موجود نیست")
            return True
    except Exception as e:
        logger.error(f"❌ خطا در تست مدل StaticContent: {e}")
        return False

def run_all_tests():
    """اجرای تمام تست‌ها و نمایش نتایج"""
    print("===== شروع تست‌های دیتابیس =====")
    
    tests = {
        "اتصال به دیتابیس": test_database_connection,
        "مدل User": test_user_model,
        "مدل Category": test_category_model,
        "مدل Product و Service": test_product_model,
        "مدل‌های ProductMedia و ServiceMedia": test_media_models,
        "مدل Inquiry": test_inquiry_model,
        "مدل EducationalContent": test_educational_content_model,
        "مدل StaticContent": test_static_content_model
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
    
    print("\n===== پایان تست‌های دیتابیس =====")
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)