#!/usr/bin/env python3
"""
اسکریپت تولید دیتای نمونه برای شرکت RFTEST
محصولات، خدمات و مطالب آموزشی تجهیزات اندازه‌گیری مخابراتی
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import random
from database import Database

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RFTestDataSeeder:
    def __init__(self):
        self.db = Database()
        
    def confirm_data_reset(self):
        """درخواست تایید از کاربر برای پاک کردن دیتا"""
        print("\n" + "="*60)
        print("🗄️  بازنشانی دیتابیس شرکت RFTEST")
        print("="*60)
        print("این عملیات موارد زیر را پاک خواهد کرد:")
        print("❌ همه محصولات و رسانه‌های مرتبط")
        print("❌ همه خدمات و رسانه‌های مرتبط") 
        print("❌ همه مطالب آموزشی و رسانه‌های مرتبط")
        print("❌ همه دسته‌بندی‌های محصولات، خدمات و آموزشی")
        print("❌ همه استعلام‌ها")
        print()
        print("⚠️  توجه: اطلاعات کاربران و ادمین‌ها پاک نخواهد شد")
        print()
        
        while True:
            response = input("آیا مایل به ادامه هستید؟ (بله/خیر): ").strip().lower()
            if response in ['بله', 'yes', 'y']:
                return True
            elif response in ['خیر', 'no', 'n']:
                print("❌ عملیات لغو شد.")
                return False
            else:
                print("لطفاً 'بله' یا 'خیر' وارد کنید.")

    def clear_existing_data(self):
        """پاک کردن دیتای موجود (بجز کاربران و ادمین‌ها)"""
        logger.info("در حال پاک کردن دیتای موجود...")
        
        conn = self.db.get_conn()
        try:
            with conn.cursor() as cur:
                # پاک کردن رسانه‌ها
                cur.execute("DELETE FROM product_media")
                cur.execute("DELETE FROM service_media") 
                cur.execute("DELETE FROM educational_content_media")
                
                # پاک کردن محصولات و خدمات و آموزشی
                cur.execute("DELETE FROM products")
                cur.execute("DELETE FROM services")
                cur.execute("DELETE FROM educational_content")
                
                # پاک کردن دسته‌بندی‌ها
                cur.execute("DELETE FROM product_categories")
                cur.execute("DELETE FROM service_categories")
                cur.execute("DELETE FROM educational_categories")
                
                # پاک کردن استعلام‌ها
                cur.execute("DELETE FROM inquiries")
                
                conn.commit()
                logger.info("✅ دیتای قبلی با موفقیت پاک شد")
                
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ خطا در پاک کردن دیتا: {e}")
            raise
        finally:
            conn.close()

    def create_product_categories(self):
        """ایجاد دسته‌بندی‌های محصولات"""
        logger.info("ایجاد دسته‌بندی‌های محصولات...")
        
        # دسته‌بندی‌های اصلی محصولات
        main_categories = [
            "اسیلوسکوپ",
            "اسپکتروم آنالایزر", 
            "سیگنال ژنراتور",
            "نتورک آنالایزر",
            "پاورمتر و سنسور",
            "رادیوتستر",
            "فرکانس متر",
            "مالتی متر دیجیتال",
            "تجهیزات کالیبراسیون"
        ]
        
        conn = self.db.get_conn()
        category_mapping = {}
        
        try:
            with conn.cursor() as cur:
                for category_name in main_categories:
                    cur.execute("""
                        INSERT INTO product_categories (name, parent_id, created_at)
                        VALUES (%s, %s, %s) RETURNING id
                    """, (category_name, None, datetime.now()))
                    
                    result = cur.fetchone()
                    if result:
                        category_id = result[0]
                        category_mapping[category_name] = category_id
                        logger.info(f"✅ دسته محصولات ایجاد شد: {category_name} (ID: {category_id})")
                    else:
                        logger.error(f"❌ خطا در دریافت ID برای دسته: {category_name}")
                
                conn.commit()
                logger.info(f"✅ کل دسته‌بندی‌های محصولات: {category_mapping}")
                
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ خطا در ایجاد دسته‌بندی محصولات: {e}")
            raise
        finally:
            conn.close()
            
        return category_mapping

    def create_service_categories(self):
        """ایجاد دسته‌بندی‌های خدمات"""
        logger.info("ایجاد دسته‌بندی‌های خدمات...")
        
        service_categories = [
            "کالیبراسیون تجهیزات",
            "تعمیرات تخصصی",
            "آموزش کاربردی",
            "مشاوره فنی",
            "تنظیم و راه‌اندازی",
            "نگهداری دوره‌ای",
            "پشتیبانی فنی"
        ]
        
        conn = self.db.get_conn()
        category_ids = []
        
        try:
            with conn.cursor() as cur:
                for category_name in service_categories:
                    cur.execute("""
                        INSERT INTO service_categories (name, parent_id, created_at)
                        VALUES (%s, %s, %s) RETURNING id
                    """, (category_name, None, datetime.now()))
                    
                    category_id = cur.fetchone()[0]
                    category_ids.append(category_id)
                    logger.info(f"✅ دسته خدمات ایجاد شد: {category_name}")
                
                conn.commit()
                
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ خطا در ایجاد دسته‌بندی خدمات: {e}")
            raise
        finally:
            conn.close()
            
        return category_ids

    def create_educational_categories(self):
        """ایجاد دسته‌بندی‌های آموزشی"""
        logger.info("ایجاد دسته‌بندی‌های آموزشی...")
        
        educational_categories = [
            "راهنمای کاربری دستگاه‌ها",
            "اصول اندازه‌گیری RF",
            "کالیبراسیون و استانداردها",
            "تست و عیب‌یابی",
            "نکات فنی و ترفندها",
            "معرفی تکنولوژی‌های جدید",
            "پروژه‌های عملی"
        ]
        
        conn = self.db.get_conn()
        category_ids = []
        
        try:
            with conn.cursor() as cur:
                for category_name in educational_categories:
                    cur.execute("""
                        INSERT INTO educational_categories (name, parent_id, created_at)
                        VALUES (%s, %s, %s) RETURNING id
                    """, (category_name, None, datetime.now()))
                    
                    category_id = cur.fetchone()[0]
                    category_ids.append(category_id)
                    logger.info(f"✅ دسته آموزشی ایجاد شد: {category_name}")
                
                conn.commit()
                
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ خطا در ایجاد دسته‌بندی آموزشی: {e}")
            raise
        finally:
            conn.close()
            
        return category_ids

    def create_default_media_files(self):
        """ساخت فایل‌های رسانه‌ای پیش‌فرض"""
        logger.info("ساخت فایل‌های رسانه‌ای پیش‌فرض...")
        
        import os
        from PIL import Image, ImageDraw, ImageFont
        
        # ایجاد پوشه‌های مورد نیاز
        dirs = [
            "static/uploads/products",
            "static/uploads/services", 
            "static/uploads/educational",
            "static/uploads/default"
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
            
        # ساخت تصویر پیش‌فرض
        def create_default_image(filename, text, bg_color=(240, 240, 240)):
            img = Image.new('RGB', (800, 600), bg_color)
            draw = ImageDraw.Draw(img)
            
            try:
                # سعی در استفاده از فونت سیستم
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # محاسبه موقعیت متن برای مرکز تصویر
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (800 - text_width) // 2
            y = (600 - text_height) // 2
            
            draw.text((x, y), text, fill=(100, 100, 100), font=font)
            img.save(filename)
            return filename
        
        # ساخت تصاویر پیش‌فرض
        default_images = {
            "product": create_default_image("static/uploads/default/product_default.jpg", "محصول RFTEST"),
            "service": create_default_image("static/uploads/default/service_default.jpg", "خدمات RFTEST"),
            "educational": create_default_image("static/uploads/default/educational_default.jpg", "آموزش RFTEST")
        }
        
        logger.info("✅ فایل‌های رسانه‌ای پیش‌فرض ساخته شد")
        return default_images

    def create_products(self, category_mapping):
        """ایجاد محصولات نمونه"""
        logger.info("ایجاد محصولات نمونه...")
        logger.info(f"دریافت شده category_mapping: {category_mapping}")
        
        # استفاده از category_mapping که از تابع قبل ارسال شده
        categories = category_mapping
        
        products_data = [
            # اسیلوسکوپ‌ها
            {
                "name": "اسیلوسکوپ دیجیتال Keysight DSOX2002A",
                "description": "اسیلوسکوپ دیجیتال 2 کاناله با پهنای باند 70MHz و نرخ نمونه‌برداری 2GSa/s. مناسب برای کاربردهای عمومی و آموزشی.",
                "price": 45000000,
                "category_name": "اسیلوسکوپ",
                "brand": "Keysight",
                "model": "DSOX2002A",
                "tags": "اسیلوسکوپ،دیجیتال،70MHz،2کانال",
                "in_stock": True,
                "featured": True
            },
            {
                "name": "اسیلوسکوپ دیجیتال Keysight DSOX3024T",
                "description": "اسیلوسکوپ دیجیتال 4 کاناله با پهنای باند 200MHz. مجهز به تاچ اسکرین و قابلیت‌های پیشرفته تحلیل سیگنال.",
                "price": 85000000,
                "category_name": "اسیلوسکوپ",
                "brand": "Keysight",
                "model": "DSOX3024T",
                "tags": "اسیلوسکوپ،دیجیتال،200MHz،4کانال،تاچ",
                "in_stock": True,
                "featured": True
            },
            {
                "name": "اسیلوسکوپ آنالوگ Tektronix 2235",
                "description": "اسیلوسکوپ آنالوگ کلاسیک 2 کاناله با پهنای باند 100MHz. بسیار مقاوم و قابل اعتماد برای کاربردهای صنعتی.",
                "price": 18000000,
                "category_name": "اسیلوسکوپ",
                "brand": "Tektronix",
                "model": "2235",
                "tags": "اسیلوسکوپ،آنالوگ،100MHz،کلاسیک",
                "in_stock": True,
                "featured": False
            },
            {
                "name": "اسیلوسکوپ دیجیتال Rigol DS1054Z",
                "description": "اسیلوسکوپ دیجیتال اقتصادی 4 کاناله با پهنای باند 50MHz. مناسب برای مبتدیان و کاربردهای عمومی.",
                "price": 22000000,
                "category_name": "اسیلوسکوپ", 
                "brand": "Rigol",
                "model": "DS1054Z",
                "tags": "اسیلوسکوپ،دیجیتال،50MHz،اقتصادی",
                "in_stock": True,
                "featured": False
            },
            # اسپکتروم آنالایزرها
            {
                "name": "اسپکتروم آنالایزر Rohde & Schwarz FSW50",
                "description": "اسپکتروم آنالایزر پیشرفته با دامنه فرکانسی تا 50GHz. مناسب برای تحلیل سیگنال‌های پیچیده و کاربردهای تحقیقاتی.",
                "price": 850000000,
                "category_name": "اسپکتروم آنالایزر",
                "brand": "Rohde & Schwarz",
                "model": "FSW50",
                "tags": "اسپکتروم،50GHz،تحلیل سیگنال،حرفه‌ای",
                "in_stock": False,
                "featured": True
            },
            {
                "name": "اسپکتروم آنالایزر Agilent E4402B",
                "description": "اسپکتروم آنالایزر ESA-E با دامنه 9kHz تا 3GHz. عملکرد عالی برای کاربردهای EMC و تست RF.",
                "price": 125000000,
                "category_name": "اسپکتروم آنالایزر",
                "brand": "Agilent",
                "model": "E4402B",
                "tags": "اسپکتروم،3GHz،EMC،RF",
                "in_stock": True,
                "featured": True
            },
            {
                "name": "اسپکتروم آنالایزر Keysight N9010A",
                "description": "اسپکتروم آنالایزر EXA با دامنه تا 26.5GHz. مناسب برای تست سیگنال‌های مخابراتی.",
                "price": 285000000,
                "category_name": "اسپکتروم آنالایزر",
                "brand": "Keysight",
                "model": "N9010A",
                "tags": "اسپکتروم،26.5GHz،مخابرات",
                "in_stock": True,
                "featured": False
            },
            # سیگنال ژنراتورها
            {
                "name": "سیگنال ژنراتور Keysight E8257D",
                "description": "سیگنال ژنراتور PSG با دامنه تا 67GHz. نویز فاز بسیار پایین و دقت بالا برای کاربردهای حساس.",
                "price": 780000000,
                "category_name": "سیگنال ژنراتور",
                "brand": "Keysight",
                "model": "E8257D",
                "tags": "سیگنال ژنراتور،67GHz،نویز فاز پایین",
                "in_stock": False,
                "featured": True
            },
            {
                "name": "سیگنال ژنراتور Agilent E4438C",
                "description": "سیگنال ژنراتور ESG با دامنه تا 6GHz. قابلیت تولید سیگنال‌های مدوله شده پیچیده.",
                "price": 185000000,
                "category_name": "سیگنال ژنراتور",
                "brand": "Agilent",
                "model": "E4438C",
                "tags": "سیگنال ژنراتور،6GHz،مدولاسیون",
                "in_stock": True,
                "featured": False
            },
            # رادیوتسترها
            {
                "name": "رادیوتستر Aeroflex 3920B",
                "description": "رادیوتستر دیجیتال پیشرفته با پشتیبانی از استانداردهای مختلف رادیویی شامل DMR، P25 و Tetra.",
                "price": 320000000,
                "category_name": "رادیوتستر",
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
                "category_name": "رادیوتستر",
                "brand": "Marconi",
                "model": "2955B",
                "tags": "رادیوتستر،آنالوگ،کلاسیک",
                "in_stock": True,
                "featured": False
            },
            {
                "name": "رادیوتستر IFR 2965",
                "description": "رادیوتستر سری 296X برای تست رادیوهای آنالوگ و دیجیتال GSM. شامل اسپکتروم آنالایزر داخلی.",
                "price": 145000000,
                "category_name": "رادیوتستر",
                "brand": "IFR",
                "model": "2965",
                "tags": "رادیوتستر،GSM،اسپکتروم آنالایزر",
                "in_stock": True,
                "featured": False
            }
        ]
        
        conn = self.db.get_conn()
        try:
            with conn.cursor() as cur:
                for product in products_data:
                    # دریافت category_id
                    category_id = categories.get(product["category_name"])
                    if not category_id:
                        continue
                    
                    # درج محصول
                    cur.execute("""
                        INSERT INTO products (
                            name, description, price, category_id, brand, model,
                            tags, in_stock, featured, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        product["name"], product["description"], product["price"],
                        category_id, product["brand"], product["model"],
                        product["tags"], product["in_stock"], product["featured"], datetime.now()
                    ))
                    
                    product_id = cur.fetchone()[0]
                    
                    # ایجاد پوشه محصول
                    product_dir = f"static/uploads/products/{product_id}"
                    os.makedirs(product_dir, exist_ok=True)
                    
                    # کپی کردن تصویر پیش‌فرض به عنوان تصویر اصلی
                    import shutil
                    main_image = f"{product_dir}/main.jpg"
                    shutil.copy("static/uploads/default/product_default.jpg", main_image)
                    
                    # اضافه کردن تصویر اصلی
                    cur.execute("""
                        INSERT INTO product_media (product_id, file_id, file_type, file_name, is_main)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (product_id, f"uploads/products/{product_id}/main.jpg", 
                          "photo", "main.jpg", True))
                    
                    # اضافه کردن 2-3 تصویر اضافی
                    for i in range(2, 4):
                        extra_image = f"{product_dir}/extra_{i}.jpg"
                        shutil.copy("static/uploads/default/product_default.jpg", extra_image)
                        cur.execute("""
                            INSERT INTO product_media (product_id, file_id, file_type, file_name, is_main)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (product_id, f"uploads/products/{product_id}/extra_{i}.jpg", 
                              "photo", f"extra_{i}.jpg", False))
                    
                    logger.info(f"✅ محصول ایجاد شد: {product['name']}")
                
                conn.commit()
                
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ خطا در ایجاد محصولات: {e}")
            raise
        finally:
            conn.close()

    def create_services(self, category_ids):
        """ایجاد خدمات نمونه"""
        logger.info("ایجاد خدمات نمونه...")
        
        services_data = [
            {
                "name": "کالیبراسیون اسیلوسکوپ",
                "description": "کالیبراسیون کامل اسیلوسکوپ‌های دیجیتال و آنالوگ طبق استانداردهای بین‌المللی. شامل بررسی دقت زمان، ولتاژ و فرکانس.",
                "price": 3500000,
                "category": 0,  # کالیبراسیون
                "tags": ["کالیبراسیون", "اسیلوسکوپ", "استاندارد"],
                "duration": "2-3 روز کاری",
                "is_featured": True
            },
            {
                "name": "تعمیر تخصصی اسپکتروم آنالایزر",
                "description": "تعمیر و نگهداری تخصصی اسپکتروم آنالایزرهای مختلف. تعویض قطعات، تنظیم مجدد و بازیابی عملکرد.",
                "price": 8500000,
                "category": 1,  # تعمیرات
                "tags": ["تعمیر", "اسپکتروم آنالایزر", "نگهداری"],
                "duration": "5-10 روز کاری",
                "is_featured": True
            },
            {
                "name": "آموزش کاربردی RF و میکروویو",
                "description": "دوره جامع آموزش اندازه‌گیری‌های RF شامل کار با تجهیزات، تفسیر نتایج و تکنیک‌های عملی.",
                "price": 12000000,
                "category": 2,  # آموزش
                "tags": ["آموزش", "RF", "میکروویو", "عملی"],
                "duration": "40 ساعت (10 جلسه)",
                "is_featured": True
            },
            {
                "name": "مشاوره انتخاب تجهیزات آزمایشگاه",
                "description": "مشاوره تخصصی برای انتخاب بهترین تجهیزات اندازه‌گیری متناسب با نیاز و بودجه شما.",
                "price": 2000000,
                "category": 3,  # مشاوره
                "tags": ["مشاوره", "انتخاب تجهیزات", "آزمایشگاه"],
                "duration": "1-2 جلسه",
                "is_featured": False
            }
        ]
        
        conn = self.db.get_conn()
        try:
            with conn.cursor() as cur:
                for service in services_data:
                    category_id = category_ids[service["category"]]
                    
                    cur.execute("""
                        INSERT INTO services (
                            name, description, price, category_id, tags,
                            duration, is_featured, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        service["name"], service["description"], service["price"],
                        category_id, service["tags"], service["duration"],
                        service["is_featured"], datetime.now()
                    ))
                    
                    service_id = cur.fetchone()[0]
                    logger.info(f"✅ خدمت ایجاد شد: {service['name']}")
                
                conn.commit()
                
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ خطا در ایجاد خدمات: {e}")
            raise
        finally:
            conn.close()

    def create_educational_content(self, category_ids):
        """ایجاد محتوای آموزشی نمونه"""
        logger.info("ایجاد محتوای آموزشی نمونه...")
        
        educational_data = [
            {
                "title": "راهنمای استفاده از اسیلوسکوپ دیجیتال",
                "content": "در این مطلب با نحوه صحیح استفاده از اسیلوسکوپ دیجیتال آشنا می‌شوید...",
                "category": 0,  # راهنمای کاربری
                "tags": ["اسیلوسکوپ", "راهنما", "دیجیتال"],
                "is_featured": True
            },
            {
                "title": "اصول کالیبراسیون تجهیزات اندازه‌گیری",
                "content": "کالیبراسیون فرآیند مقایسه دستگاه اندازه‌گیری با استاندارد مرجع است...",
                "category": 2,  # کالیبراسیون
                "tags": ["کالیبراسیون", "استاندارد", "اصول"],
                "is_featured": True
            },
            {
                "title": "تفسیر نتایج اسپکتروم آنالایزر",
                "content": "نحوه خواندن و تفسیر صحیح نمودارهای اسپکتروم آنالایزر...",
                "category": 1,  # اصول اندازه‌گیری
                "tags": ["اسپکتروم آنالایزر", "تفسیر", "نمودار"],
                "is_featured": False
            }
        ]
        
        conn = self.db.get_conn()
        try:
            with conn.cursor() as cur:
                for content in educational_data:
                    category_id = category_ids[content["category"]]
                    
                    cur.execute("""
                        INSERT INTO educational_content (
                            title, content, category_id, tags, is_featured, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        content["title"], content["content"], category_id,
                        content["tags"], content["is_featured"], datetime.now()
                    ))
                    
                    content_id = cur.fetchone()[0]
                    logger.info(f"✅ محتوای آموزشی ایجاد شد: {content['title']}")
                
                conn.commit()
                
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ خطا در ایجاد محتوای آموزشی: {e}")
            raise
        finally:
            conn.close()

    def create_sample_inquiries(self):
        """ایجاد استعلام‌های نمونه"""
        logger.info("ایجاد استعلام‌های نمونه...")
        
        inquiries_data = [
            {
                "name": "مهندس احمدی",
                "email": "ahmadi@company.com",
                "phone": "09121234567",
                "message": "استعلام قیمت اسیلوسکوپ 100MHz برای آزمایشگاه دانشگاه",
                "type": "price_inquiry"
            },
            {
                "name": "شرکت فناوری پارس",
                "email": "info@parstech.com", 
                "phone": "02144556677",
                "message": "درخواست کالیبراسیون 3 دستگاه اسپکتروم آنالایزر",
                "type": "service_request"
            },
            {
                "name": "دکتر محمدی",
                "email": "mohammadi@uni.ac.ir",
                "phone": "09359876543",
                "message": "آیا دوره آموزشی RF برای دانشجویان ارشد برگزار می‌کنید؟",
                "type": "training_inquiry"
            }
        ]
        
        conn = self.db.get_conn()
        try:
            with conn.cursor() as cur:
                for inquiry in inquiries_data:
                    cur.execute("""
                        INSERT INTO inquiries (
                            name, email, phone, message, inquiry_type, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        inquiry["name"], inquiry["email"], inquiry["phone"],
                        inquiry["message"], inquiry["type"], datetime.now()
                    ))
                    
                    logger.info(f"✅ استعلام ایجاد شد: {inquiry['name']}")
                
                conn.commit()
                
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ خطا در ایجاد استعلام‌ها: {e}")
            raise
        finally:
            conn.close()

    def create_sample_inquiries(self):
        """ایجاد استعلام‌های نمونه"""
        logger.info("ایجاد استعلام‌های نمونه...")
        
        inquiries_data = [
            {
                "user_id": 7625738591,  # تلگرام ID نمونه
                "name": "مهندس احمد رضایی",
                "phone": "09121234567",
                "description": "استعلام قیمت اسیلوسکوپ 100MHz برای آزمایشگاه دانشگاه صنعتی شریف. تعداد مورد نیاز 3 دستگاه."
            },
            {
                "user_id": 987654321,
                "name": "شرکت فناوری پارس",
                "phone": "02144556677",
                "description": "درخواست کالیبراسیون 5 دستگاه اسپکتروم آنالایزر Agilent. آیا امکان کالیبراسیون در محل وجود دارد؟"
            },
            {
                "user_id": 123456789,
                "name": "دکتر محمد محمدی",
                "phone": "09359876543",
                "description": "آیا دوره آموزشی RF برای دانشجویان ارشد برگزار می‌کنید؟ تعداد شرکت‌کنندگان حدود 15 نفر."
            },
            {
                "user_id": 555666777,
                "name": "مهندس فاطمه نوری",
                "phone": "09128887766",
                "description": "نیاز به مشاوره برای تجهیز آزمایشگاه تست EMC دارم. بودجه تقریبی 2 میلیارد تومان."
            },
            {
                "user_id": 111222333,
                "name": "شرکت الکترونیک آریا",
                "phone": "02133445566",
                "description": "استعلام قیمت رادیوتستر Aeroflex 3920B همراه با آپشن‌های Tetra و DMR."
            }
        ]
        
        conn = self.db.get_conn()
        try:
            with conn.cursor() as cur:
                for inquiry in inquiries_data:
                    cur.execute("""
                        INSERT INTO inquiries (
                            user_id, name, phone, description, status, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        inquiry["user_id"], inquiry["name"], inquiry["phone"],
                        inquiry["description"], "pending", datetime.now()
                    ))
                    
                    logger.info(f"✅ استعلام ایجاد شد: {inquiry['name']}")
                
                conn.commit()
                
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ خطا در ایجاد استعلام‌ها: {e}")
            raise
        finally:
            conn.close()

    def run(self):
        """اجرای کامل فرآیند تولید دیتا"""
        try:
            # درخواست تایید از کاربر
            if not self.confirm_data_reset():
                sys.exit(0)
            
            print("\n🚀 شروع فرآیند تولید دیتای نمونه...")
            
            # پاک کردن دیتای موجود
            self.clear_existing_data()
            
            # ساخت فایل‌های رسانه‌ای پیش‌فرض
            self.create_default_media_files()
            
            # ایجاد دسته‌بندی‌ها
            product_categories = self.create_product_categories()
            service_categories = self.create_service_categories()
            educational_categories = self.create_educational_categories()
            
            # ایجاد محتوا
            self.create_products(product_categories)
            self.create_services(service_categories)
            self.create_educational_content(educational_categories)
            self.create_sample_inquiries()
            
            print("\n" + "="*60)
            print("🎉 تولید دیتای نمونه با موفقیت کامل شد!")
            print("="*60)
            print("✅ دسته‌بندی‌های محصولات، خدمات و آموزشی ایجاد شد")
            print("✅ 12 محصول تجهیزات اندازه‌گیری با تصاویر اضافه شد")
            print("✅ 16 خدمات شرکت RFTEST با رسانه‌ها تعریف شد")
            print("✅ 15 مطلب آموزشی کاربردی با تصاویر ایجاد شد")
            print("✅ استعلام‌های نمونه با telegram ID اضافه شد")
            print("✅ فایل‌های رسانه‌ای پیش‌فرض ساخته شد")
            print()
            print("🌐 وب پنل: http://YOUR_SERVER_IP")
            print("🤖 بات تلگرام: @RFCatbot")
            print("="*60)
            
        except Exception as e:
            logger.error(f"❌ خطا در تولید دیتا: {e}")
            sys.exit(1)

if __name__ == "__main__":
    seeder = RFTestDataSeeder()
    seeder.run()