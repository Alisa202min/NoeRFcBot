#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فایل پر کردن دیتابیس با اطلاعات کامل - نسخه ساده
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# تنظیم logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """دریافت اتصال به دیتابیس"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL not found in environment variables")
    
    return psycopg2.connect(database_url)

def confirm_reset():
    """تایید پاک کردن داده‌ها"""
    print("\n" + "="*60)
    print("🚨 هشدار: پاک کردن داده‌های موجود")
    print("="*60)
    print("این عمل تمام داده‌های موجود را پاک می‌کند.")
    print("آیا مطمئن هستید؟ (y/N): ", end="")
    
    response = input().lower().strip()
    return response in ['y', 'yes', 'بله']

def clear_data():
    """پاک کردن داده‌های موجود"""
    logger.info("پاک کردن داده‌های موجود...")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # حذف به ترتیب وابستگی
            cursor.execute("DELETE FROM product_media")
            cursor.execute("DELETE FROM service_media") 
            cursor.execute("DELETE FROM educational_media")
            cursor.execute("DELETE FROM inquiries")
            cursor.execute("DELETE FROM products")
            cursor.execute("DELETE FROM services")
            cursor.execute("DELETE FROM educational_content")
            cursor.execute("DELETE FROM product_categories")
            cursor.execute("DELETE FROM service_categories")
            cursor.execute("DELETE FROM educational_categories")
        conn.commit()
        logger.info("✅ داده‌ها پاک شدند")
    finally:
        conn.close()

def seed_categories():
    """ایجاد دسته‌بندی‌ها"""
    logger.info("ایجاد دسته‌بندی‌ها...")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # دسته‌بندی محصولات
            product_cats = ["اسیلوسکوپ", "اسپکتروم آنالایزر", "سیگنال ژنراتور", "نتورک آنالایزر", "پاور متر", "رادیوتستر", "فرکانس متر", "سایت مستر"]
            for cat in product_cats:
                cursor.execute("INSERT INTO product_categories (name) VALUES (%s)", (cat,))
            
            # دسته‌بندی خدمات  
            service_cats = ["کالیبراسیون", "تعمیرات", "مشاوره فنی", "آموزش"]
            for cat in service_cats:
                cursor.execute("INSERT INTO service_categories (name) VALUES (%s)", (cat,))
            
            # دسته‌بندی آموزشی
            edu_cats = ["مبانی اندازه‌گیری", "کار با دستگاه‌ها", "کالیبراسیون", "تعمیرات"]
            for cat in edu_cats:
                cursor.execute("INSERT INTO educational_categories (name) VALUES (%s)", (cat,))
        
        conn.commit()
        logger.info("✅ دسته‌بندی‌ها ایجاد شدند")
    finally:
        conn.close()

