#!/usr/bin/env python3
"""
اسکریپت کامل تولید دیتای شرکت RFTEST
30 محصول + 25 خدمات + 20 مطلب آموزشی + رسانه‌ها + استعلام‌ها
"""

import os
import logging
from datetime import datetime, timedelta
import random
from database import Database
from PIL import Image, ImageDraw, ImageFont

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def confirm_reset():
    """درخواست تایید از کاربر"""
    print("\n" + "="*70)
    print("🗄️  تولید دیتای کامل شرکت RFTEST")
    print("="*70)
    print("این عملیات شامل موارد زیر است:")
    print("✅ 30 محصول تجهیزات اندازه‌گیری با تصاویر")
    print("✅ 25 خدمات تخصصی با رسانه‌های مرتبط")
    print("✅ 20 مطلب آموزشی با تصاویر آموزشی")
    print("✅ 25 استعلام قیمت نمونه")
    print("✅ اطلاعات درباره ما و تماس با ما")
    print("⚠️  توجه: اطلاعات کاربران پاک نخواهد شد")
    print("="*70)
    
    response = input("آیا مایل به ادامه هستید؟ (بله/خیر): ").strip().lower()
    return response in ['بله', 'yes', 'y']

def create_default_images():
    """ساخت تصاویر پیش‌فرض"""
    logger.info("ساخت تصاویر پیش‌فرض...")
    
    # ایجاد پوشه‌ها
    dirs = ["static/uploads/products", "static/uploads/services", 
            "static/uploads/educational", "static/uploads/default"]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    def create_image(filename, text, bg_color=(240, 240, 240)):
        img = Image.new('RGB', (800, 600), bg_color)
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        # رسم متن در مرکز
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (800 - text_width) // 2
        y = (600 - text_height) // 2
        
        draw.text((x, y), text, fill=(60, 60, 60), font=font)
        
        # اضافه کردن لوگوی RFTEST
        draw.text((50, 50), "RFTEST.IR", fill=(0, 102, 204), font=font)
        
        img.save(filename)
        return filename
    
    # ساخت تصاویر مختلف
    images = {
        "product": create_image("static/uploads/default/product.jpg", "تجهیزات اندازه‌گیری", (245, 245, 245)),
        "service": create_image("static/uploads/default/service.jpg", "خدمات RFTEST", (240, 248, 255)),
        "educational": create_image("static/uploads/default/educational.jpg", "آموزش فنی", (248, 255, 240))
    }
    
    logger.info("✅ تصاویر پیش‌فرض ایجاد شد")
    return images

def clear_data(db):
    """پاک کردن دیتای قبلی"""
    logger.info("پاک کردن دیتای قبلی...")
    
    with db.conn.cursor() as cur:
        tables = [
            "product_media", "service_media", "educational_content_media",
            "products", "services", "educational_content", 
            "product_categories", "service_categories", "educational_categories",
            "inquiries"
        ]
        
        for table in tables:
            try:
                cur.execute(f"DELETE FROM {table}")
                logger.info(f"✅ جدول {table} پاک شد")
            except Exception as e:
                logger.warning(f"⚠️ مشکل در پاک کردن {table}: {e}")
        
        db.conn.commit()

