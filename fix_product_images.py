#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
این اسکریپت مشکل مسیرهای تصاویر محصولات و خدمات را برطرف می‌کند
با کپی کردن تصویر پیش‌فرض به مسیر مناسب برای هر محصول و به‌روزرسانی مسیر‌های محلی در دیتابیس
"""

import os
import shutil
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# بارگذاری متغیرهای محیطی
load_dotenv()

# اتصال به دیتابیس
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    logger.error("DATABASE_URL محیطی تنظیم نشده است")
    exit(1)

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

def ensure_directories():
    """اطمینان از وجود دایرکتوری‌های مورد نیاز"""
    directories = [
        "static/media/products",
        "static/media/services",
        "static/images"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"دایرکتوری {directory} ایجاد شد یا از قبل وجود داشت")

def copy_default_image():
    """کپی تصویر پیش‌فرض به مسیر مناسب"""
    default_img_path = "static/images/no-image.png"
    
    # اگر تصویر پیش‌فرض موجود نیست، آن را از attached_assets کپی می‌کنیم
    if not os.path.exists(default_img_path):
        fallback_img = "attached_assets/show.jpg"
        if os.path.exists(fallback_img):
            shutil.copy(fallback_img, default_img_path)
            logger.info(f"تصویر پیش‌فرض از {fallback_img} به {default_img_path} کپی شد")
        else:
            logger.error(f"تصویر پیش‌فرض {fallback_img} پیدا نشد")
            return False
    return True

def fix_product_media():
    """برطرف کردن مشکل مسیر‌های محلی برای تصاویر محصولات"""
    try:
        # دریافت تمام رکوردهای media برای محصولات که local_path آن‌ها NULL است
        query = text("""
            SELECT id, product_id, file_id 
            FROM product_media 
            WHERE local_path IS NULL OR local_path = ''
        """)
        result = session.execute(query)
        
        count = 0
        for row in result:
            media_id = row[0]
            product_id = row[1]
            file_id = row[2]
            
            # ساخت مسیر فایل محلی
            filename = f"{file_id}.jpg"
            filepath = f"static/media/products/{filename}"
            
            # کپی تصویر پیش‌فرض به مسیر مورد نظر اگر فایل هنوز وجود ندارد
            if not os.path.exists(filepath):
                shutil.copy("static/images/no-image.png", filepath)
                logger.info(f"تصویر پیش‌فرض برای محصول {product_id} به مسیر {filepath} کپی شد")
            
            # به‌روزرسانی مسیر محلی در دیتابیس
            update_query = text("""
                UPDATE product_media
                SET local_path = :local_path
                WHERE id = :media_id
            """)
            session.execute(update_query, {"local_path": filepath, "media_id": media_id})
            count += 1
        
        session.commit()
        logger.info(f"تعداد {count} رکورد تصویر محصول به‌روزرسانی شد")
    except Exception as e:
        session.rollback()
        logger.error(f"خطا در به‌روزرسانی تصاویر محصولات: {str(e)}")
        raise

def fix_service_media():
    """برطرف کردن مشکل مسیر‌های محلی برای تصاویر خدمات"""
    try:
        # دریافت تمام رکوردهای media برای خدمات که local_path آن‌ها NULL است
        query = text("""
            SELECT id, service_id, file_id 
            FROM service_media 
            WHERE local_path IS NULL OR local_path = ''
        """)
        result = session.execute(query)
        
        count = 0
        for row in result:
            media_id = row[0]
            service_id = row[1]
            file_id = row[2]
            
            # ساخت مسیر فایل محلی
            filename = f"{file_id}.jpg"
            filepath = f"static/media/services/{filename}"
            
            # کپی تصویر پیش‌فرض به مسیر مورد نظر اگر فایل هنوز وجود ندارد
            if not os.path.exists(filepath):
                shutil.copy("static/images/no-image.png", filepath)
                logger.info(f"تصویر پیش‌فرض برای خدمت {service_id} به مسیر {filepath} کپی شد")
            
            # به‌روزرسانی مسیر محلی در دیتابیس
            update_query = text("""
                UPDATE service_media
                SET local_path = :local_path
                WHERE id = :media_id
            """)
            session.execute(update_query, {"local_path": filepath, "media_id": media_id})
            count += 1
        
        session.commit()
        logger.info(f"تعداد {count} رکورد تصویر خدمت به‌روزرسانی شد")
    except Exception as e:
        session.rollback()
        logger.error(f"خطا در به‌روزرسانی تصاویر خدمات: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        logger.info("شروع فرآیند تعمیر مسیرهای تصاویر")
        ensure_directories()
        if copy_default_image():
            fix_product_media()
            fix_service_media()
            logger.info("فرآیند تعمیر مسیرهای تصاویر با موفقیت به پایان رسید")
        else:
            logger.error("فرآیند به دلیل عدم وجود تصویر پیش‌فرض متوقف شد")
    except Exception as e:
        logger.error(f"خطای کلی: {str(e)}")
    finally:
        session.close()