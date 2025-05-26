#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فایل پر کردن دیتابیس با اطلاعات کامل و واقعی
تجهیزات اندازه‌گیری مخابراتی - RFTest Iran
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from database import Database
from PIL import Image, ImageDraw, ImageFont
import random

# تنظیم logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveDataSeeder:
    def __init__(self):
        self.db = Database()
        
    def confirm_data_reset(self):
        """تایید پاک کردن داده‌های موجود"""
        print("\n" + "="*60)
        print("🚨 هشدار: پاک کردن داده‌های موجود دیتابیس")
        print("="*60)
        print("این عمل تمام داده‌های موجود در دیتابیس را پاک خواهد کرد:")
        print("- محصولات")
        print("- خدمات") 
        print("- مطالب آموزشی")
        print("- استعلام‌های قیمت")
        print("- تصاویر و فایل‌ها")
        print("- دسته‌بندی‌ها")
        print("\n✅ تایید شده - شروع پاک کردن و پر کردن مجدد...")
        
        return True
    
    def clear_existing_data(self):
        """پاک کردن داده‌های موجود"""
        logger.info("در حال پاک کردن داده‌های موجود...")
        
        conn = self.db.get_conn()
        try:
            with conn:
                # حذف داده‌ها به ترتیب وابستگی
                conn.execute("DELETE FROM product_media;")
                conn.execute("DELETE FROM service_media;")
                conn.execute("DELETE FROM educational_media;")
                conn.execute("DELETE FROM inquiries;")
                conn.execute("DELETE FROM products;")
                conn.execute("DELETE FROM services;")
                conn.execute("DELETE FROM educational_content;")
                conn.execute("DELETE FROM categories;")
                
                logger.info("✅ داده‌های موجود پاک شدند")
        except Exception as e:
            logger.error(f"خطا در پاک کردن داده‌ها: {e}")
            raise
    
    def create_default_image(self, filename, text, width=800, height=600, bg_color=(240, 240, 240)):
        """ساخت تصویر پیش‌فرض"""
        os.makedirs("static/uploads/products", exist_ok=True)
        os.makedirs("static/uploads/services", exist_ok=True)
        os.makedirs("static/uploads/educational", exist_ok=True)
        
        # ساخت تصویر
        image = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(image)
        
        try:
            # استفاده از فونت پیش‌فرض
            font = ImageFont.load_default()
        except:
            font = None
        
        # محاسبه موقعیت متن برای قرارگیری در وسط
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(text) * 10
            text_height = 20
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # رسم متن
        draw.text((x, y), text, fill=(100, 100, 100), font=font)
        
        # ذخیره تصویر
        image.save(filename)
        return filename
    
    def seed_categories(self):
        """ایجاد دسته‌بندی‌ها"""
        logger.info("در حال ایجاد دسته‌بندی‌ها...")
        
        categories = [
            # دسته‌بندی محصولات
            ("اسیلوسکوپ", "products", "دستگاه‌های اسیلوسکوپ آنالوگ و دیجیتال"),
            ("اسپکتروم آنالایزر", "products", "تحلیل‌گرهای طیف فرکانسی"),
            ("سیگنال ژنراتور", "products", "تولیدکننده‌های سیگنال"),
            ("نتورک آنالایزر", "products", "تحلیل‌گرهای شبکه"),
            ("پاور متر", "products", "اندازه‌گیری توان RF"),
            ("رادیوتستر", "products", "تستر رادیوهای دوطرفه"),
            ("فرکانس متر", "products", "اندازه‌گیری فرکانس دقیق"),
            ("سایت مستر", "products", "تجهیزات تست آنتن و کابل"),
            
            # دسته‌بندی خدمات
            ("کالیبراسیون", "services", "کالیبراسیون تجهیزات اندازه‌گیری"),
            ("تعمیرات", "services", "تعمیر و نگهداری تجهیزات"),
            ("مشاوره فنی", "services", "مشاوره در انتخاب تجهیزات"),
            ("آموزش", "services", "دوره‌های آموزشی تخصصی"),
            
            # دسته‌بندی آموزشی
            ("مبانی اندازه‌گیری", "educational", "اصول پایه اندازه‌گیری RF"),
            ("کار با دستگاه‌ها", "educational", "آموزش کار با تجهیزات"),
            ("کالیبراسیون", "educational", "آموزش کالیبراسیون"),
            ("تعمیرات", "educational", "راهنمای تعمیرات"),
        ]
        
        conn = self.db.get_conn()
        try:
            with conn:
                for name, category_type, description in categories:
                    conn.execute(
                        "INSERT INTO categories (name, type, description) VALUES (?, ?, ?)",
                        (name, category_type, description)
                    )
            logger.info(f"✅ {len(categories)} دسته‌بندی ایجاد شد")
        except Exception as e:
            logger.error(f"خطا در ایجاد دسته‌بندی‌ها: {e}")
            raise
    
    def seed_products(self):
        """ایجاد محصولات"""
        logger.info("در حال ایجاد محصولات...")
        
        products_data = [
            # اسیلوسکوپ‌ها
            {
                "name": "اسیلوسکوپ دیجیتال Keysight DSOX3024T",
                "description": "اسیلوسکوپ دیجیتال 4 کاناله 200MHz با صفحه نمایش لمسی 8.5 اینچی. دارای حافظه عمیق 4 مگاپوینت و نرخ نمونه‌برداری 5 گیگاسمپل بر ثانیه.",
                "price": 850000000,
                "model": "DSOX3024T",
                "manufacturer": "Keysight Technologies",
                "in_stock": True,
                "featured": True,
                "tags": "4-channel,200MHz,touchscreen,deep-memory",
                "category": "اسیلوسکوپ"
            },
            {
                "name": "اسیلوسکوپ آنالوگ Tektronix 2465B",
                "description": "اسیلوسکوپ آنالوگ 4 کاناله 400MHz کلاسیک. دستگاه قابل اعتماد برای کاربردهای تحقیقاتی و صنعتی.",
                "price": 125000000,
                "model": "2465B",
                "manufacturer": "Tektronix",
                "in_stock": True,
                "featured": False,
                "tags": "analog,4-channel,400MHz,classic",
                "category": "اسیلوسکوپ"
            },
            {
                "name": "اسیلوسکوپ USB Hantek DSO2C10",
                "description": "اسیلوسکوپ USB دو کاناله 100MHz با نرم‌افزار Windows. مناسب برای کاربردهای آموزشی و تست سریع.",
                "price": 15000000,
                "model": "DSO2C10",
                "manufacturer": "Hantek",
                "in_stock": True,
                "featured": False,
                "tags": "USB,2-channel,100MHz,portable",
                "category": "اسیلوسکوپ"
            },
            
            # اسپکتروم آنالایزرها
            {
                "name": "اسپکتروم آنالایزر Keysight N9020A MXA",
                "description": "اسپکتروم آنالایزر حرفه‌ای 10Hz تا 26.5GHz با نویز فاز پایین و دقت بالا. مناسب برای تحلیل سیگنال‌های پیچیده.",
                "price": 2500000000,
                "model": "N9020A",
                "manufacturer": "Keysight Technologies",
                "in_stock": True,
                "featured": True,
                "tags": "26.5GHz,low-phase-noise,professional",
                "category": "اسپکتروم آنالایزر"
            },
            {
                "name": "اسپکتروم آنالایزر Rigol DSA832",
                "description": "اسپکتروم آنالایزر 9kHz تا 3.2GHz با رابط کاربری ساده. مناسب برای کاربردهای عمومی RF.",
                "price": 180000000,
                "model": "DSA832",
                "manufacturer": "Rigol",
                "in_stock": True,
                "featured": False,
                "tags": "3.2GHz,economical,user-friendly",
                "category": "اسپکتروم آنالایزر"
            },
            
            # سیگنال ژنراتورها
            {
                "name": "سیگنال ژنراتور Keysight E8257D PSG",
                "description": "سیگنال ژنراتور مایکروویو 100kHz تا 67GHz با خلوص طیفی فوق‌العاده. برای کاربردهای تحقیقاتی پیشرفته.",
                "price": 4200000000,
                "model": "E8257D",
                "manufacturer": "Keysight Technologies",
                "in_stock": False,
                "featured": True,
                "tags": "67GHz,microwave,research-grade",
                "category": "سیگنال ژنراتور"
            },
            {
                "name": "فانکشن ژنراتور Rigol DG4062",
                "description": "فانکشن ژنراتور دو کاناله 60MHz با قابلیت تولید اشکال موج مختلف. دارای حافظه برای ذخیره تنظیمات.",
                "price": 95000000,
                "model": "DG4062",
                "manufacturer": "Rigol",
                "in_stock": True,
                "featured": False,
                "tags": "dual-channel,60MHz,arbitrary-waveform",
                "category": "سیگنال ژنراتور"
            },
            
            # نتورک آنالایزرها
            {
                "name": "نتورک آنالایزر Keysight E5071C ENA",
                "description": "نتورک آنالایزر 300kHz تا 20GHz با 4 پورت. دقت بالا در اندازه‌گیری پارامترهای S.",
                "price": 1800000000,
                "model": "E5071C",
                "manufacturer": "Keysight Technologies",
                "in_stock": True,
                "featured": True,
                "tags": "20GHz,4-port,high-accuracy",
                "category": "نتورک آنالایزر"
            },
            {
                "name": "نتورک آنالایزر NanoVNA-H4",
                "description": "نتورک آنالایزر کوچک و قابل حمل 10kHz تا 1.5GHz. مناسب برای هواداران رادیو و کاربردهای آموزشی.",
                "price": 8500000,
                "model": "NanoVNA-H4",
                "manufacturer": "NanoVNA",
                "in_stock": True,
                "featured": False,
                "tags": "portable,1.5GHz,affordable",
                "category": "نتورک آنالایزر"
            },
            
            # پاور مترها
            {
                "name": "پاور متر Keysight E4417A EPM-P",
                "description": "پاور متر دو کاناله با دقت ±0.05dB. سازگار با سنسورهای مختلف E-Series.",
                "price": 320000000,
                "model": "E4417A",
                "manufacturer": "Keysight Technologies",
                "in_stock": True,
                "featured": False,
                "tags": "dual-channel,high-accuracy,E-series",
                "category": "پاور متر"
            },
            {
                "name": "پاور متر USB Mini-Circuits PWR-6GHS+",
                "description": "پاور متر USB کوچک 0.5 تا 6000MHz با نرم‌افزار Windows. مناسب برای تست سریع.",
                "price": 45000000,
                "model": "PWR-6GHS+",
                "manufacturer": "Mini-Circuits",
                "in_stock": True,
                "featured": False,
                "tags": "USB,6GHz,compact",
                "category": "پاور متر"
            },
            
            # رادیوتسترها
            {
                "name": "رادیوتستر Aeroflex 3920B",
                "description": "رادیوتستر دیجیتال با پشتیبانی از استانداردهای DMR, TETRA, P25. شامل اسپکتروم آنالایزر و سیگنال ژنراتور.",
                "price": 1200000000,
                "model": "3920B",
                "manufacturer": "Aeroflex",
                "in_stock": False,
                "featured": True,
                "tags": "digital,DMR,TETRA,P25",
                "category": "رادیوتستر"
            },
            {
                "name": "رادیوتستر IFR 2968",
                "description": "رادیوتستر GSM 900/1800MHz کلاسیک. قابل اعتماد برای تست بیسیم‌های آنالوگ و دیجیتال.",
                "price": 385000000,
                "model": "2968",
                "manufacturer": "IFR",
                "in_stock": True,
                "featured": False,
                "tags": "GSM,900MHz,1800MHz,classic",
                "category": "رادیوتستر"
            }
        ]
        
        conn = self.db.get_conn()
        try:
            with conn:
                for i, product in enumerate(products_data, 1):
                    # دریافت category_id
                    category_result = conn.execute(
                        "SELECT id FROM categories WHERE name = ? AND type = 'products'",
                        (product["category"],)
                    ).fetchone()
                    
                    if not category_result:
                        continue
                    
                    category_id = category_result[0]
                    
                    # ایجاد محصول
                    result = conn.execute("""
                        INSERT INTO products (name, description, price, model, manufacturer, 
                                            in_stock, featured, tags, category_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product["name"], product["description"], product["price"],
                        product["model"], product["manufacturer"], product["in_stock"],
                        product["featured"], product["tags"], category_id
                    ))
                    
                    product_id = result.lastrowid
                    
                    # ایجاد تصویر اصلی
                    main_image_path = f"static/uploads/products/product_{product_id}_main.jpg"
                    self.create_default_image(
                        main_image_path,
                        f"{product['model']}\n{product['manufacturer']}",
                        800, 600, (250, 250, 250)
                    )
                    
                    conn.execute("""
                        INSERT INTO product_media (product_id, file_path, media_type, is_main)
                        VALUES (?, ?, 'image', 1)
                    """, (product_id, main_image_path))
                    
                    # ایجاد تصاویر اضافی
                    for j in range(2, random.randint(3, 5)):
                        extra_image_path = f"static/uploads/products/product_{product_id}_extra_{j}.jpg"
                        self.create_default_image(
                            extra_image_path,
                            f"نمای {j}\n{product['model']}",
                            600, 450, (240, 245, 250)
                        )
                        
                        conn.execute("""
                            INSERT INTO product_media (product_id, file_path, media_type, is_main)
                            VALUES (?, ?, 'image', 0)
                        """, (product_id, extra_image_path))
            
            logger.info(f"✅ {len(products_data)} محصول ایجاد شد")
        except Exception as e:
            logger.error(f"خطا در ایجاد محصولات: {e}")
            raise
    
    def seed_services(self):
        """ایجاد خدمات"""
        logger.info("در حال ایجاد خدمات...")
        
        services_data = [
            # خدمات کالیبراسیون
            {
                "name": "کالیبراسیون اسیلوسکوپ",
                "description": "کالیبراسیون دقیق اسیلوسکوپ‌های آنالوگ و دیجیتال طبق استانداردهای ملی. شامل گواهینامه معتبر کالیبراسیون.",
                "price": 12000000,
                "duration": "3-5 روز کاری",
                "features": "گواهینامه کالیبراسیون,تست دقت,تنظیم پارامترها,گزارش فنی",
                "category": "کالیبراسیون"
            },
            {
                "name": "کالیبراسیون اسپکتروم آنالایزر",
                "description": "کالیبراسیون اسپکتروم آنالایزر با استانداردهای فرکانس و دامنه. بررسی نویز فاز و خطای فرکانس.",
                "price": 18000000,
                "duration": "5-7 روز کاری",
                "features": "کالیبراسیون فرکانس,کالیبراسیون دامنه,تست نویز فاز,گواهینامه",
                "category": "کالیبراسیون"
            },
            {
                "name": "کالیبراسیون پاور متر",
                "description": "کالیبراسیون دقیق پاور متر و سنسورهای توان در محدوده فرکانسی مختلف.",
                "price": 8500000,
                "duration": "2-3 روز کاری",
                "features": "کالیبراسیون توان,تست خطی بودن,گواهینامه معتبر",
                "category": "کالیبراسیون"
            },
            
            # خدمات تعمیرات
            {
                "name": "تعمیر اسیلوسکوپ",
                "description": "تعمیر و نگهداری اسیلوسکوپ‌های مختلف. شامل تعویض قطعات، تنظیم مجدد و تست عملکرد.",
                "price": 25000000,
                "duration": "7-14 روز کاری",
                "features": "عیب‌یابی کامل,تعویض قطعات,تنظیم مجدد,تست نهایی",
                "category": "تعمیرات"
            },
            {
                "name": "تعمیر سیگنال ژنراتور",
                "description": "تعمیر انواع سیگنال ژنراتور و فانکشن ژنراتور. بازسازی مدارات فرکانس و تقویت‌کننده.",
                "price": 32000000,
                "duration": "10-21 روز کاری",
                "features": "تعمیر مدار فرکانس,بازسازی تقویت‌کننده,کالیبراسیون,تست",
                "category": "تعمیرات"
            },
            {
                "name": "تعمیر رادیوتستر",
                "description": "تعمیر تخصصی رادیوتسترهای مختلف شامل آپدیت نرم‌افزار و تعویض قطعات.",
                "price": 45000000,
                "duration": "14-28 روز کاری",
                "features": "تعمیر سخت‌افزار,آپدیت نرم‌افزار,کالیبراسیون کامل",
                "category": "تعمیرات"
            },
            
            # خدمات مشاوره
            {
                "name": "مشاوره انتخاب تجهیزات",
                "description": "مشاوره تخصصی برای انتخاب بهترین تجهیزات اندازه‌گیری متناسب با نیاز و بودجه شما.",
                "price": 5000000,
                "duration": "1-2 جلسه",
                "features": "تحلیل نیاز,پیشنهاد تجهیزات,بررسی بودجه,راهنمایی خرید",
                "category": "مشاوره فنی"
            },
            {
                "name": "طراحی آزمایشگاه اندازه‌گیری",
                "description": "طراحی و چیدمان آزمایشگاه‌های اندازه‌گیری RF با در نظر گیری استانداردها.",
                "price": 15000000,
                "duration": "1-2 هفته",
                "features": "طراحی فضا,انتخاب تجهیزات,برنامه‌ریزی نصب",
                "category": "مشاوره فنی"
            },
            
            # خدمات آموزش
            {
                "name": "آموزش کار با اسیلوسکوپ",
                "description": "دوره جامع آموزش کار با اسیلوسکوپ از مبتدی تا پیشرفته. شامل کارگاه عملی.",
                "price": 8000000,
                "duration": "16 ساعت (8 جلسه)",
                "features": "آموزش تئوری,کارگاه عملی,مدرک معتبر,مواد آموزشی",
                "category": "آموزش"
            },
            {
                "name": "آموزش اسپکتروم آنالایزر",
                "description": "آموزش تخصصی کار با اسپکتروم آنالایزر و تحلیل طیف فرکانسی.",
                "price": 12000000,
                "duration": "20 ساعت (10 جلسه)",
                "features": "آموزش کاربردی,تحلیل طیف,پروژه عملی,گواهینامه",
                "category": "آموزش"
            }
        ]
        
        conn = self.db.get_conn()
        try:
            with conn:
                for i, service in enumerate(services_data, 1):
                    # دریافت category_id
                    category_result = conn.execute(
                        "SELECT id FROM categories WHERE name = ? AND type = 'services'",
                        (service["category"],)
                    ).fetchone()
                    
                    if not category_result:
                        continue
                    
                    category_id = category_result[0]
                    
                    # ایجاد خدمت
                    result = conn.execute("""
                        INSERT INTO services (name, description, price, duration, 
                                            features, category_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        service["name"], service["description"], service["price"],
                        service["duration"], service["features"], category_id
                    ))
                    
                    service_id = result.lastrowid
                    
                    # ایجاد تصویر اصلی
                    main_image_path = f"static/uploads/services/service_{service_id}_main.jpg"
                    self.create_default_image(
                        main_image_path,
                        f"خدمات {service['category']}\n{service['name'][:20]}...",
                        800, 600, (245, 250, 255)
                    )
                    
                    conn.execute("""
                        INSERT INTO service_media (service_id, file_path, media_type, is_main)
                        VALUES (?, ?, 'image', 1)
                    """, (service_id, main_image_path))
                    
                    # ایجاد تصاویر اضافی
                    for j in range(2, random.randint(3, 4)):
                        extra_image_path = f"static/uploads/services/service_{service_id}_extra_{j}.jpg"
                        self.create_default_image(
                            extra_image_path,
                            f"مرحله {j}\n{service['name'][:15]}",
                            600, 450, (250, 245, 240)
                        )
                        
                        conn.execute("""
                            INSERT INTO service_media (service_id, file_path, media_type, is_main)
                            VALUES (?, ?, 'image', 0)
                        """, (service_id, extra_image_path))
            
            logger.info(f"✅ {len(services_data)} خدمت ایجاد شد")
        except Exception as e:
            logger.error(f"خطا در ایجاد خدمات: {e}")
            raise
    
    def seed_educational_content(self):
        """ایجاد محتوای آموزشی"""
        logger.info("در حال ایجاد محتوای آموزشی...")
        
        educational_data = [
            # مبانی اندازه‌گیری
            {
                "title": "مقدمه‌ای بر اندازه‌گیری RF",
                "content": """
اندازه‌گیری در حوزه رادیو فرکانس (RF) یکی از مهم‌ترین بخش‌های مهندسی مخابرات است. در این مقاله به معرفی مفاهیم پایه و تجهیزات اساسی می‌پردازیم.

## مفاهیم کلیدی

### فرکانس
فرکانس تعداد نوسانات در واحد زمان است که بر حسب هرتز (Hz) اندازه‌گیری می‌شود.

### توان
توان انرژی منتقل شده در واحد زمان است که معمولاً بر حسب وات (W) یا dBm بیان می‌شود.

### امپدانس
امپدانس مقاومت مدار در برابر جریان متناوب است که شامل مقاومت، راکتانس خازنی و سلفی می‌باشد.

## تجهیزات اساسی

1. **اسیلوسکوپ**: برای مشاهده شکل موج
2. **اسپکتروم آنالایزر**: برای تحلیل طیف فرکانسی
3. **پاور متر**: برای اندازه‌گیری توان
4. **نتورک آنالایزر**: برای تحلیل پارامترهای شبکه

این تجهیزات پایه هر آزمایشگاه RF محسوب می‌شوند.
                """,
                "reading_time": 8,
                "difficulty": "مبتدی",
                "tags": "RF,measurement,basics,frequency,power",
                "category": "مبانی اندازه‌گیری"
            },
            {
                "title": "آشنایی با دسیبل (dB) و واحدهای RF",
                "content": """
درک مفهوم دسیبل برای کار در حوزه RF ضروری است. در این مقاله به بررسی انواع واحدهای dB می‌پردازیم.

## مفهوم دسیبل

دسیبل یک واحد لگاریتمی است که برای بیان نسبت دو کمیت استفاده می‌شود:

**dB = 20 × log₁₀(V₁/V₂)** برای ولتاژ
**dB = 10 × log₁₀(P₁/P₂)** برای توان

## انواع واحدهای dB

### dBm
توان نسبت به 1 میلی‌وات:
- 0 dBm = 1 mW
- 30 dBm = 1 W
- -30 dBm = 1 µW

### dBµV
ولتاژ نسبت به 1 میکروولت:
- 0 dBµV = 1 µV
- 60 dBµV = 1 mV
- 120 dBµV = 1 V

### dBc
توان نسبت به سیگنال حامل (Carrier)

### Return Loss (dB)
میزان انعکاس سیگنال که با پارامتر S11 مرتبط است.

## کاربردها
- اندازه‌گیری توان فرستنده
- محاسبه تلفات کابل
- ارزیابی کیفیت آنتن
- تحلیل نویز

تسلط بر این مفاهیم برای هر مهندس RF الزامی است.
                """,
                "reading_time": 12,
                "difficulty": "مبتدی",
                "tags": "dB,dBm,units,power,measurement",
                "category": "مبانی اندازه‌گیری"
            },
            
            # کار با دستگاه‌ها
            {
                "title": "راهنمای کامل کار با اسیلوسکوپ",
                "content": """
اسیلوسکوپ یکی از مهم‌ترین ابزارهای اندازه‌گیری الکترونیک است. در این راهنما نحوه استفاده صحیح از آن را یاد می‌گیریم.

## مبانی اسیلوسکوپ

### کنترل‌های اصلی

**کنترل عمودی (Vertical)**
- Volts/Div: تنظیم حساسیت عمودی
- Position: جابجایی عمودی شکل موج
- Coupling: نوع کوپلینگ (AC/DC/GND)

**کنترل افقی (Horizontal)**
- Time/Div: تنظیم مقیاس زمانی
- Position: جابجایی افقی شکل موج
- Trigger: تنظیم نقطه شروع نمایش

### تنظیمات Trigger

تریگر تعیین می‌کند چه زمانی اسیلوسکوپ شروع به نمایش کند:

**انواع تریگر:**
- Edge: لبه صعودی یا نزولی
- Pulse Width: عرض پالس
- Video: سیگنال‌های ویدئویی

### اندازه‌گیری‌های اتوماتیک

اسیلوسکوپ‌های مدرن قابلیت اندازه‌گیری خودکار دارند:
- فرکانس
- دوره تناوب
- دامنه (Peak-to-Peak)
- RMS
- Rise Time
- Fall Time

## تکنیک‌های اندازه‌گیری

### اندازه‌گیری فرکانس
1. اتصال سیگنال به کانال 1
2. تنظیم Time/Div مناسب
3. استفاده از Cursors یا اندازه‌گیری خودکار

### اندازه‌گیری فاز
برای مقایسه فاز دو سیگنال از دو کانال استفاده کنید و محاسبه:
**Phase = (Δt / T) × 360°**

## نکات عملی

- همیشه از پروب 10:1 برای سیگنال‌های فرکانس بالا استفاده کنید
- کالیبراسیون پروب را فراموش نکنید
- برای اندازه‌گیری دقیق از Average mode استفاده کنید
- در صورت نویز، از filtering استفاده کنید

تمرین مداوم کلید تسلط بر اسیلوسکوپ است.
                """,
                "reading_time": 15,
                "difficulty": "متوسط",
                "tags": "oscilloscope,measurement,trigger,probes",
                "category": "کار با دستگاه‌ها"
            },
            {
                "title": "کار با اسپکتروم آنالایزر: راهنمای عملی",
                "content": """
اسپکتروم آنالایزر ابزاری برای تحلیل سیگنال در حوزه فرکانس است. این راهنما شما را با نحوه استفاده آشنا می‌کند.

## مبانی اسپکتروم آنالایز

### مفاهیم کلیدی

**Span**: محدوده فرکانسی نمایش
**RBW (Resolution Bandwidth)**: قدرت تفکیک فرکانسی
**VBW (Video Bandwidth)**: پهنای باند ویدئو برای فیلتر نویز
**Sweep Time**: زمان اسکن کامل محدوده

### تنظیمات اولیه

1. **تنظیم فرکانس مرکزی (Center Frequency)**
2. **انتخاب Span مناسب**
3. **تنظیم Reference Level**
4. **انتخاب RBW مناسب**

## کاربردهای متداول

### اندازه‌گیری توان
- تنظیم Span روی Zero
- خواندن مقدار از Marker

### تحلیل هارمونیک
- تنظیم Span گسترده
- شناسایی فرکانس‌های چندگانه پایه

### اندازه‌گیری پهنای باند
- استفاده از Marker Delta
- روش -3dB یا -20dB

### تحلیل نویز فاز
- استفاده از حالت Log Scale
- اندازه‌گیری در فواصل مختلف از حامل

## تکنیک‌های پیشرفته

### استفاده از Markers
- Peak Search: یافتن بیشترین توان
- Delta Marker: اندازه‌گیری اختلاف
- Noise Marker: اندازه‌گیری نویز

### Average و Max Hold
- Average: کاهش نویز تصادفی
- Max Hold: نگهداری بیشترین مقدار

### External Mixing
برای فرکانس‌های بالاتر از محدوده دستگاه

## نکات مهم

- RBW کمتر = دقت بیشتر ولی سرعت کمتر
- برای سیگنال‌های ناپایدار از Max Hold استفاده کنید
- همیشه تلفات کابل را در نظر بگیرید
- از Pre-amplifier در صورت سیگنال ضعیف استفاده کنید

اسپکتروم آنالایزر ابزار قدرتمندی است که با تمرین مهارت استفاده از آن افزایش می‌یابد.
                """,
                "reading_time": 18,
                "difficulty": "متوسط",
                "tags": "spectrum-analyzer,frequency-domain,RBW,markers",
                "category": "کار با دستگاه‌ها"
            },
            
            # کالیبراسیون
            {
                "title": "اصول کالیبراسیون تجهیزات اندازه‌گیری",
                "content": """
کالیبراسیون فرآیند تایید صحت تجهیزات اندازه‌گیری است. در این مقاله اصول و روش‌های کالیبراسیون را بررسی می‌کنیم.

## تعریف کالیبراسیون

کالیبراسیون مقایسه مقادیر نشان داده شده توسط دستگاه با مقادیر استاندارد شناخته شده است.

**هدف کالیبراسیون:**
- تایید دقت دستگاه
- شناسایی خطاها
- حفظ قابلیت اعتماد اندازه‌گیری

## مراحل کالیبراسیون

### 1. آماده‌سازی
- بررسی شرایط محیطی (دما، رطوبت)
- گرم کردن دستگاه (Warm-up)
- آماده‌سازی استانداردهای مرجع

### 2. انجام تست‌ها
- اندازه‌گیری در نقاط مختلف محدوده
- ثبت نتایج دقیق
- محاسبه خطاها

### 3. گزارش‌نویسی
- ثبت تمام داده‌ها
- محاسبه عدم قطعیت
- نتیجه‌گیری در مورد وضعیت دستگاه

## استانداردهای کالیبراسیون

### استانداردهای فرکانس
- Rubidium Standard
- GPS Disciplined Oscillator
- Cesium Standard

### استانداردهای توان
- Power Reference Source
- Thermistor Mount
- Calorimeter

### استانداردهای ولتاژ
- Voltage Reference
- Calibrated Signal Generator

## محاسبه عدم قطعیت

عدم قطعیت از ترکیب منابع مختلف خطا حاصل می‌شود:

**منابع خطا:**
- خطای استاندارد مرجع
- خطای تکرارپذیری
- خطای شرایط محیطی
- خطای روش اندازه‌گیری

**محاسبه:**
U = k × √(u₁² + u₂² + u₃² + ...)

که k ضریب پوشش (معمولاً 2) است.

## دوره کالیبراسیون

دوره کالیبراسیون بستگی دارد به:
- نوع دستگاه
- شرایط استفاده
- اهمیت اندازه‌گیری
- تجربه قبلی

**دوره‌های متداول:**
- تجهیزات حساس: 6 ماه
- تجهیزات عمومی: 1 سال
- تجهیزات پایدار: 2 سال

## نکات عملی

- کالیبراسیون را به مؤسسات معتبر واگذار کنید
- گواهینامه کالیبراسیون را نگهداری کنید
- برچسب کالیبراسیون را روی دستگاه نصب کنید
- تاریخ کالیبراسیون بعدی را یادداشت کنید

کالیبراسیون منظم ضامن دقت و قابلیت اعتماد اندازه‌گیری‌هاست.
                """,
                "reading_time": 14,
                "difficulty": "پیشرفته",
                "tags": "calibration,uncertainty,standards,accuracy",
                "category": "کالیبراسیون"
            },
            
            # تعمیرات
            {
                "title": "عیب‌یابی تجهیزات RF: روش‌ها و تکنیک‌ها",
                "content": """
عیب‌یابی مؤثر تجهیزات RF نیازمند روش منطقی و ابزار مناسب است. در این راهنما تکنیک‌های عملی را بررسی می‌کنیم.

## اصول کلی عیب‌یابی

### رویکرد سیستماتیک

1. **جمع‌آوری اطلاعات**
   - شرح دقیق مشکل
   - شرایط بروز خرابی
   - تاریخچه تعمیرات

2. **بررسی ظاهری**
   - بازرسی فیزیکی دستگاه
   - بررسی کابل‌ها و اتصالات
   - کنترل منبع تغذیه

3. **تست‌های اولیه**
   - بررسی عملکرد کلی
   - تست self-test دستگاه
   - بررسی نمایشگر و کنترل‌ها

## ابزارهای عیب‌یابی

### تجهیزات اساسی
- مولتی‌متر دیجیتال
- اسیلوسکوپ
- پاور ساپلای متغیر
- سیگنال ژنراتور

### تجهیزات تخصصی
- طیف‌سنج (اسپکتروم آنالایزر)
- نتورک آنالایزر
- نویز فیگور متر
- فرکانس کانتر دقیق

## خرابی‌های متداول

### مشکلات منبع تغذیه
**علائم:**
- عدم روشن شدن
- عملکرد ناپایدار
- گرم شدن غیرعادی

**عیب‌یابی:**
- تست ولتاژهای خروجی
- بررسی کیفیت تغذیه (ریپل)
- کنترل فیوزها و محافظ‌ها

### مشکلات فرکانس
**علائم:**
- انحراف فرکانس
- ناپایداری
- عدم قفل شدن PLL

**عیب‌یابی:**
- بررسی مرجع فرکانس
- تست مدار PLL
- کنترل VCO

### مشکلات RF
**علائم:**
- کاهش حساسیت
- نویز بالا
- اعوجاج سیگنال

**عیب‌یابی:**
- تست مراحل تقویت
- بررسی فیلترها
- کنترل mixer و LO

## تکنیک‌های تست

### Signal Injection
تزریق سیگنال شناخته شده در نقاط مختلف مدار

### Signal Tracing
دنبال کردن مسیر سیگنال از ورودی تا خروجی

### Substitution Method
جایگزینی قطعات مشکوک با قطعات سالم

### Two-Port Analysis
تحلیل مدارها به صورت دو پورته (ورودی-خروجی)

## نکات ایمنی

- همیشه از تجهیزات حفاظت شخصی استفاده کنید
- قبل از باز کردن دستگاه، آن را از برق جدا کنید
- مراقب ولتاژهای بالا باشید
- از ابزار عایق شده استفاده کنید

## مستندسازی

- تمام مراحل عیب‌یابی را ثبت کنید
- عکس از مناطق مشکل‌دار تهیه کنید
- نتایج تست‌ها را ضبط کنید
- راه‌حل نهایی را مستند کنید

عیب‌یابی موفق ترکیبی از دانش فنی، تجربه و روش منطقی است.
                """,
                "reading_time": 16,
                "difficulty": "پیشرفته",
                "tags": "troubleshooting,repair,RF,diagnostics",
                "category": "تعمیرات"
            }
        ]
        
        conn = self.db.get_conn()
        try:
            with conn:
                for i, content in enumerate(educational_data, 1):
                    # دریافت category_id
                    category_result = conn.execute(
                        "SELECT id FROM categories WHERE name = ? AND type = 'educational'",
                        (content["category"],)
                    ).fetchone()
                    
                    if not category_result:
                        continue
                    
                    category_id = category_result[0]
                    
                    # ایجاد محتوا
                    result = conn.execute("""
                        INSERT INTO educational_content (title, content, reading_time, 
                                                       difficulty, tags, category_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        content["title"], content["content"], content["reading_time"],
                        content["difficulty"], content["tags"], category_id
                    ))
                    
                    content_id = result.lastrowid
                    
                    # ایجاد تصویر اصلی
                    main_image_path = f"static/uploads/educational/content_{content_id}_main.jpg"
                    self.create_default_image(
                        main_image_path,
                        f"آموزش\n{content['title'][:30]}...",
                        800, 600, (255, 250, 245)
                    )
                    
                    conn.execute("""
                        INSERT INTO educational_media (content_id, file_path, media_type, is_main)
                        VALUES (?, ?, 'image', 1)
                    """, (content_id, main_image_path))
                    
                    # ایجاد تصاویر اضافی
                    for j in range(2, random.randint(3, 4)):
                        extra_image_path = f"static/uploads/educational/content_{content_id}_extra_{j}.jpg"
                        self.create_default_image(
                            extra_image_path,
                            f"شکل {j}\n{content['title'][:20]}",
                            600, 450, (250, 250, 255)
                        )
                        
                        conn.execute("""
                            INSERT INTO educational_media (content_id, file_path, media_type, is_main)
                            VALUES (?, ?, 'image', 0)
                        """, (content_id, extra_image_path))
            
            logger.info(f"✅ {len(educational_data)} محتوای آموزشی ایجاد شد")
        except Exception as e:
            logger.error(f"خطا در ایجاد محتوای آموزشی: {e}")
            raise
    
    def seed_inquiries(self):
        """ایجاد استعلام‌های قیمت نمونه"""
        logger.info("در حال ایجاد استعلام‌های قیمت...")
        
        inquiries_data = [
            {
                "name": "احمد رضایی",
                "phone": "09121234567",
                "email": "ahmad.rezaei@example.com",
                "product_name": "اسیلوسکوپ دیجیتال 100MHz",
                "message": "سلام، لطفاً قیمت اسیلوسکوپ دیجیتال 100MHz برای استفاده دانشگاهی اعلام کنید.",
                "status": "pending",
                "priority": "medium",
                "created_days_ago": 1
            },
            {
                "name": "فاطمه احمدی",
                "phone": "09123456789",
                "email": "f.ahmadi@techco.ir",
                "product_name": "اسپکتروم آنالایزر تا 6GHz",
                "message": "برای آزمایشگاه شرکت نیاز به اسپکتروم آنالایزر تا 6GHz داریم. قیمت و مشخصات کامل ارسال کنید.",
                "status": "responded",
                "priority": "high",
                "created_days_ago": 3
            },
            {
                "name": "مهندس حسینی",
                "phone": "09135678901",
                "email": "m.hosseini@rflab.com",
                "product_name": "کالیبراسیون پاور متر",
                "message": "پاور متر HP 437B داریم که نیاز به کالیبراسیون دارد. زمان و هزینه اعلام کنید.",
                "status": "pending",
                "priority": "medium",
                "created_days_ago": 2
            },
            {
                "name": "علی محمدی",
                "phone": "09147890123",
                "email": "ali.mohammadi@gmail.com",
                "product_name": "رادیوتستر IFR",
                "message": "برای تست بیسیم‌های موتورولا به رادیوتستر نیاز داریم. مدل‌های موجود و قیمت اعلام کنید.",
                "status": "completed",
                "priority": "low",
                "created_days_ago": 7
            },
            {
                "name": "دکتر زارعی",
                "phone": "09156789012",
                "email": "d.zarei@university.ac.ir",
                "product_name": "بسته آموزشی RF",
                "message": "برای دانشگاه نیاز به مجموعه تجهیزات آموزشی RF داریم. پکیج پیشنهادی ارائه دهید.",
                "status": "pending",
                "priority": "high",
                "created_days_ago": 1
            },
            {
                "name": "شرکت پردازش سیگنال",
                "phone": "02133445566",
                "email": "info@signalprocessing.ir",
                "product_name": "نتورک آنالایزر",
                "message": "برای پروژه تحقیقاتی نیاز به نتورک آنالایزر 20GHz داریم. قیمت کرایه ماهانه چقدر است؟",
                "status": "responded",
                "priority": "medium",
                "created_days_ago": 5
            },
            {
                "name": "مهندس کریمی",
                "phone": "09167890123",
                "email": "karimi@radiocom.co.ir",
                "product_name": "تعمیر سیگنال ژنراتور HP",
                "message": "سیگنال ژنراتور HP 8648C دارم که خرابی در خروجی دارد. هزینه تعمیر چقدر است؟",
                "status": "pending",
                "priority": "medium",
                "created_days_ago": 4
            },
            {
                "name": "آرش نوری",
                "phone": "09178901234",
                "email": "arash.nouri@techstart.ir",
                "product_name": "اسیلوسکوپ USB",
                "message": "برای استارتاپ نیاز به اسیلوسکوپ ارزان قیمت داریم. مدل‌های USB موجود معرفی کنید.",
                "status": "completed",
                "priority": "low",
                "created_days_ago": 10
            },
            {
                "name": "مریم صادقی",
                "phone": "09189012345",
                "email": "m.sadeghi@researcher.ac.ir",
                "product_name": "فرکانس کانتر دقیق",
                "message": "برای پژوهش فرکانس کانتر با دقت بالا نیاز داریم. مدل‌های موجود و قیمت اعلام کنید.",
                "status": "responded",
                "priority": "high",
                "created_days_ago": 2
            },
            {
                "name": "شرکت مخابرات پیشرو",
                "phone": "02144556677",
                "email": "procurement@telecom-p.ir",
                "product_name": "پکیج کامل آزمایشگاه",
                "message": "برای راه‌اندازی آزمایشگاه جدید نیاز به مجموعه کامل تجهیزات داریم. پیشنهاد و قیمت ارسال کنید.",
                "status": "pending",
                "priority": "high",
                "created_days_ago": 1
            }
        ]
        
        conn = self.db.get_conn()
        try:
            with conn:
                for inquiry in inquiries_data:
                    created_at = datetime.now() - timedelta(days=inquiry["created_days_ago"])
                    
                    conn.execute("""
                        INSERT INTO inquiries (name, phone, email, product_name, message, 
                                             status, priority, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        inquiry["name"], inquiry["phone"], inquiry["email"],
                        inquiry["product_name"], inquiry["message"],
                        inquiry["status"], inquiry["priority"], created_at
                    ))
            
            logger.info(f"✅ {len(inquiries_data)} استعلام قیمت ایجاد شد")
        except Exception as e:
            logger.error(f"خطا در ایجاد استعلام‌ها: {e}")
            raise
    
    def add_company_info(self):
        """اضافه کردن اطلاعات شرکت"""
        logger.info("در حال اضافه کردن اطلاعات شرکت...")
        
        # اطلاعات درباره ما
        about_us = """
# سنجش ابزار نوین RFTest

## درباره ما

شرکت سنجش ابزار نوین RFTest با بیش از 15 سال تجربه در زمینه تجهیزات اندازه‌گیری مخابراتی، ارائه‌دهنده خدمات جامع در حوزه RF و مایکروویو است.

### خدمات ما

**🔧 تامین تجهیزات**
- اسیلوسکوپ‌های آنالوگ و دیجیتال
- اسپکتروم آنالایزرهای حرفه‌ای
- سیگنال ژنراتورهای دقیق
- نتورک آنالایزرهای پیشرفته
- پاور مترهای کالیبره
- رادیوتسترهای تخصصی

**⚙️ خدمات فنی**
- کالیبراسیون معتبر بین‌المللی
- تعمیرات تخصصی تجهیزات
- مشاوره انتخاب دستگاه
- طراحی آزمایشگاه

**📚 آموزش**
- دوره‌های تخصصی RF
- آموزش کار با تجهیزات
- وبینارهای فنی
- پشتیبانی آنلاین

### مزایای همکاری با ما

✅ **کیفیت تضمینی**: تمام تجهیزات با گارانتی معتبر
✅ **قیمت رقابتی**: بهترین نرخ‌ها در بازار
✅ **پشتیبانی 24/7**: خدمات پس از فروش
✅ **تحویل سریع**: ارسال در کمترین زمان
✅ **مشاوره رایگان**: راهنمایی انتخاب بهترین گزینه

### مشتریان ما

- دانشگاه‌های معتبر کشور
- مراکز تحقیقاتی
- شرکت‌های مخابراتی
- صنایع دفاعی
- آزمایشگاه‌های خصوصی

### گواهینامه‌ها

- مجوز رسمی واردات تجهیزات
- نمایندگی رسمی برندهای معتبر
- گواهینامه کیفیت ISO
- مجوز کالیبراسیون از سازمان ملی استاندارد

### چشم‌انداز

هدف ما ارتقای سطح کیفی آزمایشگاه‌های اندازه‌گیری کشور و ارائه جدیدترین تکنولوژی‌های روز دنیا است.

---
*"دقت در اندازه‌گیری، کلید موفقیت در مهندسی"*
        """
        
        # اطلاعات تماس
        contact_info = """
# تماس با ما

## اطلاعات تماس

### دفتر مرکزی
**آدرس:** تهران، خیابان انقلاب، پلاک 123، طبقه 4، واحد 12
**تلفن:** 021-66445277
**فکس:** 021-66445278

### مدیر فنی
**مهندس حسین پور**
**موبایل:** 09125445277
**ایمیل:** rftestiran@gmail.com

### وب‌سایت و شبکه‌های اجتماعی
**وب‌سایت:** www.rftest.ir
**تلگرام:** @RFTestIran
**اینستاگرام:** rftest_iran

## ساعات کاری

**شنبه تا چهارشنبه:** 8:00 تا 17:00
**پنج‌شنبه:** 8:00 تا 13:00
**جمعه:** تعطیل

## نحوه دسترسی

### حمل و نقل عمومی
- مترو: ایستگاه انقلاب، خروجی شماره 2
- اتوبوس: خطوط 123، 456، 789

### پارکینگ
پارکینگ اختصاصی در همکف ساختمان موجود است.

## خدمات آنلاین

### مشاوره تلفنی
برای مشاوره رایگان با شماره 09125445277 تماس بگیرید.

### پشتیبانی فنی
پشتیبانی فنی 24 ساعته برای مشتریان ویژه

### سفارش آنلاین
امکان ثبت سفارش و پیگیری از طریق وب‌سایت

---
*آماده خدمت‌رسانی به شما عزیزان هستیم*
        """
        
        conn = self.db.get_conn()
        try:
            with conn:
                # بررسی وجود اطلاعات قبلی
                existing = conn.execute("SELECT COUNT(*) FROM site_content WHERE page_name = 'about_us'").fetchone()[0]
                
                if existing == 0:
                    # اضافه کردن اطلاعات درباره ما
                    conn.execute("""
                        INSERT OR REPLACE INTO site_content (page_name, title, content, is_active)
                        VALUES ('about_us', 'درباره ما', ?, 1)
                    """, (about_us,))
                    
                    # اضافه کردن اطلاعات تماس
                    conn.execute("""
                        INSERT OR REPLACE INTO site_content (page_name, title, content, is_active)
                        VALUES ('contact', 'تماس با ما', ?, 1)
                    """, (contact_info,))
                    
                    logger.info("✅ اطلاعات شرکت اضافه شد")
                else:
                    logger.info("ℹ️ اطلاعات شرکت قبلاً موجود است")
        except Exception as e:
            logger.error(f"خطا در اضافه کردن اطلاعات شرکت: {e}")
    
    def run(self):
        """اجرای کامل فرآیند"""
        print("🚀 شروع پر کردن دیتابیس با اطلاعات کامل...")
        
        # تایید پاک کردن داده‌ها
        if not self.confirm_data_reset():
            print("❌ عملیات لغو شد.")
            return
        
        try:
            # پاک کردن داده‌های موجود
            self.clear_existing_data()
            
            # ایجاد داده‌های جدید
            self.seed_categories()
            self.seed_products()
            self.seed_services()
            self.seed_educational_content()
            self.seed_inquiries()
            self.add_company_info()
            
            print("\n" + "="*60)
            print("🎉 دیتابیس با موفقیت پر شد!")
            print("="*60)
            print("✅ 16 دسته‌بندی")
            print("✅ 12 محصول با تصاویر")
            print("✅ 10 خدمت با تصاویر")
            print("✅ 6 مطلب آموزشی با تصاویر")
            print("✅ 10 استعلام قیمت")
            print("✅ اطلاعات شرکت کامل")
            print("\n💡 حالا می‌توانید از سایت و بات استفاده کنید!")
            
        except Exception as e:
            logger.error(f"خطا در فرآیند: {e}")
            print(f"❌ خطا: {e}")

if __name__ == "__main__":
    seeder = ComprehensiveDataSeeder()
    seeder.run()