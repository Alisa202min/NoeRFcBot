#!/usr/bin/env python3
"""
تولید سریع و کامل دیتای RFTEST
بدون وقفه - همه چیز در یک اجرا
"""

import os
import logging
from datetime import datetime, timedelta
import random
from database import Database
from PIL import Image, ImageDraw, ImageFont
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def quick_generate():
    print("🚀 تولید سریع دیتای کامل RFTEST...")
    
    db = Database()
    
    # پاک کردن دیتای قبلی
    with db.conn.cursor() as cur:
        tables = ["product_media", "service_media", "educational_content_media",
                 "products", "services", "educational_content", 
                 "product_categories", "service_categories", "educational_categories", "inquiries"]
        
        for table in tables:
            try:
                cur.execute(f"DELETE FROM {table}")
            except:
                pass
        db.conn.commit()
    
    # ایجاد پوشه‌ها
    os.makedirs("static/uploads/default", exist_ok=True)
    
    # ساخت تصویر پیش‌فرض
    img = Image.new('RGB', (800, 600), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.text((350, 280), "RFTEST", fill=(60, 60, 60))
    img.save("static/uploads/default/default.jpg")
    
    with db.conn.cursor() as cur:
        # دسته‌بندی‌های سلسله مراتبی
        # دسته اصلی محصولات
        cur.execute("INSERT INTO product_categories (name, parent_id, created_at) VALUES (%s, %s, %s) RETURNING id",
                   ("تجهیزات اندازه‌گیری", None, datetime.now()))
        main_prod = cur.fetchone()[0]
        
        # زیردسته‌های محصولات
        prod_cats = {}
        categories = ["اسیلوسکوپ دیجیتال", "اسپکتروم آنالایزر", "سیگنال ژنراتور", "نتورک آنالایزر"]
        for cat in categories:
            cur.execute("INSERT INTO product_categories (name, parent_id, created_at) VALUES (%s, %s, %s) RETURNING id",
                       (cat, main_prod, datetime.now()))
            prod_cats[cat] = cur.fetchone()[0]
        
        # دسته اصلی خدمات
        cur.execute("INSERT INTO service_categories (name, parent_id, created_at) VALUES (%s, %s, %s) RETURNING id",
                   ("خدمات RFTEST", None, datetime.now()))
        main_service = cur.fetchone()[0]
        
        # زیردسته‌های خدمات
        service_cats = {}
        s_categories = ["کالیبراسیون تجهیزات", "تعمیرات تخصصی", "آموزش فنی", "مشاوره تخصصی"]
        for cat in s_categories:
            cur.execute("INSERT INTO service_categories (name, parent_id, created_at) VALUES (%s, %s, %s) RETURNING id",
                       (cat, main_service, datetime.now()))
            service_cats[cat] = cur.fetchone()[0]
        
        # دسته اصلی آموزشی
        cur.execute("INSERT INTO educational_categories (name, parent_id, created_at) VALUES (%s, %s, %s) RETURNING id",
                   ("محتوای آموزشی", None, datetime.now()))
        main_edu = cur.fetchone()[0]
        
        # زیردسته‌های آموزشی
        edu_cats = {}
        e_categories = ["راهنمای کاربری", "اصول اندازه‌گیری RF", "تست و عیب‌یابی"]
        for cat in e_categories:
            cur.execute("INSERT INTO educational_categories (name, parent_id, created_at) VALUES (%s, %s, %s) RETURNING id",
                       (cat, main_edu, datetime.now()))
            edu_cats[cat] = cur.fetchone()[0]
        
        print("✅ دسته‌بندی‌های سلسله مراتبی ایجاد شد")
        
        # تولید 30 محصول
        products = [
            ("اسیلوسکوپ دیجیتال Keysight DSOX2002A", "اسیلوسکوپ دیجیتال", 45000000, "Keysight", "DSOX2002A"),
            ("اسیلوسکوپ دیجیتال Keysight DSOX3024T", "اسیلوسکوپ دیجیتال", 85000000, "Keysight", "DSOX3024T"),
            ("اسیلوسکوپ دیجیتال Rigol DS1054Z", "اسیلوسکوپ دیجیتال", 22000000, "Rigol", "DS1054Z"),
            ("اسیلوسکوپ دیجیتال Tektronix TBS1102B", "اسیلوسکوپ دیجیتال", 12000000, "Tektronix", "TBS1102B"),
            ("اسیلوسکوپ USB Hantek DSO2C10", "اسیلوسکوپ دیجیتال", 3500000, "Hantek", "DSO2C10"),
            ("اسیلوسکوپ پرتابل Fluke ScopeMeter 199C", "اسیلوسکوپ دیجیتال", 78000000, "Fluke", "199C"),
            ("اسیلوسکوپ میکسد سیگنال Keysight MSOX3104T", "اسیلوسکوپ دیجیتال", 165000000, "Keysight", "MSOX3104T"),
            ("اسپکتروم آنالایزر Rohde & Schwarz FSW50", "اسپکتروم آنالایزر", 850000000, "Rohde & Schwarz", "FSW50"),
            ("اسپکتروم آنالایزر Agilent E4402B", "اسپکتروم آنالایزر", 125000000, "Agilent", "E4402B"),
            ("اسپکتروم آنالایزر Keysight N9010A", "اسپکتروم آنالایزر", 285000000, "Keysight", "N9010A"),
            ("اسپکتروم آنالایزر Anritsu MS2720T", "اسپکتروم آنالایزر", 195000000, "Anritsu", "MS2720T"),
            ("اسپکتروم آنالایزر پرتابل Rigol DSA832", "اسپکتروم آنالایزر", 45000000, "Rigol", "DSA832"),
            ("اسپکتروم آنالایزر USB TinySA Ultra", "اسپکتروم آنالایزر", 2800000, "TinySA", "Ultra"),
            ("سیگنال ژنراتور Keysight E8257D", "سیگنال ژنراتور", 780000000, "Keysight", "E8257D"),
            ("سیگنال ژنراتور Agilent E4438C", "سیگنال ژنراتور", 185000000, "Agilent", "E4438C"),
            ("سیگنال ژنراتور Rohde & Schwarz SMB100A", "سیگنال ژنراتور", 125000000, "Rohde & Schwarz", "SMB100A"),
            ("فانکشن ژنراتور Rigol DG1062Z", "سیگنال ژنراتور", 15000000, "Rigol", "DG1062Z"),
            ("آربیتری ژنراتور Keysight 33622A", "سیگنال ژنراتور", 95000000, "Keysight", "33622A"),
            ("نتورک آنالایزر Keysight E5071C", "نتورک آنالایزر", 385000000, "Keysight", "E5071C"),
            ("نتورک آنالایزر Rohde & Schwarz ZNB20", "نتورک آنالایزر", 485000000, "Rohde & Schwarz", "ZNB20"),
            ("VNA پرتابل NanoVNA H4", "نتورک آنالایزر", 1200000, "NanoVNA", "H4"),
            ("پاورمتر Keysight N1911A", "اسپکتروم آنالایزر", 65000000, "Keysight", "N1911A"),
            ("سنسور توان Rohde & Schwarz NRP-Z21", "اسپکتروم آنالایزر", 28000000, "Rohde & Schwarz", "NRP-Z21"),
            ("رادیوتستر Aeroflex 3920B", "اسپکتروم آنالایزر", 320000000, "Aeroflex", "3920B"),
            ("رادیوتستر Marconi 2955B", "اسپکتروم آنالایزر", 85000000, "Marconi", "2955B"),
            ("رادیوتستر IFR 2965", "اسپکتروم آنالایزر", 145000000, "IFR", "2965"),
            ("فرکانس کانتر Keysight 53230A", "اسیلوسکوپ دیجیتال", 145000000, "Keysight", "53230A"),
            ("مالتی متر دقیق Keysight 34470A", "اسیلوسکوپ دیجیتال", 32000000, "Keysight", "34470A"),
            ("آنتن آنالایزر Keysight E5071B", "نتورک آنالایزر", 185000000, "Keysight", "E5071B"),
            ("کالیبراتور VNA Keysight 85032F", "نتورک آنالایزر", 65000000, "Keysight", "85032F")
        ]
        
        for i, (name, cat, price, brand, model) in enumerate(products, 1):
            category_id = prod_cats.get(cat, list(prod_cats.values())[0])
            
            cur.execute("""
                INSERT INTO products (name, description, price, category_id, brand, model, tags, in_stock, featured, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (name, f"تجهیز پیشرفته {cat} از برند {brand}", price, category_id, brand, model, 
                  f"{cat},{brand}", True, i <= 10, datetime.now()))
            
            product_id = cur.fetchone()[0]
            
            # اضافه کردن تصاویر
            product_dir = f"static/uploads/products/{product_id}"
            os.makedirs(product_dir, exist_ok=True)
            
            for j in range(4):
                img_name = "main.jpg" if j == 0 else f"extra_{j}.jpg"
                shutil.copy("static/uploads/default/default.jpg", f"{product_dir}/{img_name}")
                cur.execute("INSERT INTO product_media (product_id, file_id, file_type) VALUES (%s, %s, %s)",
                           (product_id, f"uploads/products/{product_id}/{img_name}", "photo"))
        
        print(f"✅ {len(products)} محصول ایجاد شد")
        
        # تولید 50 خدمات
        services = [
            ("کالیبراسیون اسیلوسکوپ", "کالیبراسیون تجهیزات", 3500000),
            ("کالیبراسیون اسپکتروم آنالایزر", "کالیبراسیون تجهیزات", 4500000),
            ("کالیبراسیون سیگنال ژنراتور", "کالیبراسیون تجهیزات", 4000000),
            ("کالیبراسیون نتورک آنالایزر", "کالیبراسیون تجهیزات", 5500000),
            ("کالیبراسیون پاورمتر", "کالیبراسیون تجهیزات", 2500000),
            ("کالیبراسیون رادیوتستر", "کالیبراسیون تجهیزات", 6000000),
            ("کالیبراسیون فرکانس کانتر", "کالیبراسیون تجهیزات", 3000000),
            ("کالیبراسیون مالتی متر", "کالیبراسیون تجهیزات", 1500000),
            ("کالیبراسیون آنتن آنالایزر", "کالیبراسیون تجهیزات", 3500000),
            ("کالیبراسیون نویز فیگور متر", "کالیبراسیون تجهیزات", 4200000),
            ("تعمیر اسیلوسکوپ", "تعمیرات تخصصی", 5500000),
            ("تعمیر اسپکتروم آنالایزر", "تعمیرات تخصصی", 8500000),
            ("تعمیر سیگنال ژنراتور", "تعمیرات تخصصی", 6500000),
            ("تعمیر نتورک آنالایزر", "تعمیرات تخصصی", 9500000),
            ("تعمیر رادیوتستر", "تعمیرات تخصصی", 12000000),
            ("بازسازی تجهیزات قدیمی", "تعمیرات تخصصی", 15000000),
            ("تعمیر پاورمتر", "تعمیرات تخصصی", 4500000),
            ("تعمیر آنتن آنالایزر", "تعمیرات تخصصی", 5200000),
            ("آپگرید نرم‌افزار تجهیزات", "تعمیرات تخصصی", 2500000),
            ("تعمیر فرکانس کانتر", "تعمیرات تخصصی", 3800000),
            ("آموزش کاربردی RF و میکروویو", "آموزش فنی", 12000000),
            ("آموزش استفاده از اسیلوسکوپ", "آموزش فنی", 6000000),
            ("آموزش اسپکتروم آنالیز", "آموزش فنی", 8000000),
            ("آموزش S-parameter measurements", "آموزش فنی", 10000000),
            ("دوره جامع تست EMC", "آموزش فنی", 15000000),
            ("آموزش کار با نتورک آنالایزر", "آموزش فنی", 9000000),
            ("آموزش تکنیک‌های اندازه‌گیری", "آموزش فنی", 7500000),
            ("آموزش تست آنتن", "آموزش فنی", 8500000),
            ("آموزش کالیبراسیون عملی", "آموزش فنی", 6500000),
            ("دوره تخصصی 5G Testing", "آموزش فنی", 18000000),
            ("مشاوره انتخاب تجهیزات آزمایشگاه", "مشاوره تخصصی", 2000000),
            ("مشاوره طراحی آزمایشگاه RF", "مشاوره تخصصی", 5000000),
            ("مشاوره استانداردهای کالیبراسیون", "مشاوره تخصصی", 3000000),
            ("بررسی و ارزیابی تجهیزات", "مشاوره تخصصی", 2500000),
            ("مشاوره بهینه‌سازی اندازه‌گیری", "مشاوره تخصصی", 3500000),
            ("مشاوره استراتژی تست", "مشاوره تخصصی", 4000000),
            ("مشاوره انتخاب استاندارد", "مشاوره تخصصی", 2800000),
            ("مشاوره طراحی سیستم تست", "مشاوره تخصصی", 6000000),
            ("تنظیم و راه‌اندازی تجهیزات", "کالیبراسیون تجهیزات", 3000000),
            ("قرارداد نگهداری سالانه", "کالیبراسیون تجهیزات", 15000000),
            ("پشتیبانی فنی 24 ساعته", "مشاوره تخصصی", 500000),
            ("خدمات اورژانسی", "تعمیرات تخصصی", 8000000),
            ("طراحی کامل آزمایشگاه", "مشاوره تخصصی", 25000000),
            ("نصب و راه‌اندازی سیستم", "تعمیرات تخصصی", 8000000),
            ("بازدید و ارزیابی دوره‌ای", "کالیبراسیون تجهیزات", 1500000),
            ("آموزش کارکنان مشتری", "آموزش فنی", 5500000),
            ("تحلیل عملکرد تجهیزات", "مشاوره تخصصی", 2200000),
            ("گزارش‌نویسی فنی تخصصی", "مشاوره تخصصی", 1800000),
            ("خدمات کنترل کیفیت", "کالیبراسیون تجهیزات", 3200000),
            ("خدمات اجاره تجهیزات", "تعمیرات تخصصی", 2500000)
        ]
        
        for i, (name, cat, price) in enumerate(services, 1):
            category_id = service_cats.get(cat, list(service_cats.values())[0])
            
            cur.execute("""
                INSERT INTO services (name, description, price, category_id, tags, featured, available, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (name, f"خدمات تخصصی {cat} توسط متخصصان RFTEST", price, category_id, 
                  f"{cat},RFTEST", i <= 10, True, datetime.now()))
            
            service_id = cur.fetchone()[0]
            
            # اضافه کردن تصویر خدمات
            service_dir = f"static/uploads/services/{service_id}"
            os.makedirs(service_dir, exist_ok=True)
            shutil.copy("static/uploads/default/default.jpg", f"{service_dir}/main.jpg")
            cur.execute("INSERT INTO service_media (service_id, file_id, file_type) VALUES (%s, %s, %s)",
                       (service_id, f"uploads/services/{service_id}/main.jpg", "photo"))
        
        print(f"✅ {len(services)} خدمات ایجاد شد")
        
        # تولید 20 مطلب آموزشی
        educational = [
            ("راهنمای کامل استفاده از اسیلوسکوپ دیجیتال", "راهنمای کاربری"),
            ("نحوه کار با اسپکتروم آنالایزر", "راهنمای کاربری"),
            ("راهنمای استفاده از نتورک آنالایزر", "راهنمای کاربری"),
            ("تنظیمات اولیه رادیوتستر", "راهنمای کاربری"),
            ("راهنمای تعمیر و نگهداری تجهیزات", "راهنمای کاربری"),
            ("راهنمای ایمنی در آزمایشگاه RF", "راهنمای کاربری"),
            ("راهنمای انتخاب کابل و کانکتور", "راهنمای کاربری"),
            ("اصول اندازه‌گیری توان RF", "اصول اندازه‌گیری RF"),
            ("مفهوم نویز فاز در سیگنال‌ها", "اصول اندازه‌گیری RF"),
            ("تئوری اسپکتروم و تحلیل فرکانسی", "اصول اندازه‌گیری RF"),
            ("اندازه‌گیری امپدانس و SWR", "اصول اندازه‌گیری RF"),
            ("اصول پراکندگی S-parameters", "اصول اندازه‌گیری RF"),
            ("روش‌های عیب‌یابی در مدارات RF", "تست و عیب‌یابی"),
            ("تکنیک‌های اندازه‌گیری S-parameters", "تست و عیب‌یابی"),
            ("تست تداخل و EMC", "تست و عیب‌یابی"),
            ("عیب‌یابی تجهیزات اندازه‌گیری", "تست و عیب‌یابی"),
            ("تکنیک‌های تست آنتن", "تست و عیب‌یابی"),
            ("روش‌های کنترل کیفیت در اندازه‌گیری", "تست و عیب‌یابی"),
            ("تست و ارزیابی کارکرد فیلترها", "تست و عیب‌یابی"),
            ("پروژه طراحی و تست فیلتر RF", "تست و عیب‌یابی")
        ]
        
        for i, (title, cat) in enumerate(educational, 1):
            category_id = edu_cats.get(cat, list(edu_cats.values())[0])
            content = f"این مطلب جامع در زمینه {cat} تهیه شده است. شامل توضیحات کامل، مثال‌های عملی و نکات کاربردی برای متخصصان و علاقه‌مندان به تجهیزات اندازه‌گیری RF."
            
            cur.execute("""
                INSERT INTO educational_content (title, content, category, category_id, created_at)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (title, content, cat, category_id, datetime.now()))
            
            content_id = cur.fetchone()[0]
            
            # اضافه کردن تصویر آموزشی
            edu_dir = f"static/uploads/educational/{content_id}"
            os.makedirs(edu_dir, exist_ok=True)
            shutil.copy("static/uploads/default/default.jpg", f"{edu_dir}/main.jpg")
            cur.execute("INSERT INTO educational_content_media (educational_content_id, file_id, file_type) VALUES (%s, %s, %s)",
                       (content_id, f"uploads/educational/{content_id}/main.jpg", "photo"))
        
        print(f"✅ {len(educational)} مطلب آموزشی ایجاد شد")
        
        # تولید 25 استعلام قیمت
        inquiries = [
            (7625738591, "مهندس احمد رضایی", "09121234567", "استعلام قیمت اسیلوسکوپ 100MHz برای آزمایشگاه دانشگاه"),
            (987654321, "شرکت فناوری پارس", "02144556677", "درخواست کالیبراسیون 5 دستگاه اسپکتروم آنالایزر"),
            (123456789, "دکتر محمد محمدی", "09359876543", "آیا دوره آموزشی RF برای دانشجویان ارشد برگزار می‌کنید؟"),
            (555666777, "مهندس فاطمه نوری", "09128887766", "نیاز به مشاوره برای تجهیز آزمایشگاه تست EMC"),
            (111222333, "شرکت الکترونیک آریا", "02133445566", "استعلام قیمت رادیوتستر Aeroflex 3920B"),
            (444555666, "آقای علی احمدی", "09135554433", "آیا تعمیر اسیلوسکوپ Tektronix 2465 را انجام می‌دهید؟"),
            (777888999, "مهندس سارا کریمی", "09124443322", "درخواست آموزش کار با نتورک آنالایزر"),
            (333444555, "شرکت مخابرات ایران", "02177889900", "استعلام قیمت سیگنال ژنراتور تا 6GHz"),
            (666777888, "دکتر رضا پوری", "09366655544", "نیاز به کالیبراسیون فوری پاورمتر HP 437B"),
            (222333444, "مهندس حسن زارعی", "09357778899", "استعلام قیمت اسپکتروم آنالایزر Rohde & Schwarz FSW"),
            (888999111, "شرکت رادار پردازش", "02155667788", "نیاز به آموزش تخصصی S-parameter measurements"),
            (999111222, "مهندس مریم صادقی", "09147775566", "استعلام قیمت کالیبراسیون سالانه 8 دستگاه"),
            (111333555, "آقای محسن رستمی", "09198886644", "آیا رادیوتستر Marconi 2955B دست دوم در انبار دارید؟"),
            (444666888, "شرکت نوآوری فن", "02166554433", "درخواست مشاوره انتخاب تجهیزات برای آزمایشگاه تست IoT"),
            (777999222, "دکتر امیر حسینی", "09351112233", "استعلام اجاره کوتاه مدت نتورک آنالایزر"),
            (555777999, "مهندس زهرا احمدی", "09122223344", "درخواست قیمت مجموعه کامل تجهیزات آزمایشگاه RF"),
            (333555777, "شرکت ایمن الکترونیک", "02144445566", "آیا امکان تعمیر تجهیزات قدیمی HP وجود دارد؟"),
            (666888111, "مهندس کامران رضایی", "09133334455", "نیاز به آموزش تست EMC برای تیم طراحی"),
            (222444666, "آقای مهدی کریمی", "09144445566", "استعلام قیمت اسیلوسکوپ میکسد سیگنال"),
            (888111333, "شرکت فناور سپهر", "02155556677", "درخواست مشاوره طراحی آزمایشگاه استاندارد"),
            (111444777, "دکتر فریده پورحسن", "09155557788", "آیا کالیبراسیون تجهیزات در محل دانشگاه انجام می‌شود؟"),
            (999222555, "مهندس بهزاد نظری", "09166668899", "استعلام قیمت پکیج کامل تجهیزات تست 5G"),
            (444777111, "شرکت پیشرو تک", "02177778899", "نیاز به پشتیبانی فنی مداوم برای آزمایشگاه"),
            (777111444, "مهندس نیما فتحی", "09177779911", "درخواست آموزش کار با VNA و تفسیر نتایج"),
            (555888222, "شرکت دانش‌پژوه", "02188889911", "استعلام قیمت قرارداد نگهداری ساليانه تجهیزات")
        ]
        
        for user_id, name, phone, desc in inquiries:
            days_ago = random.randint(1, 180)
            created_date = datetime.now() - timedelta(days=days_ago)
            
            cur.execute("""
                INSERT INTO inquiries (user_id, name, phone, description, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, name, phone, desc, "pending", created_date))
        
        print(f"✅ {len(inquiries)} استعلام قیمت ایجاد شد")
        
        db.conn.commit()
    
    # گزارش نهایی
    with db.conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM products')
        products_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM services')
        services_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM educational_content')
        educational_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM inquiries')
        inquiries_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM product_media')
        product_media_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM service_media')
        service_media_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM educational_content_media')
        edu_media_count = cur.fetchone()[0]
    
    print("\n" + "="*60)
    print("🎉 دیتای کامل RFTEST با موفقیت تولید شد!")
    print("="*60)
    print(f"✅ {products_count} محصول تجهیزات اندازه‌گیری")
    print(f"✅ {services_count} خدمات تخصصی")
    print(f"✅ {educational_count} مطلب آموزشی")
    print(f"✅ {inquiries_count} استعلام قیمت")
    print(f"✅ {product_media_count} تصویر محصولات")
    print(f"✅ {service_media_count} تصویر خدمات")
    print(f"✅ {edu_media_count} تصویر آموزشی")
    print("✅ دسته‌بندی‌های سلسله مراتبی کامل")
    print()
    print("🌐 وب پنل: مدیریت کامل محتوا")
    print("🤖 بات تلگرام: @RFCatbot")
    print("📧 ایمیل: rftestiran@gmail.com")
    print("📞 تلفن: 09125445277")
    print("🌍 وبسایت: www.rftest.ir")
    print("="*60)

if __name__ == "__main__":
    quick_generate()