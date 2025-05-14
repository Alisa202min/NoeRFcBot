"""
مهاجرت داده‌ها از جدول categories به جداول جدید و حذف جدول categories
"""

import os
import sys
import logging
from app import app, db
from models import Category, Product, Service, ProductCategory, ServiceCategory

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_foreign_keys():
    """پاک کردن کلیدهای خارجی مرتبط با جدول categories"""
    with app.app_context():
        try:
            # یافتن همه محصولات مرتبط با categories
            products_with_categories = Product.query.filter(
                Product.category_id.in_(
                    db.session.query(Category.id)
                )
            ).all()
            
            logger.info(f"تعداد {len(products_with_categories)} محصول با دسته‌بندی قدیمی پیدا شد")
            
            # یافتن دسته‌بندی‌های محصول مرتبط با هر محصول یا ایجاد دسته‌بندی پیش‌فرض
            default_product_category = ProductCategory.query.first()
            if not default_product_category:
                default_product_category = ProductCategory(name="دسته‌بندی پیش‌فرض محصولات")
                db.session.add(default_product_category)
                db.session.commit()
            
            # به‌روزرسانی محصولات
            for product in products_with_categories:
                old_category = Category.query.get(product.category_id)
                if old_category:
                    # تلاش برای یافتن دسته‌بندی جدید با همان نام
                    new_category = ProductCategory.query.filter_by(name=old_category.name).first()
                    if not new_category:
                        product.category_id = default_product_category.id
                    else:
                        product.category_id = new_category.id
                else:
                    product.category_id = default_product_category.id
            
            db.session.commit()
            logger.info(f"دسته‌بندی‌های محصولات به‌روزرسانی شد")
            
            # یافتن همه خدمات مرتبط با categories
            services_with_categories = Service.query.filter(
                Service.category_id.in_(
                    db.session.query(Category.id)
                )
            ).all()
            
            logger.info(f"تعداد {len(services_with_categories)} خدمت با دسته‌بندی قدیمی پیدا شد")
            
            # یافتن دسته‌بندی‌های خدمت مرتبط با هر خدمت یا ایجاد دسته‌بندی پیش‌فرض
            default_service_category = ServiceCategory.query.first()
            if not default_service_category:
                default_service_category = ServiceCategory(name="دسته‌بندی پیش‌فرض خدمات")
                db.session.add(default_service_category)
                db.session.commit()
            
            # به‌روزرسانی خدمات
            for service in services_with_categories:
                old_category = Category.query.get(service.category_id)
                if old_category:
                    # تلاش برای یافتن دسته‌بندی جدید با همان نام
                    new_category = ServiceCategory.query.filter_by(name=old_category.name).first()
                    if not new_category:
                        service.category_id = default_service_category.id
                    else:
                        service.category_id = new_category.id
                else:
                    service.category_id = default_service_category.id
            
            db.session.commit()
            logger.info(f"دسته‌بندی‌های خدمات به‌روزرسانی شد")
            
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"خطا در به‌روزرسانی کلیدهای خارجی: {str(e)}")
            return False

def transfer_categories():
    """انتقال دسته‌بندی‌های موجود در جدول categories به جداول جدید"""
    with app.app_context():
        try:
            # انتقال دسته‌بندی‌های محصول
            product_categories = Category.query.filter_by(cat_type='product').all()
            
            # ساخت دیکشنری برای نگاشت id های قدیمی به جدید برای دسته‌بندی‌های والد
            old_to_new_product = {}
            
            for category in product_categories:
                if not ProductCategory.query.filter_by(name=category.name).first():
                    new_category = ProductCategory(name=category.name)
                    # فعلاً parent_id را نمی‌گذاریم، در مرحله بعد اضافه می‌کنیم
                    db.session.add(new_category)
                    db.session.flush()  # برای دریافت ID جدید
                    old_to_new_product[category.id] = new_category.id
            
            db.session.commit()
            logger.info(f"تعداد {len(old_to_new_product)} دسته‌بندی محصول منتقل شد")
            
            # به‌روزرسانی parent_id ها
            for category in product_categories:
                if category.parent_id and category.parent_id in old_to_new_product:
                    new_category = ProductCategory.query.filter_by(name=category.name).first()
                    if new_category:
                        new_category.parent_id = old_to_new_product.get(category.parent_id)
            
            db.session.commit()
            logger.info(f"روابط والد-فرزندی دسته‌بندی‌های محصول به‌روزرسانی شد")
            
            # انتقال دسته‌بندی‌های خدمت
            service_categories = Category.query.filter_by(cat_type='service').all()
            
            # ساخت دیکشنری برای نگاشت id های قدیمی به جدید برای دسته‌بندی‌های والد
            old_to_new_service = {}
            
            for category in service_categories:
                if not ServiceCategory.query.filter_by(name=category.name).first():
                    new_category = ServiceCategory(name=category.name)
                    # فعلاً parent_id را نمی‌گذاریم، در مرحله بعد اضافه می‌کنیم
                    db.session.add(new_category)
                    db.session.flush()  # برای دریافت ID جدید
                    old_to_new_service[category.id] = new_category.id
            
            db.session.commit()
            logger.info(f"تعداد {len(old_to_new_service)} دسته‌بندی خدمت منتقل شد")
            
            # به‌روزرسانی parent_id ها
            for category in service_categories:
                if category.parent_id and category.parent_id in old_to_new_service:
                    new_category = ServiceCategory.query.filter_by(name=category.name).first()
                    if new_category:
                        new_category.parent_id = old_to_new_service.get(category.parent_id)
            
            db.session.commit()
            logger.info(f"روابط والد-فرزندی دسته‌بندی‌های خدمت به‌روزرسانی شد")
            
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"خطا در انتقال دسته‌بندی‌ها: {str(e)}")
            return False

def drop_categories_table():
    """حذف کامل جدول categories"""
    with app.app_context():
        try:
            # حذف همه رکوردهای جدول
            Category.query.delete()
            db.session.commit()
            logger.info(f"همه رکوردهای جدول categories حذف شد")
            
            # اجرای دستور SQL برای حذف خود جدول
            # این بخش را در کامنت قرار می‌دهیم چون ممکن است فریمورک SQLAlchemy به آن نیاز داشته باشد
            # db.engine.execute("DROP TABLE IF EXISTS categories CASCADE")
            
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"خطا در حذف جدول categories: {str(e)}")
            return False

def main():
    """تابع اصلی برای اجرای مهاجرت"""
    logger.info("شروع فرآیند مهاجرت و حذف جدول categories")
    
    # انتقال دسته‌بندی‌ها
    logger.info("در حال انتقال دسته‌بندی‌ها به جداول جدید...")
    if not transfer_categories():
        logger.error("خطا در انتقال دسته‌بندی‌ها. فرآیند متوقف شد.")
        return False
    
    # پاکسازی کلیدهای خارجی
    logger.info("در حال پاکسازی کلیدهای خارجی...")
    if not clean_foreign_keys():
        logger.error("خطا در پاکسازی کلیدهای خارجی. فرآیند متوقف شد.")
        return False
    
    # حذف جدول categories
    logger.info("در حال حذف جدول categories...")
    if not drop_categories_table():
        logger.error("خطا در حذف جدول categories. فرآیند متوقف شد.")
        return False
    
    logger.info("فرآیند مهاجرت و حذف جدول categories با موفقیت انجام شد.")
    return True

if __name__ == "__main__":
    main()