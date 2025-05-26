#!/usr/bin/env python3
"""
اسکریپت ساده و کارآمد برای اضافه کردن دیتای RFTEST
"""

import os
import logging
from datetime import datetime
from database import Database

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def confirm_reset():
    """درخواست تایید از کاربر"""
    print("\n" + "="*60)
    print("🗄️  بازنشانی دیتابیس شرکت RFTEST")
    print("="*60)
    print("این عملیات دیتای قبلی را پاک می‌کند و دیتای جدید اضافه می‌کند")
    print("⚠️  توجه: اطلاعات کاربران پاک نخواهد شد")
    print()
    
    response = input("آیا مایل به ادامه هستید؟ (بله/خیر): ").strip().lower()
    return response in ['بله', 'yes', 'y']

def main():
    """اجرای اصلی"""
    if not confirm_reset():
        print("❌ عملیات لغو شد.")
        return
    
    print("\n🚀 شروع فرآیند تولید دیتای RFTEST...")
    
    try:
        # اتصال به دیتابیس
        db = Database()
        
        logger.info("پاک کردن دیتای قبلی...")
        with db.conn.cursor() as cur:
            # پاک کردن دیتای قبلی
            tables = [
                "product_media", "service_media", "educational_content_media",
                "products", "services", "educational_content", 
                "product_categories", "service_categories", "educational_categories"
            ]
            
            for table in tables:
                try:
                    cur.execute(f"DELETE FROM {table}")
                    logger.info(f"✅ جدول {table} پاک شد")
                except Exception as e:
                    logger.warning(f"⚠️ مشکل در پاک کردن {table}: {e}")
            
            db.conn.commit()
        
        logger.info("اضافه کردن دسته‌بندی‌های محصولات...")
        product_categories = {}
        with db.conn.cursor() as cur:
            categories = [
                "اسیلوسکوپ", "اسپکتروم آنالایزر", "سیگنال ژنراتور",
                "نتورک آنالایزر", "پاورمتر و سنسور", "رادیوتستر",
                "فرکانس متر", "مالتی متر دیجیتال", "تجهیزات کالیبراسیون"
            ]
            
            for cat_name in categories:
                cur.execute("""
                    INSERT INTO product_categories (name, parent_id, created_at)
                    VALUES (%s, %s, %s) RETURNING id
                """, (cat_name, None, datetime.now()))
                
                result = cur.fetchone()
                if result:
                    product_categories[cat_name] = result[0]
                    logger.info(f"✅ دسته محصولات: {cat_name} (ID: {result[0]})")
            
            db.conn.commit()
        
        logger.info("اضافه کردن محصولات RFTEST...")
        products_data = [
            {
                "name": "اسیلوسکوپ دیجیتال Keysight DSOX2002A",
                "description": "اسیلوسکوپ دیجیتال 2 کاناله با پهنای باند 70MHz. مناسب برای کاربردهای عمومی و آموزشی.",
                "price": 45000000,
                "category": "اسیلوسکوپ",
                "brand": "Keysight",
                "model": "DSOX2002A",
                "tags": "اسیلوسکوپ،دیجیتال،70MHz،2کانال",
                "in_stock": True,
                "featured": True
            },
            {
                "name": "اسیلوسکوپ آنالوگ Tektronix 2235",
                "description": "اسیلوسکوپ آنالوگ کلاسیک 2 کاناله با پهنای باند 100MHz. بسیار مقاوم و قابل اعتماد.",
                "price": 18000000,
                "category": "اسیلوسکوپ",
                "brand": "Tektronix",
                "model": "2235",
                "tags": "اسیلوسکوپ،آنالوگ،100MHz،کلاسیک",
                "in_stock": True,
                "featured": False
            },
            {
                "name": "اسپکتروم آنالایزر Agilent E4402B",
                "description": "اسپکتروم آنالایزر ESA-E با دامنه 9kHz تا 3GHz. عملکرد عالی برای کاربردهای EMC.",
                "price": 125000000,
                "category": "اسپکتروم آنالایزر",
                "brand": "Agilent",
                "model": "E4402B",
                "tags": "اسپکتروم،3GHz،EMC،RF",
                "in_stock": True,
                "featured": True
            },
            {
                "name": "سیگنال ژنراتور Keysight E8257D",
                "description": "سیگنال ژنراتور PSG با دامنه تا 67GHz. نویز فاز بسیار پایین و دقت بالا.",
                "price": 780000000,
                "category": "سیگنال ژنراتور",
                "brand": "Keysight",
                "model": "E8257D",
                "tags": "سیگنال ژنراتور،67GHz،نویز فاز پایین",
                "in_stock": False,
                "featured": True
            },
            {
                "name": "رادیوتستر Aeroflex 3920B",
                "description": "رادیوتستر دیجیتال پیشرفته با پشتیبانی از استانداردهای DMR، P25 و Tetra.",
                "price": 320000000,
                "category": "رادیوتستر",
                "brand": "Aeroflex",
                "model": "3920B",
                "tags": "رادیوتستر،DMR،P25،Tetra",
                "in_stock": True,
                "featured": True
            },
            {
                "name": "رادیوتستر Marconi 2955B",
                "description": "رادیوتستر آنالوگ کلاسیک برای تست رادیوهای آنالوگ. بسیار مقاوم و قابل اعتماد.",
                "price": 85000000,
                "category": "رادیوتستر",
                "brand": "Marconi",
                "model": "2955B",
                "tags": "رادیوتستر،آنالوگ،کلاسیک",
                "in_stock": True,
                "featured": False
            }
        ]
        
        with db.conn.cursor() as cur:
            for product in products_data:
                category_id = product_categories.get(product["category"])
                if not category_id:
                    continue
                
                cur.execute("""
                    INSERT INTO products (
                        name, description, price, category_id, brand, model,
                        tags, in_stock, featured, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    product["name"], product["description"], product["price"],
                    category_id, product["brand"], product["model"],
                    product["tags"], product["in_stock"], product["featured"], datetime.now()
                ))
                
                logger.info(f"✅ محصول اضافه شد: {product['name']}")
            
            db.conn.commit()
        
        print("\n" + "="*60)
        print("🎉 دیتای RFTEST با موفقیت اضافه شد!")
        print("="*60)
        print("✅ دسته‌بندی‌های محصولات ایجاد شد")
        print("✅ محصولات تجهیزات اندازه‌گیری اضافه شد")
        print("🌐 وب پنل و بات تلگرام آماده استفاده!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"❌ خطا در تولید دیتا: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()