#!/usr/bin/env python3
"""
تولیدکننده دیتای کامل RFTEST
فایل واحد و بهینه برای تولید همه دیتا
15 محصول + 15 خدمات + 15 مطلب آموزشی + 15 استعلام
"""

import os
from datetime import datetime, timedelta
import random
from database import Database
from PIL import Image, ImageDraw, ImageFont
import shutil

def create_image(path, text):
    """ساخت تصویر با متن مشخص"""
    img = Image.new('RGB', (800, 600), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((300, 280), text, fill=(60, 60, 60), font=font)
    draw.text((50, 50), "RFTEST.IR", fill=(0, 102, 204), font=font)
    img.save(path)

def clear_all_data(db):
    """پاک کردن تمام دیتای قبلی"""
    print("🗑️ پاک کردن دیتای قبلی...")
    
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
            except Exception as e:
                pass
        
        db.conn.commit()
    print("✅ دیتای قبلی پاک شد")

def create_hierarchical_categories(db):
    """ایجاد دسته‌بندی‌های سلسله مراتبی"""
    print("🗂️ ایجاد دسته‌بندی‌های سلسله مراتبی...")
    
    categories = {}
    
    with db.conn.cursor() as cur:
        # === دسته‌های محصولات ===
        cur.execute("""
            INSERT INTO product_categories (name, parent_id, created_at) 
            VALUES (%s, %s, %s) RETURNING id
        """, ("تجهیزات اندازه‌گیری", None, datetime.now()))
        main_prod = cur.fetchone()[0]
        
        prod_subcats = ["اسیلوسکوپ", "اسپکتروم آنالایزر", "سیگنال ژنراتور"]
        for cat in prod_subcats:
            cur.execute("""
                INSERT INTO product_categories (name, parent_id, created_at) 
                VALUES (%s, %s, %s) RETURNING id
            """, (cat, main_prod, datetime.now()))
            categories[f"product_{cat}"] = cur.fetchone()[0]
        
        # === دسته‌های خدمات ===
        cur.execute("""
            INSERT INTO service_categories (name, parent_id, created_at) 
            VALUES (%s, %s, %s) RETURNING id
        """, ("خدمات RFTEST", None, datetime.now()))
        main_service = cur.fetchone()[0]
        
        service_subcats = ["کالیبراسیون", "تعمیرات", "آموزش"]
        for cat in service_subcats:
            cur.execute("""
                INSERT INTO service_categories (name, parent_id, created_at) 
                VALUES (%s, %s, %s) RETURNING id
            """, (cat, main_service, datetime.now()))
            categories[f"service_{cat}"] = cur.fetchone()[0]
        
        # === دسته‌های آموزشی ===
        cur.execute("""
            INSERT INTO educational_categories (name, parent_id, created_at) 
            VALUES (%s, %s, %s) RETURNING id
        """, ("محتوای آموزشی", None, datetime.now()))
        main_edu = cur.fetchone()[0]
        
        edu_subcats = ["راهنما", "تئوری", "عملی"]
        for cat in edu_subcats:
            cur.execute("""
                INSERT INTO educational_categories (name, parent_id, created_at) 
                VALUES (%s, %s, %s) RETURNING id
            """, (cat, main_edu, datetime.now()))
            categories[f"educational_{cat}"] = cur.fetchone()[0]
        
        db.conn.commit()
    
    print("✅ دسته‌بندی‌های سلسله مراتبی ایجاد شد")
    return categories

def create_products_with_images(db, categories):
    """ایجاد 15 محصول با تصاویر کامل"""
    print("📦 ایجاد 15 محصول با تصاویر...")
    
    products_data = [
        ("اسیلوسکوپ Keysight DSOX2002A", "اسیلوسکوپ", 45000000, "Keysight"),
        ("اسیلوسکوپ Rigol DS1054Z", "اسیلوسکوپ", 22000000, "Rigol"),
        ("اسیلوسکوپ Tektronix TBS1102B", "اسیلوسکوپ", 12000000, "Tektronix"),
        ("اسیلوسکوپ Hantek DSO2C10", "اسیلوسکوپ", 3500000, "Hantek"),
        ("اسیلوسکوپ Fluke ScopeMeter", "اسیلوسکوپ", 78000000, "Fluke"),
        ("اسپکتروم آنالایزر Rohde & Schwarz FSW50", "اسپکتروم آنالایزر", 850000000, "Rohde & Schwarz"),
        ("اسپکتروم آنالایزر Agilent E4402B", "اسپکتروم آنالایزر", 125000000, "Agilent"),
        ("اسپکتروم آنالایزر Keysight N9010A", "اسپکتروم آنالایزر", 285000000, "Keysight"),
        ("اسپکتروم آنالایزر Anritsu MS2720T", "اسپکتروم آنالایزر", 195000000, "Anritsu"),
        ("اسپکتروم آنالایزر Rigol DSA832", "اسپکتروم آنالایزر", 45000000, "Rigol"),
        ("سیگنال ژنراتور Keysight E8257D", "سیگنال ژنراتور", 780000000, "Keysight"),
        ("سیگنال ژنراتور Agilent E4438C", "سیگنال ژنراتور", 185000000, "Agilent"),
        ("سیگنال ژنراتور Rohde & Schwarz SMB100A", "سیگنال ژنراتور", 125000000, "Rohde & Schwarz"),
        ("فانکشن ژنراتور Rigol DG1062Z", "سیگنال ژنراتور", 15000000, "Rigol"),
        ("آربیتری ژنراتور Keysight 33622A", "سیگنال ژنراتور", 95000000, "Keysight")
    ]
    
    with db.conn.cursor() as cur:
        for i, (name, cat, price, brand) in enumerate(products_data, 1):
            category_id = categories[f"product_{cat}"]
            
            # ایجاد محصول
            cur.execute("""
                INSERT INTO products (name, description, price, category_id, brand, model, tags, in_stock, featured, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (name, f"تجهیز پیشرفته {cat} از برند معتبر {brand}", price, category_id, 
                  brand, f"MODEL-{i:03d}", f"{cat},{brand},تجهیزات اندازه‌گیری", True, i <= 5, datetime.now()))
            
            product_id = cur.fetchone()[0]
            
            # ایجاد پوشه محصول
            product_dir = f"static/uploads/products/{product_id}"
            os.makedirs(product_dir, exist_ok=True)
            
            # تصویر اصلی + 3 تصویر اضافی
            for j in range(4):
                if j == 0:
                    img_name = "main.jpg"
                    text = f"{name[:25]}..."
                else:
                    img_name = f"extra_{j}.jpg"
                    text = f"تصویر اضافی {j}"
                
                img_path = f"{product_dir}/{img_name}"
                create_image(img_path, text)
                
                cur.execute("""
                    INSERT INTO product_media (product_id, file_id, file_type) 
                    VALUES (%s, %s, %s)
                """, (product_id, f"uploads/products/{product_id}/{img_name}", "photo"))
        
        db.conn.commit()
    
    print("✅ 15 محصول با تصاویر کامل ایجاد شد")

def create_services_with_images(db, categories):
    """ایجاد 15 خدمات با تصاویر"""
    print("🔧 ایجاد 15 خدمات با تصاویر...")
    
    services_data = [
        ("کالیبراسیون اسیلوسکوپ", "کالیبراسیون", 3500000),
        ("کالیبراسیون اسپکتروم آنالایزر", "کالیبراسیون", 4500000),
        ("کالیبراسیون سیگنال ژنراتور", "کالیبراسیون", 4000000),
        ("کالیبراسیون نتورک آنالایزر", "کالیبراسیون", 5500000),
        ("کالیبراسیون پاورمتر و سنسور", "کالیبراسیون", 2500000),
        ("تعمیر اسیلوسکوپ دیجیتال", "تعمیرات", 5500000),
        ("تعمیر اسپکتروم آنالایزر", "تعمیرات", 8500000),
        ("تعمیر سیگنال ژنراتور", "تعمیرات", 6500000),
        ("تعمیر نتورک آنالایزر", "تعمیرات", 9500000),
        ("بازسازی تجهیزات قدیمی", "تعمیرات", 15000000),
        ("آموزش کاربردی RF و میکروویو", "آموزش", 12000000),
        ("آموزش استفاده از اسیلوسکوپ", "آموزش", 6000000),
        ("آموزش اسپکتروم آنالیز", "آموزش", 8000000),
        ("دوره جامع تست EMC", "آموزش", 15000000),
        ("آموزش کار با نتورک آنالایزر", "آموزش", 9000000)
    ]
    
    with db.conn.cursor() as cur:
        for i, (name, cat, price) in enumerate(services_data, 1):
            category_id = categories[f"service_{cat}"]
            
            # ایجاد خدمت
            cur.execute("""
                INSERT INTO services (name, description, price, category_id, tags, featured, available, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (name, f"خدمات تخصصی {cat} توسط متخصصان مجرب RFTEST. کیفیت بالا و قیمت مناسب.", 
                  price, category_id, f"{cat},RFTEST,خدمات تخصصی", i <= 5, True, datetime.now()))
            
            service_id = cur.fetchone()[0]
            
            # ایجاد تصویر خدمات
            service_dir = f"static/uploads/services/{service_id}"
            os.makedirs(service_dir, exist_ok=True)
            
            img_path = f"{service_dir}/main.jpg"
            create_image(img_path, f"خدمات {cat}")
            
            cur.execute("""
                INSERT INTO service_media (service_id, file_id, file_type) 
                VALUES (%s, %s, %s)
            """, (service_id, f"uploads/services/{service_id}/main.jpg", "photo"))
        
        db.conn.commit()
    
    print("✅ 15 خدمات با تصاویر ایجاد شد")

def create_educational_content_with_images(db, categories):
    """ایجاد 15 مطلب آموزشی با تصاویر"""
    print("📚 ایجاد 15 مطلب آموزشی با تصاویر...")
    
    educational_data = [
        ("راهنمای کامل استفاده از اسیلوسکوپ دیجیتال", "راهنما"),
        ("نحوه کار با اسپکتروم آنالایزر", "راهنما"),
        ("راهنمای استفاده از نتورک آنالایزر", "راهنما"),
        ("تنظیمات اولیه رادیوتستر", "راهنما"),
        ("راهنمای ایمنی در آزمایشگاه RF", "راهنما"),
        ("اصول اندازه‌گیری توان RF", "تئوری"),
        ("مفهوم نویز فاز در سیگنال‌ها", "تئوری"),
        ("تئوری اسپکتروم و تحلیل فرکانسی", "تئوری"),
        ("اندازه‌گیری امپدانس و SWR", "تئوری"),
        ("اصول پراکندگی S-parameters", "تئوری"),
        ("روش‌های عیب‌یابی در مدارات RF", "عملی"),
        ("تکنیک‌های اندازه‌گیری S-parameters", "عملی"),
        ("تست تداخل و EMC", "عملی"),
        ("تکنیک‌های تست آنتن", "عملی"),
        ("پروژه طراحی و تست فیلتر RF", "عملی")
    ]
    
    with db.conn.cursor() as cur:
        for i, (title, cat) in enumerate(educational_data, 1):
            category_id = categories[f"educational_{cat}"]
            
            content = f"""این مطلب جامع در زمینه {cat} تهیه شده است. شامل توضیحات کامل، مثال‌های عملی و نکات کاربردی برای متخصصان و علاقه‌مندان به تجهیزات اندازه‌گیری RF.

محتوای این مطلب شامل:
- اصول کلی و مبانی تئوری
- راهنمای گام به گام عملی
- نکات و ترفندهای کاربردی
- مثال‌های واقعی از پروژه‌ها
- منابع و مراجع تکمیلی

این محتوا مناسب برای سطوح مختلف دانش فنی و به صورت کاربردی تنظیم شده است."""
            
            # ایجاد مطلب آموزشی
            cur.execute("""
                INSERT INTO educational_content (title, content, category, category_id, created_at)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (title, content, cat, category_id, datetime.now()))
            
            content_id = cur.fetchone()[0]
            
            # ایجاد تصویر آموزشی (مسیر جدید)
            edu_dir = f"static/media/educational"
            os.makedirs(edu_dir, exist_ok=True)
            
            img_name = f"edu_{content_id}_main.jpg"
            img_path = f"{edu_dir}/{img_name}"
            create_image(img_path, f"آموزش {cat}")
            
            cur.execute("""
                INSERT INTO educational_content_media (educational_content_id, file_id, file_type, local_path) 
                VALUES (%s, %s, %s, %s)
            """, (content_id, f"educational_media_{content_id}_main", "photo", f"./static/media/educational/{img_name}"))
        
        db.conn.commit()
    
    print("✅ 15 مطلب آموزشی با تصاویر ایجاد شد")

def create_inquiries(db):
    """ایجاد 15 استعلام قیمت"""
    print("📋 ایجاد 15 استعلام قیمت...")
    
    inquiries_data = [
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
        (777999222, "دکتر امیر حسینی", "09351112233", "استعلام اجاره کوتاه مدت نتورک آنالایزر")
    ]
    
    with db.conn.cursor() as cur:
        for user_id, name, phone, desc in inquiries_data:
            # تاریخ تصادفی در 2 ماه اخیر
            days_ago = random.randint(1, 60)
            created_date = datetime.now() - timedelta(days=days_ago)
            
            cur.execute("""
                INSERT INTO inquiries (user_id, name, phone, description, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, name, phone, desc, "pending", created_date))
        
        db.conn.commit()
    
    print("✅ 15 استعلام قیمت ایجاد شد")

def generate_final_report(db):
    """تولید گزارش نهایی"""
    with db.conn.cursor() as cur:
        # شمارش کلی
        cur.execute('SELECT COUNT(*) FROM products')
        products_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM services')
        services_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM educational_content')
        educational_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM inquiries')
        inquiries_count = cur.fetchone()[0]
        
        # شمارش رسانه‌ها
        cur.execute('SELECT COUNT(*) FROM product_media')
        product_media_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM service_media')
        service_media_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM educational_content_media')
        edu_media_count = cur.fetchone()[0]
        
        # شمارش دسته‌بندی‌های سلسله مراتبی
        cur.execute('SELECT COUNT(*) FROM product_categories WHERE parent_id IS NOT NULL')
        hierarchical_cats = cur.fetchone()[0]
    
    # چاپ گزارش نهایی
    print("\n" + "="*70)
    print("🎉 دیتای کامل RFTEST با موفقیت تولید شد!")
    print("="*70)
    print(f"✅ {products_count} محصول تجهیزات اندازه‌گیری")
    print(f"✅ {services_count} خدمات تخصصی")
    print(f"✅ {educational_count} مطلب آموزشی")
    print(f"✅ {inquiries_count} استعلام قیمت")
    print()
    print(f"🖼️ {product_media_count} تصویر محصولات (شامل اصلی و اضافی)")
    print(f"🖼️ {service_media_count} تصویر خدمات")
    print(f"🖼️ {edu_media_count} تصویر آموزشی")
    print()
    print(f"🗂️ {hierarchical_cats} دسته‌بندی سلسله مراتبی")
    print("✅ ساختار والد-فرزند کامل")
    print()
    print("🌐 وب پنل: مدیریت کامل محتوا")
    print("🤖 بات تلگرام: @RFCatbot")
    print("📧 ایمیل: rftestiran@gmail.com")
    print("📞 تلفن: 09125445277")
    print("🌍 وبسایت: www.rftest.ir")
    print("="*70)
    print("🚀 سیستم RFTEST آماده استفاده!")

def main():
    """تابع اصلی - تولید کامل دیتای RFTEST"""
    print("🚀 تولیدکننده دیتای کامل RFTEST")
    print("15 محصول + 15 خدمات + 15 مطلب آموزشی + 15 استعلام")
    print("="*60)
    
    try:
        # اتصال به دیتابیس
        db = Database()
        
        # ایجاد پوشه پیش‌فرض
        os.makedirs("static/uploads/default", exist_ok=True)
        create_image("static/uploads/default/default.jpg", "RFTEST")
        
        # مراحل تولید دیتا
        clear_all_data(db)
        categories = create_hierarchical_categories(db)
        create_products_with_images(db, categories)
        create_services_with_images(db, categories)
        create_educational_content_with_images(db, categories)
        create_inquiries(db)
        
        # گزارش نهایی
        generate_final_report(db)
        
        return True
        
    except Exception as e:
        print(f"❌ خطا در تولید دیتا: {e}")
        return False

if __name__ == "__main__":
    main()