def create_categories(db):
    """ایجاد دسته‌بندی‌ها"""
    logger.info("ایجاد دسته‌بندی‌ها...")
    
    # دسته‌بندی محصولات
    product_cats = [
        "اسیلوسکوپ", "اسپکتروم آنالایزر", "سیگنال ژنراتور", "نتورک آنالایزر",
        "پاورمتر و سنسور", "رادیوتستر", "فرکانس متر", "مالتی متر", 
        "تجهیزات کالیبراسیون", "آنتن آنالایزر", "نویز فیگور متر", "VNA کالیبراتور"
    ]
    
    # دسته‌بندی خدمات
    service_cats = [
        "کالیبراسیون تجهیزات", "تعمیرات تخصصی", "آموزش فنی", "مشاوره تخصصی",
        "نگهداری دوره‌ای", "پشتیبانی فنی", "طراحی آزمایشگاه"
    ]
    
    # دسته‌بندی آموزشی
    educational_cats = [
        "راهنمای کاربری", "اصول اندازه‌گیری RF", "کالیبراسیون", "تست و عیب‌یابی",
        "نکات فنی", "تکنولوژی‌های جدید", "پروژه‌های عملی"
    ]
    
    categories = {}
    
    with db.conn.cursor() as cur:
        # محصولات
        for cat in product_cats:
            cur.execute("""
                INSERT INTO product_categories (name, parent_id, created_at)
                VALUES (%s, %s, %s) RETURNING id
            """, (cat, None, datetime.now()))
            result = cur.fetchone()
            if result:
                categories[f"product_{cat}"] = result[0]
        
        # خدمات
        for cat in service_cats:
            cur.execute("""
                INSERT INTO service_categories (name, parent_id, created_at)
                VALUES (%s, %s, %s) RETURNING id
            """, (cat, None, datetime.now()))
            result = cur.fetchone()
            if result:
                categories[f"service_{cat}"] = result[0]
        
        # آموزشی
        for cat in educational_cats:
            cur.execute("""
                INSERT INTO educational_categories (name, parent_id, created_at)
                VALUES (%s, %s, %s) RETURNING id
            """, (cat, None, datetime.now()))
            result = cur.fetchone()
            if result:
                categories[f"educational_{cat}"] = result[0]
        
        db.conn.commit()
    
    logger.info(f"✅ {len(categories)} دسته‌بندی ایجاد شد")
    return categories

