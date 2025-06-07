"""
خالی کردن جدول categories و ایجاد دسته‌بندی‌های جدید در جداول جدید
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

def copy_categories():
    """کپی کردن دسته‌بندی‌ها به جداول جدید بدون تغییر در جدول اصلی"""
    with app.app_context():
        try:
            # کپی دسته‌بندی‌های محصول
            product_categories = Category.query.filter_by(cat_type='product').all()
            
            for category in product_categories:
                # بررسی وجود دسته‌بندی مشابه
                if not ProductCategory.query.filter_by(name=category.name).first():
                    new_category = ProductCategory(
                        name=category.name,
                        parent_id=category.parent_id,
                        created_at=category.created_at or datetime.utcnow()
                    )
                    db.session.add(new_category)
            
            db.session.commit()
            logger.info(f"تعداد {len(product_categories)} دسته‌بندی محصول به جدول جدید کپی شد")
            
            # کپی دسته‌بندی‌های خدمات
            service_categories = Category.query.filter_by(cat_type='service').all()
            
            for category in service_categories:
                # بررسی وجود دسته‌بندی مشابه
                if not ServiceCategory.query.filter_by(name=category.name).first():
                    new_category = ServiceCategory(
                        name=category.name,
                        parent_id=category.parent_id,
                        created_at=category.created_at or datetime.utcnow()
                    )
                    db.session.add(new_category)
            
            db.session.commit()
            logger.info(f"تعداد {len(service_categories)} دسته‌بندی خدمات به جدول جدید کپی شد")
            
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"خطا در کپی دسته‌بندی‌ها: {str(e)}")
            return False

def main():
    """تابع اصلی برای کپی دسته‌بندی‌ها"""
    logger.info("شروع فرآیند کپی دسته‌بندی‌ها به جداول جدید")
    
    if copy_categories():
        logger.info("فرآیند کپی دسته‌بندی‌ها با موفقیت انجام شد")
        return True
    else:
        logger.error("خطا در کپی دسته‌بندی‌ها")
        return False

if __name__ == "__main__":
    main()