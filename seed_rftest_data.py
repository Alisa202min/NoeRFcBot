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
                cur.execute("DELETE FROM educational_media")
                
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
        category_ids = []
        
        try:
            with conn.cursor() as cur:
                for category_name in main_categories:
                    cur.execute("""
                        INSERT INTO product_categories (name, parent_id, created_at)
                        VALUES (%s, %s, %s) RETURNING id
                    """, (category_name, None, datetime.now()))
                    
                    category_id = cur.fetchone()[0]
                    category_ids.append(category_id)
                    logger.info(f"✅ دسته محصولات ایجاد شد: {category_name}")
                
                conn.commit()
                
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ خطا در ایجاد دسته‌بندی محصولات: {e}")
            raise
        finally:
            conn.close()
            
        return category_ids

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

    def create_products(self, category_ids):
        """ایجاد محصولات نمونه"""
        logger.info("ایجاد محصولات نمونه...")
        
        products_data = [
            # اسیلوسکوپ‌ها
            {
                "name": "اسیلوسکوپ دیجیتال Keysight DSOX2002A",
                "description": "اسیلوسکوپ دیجیتال 2 کاناله با پهنای باند 70MHz و نرخ نمونه‌برداری 2GSa/s. مناسب برای کاربردهای عمومی و آموزشی.",
                "price": 45000000,
                "category": 0,  # اسیلوسکوپ
                "brand": "Keysight",
                "model": "DSOX2002A",
                "tags": ["اسیلوسکوپ", "دیجیتال", "70MHz", "2کانال"],
                "specifications": "پهنای باند: 70MHz\nتعداد کانال: 2\nنرخ نمونه‌برداری: 2GSa/s\nحافظه: 1Mpts\nنمایشگر: 8.5 اینچ رنگی",
                "in_stock": True,
                "is_featured": True
            },
            {
                "name": "اسیلوسکوپ آنالوگ Tektronix 2235",
                "description": "اسیلوسکوپ آنالوگ کلاسیک 2 کاناله با پهنای باند 100MHz. بسیار مقاوم و قابل اعتماد برای کاربردهای صنعتی.",
                "price": 18000000,
                "category": 0,
                "brand": "Tektronix", 
                "model": "2235",
                "tags": ["اسیلوسکوپ", "آنالوگ", "100MHz", "کلاسیک"],
                "specifications": "پهنای باند: 100MHz\nتعداد کانال: 2\nحساسیت: 5mV/div\nپایدار و مقاوم",
                "in_stock": True,
                "is_featured": False
            },
            # اسپکتروم آنالایزرها
            {
                "name": "اسپکتروم آنالایزر Rohde & Schwarz FSW",
                "description": "اسپکتروم آنالایزر پیشرفته با دامنه فرکانسی تا 50GHz. مناسب برای تحلیل سیگنال‌های پیچیده و کاربردهای تحقیقاتی.",
                "price": 850000000,
                "category": 1,  # اسپکتروم آنالایزر
                "brand": "Rohde & Schwarz",
                "model": "FSW50",
                "tags": ["اسپکتروم", "50GHz", "تحلیل سیگنال", "حرفه‌ای"],
                "specifications": "دامنه فرکانس: 2Hz تا 50GHz\nنویز فاز: بهتر از -110dBc/Hz\nدقت دامنه: ±0.3dB\nنمایشگر: 12 اینچ رنگی",
                "in_stock": False,
                "is_featured": True
            },
            {
                "name": "اسپکتروم آنالایزر Agilent E4402B",
                "description": "اسپکتروم آنالایزر ESA-E با دامنه 9kHz تا 3GHz. عملکرد عالی برای کاربردهای EMC و تست RF.",
                "price": 125000000,
                "category": 1,
                "brand": "Agilent",
                "model": "E4402B",
                "tags": ["اسپکتروم", "3GHz", "EMC", "RF"],
                "specifications": "دامنه فرکانس: 9kHz تا 3GHz\nکف نویز: -135dBm\nدقت فرکانس: ±1ppm\nRBW: 1Hz تا 3MHz",
                "in_stock": True,
                "is_featured": False
            },
            # سیگنال ژنراتورها
            {
                "name": "سیگنال ژنراتور Keysight E8257D",
                "description": "سیگنال ژنراتور PSG با دامنه تا 67GHz. نویز فاز بسیار پایین و دقت بالا برای کاربردهای حساس.",
                "price": 780000000,
                "category": 2,  # سیگنال ژنراتور
                "brand": "Keysight",
                "model": "E8257D",
                "tags": ["سیگنال ژنراتور", "67GHz", "نویز فاز پایین"],
                "specifications": "دامنه فرکانس: 100kHz تا 67GHz\nتوان خروجی: +20dBm\nنویز فاز: -110dBc/Hz @ 10kHz offset\nدقت فرکانس: ±5×10⁻⁸",
                "in_stock": False,
                "is_featured": True
            },
            # رادیوتسترها
            {
                "name": "رادیوتستر Aeroflex 3920B",
                "description": "رادیوتستر دیجیتال پیشرفته با پشتیبانی از استانداردهای مختلف رادیویی شامل DMR، P25 و Tetra.",
                "price": 320000000,
                "category": 5,  # رادیوتستر
                "brand": "Aeroflex",
                "model": "3920B",
                "tags": ["رادیوتستر", "DMR", "P25", "Tetra"],
                "specifications": "دامنه فرکانس: 80MHz تا 2.7GHz\nاستانداردها: DMR, P25, Tetra\nتوان تست: -130 تا +30dBm\nمدولاسیون: AM, FM, PM",
                "in_stock": True,
                "is_featured": True
            },
            {
                "name": "رادیوتستر Marconi 2955B",
                "description": "رادیوتستر آنالوگ کلاسیک برای تست رادیوهای آنالوگ. بسیار مقاوم و قابل اعتماد.",
                "price": 85000000,
                "category": 5,
                "brand": "Marconi",
                "model": "2955B",
                "tags": ["رادیوتستر", "آنالوگ", "کلاسیک", "مقاوم"],
                "specifications": "دامنه فرکانس: 80MHz تا 1GHz\nمدولاسیون: AM, FM\nتوان تست: -120 تا +30dBm\nسیناد متر داخلی",
                "in_stock": True,
                "is_featured": False
            }
            # ادامه محصولات...
        ]
        
        conn = self.db.get_conn()
        try:
            with conn.cursor() as cur:
                for i, product in enumerate(products_data):
                    # انتخاب دسته‌بندی
                    category_id = category_ids[product["category"]]
                    
                    # درج محصول
                    cur.execute("""
                        INSERT INTO products (
                            name, description, price, category_id, brand, model,
                            tags, specifications, in_stock, is_featured, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        product["name"], product["description"], product["price"],
                        category_id, product["brand"], product["model"],
                        product["tags"], product["specifications"],
                        product["in_stock"], product["is_featured"], datetime.now()
                    ))
                    
                    product_id = cur.fetchone()[0]
                    
                    # اضافه کردن تصویر اصلی (برای سادگی از همان تصویر استفاده می‌کنیم)
                    image_filename = f"product_{product_id}_main.jpg"
                    cur.execute("""
                        INSERT INTO product_media (product_id, file_id, file_type, file_name, is_main)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (product_id, f"uploads/products/{product_id}/{image_filename}", 
                          "photo", image_filename, True))
                    
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

    def run(self):
        """اجرای کامل فرآیند تولید دیتا"""
        try:
            # درخواست تایید از کاربر
            if not self.confirm_data_reset():
                sys.exit(0)
            
            print("\n🚀 شروع فرآیند تولید دیتای نمونه...")
            
            # پاک کردن دیتای موجود
            self.clear_existing_data()
            
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
            print("✅ محصولات نمونه تجهیزات اندازه‌گیری اضافه شد")
            print("✅ خدمات شرکت RFTEST تعریف شد")
            print("✅ محتوای آموزشی ایجاد شد")
            print("✅ استعلام‌های نمونه اضافه شد")
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