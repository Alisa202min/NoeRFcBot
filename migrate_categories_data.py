"""
انتقال داده‌های جدول categories به جداول جدید و حفظ ساختار جدول
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import text
from app import app, db
from models import Category, Product, Service, ProductCategory, ServiceCategory

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_product_categories():
    """انتقال دسته‌بندی‌های محصول و اصلاح ارجاعات محصولات"""
    with app.app_context():
        try:
            # انتقال دسته‌بندی‌های محصول
            product_categories = Category.query.filter_by(cat_type='product').all()
            
            # ساخت دیکشنری برای نگاشت id های قدیمی به جدید
            old_to_new = {}
            
            # مرحله 1: ساخت تمام دسته‌بندی‌های جدید
            for category in product_categories:
                # بررسی وجود دسته‌بندی مشابه
                new_category = ProductCategory.query.filter_by(name=category.name).first()
                if not new_category:
                    new_category = ProductCategory(
                        name=category.name,
                        created_at=category.created_at or datetime.utcnow()
                    )
                    db.session.add(new_category)
                    db.session.flush()
                
                old_to_new[category.id] = new_category.id
            
            db.session.commit()
            logger.info(f"دسته‌بندی‌های محصول منتقل شدند: {len(old_to_new)} دسته‌بندی")
            
            # مرحله 2: اضافه کردن ارتباطات والد-فرزند
            for category in product_categories:
                if category.parent_id and category.parent_id in old_to_new:
                    new_category_id = old_to_new[category.id]
                    new_parent_id = old_to_new[category.parent_id]
                    
                    new_category = ProductCategory.query.get(new_category_id)
                    if new_category:
                        new_category.parent_id = new_parent_id
            
            db.session.commit()
            logger.info("روابط والد-فرزند محصولات به‌روزرسانی شدند")
            
            # مرحله 3: به‌روزرسانی محصولات
            products = Product.query.all()
            updated_count = 0
            
            for product in products:
                if product.category_id in old_to_new:
                    product.category_id = old_to_new[product.category_id]
                    updated_count += 1
            
            db.session.commit()
            logger.info(f"دسته‌بندی {updated_count} محصول به‌روزرسانی شد")
            
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"خطا در انتقال دسته‌بندی‌های محصول: {str(e)}")
            return False

def migrate_service_categories():
    """انتقال دسته‌بندی‌های خدمات و اصلاح ارجاعات خدمات"""
    with app.app_context():
        try:
            # انتقال دسته‌بندی‌های خدمات
            service_categories = Category.query.filter_by(cat_type='service').all()
            
            # ساخت دیکشنری برای نگاشت id های قدیمی به جدید
            old_to_new = {}
            
            # مرحله 1: ساخت تمام دسته‌بندی‌های جدید
            for category in service_categories:
                # بررسی وجود دسته‌بندی مشابه
                new_category = ServiceCategory.query.filter_by(name=category.name).first()
                if not new_category:
                    new_category = ServiceCategory(
                        name=category.name,
                        created_at=category.created_at or datetime.utcnow()
                    )
                    db.session.add(new_category)
                    db.session.flush()
                
                old_to_new[category.id] = new_category.id
            
            db.session.commit()
            logger.info(f"دسته‌بندی‌های خدمات منتقل شدند: {len(old_to_new)} دسته‌بندی")
            
            # مرحله 2: اضافه کردن ارتباطات والد-فرزند
            for category in service_categories:
                if category.parent_id and category.parent_id in old_to_new:
                    new_category_id = old_to_new[category.id]
                    new_parent_id = old_to_new[category.parent_id]
                    
                    new_category = ServiceCategory.query.get(new_category_id)
                    if new_category:
                        new_category.parent_id = new_parent_id
            
            db.session.commit()
            logger.info("روابط والد-فرزند خدمات به‌روزرسانی شدند")
            
            # مرحله 3: به‌روزرسانی خدمات
            services = Service.query.all()
            updated_count = 0
            
            for service in services:
                if service.category_id in old_to_new:
                    service.category_id = old_to_new[service.category_id]
                    updated_count += 1
            
            db.session.commit()
            logger.info(f"دسته‌بندی {updated_count} خدمت به‌روزرسانی شد")
            
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"خطا در انتقال دسته‌بندی‌های خدمات: {str(e)}")
            return False

def clear_categories():
    """خالی کردن جدول categories بدون حذف کامل آن"""
    with app.app_context():
        try:
            # خالی کردن جدول با استفاده از SQL مستقیم برای اطمینان از عدم تأثیر بر کلیدهای خارجی
            db.session.execute(text("DELETE FROM categories"))
            db.session.commit()
            logger.info("جدول categories با موفقیت خالی شد")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"خطا در خالی کردن جدول categories: {str(e)}")
            return False

def main():
    """تابع اصلی برای انجام مهاجرت"""
    logger.info("شروع فرآیند انتقال داده‌های جدول categories")
    
    if not migrate_product_categories():
        logger.error("خطا در انتقال دسته‌بندی‌های محصول. عملیات متوقف شد.")
        return False
    
    if not migrate_service_categories():
        logger.error("خطا در انتقال دسته‌بندی‌های خدمات. عملیات متوقف شد.")
        return False
    
    if not clear_categories():
        logger.error("خطا در خالی کردن جدول categories. عملیات متوقف شد.")
        return False
    
    logger.info("فرآیند انتقال داده‌های جدول categories با موفقیت انجام شد")
    return True

if __name__ == "__main__":
    main()