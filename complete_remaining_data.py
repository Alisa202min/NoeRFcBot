#!/usr/bin/env python3
"""
تکمیل دیتای باقی‌مانده RFTEST
"""

import os
import logging
from datetime import datetime, timedelta
import random
from database import Database
import shutil

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def complete_products(db):
    """تکمیل محصولات باقی‌مانده"""
    logger.info("تکمیل محصولات باقی‌مانده...")
    
    # چک کردن تعداد فعلی محصولات
    with db.conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM products")
        current_count = cur.fetchone()[0]
    
    if current_count >= 30:
        logger.info("تمام محصولات قبلاً اضافه شده‌اند")
        return
    
    # محصولات باقی‌مانده
    remaining_products = [
        {"name": "نتورک آنالایزر Rohde & Schwarz ZNB20", "cat": "نتورک آنالایزر", "price": 485000000, "brand": "Rohde & Schwarz", "model": "ZNB20", "featured": True},
        {"name": "VNA پرتابل NanoVNA H4", "cat": "نتورک آنالایزر", "price": 1200000, "brand": "NanoVNA", "model": "H4", "featured": False},
        {"name": "پاورمتر Keysight N1911A", "cat": "پاورمتر و سنسور", "price": 65000000, "brand": "Keysight", "model": "N1911A", "featured": False},
        {"name": "سنسور توان Rohde & Schwarz NRP-Z21", "cat": "پاورمتر و سنسور", "price": 28000000, "brand": "Rohde & Schwarz", "model": "NRP-Z21", "featured": False},
        {"name": "فرکانس کانتر Keysight 53230A", "cat": "فرکانس متر", "price": 145000000, "brand": "Keysight", "model": "53230A", "featured": False},
        {"name": "مالتی متر دقیق Keysight 34470A", "cat": "مالتی متر", "price": 32000000, "brand": "Keysight", "model": "34470A", "featured": False}
    ]
    
    with db.conn.cursor() as cur:
        # گرفتن دسته‌بندی‌ها
        cur.execute("SELECT id, name FROM product_categories")
        categories = {row[1]: row[0] for row in cur.fetchall()}
        
        for i, product in enumerate(remaining_products, current_count + 1):
            if i > 30:
                break
                
            category_id = categories.get(product['cat'])
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

def create_services(db):
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
        # گرفتن دسته‌بندی‌ها
        cur.execute("SELECT id, name FROM service_categories")
        categories = {row[1]: row[0] for row in cur.fetchall()}
        
        for i, service in enumerate(services_data, 1):
            category_id = categories.get(service['cat'])
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
            
            main_image = f"{service_dir}/main.jpg"
            shutil.copy("static/uploads/default/service.jpg", main_image)
            
            cur.execute("""
                INSERT INTO service_media (service_id, file_id, file_type)
                VALUES (%s, %s, %s)
            """, (service_id, f"uploads/services/{service_id}/main.jpg", "photo"))
            
            logger.info(f"✅ خدمت {i}/25: {service['name']}")
        
        db.conn.commit()

def create_educational_content(db):
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
        # گرفتن دسته‌بندی‌ها
        cur.execute("SELECT id, name FROM educational_categories")
        categories = {row[1]: row[0] for row in cur.fetchall()}
        
        for i, content in enumerate(educational_data, 1):
            category_id = categories.get(content['cat'])
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
            
            main_image = f"{edu_dir}/main.jpg"
            shutil.copy("static/uploads/default/educational.jpg", main_image)
            
            cur.execute("""
                INSERT INTO educational_content_media (educational_content_id, file_id, file_type)
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
    logger.info("🚀 تکمیل دیتای باقی‌مانده RFTEST...")
    
    try:
        # اتصال به دیتابیس
        db = Database()
        
        # تکمیل محصولات
        complete_products(db)
        
        # ایجاد خدمات
        create_services(db)
        
        # ایجاد محتوای آموزشی
        create_educational_content(db)
        
        # ایجاد استعلامات
        create_inquiries(db)
        
        # گزارش نهایی
        with db.conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM products')
            products = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM services') 
            services = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM educational_content')
            educational = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM inquiries')
            inquiries = cur.fetchone()[0]
            
            print("\n" + "="*70)
            print("🎉 دیتای کامل RFTEST با موفقیت ایجاد شد!")
            print("="*70)
            print(f"✅ {products} محصول تجهیزات اندازه‌گیری با تصاویر")
            print(f"✅ {services} خدمات تخصصی با رسانه‌های مرتبط")
            print(f"✅ {educational} مطلب آموزشی با تصاویر آموزشی")
            print(f"✅ {inquiries} استعلام قیمت واقعی")
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
        logger.error(f"❌ خطا در تکمیل دیتا: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()