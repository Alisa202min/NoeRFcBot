"""
اسکریپت مهاجرت دسته‌بندی‌ها به ساختار جدید
این اسکریپت داده‌های دسته‌بندی قدیمی را به ساختار جدیدی که از سه جدول مجزا استفاده می‌کند منتقل می‌کند.
"""

import sys
import os
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, scoped_session

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# اضافه کردن مسیر پروژه به PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# وارد کردن ماژول‌های مورد نیاز
from src.web.app import db  # noqa: E402
from src.models.models import (  # noqa: E402
    Category, ProductCategory, ServiceCategory, 
    Product, Service
)


def create_tables_if_not_exist():
    """ایجاد جداول اگر وجود ندارند"""
    try:
        # بررسی وجود جداول
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if 'product_categories' not in existing_tables:
            logger.info("Creating table: product_categories")
            ProductCategory.__table__.create(db.engine)
        
        if 'service_categories' not in existing_tables:
            logger.info("Creating table: service_categories")
            ServiceCategory.__table__.create(db.engine)
            
        logger.info("Tables checked and created if needed")
    except SQLAlchemyError as e:
        logger.error(f"Error creating tables: {e}")
        raise


def migrate_product_categories():
    """انتقال دسته‌بندی‌های محصول از جدول قدیمی به جدول جدید"""
    try:
        # دریافت تمام دسته‌بندی‌های محصول
        product_categories = Category.query.filter_by(cat_type='product').all()
        
        # نگاشت ID قدیمی به ID جدید برای حفظ روابط والد-فرزند
        old_to_new_id_map = {}
        
        # مهاجرت دسته‌بندی‌ها بدون والد ابتدا
        for old_cat in product_categories:
            if old_cat.parent_id is None:
                new_cat = ProductCategory(
                    name=old_cat.name,
                    parent_id=None,
                    created_at=old_cat.created_at
                )
                db.session.add(new_cat)
                db.session.flush()  # برای دریافت ID جدید
                
                old_to_new_id_map[old_cat.id] = new_cat.id
                logger.info(f"Migrated root product category: {old_cat.name} (ID: {old_cat.id} -> {new_cat.id})")
        
        # مهاجرت دسته‌بندی‌های با والد
        for old_cat in product_categories:
            if old_cat.parent_id is not None:
                # اگر والد قبلاً مهاجرت شده، آن را استفاده کن
                new_parent_id = old_to_new_id_map.get(old_cat.parent_id)
                
                # اگر هنوز مهاجرت نشده، ایجاد کن
                if old_cat.id not in old_to_new_id_map:
                    new_cat = ProductCategory(
                        name=old_cat.name,
                        parent_id=new_parent_id,
                        created_at=old_cat.created_at
                    )
                    db.session.add(new_cat)
                    db.session.flush()
                    
                    old_to_new_id_map[old_cat.id] = new_cat.id
                    logger.info(f"Migrated child product category: {old_cat.name} (ID: {old_cat.id} -> {new_cat.id})")
        
        # به‌روزرسانی محصولات برای اشاره به دسته‌بندی‌های جدید
        products = Product.query.all()
        for product in products:
            if product.category_id and product.category_id in old_to_new_id_map:
                product.category_id = old_to_new_id_map[product.category_id]
                logger.info(f"Updated product category reference: {product.name} (ID: {product.id})")
        
        db.session.commit()
        logger.info(f"Migrated {len(old_to_new_id_map)} product categories")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error migrating product categories: {e}")
        raise


def migrate_service_categories():
    """انتقال دسته‌بندی‌های خدمات از جدول قدیمی به جدول جدید"""
    try:
        # دریافت تمام دسته‌بندی‌های خدمات
        service_categories = Category.query.filter_by(cat_type='service').all()
        
        # نگاشت ID قدیمی به ID جدید برای حفظ روابط والد-فرزند
        old_to_new_id_map = {}
        
        # مهاجرت دسته‌بندی‌ها بدون والد ابتدا
        for old_cat in service_categories:
            if old_cat.parent_id is None:
                new_cat = ServiceCategory(
                    name=old_cat.name,
                    parent_id=None,
                    created_at=old_cat.created_at
                )
                db.session.add(new_cat)
                db.session.flush()  # برای دریافت ID جدید
                
                old_to_new_id_map[old_cat.id] = new_cat.id
                logger.info(f"Migrated root service category: {old_cat.name} (ID: {old_cat.id} -> {new_cat.id})")
        
        # مهاجرت دسته‌بندی‌های با والد
        for old_cat in service_categories:
            if old_cat.parent_id is not None:
                # اگر والد قبلاً مهاجرت شده، آن را استفاده کن
                new_parent_id = old_to_new_id_map.get(old_cat.parent_id)
                
                # اگر هنوز مهاجرت نشده، ایجاد کن
                if old_cat.id not in old_to_new_id_map:
                    new_cat = ServiceCategory(
                        name=old_cat.name,
                        parent_id=new_parent_id,
                        created_at=old_cat.created_at
                    )
                    db.session.add(new_cat)
                    db.session.flush()
                    
                    old_to_new_id_map[old_cat.id] = new_cat.id
                    logger.info(f"Migrated child service category: {old_cat.name} (ID: {old_cat.id} -> {new_cat.id})")
        
        # به‌روزرسانی خدمات برای اشاره به دسته‌بندی‌های جدید
        services = Service.query.all()
        for service in services:
            if service.category_id and service.category_id in old_to_new_id_map:
                service.category_id = old_to_new_id_map[service.category_id]
                logger.info(f"Updated service category reference: {service.name} (ID: {service.id})")
        
        db.session.commit()
        logger.info(f"Migrated {len(old_to_new_id_map)} service categories")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error migrating service categories: {e}")
        raise


def main():
    """تابع اصلی برای اجرای مهاجرت"""
    try:
        logger.info("Starting category migration")
        
        # ایجاد جداول جدید اگر وجود ندارند
        create_tables_if_not_exist()
        
        # مهاجرت دسته‌بندی‌های محصول
        migrate_product_categories()
        
        # مهاجرت دسته‌بندی‌های خدمات
        migrate_service_categories()
        
        logger.info("Category migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    with db.app.app_context():
        main()