def seed_products():
    """ایجاد محصولات"""
    logger.info("ایجاد محصولات...")
    
    products = [
        # اسیلوسکوپ‌ها
        ("اسیلوسکوپ دیجیتال Keysight DSOX3024T", "اسیلوسکوپ دیجیتال 4 کاناله 200MHz با صفحه نمایش لمسی", 850000000, "DSOX3024T", "Keysight", True, True, "4-channel,200MHz,touchscreen", "اسیلوسکوپ"),
        ("اسیلوسکوپ آنالوگ Tektronix 2465B", "اسیلوسکوپ آنالوگ 4 کاناله 400MHz کلاسیک", 125000000, "2465B", "Tektronix", True, False, "analog,4-channel,400MHz", "اسیلوسکوپ"),
        ("اسیلوسکوپ USB Hantek DSO2C10", "اسیلوسکوپ USB دو کاناله 100MHz با نرم‌افزار Windows", 15000000, "DSO2C10", "Hantek", True, False, "USB,2-channel,100MHz", "اسیلوسکوپ"),
        
        # اسپکتروم آنالایزرها
        ("اسپکتروم آنالایزر Keysight N9020A", "اسپکتروم آنالایزر 10Hz تا 26.5GHz با نویز فاز پایین", 2500000000, "N9020A", "Keysight", True, True, "26.5GHz,low-phase-noise", "اسپکتروم آنالایزر"),
        ("اسپکتروم آنالایزر Rigol DSA832", "اسپکتروم آنالایزر 9kHz تا 3.2GHz اقتصادی", 180000000, "DSA832", "Rigol", True, False, "3.2GHz,economical", "اسپکتروم آنالایزر"),
        
        # سیگنال ژنراتورها
        ("سیگنال ژنراتور Keysight E8257D", "سیگنال ژنراتور مایکروویو 100kHz تا 67GHz", 4200000000, "E8257D", "Keysight", False, True, "67GHz,microwave", "سیگنال ژنراتور"),
        ("فانکشن ژنراتور Rigol DG4062", "فانکشن ژنراتور دو کاناله 60MHz", 95000000, "DG4062", "Rigol", True, False, "dual-channel,60MHz", "سیگنال ژنراتور"),
        
        # نتورک آنالایزرها
        ("نتورک آنالایزر Keysight E5071C", "نتورک آنالایزر 300kHz تا 20GHz چهار پورت", 1800000000, "E5071C", "Keysight", True, True, "20GHz,4-port", "نتورک آنالایزر"),
        ("نتورک آنالایزر NanoVNA-H4", "نتورک آنالایزر قابل حمل 10kHz تا 1.5GHz", 8500000, "NanoVNA-H4", "NanoVNA", True, False, "portable,1.5GHz", "نتورک آنالایزر"),
        
        # پاور مترها
        ("پاور متر Keysight E4417A", "پاور متر دو کاناله با دقت ±0.05dB", 320000000, "E4417A", "Keysight", True, False, "dual-channel,high-accuracy", "پاور متر"),
        ("پاور متر USB Mini-Circuits PWR-6GHS+", "پاور متر USB کوچک 0.5 تا 6000MHz", 45000000, "PWR-6GHS+", "Mini-Circuits", True, False, "USB,6GHz", "پاور متر"),
        
        # رادیوتسترها
        ("رادیوتستر Aeroflex 3920B", "رادیوتستر دیجیتال DMR, TETRA, P25", 1200000000, "3920B", "Aeroflex", False, True, "digital,DMR,TETRA", "رادیوتستر"),
        ("رادیوتستر IFR 2968", "رادیوتستر GSM 900/1800MHz کلاسیک", 385000000, "2968", "IFR", True, False, "GSM,900MHz,1800MHz", "رادیوتستر"),
    ]
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            for name, desc, price, model, manufacturer, in_stock, featured, tags, category in products:
                # دریافت category_id
                cursor.execute("SELECT id FROM product_categories WHERE name = %s", (category,))
                cat_result = cursor.fetchone()
                if not cat_result:
                    continue
                
                category_id = cat_result[0]
                
                # ایجاد محصول
                cursor.execute("""
                    INSERT INTO products (name, description, price, model, manufacturer, 
                                        in_stock, featured, tags, category_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (name, desc, price, model, manufacturer, in_stock, featured, tags, category_id))
                
                product_id = cursor.fetchone()[0]
                
                # ایجاد media record (بدون فایل واقعی)
                cursor.execute("""
                    INSERT INTO product_media (product_id, file_path, media_type, is_main)
                    VALUES (%s, %s, 'image', true)
                """, (product_id, f'/static/uploads/products/product_{product_id}_main.jpg'))
        
        conn.commit()
        logger.info(f"✅ {len(products)} محصول ایجاد شد")
    finally:
        conn.close()

def seed_services():
    """ایجاد خدمات"""
    logger.info("ایجاد خدمات...")
    
    services = [
        ("کالیبراسیون اسیلوسکوپ", "کالیبراسیون دقیق اسیلوسکوپ‌های آنالوگ و دیجیتال", 12000000, "3-5 روز کاری", "گواهینامه,تست دقت,تنظیم", "کالیبراسیون"),
        ("کالیبراسیون اسپکتروم آنالایزر", "کالیبراسیون اسپکتروم آنالایزر با استانداردهای فرکانس", 18000000, "5-7 روز کاری", "کالیبراسیون فرکانس,دامنه,نویز فاز", "کالیبراسیون"),
        ("کالیبراسیون پاور متر", "کالیبراسیون دقیق پاور متر و سنسورهای توان", 8500000, "2-3 روز کاری", "کالیبراسیون توان,تست خطی", "کالیبراسیون"),
        ("تعمیر اسیلوسکوپ", "تعمیر و نگهداری اسیلوسکوپ‌های مختلف", 25000000, "7-14 روز کاری", "عیب‌یابی,تعویض قطعات,تنظیم", "تعمیرات"),
        ("تعمیر سیگنال ژنراتور", "تعمیر انواع سیگنال ژنراتور و فانکشن ژنراتور", 32000000, "10-21 روز کاری", "تعمیر مدار فرکانس,بازسازی", "تعمیرات"),
        ("تعمیر رادیوتستر", "تعمیر تخصصی رادیوتسترهای مختلف", 45000000, "14-28 روز کاری", "تعمیر سخت‌افزار,آپدیت نرم‌افزار", "تعمیرات"),
        ("مشاوره انتخاب تجهیزات", "مشاوره تخصصی برای انتخاب بهترین تجهیزات", 5000000, "1-2 جلسه", "تحلیل نیاز,پیشنهاد تجهیزات", "مشاوره فنی"),
        ("طراحی آزمایشگاه اندازه‌گیری", "طراحی و چیدمان آزمایشگاه‌های اندازه‌گیری RF", 15000000, "1-2 هفته", "طراحی فضا,انتخاب تجهیزات", "مشاوره فنی"),
        ("آموزش کار با اسیلوسکوپ", "دوره جامع آموزش کار با اسیلوسکوپ", 8000000, "16 ساعت", "آموزش تئوری,کارگاه عملی,مدرک", "آموزش"),
        ("آموزش اسپکتروم آنالایزر", "آموزش تخصصی کار با اسپکتروم آنالایزر", 12000000, "20 ساعت", "آموزش کاربردی,تحلیل طیف", "آموزش"),
    ]
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            for name, desc, price, duration, features, category in services:
                # دریافت category_id
                cursor.execute("SELECT id FROM service_categories WHERE name = %s", (category,))
                cat_result = cursor.fetchone()
                if not cat_result:
                    continue
                
                category_id = cat_result[0]
                
                # ایجاد خدمت
                cursor.execute("""
                    INSERT INTO services (name, description, price, duration, features, category_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (name, desc, price, duration, features, category_id))
                
                service_id = cursor.fetchone()[0]
                
                # ایجاد media record
                cursor.execute("""
                    INSERT INTO service_media (service_id, file_path, media_type, is_main)
                    VALUES (%s, %s, 'image', true)
                """, (service_id, f'/static/uploads/services/service_{service_id}_main.jpg'))
        
        conn.commit()
        logger.info(f"✅ {len(services)} خدمت ایجاد شد")
    finally:
        conn.close()

def seed_educational():
    """ایجاد محتوای آموزشی"""
    logger.info("ایجاد محتوای آموزشی...")
    
    educational = [
        ("مقدمه‌ای بر اندازه‌گیری RF", """اندازه‌گیری در حوزه رادیو فرکانس یکی از مهم‌ترین بخش‌های مهندسی مخابرات است.

## مفاهیم کلیدی

### فرکانس
فرکانس تعداد نوسانات در واحد زمان است که بر حسب هرتز اندازه‌گیری می‌شود.

### توان
توان انرژی منتقل شده در واحد زمان است که معمولاً بر حسب وات یا dBm بیان می‌شود.

### امپدانس
امپدانس مقاومت مدار در برابر جریان متناوب است.

## تجهیزات اساسی

1. **اسیلوسکوپ**: برای مشاهده شکل موج
2. **اسپکتروم آنالایزر**: برای تحلیل طیف فرکانسی
3. **پاور متر**: برای اندازه‌گیری توان
4. **نتورک آنالایزر**: برای تحلیل پارامترهای شبکه""", 8, "مبتدی", "RF,measurement,basics", "مبانی اندازه‌گیری"),
        
        ("آشنایی با دسیبل و واحدهای RF", """درک مفهوم دسیبل برای کار در حوزه RF ضروری است.

## مفهوم دسیبل

دسیبل یک واحد لگاریتمی است:
- dB = 20 × log₁₀(V₁/V₂) برای ولتاژ  
- dB = 10 × log₁₀(P₁/P₂) برای توان

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

### dBc
توان نسبت به سیگنال حامل""", 12, "مبتدی", "dB,dBm,units,power", "مبانی اندازه‌گیری"),
        
        ("راهنمای کامل کار با اسیلوسکوپ", """اسیلوسکوپ یکی از مهم‌ترین ابزارهای اندازه‌گیری الکترونیک است.

## کنترل‌های اصلی

### کنترل عمودی
- Volts/Div: تنظیم حساسیت عمودی
- Position: جابجایی عمودی شکل موج
- Coupling: نوع کوپلینگ (AC/DC/GND)

### کنترل افقی
- Time/Div: تنظیم مقیاس زمانی
- Position: جابجایی افقی شکل موج

### تنظیمات Trigger
تریگر تعیین می‌کند چه زمانی اسیلوسکوپ شروع به نمایش کند.

## اندازه‌گیری‌های اتوماتیک
- فرکانس
- دوره تناوب  
- دامنه (Peak-to-Peak)
- RMS
- Rise Time""", 15, "متوسط", "oscilloscope,measurement,trigger", "کار با دستگاه‌ها"),
        
        ("کار با اسپکتروم آنالایزر", """اسپکتروم آنالایزر ابزاری برای تحلیل سیگنال در حوزه فرکانس است.

## مفاهیم کلیدی

- **Span**: محدوده فرکانسی نمایش
- **RBW**: قدرت تفکیک فرکانسی
- **VBW**: پهنای باند ویدئو
- **Sweep Time**: زمان اسکن کامل

## کاربردهای متداول

### اندازه‌گیری توان
تنظیم Span روی Zero و خواندن از Marker

### تحلیل هارمونیک
تنظیم Span گسترده و شناسایی فرکانس‌های چندگانه

### اندازه‌گیری پهنای باند
استفاده از Marker Delta و روش -3dB

## نکات مهم
- RBW کمتر = دقت بیشتر ولی سرعت کمتر
- برای سیگنال‌های ناپایدار از Max Hold استفاده کنید
- تلفات کابل را در نظر بگیرید""", 18, "متوسط", "spectrum-analyzer,frequency-domain,RBW", "کار با دستگاه‌ها"),
        
        ("اصول کالیبراسیون تجهیزات", """کالیبراسیون فرآیند تایید صحت تجهیزات اندازه‌گیری است.

## تعریف کالیبراسیون
مقایسه مقادیر نشان داده شده توسط دستگاه با مقادیر استاندارد.

## مراحل کالیبراسیون

### 1. آماده‌سازی
- بررسی شرایط محیطی (دما، رطوبت)
- گرم کردن دستگاه
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
- Rubidium Standard برای فرکانس
- Power Reference Source برای توان
- Voltage Reference برای ولتاژ

## دوره کالیبراسیون
- تجهیزات حساس: 6 ماه
- تجهیزات عمومی: 1 سال  
- تجهیزات پایدار: 2 سال""", 14, "پیشرفته", "calibration,uncertainty,standards", "کالیبراسیون"),
        
        ("عیب‌یابی تجهیزات RF", """عیب‌یابی مؤثر تجهیزات RF نیازمند روش منطقی است.

## رویکرد سیستماتیک

### 1. جمع‌آوری اطلاعات
- شرح دقیق مشکل
- شرایط بروز خرابی
- تاریخچه تعمیرات

### 2. بررسی ظاهری
- بازرسی فیزیکی دستگاه
- بررسی کابل‌ها و اتصالات
- کنترل منبع تغذیه

### 3. تست‌های اولیه
- بررسی عملکرد کلی
- تست self-test دستگاه
- بررسی نمایشگر و کنترل‌ها

## ابزارهای عیب‌یابی
- مولتی‌متر دیجیتال
- اسیلوسکوپ
- پاور ساپلای متغیر
- سیگنال ژنراتور

## خرابی‌های متداول

### مشکلات منبع تغذیه
علائم: عدم روشن شدن، عملکرد ناپایدار

### مشکلات فرکانس  
علائم: انحراف فرکانس، ناپایداری

### مشکلات RF
علائم: کاهش حساسیت، نویز بالا

## تکنیک‌های تست
- Signal Injection
- Signal Tracing  
- Substitution Method
- Two-Port Analysis""", 16, "پیشرفته", "troubleshooting,repair,RF", "تعمیرات"),
    ]
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            for title, content, reading_time, difficulty, tags, category in educational:
                # دریافت category_id
                cursor.execute("SELECT id FROM educational_categories WHERE name = %s", (category,))
                cat_result = cursor.fetchone()
                if not cat_result:
                    continue
                
                category_id = cat_result[0]
                
                # ایجاد محتوا
                cursor.execute("""
                    INSERT INTO educational_content (title, content, reading_time, difficulty, tags, category_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (title, content, reading_time, difficulty, tags, category_id))
                
                content_id = cursor.fetchone()[0]
                
                # ایجاد media record
                cursor.execute("""
                    INSERT INTO educational_media (content_id, file_path, media_type, is_main)
                    VALUES (%s, %s, 'image', true)
                """, (content_id, f'/static/uploads/educational/content_{content_id}_main.jpg'))
        
        conn.commit()
        logger.info(f"✅ {len(educational)} محتوای آموزشی ایجاد شد")
    finally:
        conn.close()

def seed_inquiries():
    """ایجاد استعلام‌های قیمت"""
    logger.info("ایجاد استعلام‌های قیمت...")
    
    inquiries = [
        ("احمد رضایی", "09121234567", "ahmad.rezaei@example.com", "اسیلوسکوپ دیجیتال 100MHz", "لطفاً قیمت اسیلوسکوپ دیجیتال 100MHz اعلام کنید.", "pending", "medium", 1),
        ("فاطمه احمدی", "09123456789", "f.ahmadi@techco.ir", "اسپکتروم آنالایزر تا 6GHz", "برای آزمایشگاه شرکت نیاز به اسپکتروم آنالایزر داریم.", "responded", "high", 3),
        ("مهندس حسینی", "09135678901", "m.hosseini@rflab.com", "کالیبراسیون پاور متر", "پاور متر HP 437B نیاز به کالیبراسیون دارد.", "pending", "medium", 2),
        ("علی محمدی", "09147890123", "ali.mohammadi@gmail.com", "رادیوتستر IFR", "برای تست بیسیم‌های موتورولا به رادیوتستر نیاز داریم.", "completed", "low", 7),
        ("دکتر زارعی", "09156789012", "d.zarei@university.ac.ir", "بسته آموزشی RF", "برای دانشگاه نیاز به مجموعه تجهیزات آموزشی RF داریم.", "pending", "high", 1),
        ("شرکت پردازش سیگنال", "02133445566", "info@signalprocessing.ir", "نتورک آنالایزر", "برای پروژه تحقیقاتی نیاز به نتورک آنالایزر 20GHz داریم.", "responded", "medium", 5),
        ("مهندس کریمی", "09167890123", "karimi@radiocom.co.ir", "تعمیر سیگنال ژنراتور HP", "سیگنال ژنراتور HP 8648C خرابی در خروجی دارد.", "pending", "medium", 4),
        ("آرش نوری", "09178901234", "arash.nouri@techstart.ir", "اسیلوسکوپ USB", "برای استارتاپ نیاز به اسیلوسکوپ ارزان قیمت داریم.", "completed", "low", 10),
        ("مریم صادقی", "09189012345", "m.sadeghi@researcher.ac.ir", "فرکانس کانتر دقیق", "برای پژوهش فرکانس کانتر با دقت بالا نیاز داریم.", "responded", "high", 2),
        ("شرکت مخابرات پیشرو", "02144556677", "procurement@telecom-p.ir", "پکیج کامل آزمایشگاه", "برای راه‌اندازی آزمایشگاه جدید نیاز به مجموعه کامل تجهیزات داریم.", "pending", "high", 1),
    ]
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            for name, phone, email, product_name, message, status, priority, days_ago in inquiries:
                created_at = datetime.now() - timedelta(days=days_ago)
                
                cursor.execute("""
                    INSERT INTO inquiries (name, phone, email, product_name, message, status, priority, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (name, phone, email, product_name, message, status, priority, created_at))
        
        conn.commit()
        logger.info(f"✅ {len(inquiries)} استعلام قیمت ایجاد شد")
    finally:
        conn.close()

def main():
    """اجرای اصلی"""
    print("🚀 شروع پر کردن دیتابیس با اطلاعات کامل...")
    
    if not confirm_reset():
        print("❌ عملیات لغو شد.")
        return
    
    try:
        clear_data()
        seed_categories()
        seed_products()
        seed_services()
        seed_educational()
        seed_inquiries()
        
        print("\n" + "="*60)
        print("🎉 دیتابیس با موفقیت پر شد!")
        print("="*60)
        print("✅ 16 دسته‌بندی")
        print("✅ 13 محصول")
        print("✅ 10 خدمت")
        print("✅ 6 مطلب آموزشی")
        print("✅ 10 استعلام قیمت")
        print("\n💡 حالا می‌توانید از سایت و بات استفاده کنید!")
        
    except Exception as e:
        logger.error(f"خطا: {e}")
        print(f"❌ خطا: {e}")

if __name__ == "__main__":
    main()