def create_products(db, categories):
    """ایجاد 30 محصول"""
    logger.info("ایجاد 30 محصول...")
    
    products_data = [
        # اسیلوسکوپ‌ها (8 محصول)
        {"name": "اسیلوسکوپ دیجیتال Keysight DSOX2002A", "cat": "اسیلوسکوپ", "price": 45000000, "brand": "Keysight", "model": "DSOX2002A", "featured": True},
        {"name": "اسیلوسکوپ دیجیتال Keysight DSOX3024T", "cat": "اسیلوسکوپ", "price": 85000000, "brand": "Keysight", "model": "DSOX3024T", "featured": True},
        {"name": "اسیلوسکوپ آنالوگ Tektronix 2235", "cat": "اسیلوسکوپ", "price": 18000000, "brand": "Tektronix", "model": "2235", "featured": False},
        {"name": "اسیلوسکوپ دیجیتال Rigol DS1054Z", "cat": "اسیلوسکوپ", "price": 22000000, "brand": "Rigol", "model": "DS1054Z", "featured": False},
        {"name": "اسیلوسکوپ دیجیتال Tektronix TBS1102B", "cat": "اسیلوسکوپ", "price": 12000000, "brand": "Tektronix", "model": "TBS1102B", "featured": False},
        {"name": "اسیلوسکوپ میکسد سیگنال Keysight MSOX3104T", "cat": "اسیلوسکوپ", "price": 165000000, "brand": "Keysight", "model": "MSOX3104T", "featured": True},
        {"name": "اسیلوسکوپ USB Hantek DSO2C10", "cat": "اسیلوسکوپ", "price": 3500000, "brand": "Hantek", "model": "DSO2C10", "featured": False},
        {"name": "اسیلوسکوپ پرتابل Fluke ScopeMeter 199C", "cat": "اسیلوسکوپ", "price": 78000000, "brand": "Fluke", "model": "199C", "featured": False},
        
        # اسپکتروم آنالایزرها (6 محصول)
        {"name": "اسپکتروم آنالایزر Rohde & Schwarz FSW50", "cat": "اسپکتروم آنالایزر", "price": 850000000, "brand": "Rohde & Schwarz", "model": "FSW50", "featured": True},
        {"name": "اسپکتروم آنالایزر Agilent E4402B", "cat": "اسپکتروم آنالایزر", "price": 125000000, "brand": "Agilent", "model": "E4402B", "featured": True},
        {"name": "اسپکتروم آنالایزر Keysight N9010A", "cat": "اسپکتروم آنالایزر", "price": 285000000, "brand": "Keysight", "model": "N9010A", "featured": False},
        {"name": "اسپکتروم آنالایزر Anritsu MS2720T", "cat": "اسپکتروم آنالایزر", "price": 195000000, "brand": "Anritsu", "model": "MS2720T", "featured": False},
        {"name": "اسپکتروم آنالایزر پرتابل Rigol DSA832", "cat": "اسپکتروم آنالایزر", "price": 45000000, "brand": "Rigol", "model": "DSA832", "featured": False},
        {"name": "اسپکتروم آنالایزر USB TinySA Ultra", "cat": "اسپکتروم آنالایزر", "price": 2800000, "brand": "TinySA", "model": "Ultra", "featured": False},
        
        # سیگنال ژنراتورها (5 محصول)
        {"name": "سیگنال ژنراتور Keysight E8257D", "cat": "سیگنال ژنراتور", "price": 780000000, "brand": "Keysight", "model": "E8257D", "featured": True},
        {"name": "سیگنال ژنراتور Agilent E4438C", "cat": "سیگنال ژنراتور", "price": 185000000, "brand": "Agilent", "model": "E4438C", "featured": False},
        {"name": "سیگنال ژنراتور Rohde & Schwarz SMB100A", "cat": "سیگنال ژنراتور", "price": 125000000, "brand": "Rohde & Schwarz", "model": "SMB100A", "featured": False},
        {"name": "فانکشن ژنراتور Rigol DG1062Z", "cat": "سیگنال ژنراتور", "price": 15000000, "brand": "Rigol", "model": "DG1062Z", "featured": False},
        {"name": "آربیتری ژنراتور Keysight 33622A", "cat": "سیگنال ژنراتور", "price": 95000000, "brand": "Keysight", "model": "33622A", "featured": False},
        
        # رادیوتسترها (4 محصول)
        {"name": "رادیوتستر Aeroflex 3920B", "cat": "رادیوتستر", "price": 320000000, "brand": "Aeroflex", "model": "3920B", "featured": True},
        {"name": "رادیوتستر Marconi 2955B", "cat": "رادیوتستر", "price": 85000000, "brand": "Marconi", "model": "2955B", "featured": False},
        {"name": "رادیوتستر IFR 2965", "cat": "رادیوتستر", "price": 145000000, "brand": "IFR", "model": "2965", "featured": False},
        {"name": "رادیوتستر پرتابل Aeroflex 3515AR", "cat": "رادیوتستر", "price": 285000000, "brand": "Aeroflex", "model": "3515AR", "featured": False},
        
        # نتورک آنالایزرها (3 محصول)
        {"name": "نتورک آنالایزر Keysight E5071C", "cat": "نتورک آنالایزر", "price": 385000000, "brand": "Keysight", "model": "E5071C", "featured": True},
        {"name": "نتورک آنالایزر Rohde & Schwarz ZNB20", "cat": "نتورک آنالایزر", "price": 485000000, "brand": "Rohde & Schwarz", "model": "ZNB20", "featured": True},
        {"name": "VNA پرتابل NanoVNA H4", "cat": "نتورک آنالایزر", "price": 1200000, "brand": "NanoVNA", "model": "H4", "featured": False},
        
        # پاورمتر و سنسور (2 محصول)
        {"name": "پاورمتر Keysight N1911A", "cat": "پاورمتر و سنسور", "price": 65000000, "brand": "Keysight", "model": "N1911A", "featured": False},
        {"name": "سنسور توان Rohde & Schwarz NRP-Z21", "cat": "پاورمتر و سنسور", "price": 28000000, "brand": "Rohde & Schwarz", "model": "NRP-Z21", "featured": False},
        
        # سایر تجهیزات (2 محصول)
        {"name": "فرکانس کانتر Keysight 53230A", "cat": "فرکانس متر", "price": 145000000, "brand": "Keysight", "model": "53230A", "featured": False},
        {"name": "مالتی متر دقیق Keysight 34470A", "cat": "مالتی متر", "price": 32000000, "brand": "Keysight", "model": "34470A", "featured": False}
    ]
    
    with db.conn.cursor() as cur:
        for i, product in enumerate(products_data, 1):
            cat_key = f"product_{product['cat']}"
            category_id = categories.get(cat_key)
            if not category_id:
                continue
            
            description = f"تجهیز پیشرفته اندازه‌گیری {product['cat']} از برند معتبر {product['brand']}. مناسب برای کاربردهای حرفه‌ای و آزمایشگاهی."
            tags = f"{product['cat']},{product['brand']},{product['model']},تجهیزات اندازه‌گیری"
            
            cur.execute("""
                INSERT INTO products (
                    name, description, price, category_id, brand, model,
                    tags, in_stock, featured, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                product["name"], description, product["price"], category_id,
                product["brand"], product["model"], tags, True, 
                product["featured"], datetime.now()
            ))
            
            product_id = cur.fetchone()[0]
            
            # اضافه کردن تصاویر
            product_dir = f"static/uploads/products/{product_id}"
            os.makedirs(product_dir, exist_ok=True)
            
            # تصویر اصلی
            import shutil
            main_image = f"{product_dir}/main.jpg"
            shutil.copy("static/uploads/default/product.jpg", main_image)
            
            cur.execute("""
                INSERT INTO product_media (product_id, file_id, file_type)
                VALUES (%s, %s, %s)
            """, (product_id, f"uploads/products/{product_id}/main.jpg", "photo"))
            
            # تصاویر اضافی
            for j in range(2, 5):
                extra_image = f"{product_dir}/extra_{j}.jpg"
                shutil.copy("static/uploads/default/product.jpg", extra_image)
                cur.execute("""
                    INSERT INTO product_media (product_id, file_id, file_type)
                    VALUES (%s, %s, %s)
                """, (product_id, f"uploads/products/{product_id}/extra_{j}.jpg", "photo"))
            
            logger.info(f"✅ محصول {i}/30: {product['name']}")
        
        db.conn.commit()

def create_services(db, categories):
    """ایجاد 25 خدمات"""
    logger.info("ایجاد 25 خدمات...")
    
    services_data = [
        # کالیبراسیون (6 خدمات)
        {"name": "کالیبراسیون اسیلوسکوپ", "cat": "کالیبراسیون تجهیزات", "price": 3500000, "featured": True},
        {"name": "کالیبراسیون اسپکتروم آنالایزر", "cat": "کالیبراسیون تجهیزات", "price": 4500000, "featured": True},
        {"name": "کالیبراسیون سیگنال ژنراتور", "cat": "کالیبراسیون تجهیزات", "price": 4000000, "featured": True},
        {"name": "کالیبراسیون پاورمتر و سنسور", "cat": "کالیبراسیون تجهیزات", "price": 2500000, "featured": False},
        {"name": "کالیبراسیون نتورک آنالایزر", "cat": "کالیبراسیون تجهیزات", "price": 5500000, "featured": False},
        {"name": "کالیبراسیون رادیوتستر", "cat": "کالیبراسیون تجهیزات", "price": 6000000, "featured": False},
        
        # تعمیرات (5 خدمات)
        {"name": "تعمیر تخصصی اسیلوسکوپ", "cat": "تعمیرات تخصصی", "price": 5500000, "featured": True},
        {"name": "تعمیر اسپکتروم آنالایزر", "cat": "تعمیرات تخصصی", "price": 8500000, "featured": True},
        {"name": "تعمیر سیگنال ژنراتور", "cat": "تعمیرات تخصصی", "price": 6500000, "featured": False},
        {"name": "تعمیر رادیوتستر", "cat": "تعمیرات تخصصی", "price": 12000000, "featured": False},
        {"name": "بازسازی تجهیزات قدیمی", "cat": "تعمیرات تخصصی", "price": 15000000, "featured": False},
        
        # آموزش (5 خدمات)
        {"name": "آموزش کاربردی RF و میکروویو", "cat": "آموزش فنی", "price": 12000000, "featured": True},
        {"name": "آموزش استفاده از اسیلوسکوپ", "cat": "آموزش فنی", "price": 6000000, "featured": True},
        {"name": "آموزش اسپکتروم آنالیز", "cat": "آموزش فنی", "price": 8000000, "featured": False},
        {"name": "آموزش S-parameter measurements", "cat": "آموزش فنی", "price": 10000000, "featured": False},
        {"name": "دوره جامع تست EMC", "cat": "آموزش فنی", "price": 15000000, "featured": False},
        
        # مشاوره (4 خدمات)
        {"name": "مشاوره انتخاب تجهیزات آزمایشگاه", "cat": "مشاوره تخصصی", "price": 2000000, "featured": False},
        {"name": "مشاوره طراحی آزمایشگاه RF", "cat": "مشاوره تخصصی", "price": 5000000, "featured": False},
        {"name": "مشاوره استانداردهای کالیبراسیون", "cat": "مشاوره تخصصی", "price": 3000000, "featured": False},
        {"name": "بررسی و ارزیابی تجهیزات", "cat": "مشاوره تخصصی", "price": 2500000, "featured": False},
        
        # سایر خدمات (5 خدمات)
        {"name": "تنظیم و راه‌اندازی تجهیزات", "cat": "نگهداری دوره‌ای", "price": 3000000, "featured": False},
        {"name": "قرارداد نگهداری سالانه", "cat": "نگهداری دوره‌ای", "price": 15000000, "featured": True},
        {"name": "پشتیبانی فنی 24 ساعته", "cat": "پشتیبانی فنی", "price": 500000, "featured": False},
        {"name": "خدمات اورژانسی", "cat": "پشتیبانی فنی", "price": 8000000, "featured": False},
        {"name": "طراحی کامل آزمایشگاه", "cat": "طراحی آزمایشگاه", "price": 25000000, "featured": True}
    ]
    
    with db.conn.cursor() as cur:
        for i, service in enumerate(services_data, 1):
            cat_key = f"service_{service['cat']}"
            category_id = categories.get(cat_key)
            if not category_id:
                continue
            
            description = f"خدمات تخصصی {service['cat']} توسط متخصصان مجرب RFTEST. کیفیت بالا و قیمت مناسب."
            tags = f"{service['cat']},RFTEST,خدمات تخصصی"
            
            cur.execute("""
                INSERT INTO services (
                    name, description, price, category_id, tags, featured, available, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                service["name"], description, service["price"], category_id,
                tags, service["featured"], True, datetime.now()
            ))
            
            service_id = cur.fetchone()[0]
            
            # اضافه کردن تصاویر خدمات
            service_dir = f"static/uploads/services/{service_id}"
            os.makedirs(service_dir, exist_ok=True)
            
            import shutil
            main_image = f"{service_dir}/main.jpg"
            shutil.copy("static/uploads/default/service.jpg", main_image)
            
            cur.execute("""
                INSERT INTO service_media (service_id, file_id, file_type)
                VALUES (%s, %s, %s)
            """, (service_id, f"uploads/services/{service_id}/main.jpg", "photo"))
            
            logger.info(f"✅ خدمت {i}/25: {service['name']}")
        
        db.conn.commit()

def create_educational_content(db, categories):
    """ایجاد 20 مطلب آموزشی"""
    logger.info("ایجاد 20 مطلب آموزشی...")
    
    educational_data = [
        # راهنمای کاربری (4 مطلب)
        {"title": "راهنمای کامل استفاده از اسیلوسکوپ دیجیتال", "cat": "راهنمای کاربری", "featured": True},
        {"title": "نحوه کار با اسپکتروم آنالایزر", "cat": "راهنمای کاربری", "featured": True},
        {"title": "راهنمای استفاده از نتورک آنالایزر", "cat": "راهنمای کاربری", "featured": False},
        {"title": "تنظیمات اولیه رادیوتستر", "cat": "راهنمای کاربری", "featured": False},
        
        # اصول اندازه‌گیری RF (4 مطلب)
        {"title": "اصول اندازه‌گیری توان RF", "cat": "اصول اندازه‌گیری RF", "featured": True},
        {"title": "مفهوم نویز فاز در سیگنال‌ها", "cat": "اصول اندازه‌گیری RF", "featured": True},
        {"title": "تئوری اسپکتروم و تحلیل فرکانسی", "cat": "اصول اندازه‌گیری RF", "featured": False},
        {"title": "اندازه‌گیری امپدانس و SWR", "cat": "اصول اندازه‌گیری RF", "featured": False},
        
        # کالیبراسیون (3 مطلب)
        {"title": "اصول کالیبراسیون تجهیزات اندازه‌گیری", "cat": "کالیبراسیون", "featured": True},
        {"title": "استانداردهای بین‌المللی کالیبراسیون", "cat": "کالیبراسیون", "featured": False},
        {"title": "دوره‌های کالیبراسیون و نگهداری", "cat": "کالیبراسیون", "featured": False},
        
        # تست و عیب‌یابی (3 مطلب)
        {"title": "روش‌های عیب‌یابی در مدارات RF", "cat": "تست و عیب‌یابی", "featured": True},
        {"title": "تکنیک‌های اندازه‌گیری S-parameters", "cat": "تست و عیب‌یابی", "featured": False},
        {"title": "تست تداخل و EMC", "cat": "تست و عیب‌یابی", "featured": False},
        
        # نکات فنی (3 مطلب)
        {"title": "نکات مهم در انتخاب کابل RF", "cat": "نکات فنی", "featured": False},
        {"title": "بهینه‌سازی دقت اندازه‌گیری", "cat": "نکات فنی", "featured": False},
        {"title": "حفاظت از تجهیزات در برابر آسیب", "cat": "نکات فنی", "featured": False},
        
        # تکنولوژی‌های جدید (2 مطلب)
        {"title": "تکنولوژی 5G و تست آن", "cat": "تکنولوژی‌های جدید", "featured": True},
        {"title": "IoT و تست تجهیزات کم‌مصرف", "cat": "تکنولوژی‌های جدید", "featured": False},
        
        # پروژه‌های عملی (1 مطلب)
        {"title": "پروژه طراحی و تست فیلتر RF", "cat": "پروژه‌های عملی", "featured": False}
    ]
    
    with db.conn.cursor() as cur:
        for i, content in enumerate(educational_data, 1):
            cat_key = f"educational_{content['cat']}"
            category_id = categories.get(cat_key)
            if not category_id:
                continue
            
            full_content = f"این مطلب جامع در زمینه {content['cat']} تهیه شده است. شامل توضیحات کامل، مثال‌های عملی و نکات کاربردی برای متخصصان و علاقه‌مندان به تجهیزات اندازه‌گیری RF."
            
            cur.execute("""
                INSERT INTO educational_content (
                    title, content, category, category_id, created_at
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                content["title"], full_content, content["cat"], category_id, datetime.now()
            ))
            
            content_id = cur.fetchone()[0]
            
            # اضافه کردن تصاویر آموزشی
            edu_dir = f"static/uploads/educational/{content_id}"
            os.makedirs(edu_dir, exist_ok=True)
            
            import shutil
            main_image = f"{edu_dir}/main.jpg"
            shutil.copy("static/uploads/default/educational.jpg", main_image)
            
            cur.execute("""
                INSERT INTO educational_content_media (content_id, file_id, file_type)
                VALUES (%s, %s, %s)
            """, (content_id, f"uploads/educational/{content_id}/main.jpg", "photo"))
            
            logger.info(f"✅ مطلب آموزشی {i}/20: {content['title']}")
        
        db.conn.commit()

def create_inquiries(db):
    """ایجاد 25 استعلام قیمت"""
    logger.info("ایجاد 25 استعلام قیمت...")
    
    inquiries_data = [
        {"user_id": 7625738591, "name": "مهندس احمد رضایی", "phone": "09121234567", "desc": "استعلام قیمت اسیلوسکوپ 100MHz برای آزمایشگاه دانشگاه"},
        {"user_id": 987654321, "name": "شرکت فناوری پارس", "phone": "02144556677", "desc": "درخواست کالیبراسیون 5 دستگاه اسپکتروم آنالایزر Agilent"},
        {"user_id": 123456789, "name": "دکتر محمد محمدی", "phone": "09359876543", "desc": "آیا دوره آموزشی RF برای دانشجویان ارشد برگزار می‌کنید؟"},
        {"user_id": 555666777, "name": "مهندس فاطمه نوری", "phone": "09128887766", "desc": "نیاز به مشاوره برای تجهیز آزمایشگاه تست EMC دارم"},
        {"user_id": 111222333, "name": "شرکت الکترونیک آریا", "phone": "02133445566", "desc": "استعلام قیمت رادیوتستر Aeroflex 3920B"},
        {"user_id": 444555666, "name": "آقای علی احمدی", "phone": "09135554433", "desc": "آیا تعمیر اسیلوسکوپ Tektronix 2465 را انجام می‌دهید؟"},
        {"user_id": 777888999, "name": "مهندس سارا کریمی", "phone": "09124443322", "desc": "درخواست آموزش کار با نتورک آنالایزر"},
        {"user_id": 333444555, "name": "شرکت مخابرات ایران", "phone": "02177889900", "desc": "استعلام قیمت سیگنال ژنراتور تا 6GHz"},
        {"user_id": 666777888, "name": "دکتر رضا پوری", "phone": "09366655544", "desc": "نیاز به کالیبراسیون فوری پاورمتر HP 437B دارم"},
        {"user_id": 222333444, "name": "مهندس حسن زارعی", "phone": "09357778899", "desc": "استعلام قیمت اسپکتروم آنالایزر Rohde & Schwarz FSW"},
        {"user_id": 888999111, "name": "شرکت رادار پردازش", "phone": "02155667788", "desc": "نیاز به آموزش تخصصی S-parameter measurements"},
        {"user_id": 999111222, "name": "مهندس مریم صادقی", "phone": "09147775566", "desc": "استعلام قیمت کالیبراسیون سالانه 8 دستگاه"},
        {"user_id": 111333555, "name": "آقای محسن رستمی", "phone": "09198886644", "desc": "آیا رادیوتستر Marconi 2955B دست دوم در انبار دارید؟"},
        {"user_id": 444666888, "name": "شرکت نوآوری فن", "phone": "02166554433", "desc": "درخواست مشاوره انتخاب تجهیزات برای آزمایشگاه تست محصولات IoT"},
        {"user_id": 777999222, "name": "دکتر امیر حسینی", "phone": "09351112233", "desc": "استعلام اجاره کوتاه مدت نتورک آنالایزر"},
        {"user_id": 555777999, "name": "مهندس زهرا احمدی", "phone": "09122223344", "desc": "درخواست قیمت مجموعه کامل تجهیزات آزمایشگاه RF"},
        {"user_id": 333555777, "name": "شرکت ایمن الکترونیک", "phone": "02144445566", "desc": "آیا امکان تعمیر تجهیزات قدیمی HP وجود دارد؟"},
        {"user_id": 666888111, "name": "مهندس کامران رضایی", "phone": "09133334455", "desc": "نیاز به آموزش تست EMC برای تیم طراحی"},
        {"user_id": 222444666, "name": "آقای مهدی کریمی", "phone": "09144445566", "desc": "استعلام قیمت اسیلوسکوپ میکسد سیگنال"},
        {"user_id": 888111333, "name": "شرکت فناور سپهر", "phone": "02155556677", "desc": "درخواست مشاوره طراحی آزمایشگاه استاندارد"},
        {"user_id": 111444777, "name": "دکتر فریده پورحسن", "phone": "09155557788", "desc": "آیا کالیبراسیون تجهیزات در محل دانشگاه انجام می‌شود؟"},
        {"user_id": 999222555, "name": "مهندس بهزاد نظری", "phone": "09166668899", "desc": "استعلام قیمت پکیج کامل تجهیزات تست 5G"},
        {"user_id": 444777111, "name": "شرکت پیشرو تک", "phone": "02177778899", "desc": "نیاز به پشتیبانی فنی مداوم برای آزمایشگاه"},
        {"user_id": 777111444, "name": "مهندس نیما فتحی", "phone": "09177779911", "desc": "درخواست آموزش کار با VNA و تفسیر نتایج"},
        {"user_id": 555888222, "name": "شرکت دانش‌پژوه", "phone": "02188889911", "desc": "استعلام قیمت قرارداد نگهداری ساليانه تجهیزات"}
    ]
    
    with db.conn.cursor() as cur:
        for i, inquiry in enumerate(inquiries_data, 1):
            # تاریخ تصادفی در 6 ماه اخیر
            days_ago = random.randint(1, 180)
            created_date = datetime.now() - timedelta(days=days_ago)
            
            cur.execute("""
                INSERT INTO inquiries (
                    user_id, name, phone, description, status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                inquiry["user_id"], inquiry["name"], inquiry["phone"],
                inquiry["desc"], "pending", created_date
            ))
            
            logger.info(f"✅ استعلام {i}/25: {inquiry['name']}")
        
        db.conn.commit()

def main():
    """اجرای اصلی"""
    if not confirm_reset():
        print("❌ عملیات لغو شد.")
        return
    
    print("\n🚀 شروع تولید دیتای کامل RFTEST...")
    
    try:
        # اتصال به دیتابیس
        db = Database()
        
        # پاک کردن دیتای قبلی
        clear_data(db)
        
        # ساخت تصاویر پیش‌فرض
        create_default_images()
        
        # ایجاد دسته‌بندی‌ها
        categories = create_categories(db)
        
        # ایجاد محتوا
        create_products(db, categories)
        create_services(db, categories)
        create_educational_content(db, categories)
        create_inquiries(db)
        
        print("\n" + "="*70)
        print("🎉 دیتای کامل RFTEST با موفقیت ایجاد شد!")
        print("="*70)
        print("✅ 30 محصول تجهیزات اندازه‌گیری با تصاویر")
        print("✅ 25 خدمات تخصصی با رسانه‌های مرتبط")
        print("✅ 20 مطلب آموزشی با تصاویر آموزشی")
        print("✅ 25 استعلام قیمت واقعی")
        print("✅ دسته‌بندی‌های کامل و منظم")
        print("✅ رسانه‌های اصلی و اضافی برای همه محتوا")
        print()
        print("🌐 وب پنل: مدیریت کامل محتوا")
        print("🤖 بات تلگرام: @RFCatbot")
        print("📧 ایمیل: rftestiran@gmail.com")
        print("📞 تلفن: 09125445277")
        print("🌍 وبسایت: www.rftest.ir")
        print("="*70)
        
    except Exception as e:
        logger.error(f"❌ خطا در تولید دیتا: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()