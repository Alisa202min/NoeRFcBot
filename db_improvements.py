import os
import logging
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from database import Database

def safe_fetchone(cursor):
    """Safely fetch one row and return None if no rows are available"""
    result = cursor.fetchone()
    return result

def improve_database_methods():
    """Improve database methods to handle NULL values properly"""
    db = Database()
    
    # 1. Improve fetchone methods to safely handle NULL values
    methods_to_improve = [
        # Get methods for categories
        {"line_num": 155, "old": "            return cursor.fetchone()", 
         "new": "            return cursor.fetchone() or None"},
        
        # Get methods for products
        {"line_num": 236, "old": "            return cursor.fetchone()", 
         "new": "            return cursor.fetchone() or None"},
        
        # Get methods for media
        {"line_num": 268, "old": "            return cursor.fetchone()", 
         "new": "            return cursor.fetchone() or None"},
        
        # Get methods for product by media
        {"line_num": 289, "old": "            return cursor.fetchone()", 
         "new": "            return cursor.fetchone() or None"},
        
        # Get methods for service media
        {"line_num": 325, "old": "            return cursor.fetchone()", 
         "new": "            return cursor.fetchone() or None"},
        
        # Get service by media ID
        {"line_num": 343, "old": "            return cursor.fetchone()", 
         "new": "            return cursor.fetchone() or None"},
        
        # Get inquiry methods
        {"line_num": 567, "old": "            return cursor.fetchone()", 
         "new": "            return cursor.fetchone() or None"},
        
        # Get educational content
        {"line_num": 576, "old": "            return cursor.fetchone()", 
         "new": "            return cursor.fetchone() or None"},
    ]
    
    # Read the database.py file
    with open('database.py', 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # Apply the improvements
    for method in methods_to_improve:
        line_num = method["line_num"] - 1  # Adjust for 0-indexed list
        if line_num < len(lines) and method["old"].strip() in lines[line_num].strip():
            lines[line_num] = lines[line_num].replace(method["old"], method["new"])
            print(f"Improved line {method['line_num']}: {method['old']} -> {method['new']}")
    
    # Write the improved code back to database.py
    with open('database.py', 'w', encoding='utf-8') as file:
        file.writelines(lines)
    
    print("Database methods improved successfully!")

def add_sample_data():
    """Add sample data to the database"""
    db = Database()
    
    # Create categories (4 levels deep)
    print("Adding categories...")
    
    # Level 1 Categories (Main categories)
    main_categories = [
        # Product Categories
        {"name": "آنتن و فرستنده‌ها", "parent_id": None, "cat_type": "product"},
        {"name": "قطعات الکترونیکی", "parent_id": None, "cat_type": "product"},
        {"name": "ابزار اندازه‌گیری", "parent_id": None, "cat_type": "product"},
        {"name": "تجهیزات شبکه", "parent_id": None, "cat_type": "product"},
        {"name": "مدارات و بردها", "parent_id": None, "cat_type": "product"},
        
        # Service Categories
        {"name": "تعمیرات", "parent_id": None, "cat_type": "service"},
        {"name": "نصب و راه‌اندازی", "parent_id": None, "cat_type": "service"},
        {"name": "طراحی سیستم", "parent_id": None, "cat_type": "service"},
        {"name": "مشاوره تخصصی", "parent_id": None, "cat_type": "service"},
        {"name": "آموزش", "parent_id": None, "cat_type": "service"},
    ]
    
    level1_ids = {}
    for cat in main_categories:
        cat_id = db.add_category(cat["name"], cat["parent_id"], cat["cat_type"])
        level1_ids[cat["name"]] = cat_id
        print(f"Added Level 1 category: {cat['name']} (ID: {cat_id})")
    
    # Level 2 Categories
    level2_categories = [
        # Products - Antennas
        {"name": "آنتن‌های دایرکشنال", "parent_id": level1_ids["آنتن و فرستنده‌ها"], "cat_type": "product"},
        {"name": "آنتن‌های امنی‌دایرکشنال", "parent_id": level1_ids["آنتن و فرستنده‌ها"], "cat_type": "product"},
        {"name": "فرستنده‌های رادیویی", "parent_id": level1_ids["آنتن و فرستنده‌ها"], "cat_type": "product"},
        
        # Products - Electronic Components
        {"name": "خازن‌ها", "parent_id": level1_ids["قطعات الکترونیکی"], "cat_type": "product"},
        {"name": "مقاومت‌ها", "parent_id": level1_ids["قطعات الکترونیکی"], "cat_type": "product"},
        {"name": "ترانزیستورها", "parent_id": level1_ids["قطعات الکترونیکی"], "cat_type": "product"},
        
        # Products - Measurement Tools
        {"name": "اسیلوسکوپ‌ها", "parent_id": level1_ids["ابزار اندازه‌گیری"], "cat_type": "product"},
        {"name": "فرکانس‌متر‌ها", "parent_id": level1_ids["ابزار اندازه‌گیری"], "cat_type": "product"},
        {"name": "آنالایزرهای اسپکتروم", "parent_id": level1_ids["ابزار اندازه‌گیری"], "cat_type": "product"},
        
        # Services - Repairs
        {"name": "تعمیر آنتن", "parent_id": level1_ids["تعمیرات"], "cat_type": "service"},
        {"name": "تعمیر فرستنده", "parent_id": level1_ids["تعمیرات"], "cat_type": "service"},
        {"name": "تعمیر گیرنده", "parent_id": level1_ids["تعمیرات"], "cat_type": "service"},
        
        # Services - Installation
        {"name": "نصب آنتن", "parent_id": level1_ids["نصب و راه‌اندازی"], "cat_type": "service"},
        {"name": "نصب فرستنده", "parent_id": level1_ids["نصب و راه‌اندازی"], "cat_type": "service"},
        {"name": "راه‌اندازی شبکه", "parent_id": level1_ids["نصب و راه‌اندازی"], "cat_type": "service"},
    ]
    
    level2_ids = {}
    for cat in level2_categories:
        cat_id = db.add_category(cat["name"], cat["parent_id"], cat["cat_type"])
        level2_ids[cat["name"]] = cat_id
        print(f"Added Level 2 category: {cat['name']} (ID: {cat_id})")
    
    # Level 3 Categories
    level3_categories = [
        # Products - Directional Antennas
        {"name": "آنتن‌های یاگی", "parent_id": level2_ids["آنتن‌های دایرکشنال"], "cat_type": "product"},
        {"name": "آنتن‌های پارابولیک", "parent_id": level2_ids["آنتن‌های دایرکشنال"], "cat_type": "product"},
        {"name": "آنتن‌های فازی", "parent_id": level2_ids["آنتن‌های دایرکشنال"], "cat_type": "product"},
        
        # Products - Omnidirectional Antennas
        {"name": "آنتن‌های دایپل", "parent_id": level2_ids["آنتن‌های امنی‌دایرکشنال"], "cat_type": "product"},
        {"name": "آنتن‌های باند پهن", "parent_id": level2_ids["آنتن‌های امنی‌دایرکشنال"], "cat_type": "product"},
        
        # Products - Radio Transmitters
        {"name": "فرستنده‌های کم‌توان", "parent_id": level2_ids["فرستنده‌های رادیویی"], "cat_type": "product"},
        {"name": "فرستنده‌های پرتوان", "parent_id": level2_ids["فرستنده‌های رادیویی"], "cat_type": "product"},
        
        # Services - Antenna Repair
        {"name": "تعمیر آنتن‌های یاگی", "parent_id": level2_ids["تعمیر آنتن"], "cat_type": "service"},
        {"name": "تعمیر آنتن‌های پارابولیک", "parent_id": level2_ids["تعمیر آنتن"], "cat_type": "service"},
        
        # Services - Transmitter Repair
        {"name": "تعمیر فرستنده‌های FM", "parent_id": level2_ids["تعمیر فرستنده"], "cat_type": "service"},
        {"name": "تعمیر فرستنده‌های AM", "parent_id": level2_ids["تعمیر فرستنده"], "cat_type": "service"},
    ]
    
    level3_ids = {}
    for cat in level3_categories:
        cat_id = db.add_category(cat["name"], cat["parent_id"], cat["cat_type"])
        level3_ids[cat["name"]] = cat_id
        print(f"Added Level 3 category: {cat['name']} (ID: {cat_id})")
    
    # Level 4 Categories (deepest level)
    level4_categories = [
        # Products - Yagi Antennas
        {"name": "آنتن یاگی فرکانس پایین", "parent_id": level3_ids["آنتن‌های یاگی"], "cat_type": "product"},
        {"name": "آنتن یاگی فرکانس متوسط", "parent_id": level3_ids["آنتن‌های یاگی"], "cat_type": "product"},
        {"name": "آنتن یاگی فرکانس بالا", "parent_id": level3_ids["آنتن‌های یاگی"], "cat_type": "product"},
        
        # Products - Parabolic Antennas
        {"name": "آنتن پارابولیک ۶۰ سانتی", "parent_id": level3_ids["آنتن‌های پارابولیک"], "cat_type": "product"},
        {"name": "آنتن پارابولیک ۱۲۰ سانتی", "parent_id": level3_ids["آنتن‌های پارابولیک"], "cat_type": "product"},
        {"name": "آنتن پارابولیک ۱۸۰ سانتی", "parent_id": level3_ids["آنتن‌های پارابولیک"], "cat_type": "product"},
        
        # Services - FM Transmitter Repair
        {"name": "تعمیر فرستنده FM تا ۱۰۰ وات", "parent_id": level3_ids["تعمیر فرستنده‌های FM"], "cat_type": "service"},
        {"name": "تعمیر فرستنده FM بالای ۱۰۰ وات", "parent_id": level3_ids["تعمیر فرستنده‌های FM"], "cat_type": "service"},
    ]
    
    level4_ids = {}
    for cat in level4_categories:
        cat_id = db.add_category(cat["name"], cat["parent_id"], cat["cat_type"])
        level4_ids[cat["name"]] = cat_id
        print(f"Added Level 4 category: {cat['name']} (ID: {cat_id})")

    # Add Products and Media
    print("\nAdding products...")
    products = [
        # Level 1 - آنتن و فرستنده‌ها
        {"name": "آنتن مرکزی UHF/VHF", "price": 1200000, "description": "آنتن مرکزی با قابلیت دریافت سیگنال‌های UHF و VHF، مناسب برای نصب در مناطق شهری", "category_id": level1_ids["آنتن و فرستنده‌ها"], "photo_url": "static/uploads/antenna1.jpg"},
        {"name": "فرستنده FM 150 وات", "price": 8500000, "description": "فرستنده FM با توان 150 وات، مناسب برای پوشش رادیویی تا شعاع 15 کیلومتر", "category_id": level1_ids["آنتن و فرستنده‌ها"], "photo_url": "static/uploads/transmitter1.jpg"},
        
        # Level 2 - آنتن‌های دایرکشنال
        {"name": "آنتن یاگی 10 المانی", "price": 850000, "description": "آنتن یاگی با 10 المان دریافت، مناسب برای دریافت سیگنال‌های دیجیتال از فاصله دور", "category_id": level2_ids["آنتن‌های دایرکشنال"], "photo_url": "static/uploads/yagi1.jpg"},
        {"name": "آنتن دایرکشنال پهن‌باند", "price": 1350000, "description": "آنتن دایرکشنال با پهنای باند وسیع، مناسب برای دریافت طیف گسترده‌ای از فرکانس‌ها", "category_id": level2_ids["آنتن‌های دایرکشنال"], "photo_url": "static/uploads/directional1.jpg"},
        
        # Level 3 - آنتن‌های یاگی
        {"name": "آنتن یاگی VHF", "price": 750000, "description": "آنتن یاگی مخصوص باند VHF با بهره بالا و ساختار مقاوم در برابر شرایط جوی", "category_id": level3_ids["آنتن‌های یاگی"], "photo_url": "static/uploads/vhf_yagi.jpg"},
        {"name": "آنتن یاگی UHF", "price": 850000, "description": "آنتن یاگی مخصوص باند UHF با قابلیت دریافت کانال‌های دیجیتال با کیفیت HD", "category_id": level3_ids["آنتن‌های یاگی"], "photo_url": "static/uploads/uhf_yagi.jpg"},
        
        # Level 4 - آنتن یاگی فرکانس بالا
        {"name": "آنتن یاگی G5RV", "price": 950000, "description": "آنتن یاگی مدل G5RV با فرکانس بالا، مناسب برای ارتباطات رادیویی آماتوری", "category_id": level4_ids["آنتن یاگی فرکانس بالا"], "photo_url": "static/uploads/high_freq_yagi.jpg"},
        {"name": "آنتن یاگی دوبانده 15/20 متر", "price": 1250000, "description": "آنتن یاگی دوبانده با عملکرد در باندهای 15 و 20 متری، مناسب برای اپراتورهای رادیویی", "category_id": level4_ids["آنتن یاگی فرکانس بالا"], "photo_url": "static/uploads/dual_band_yagi.jpg"},
        
        # قطعات الکترونیکی
        {"name": "خازن تانتالیوم 100 میکروفاراد", "price": 15000, "description": "خازن تانتالیوم با ظرفیت 100 میکروفاراد، مناسب برای مدارات الکترونیکی دقیق", "category_id": level2_ids["خازن‌ها"], "photo_url": "static/uploads/tantalum_cap.jpg"},
        {"name": "مقاومت کربنی 10 کیلواهم", "price": 5000, "description": "مقاومت کربنی 10 کیلواهم با دقت 5 درصد، مناسب برای مدارات الکترونیکی", "category_id": level2_ids["مقاومت‌ها"], "photo_url": "static/uploads/resistor.jpg"},
        
        # ابزار اندازه‌گیری
        {"name": "اسیلوسکوپ دیجیتال 100MHz", "price": 12500000, "description": "اسیلوسکوپ دیجیتال با پهنای باند 100 مگاهرتز، صفحه نمایش 7 اینچی رنگی", "category_id": level2_ids["اسیلوسکوپ‌ها"], "photo_url": "static/uploads/oscilloscope.jpg"},
        {"name": "فرکانس‌متر دیجیتال 3GHz", "price": 5800000, "description": "فرکانس‌متر دیجیتال با محدوده اندازه‌گیری تا 3 گیگاهرتز، دقت بالا و نمایشگر LCD", "category_id": level2_ids["فرکانس‌متر‌ها"], "photo_url": "static/uploads/freq_meter.jpg"},
        
        # تجهیزات شبکه
        {"name": "آنتن شبکه وای‌فای بلندبرد", "price": 780000, "description": "آنتن بلندبرد برای افزایش برد شبکه‌های وای‌فای، با بهره 15dBi", "category_id": level1_ids["تجهیزات شبکه"], "photo_url": "static/uploads/wifi_antenna.jpg"},
        {"name": "روتر بی‌سیم N300", "price": 1450000, "description": "روتر بی‌سیم با استاندارد N و سرعت تا 300 مگابیت بر ثانیه، مناسب برای منازل و دفاتر کوچک", "category_id": level1_ids["تجهیزات شبکه"], "photo_url": "static/uploads/router.jpg"},
        
        # مدارات و بردها
        {"name": "برد آردوینو UNO", "price": 550000, "description": "برد آردوینو UNO برای پروژه‌های الکترونیکی و رباتیک، با میکروکنترلر ATmega328P", "category_id": level1_ids["مدارات و بردها"], "photo_url": "static/uploads/arduino.jpg"},
        {"name": "برد راسپبری پای 4", "price": 2800000, "description": "کامپیوتر تک‌بردی راسپبری پای 4 با رم 4 گیگابایت، مناسب برای پروژه‌های IoT و چندرسانه‌ای", "category_id": level1_ids["مدارات و بردها"], "photo_url": "static/uploads/raspberry.jpg"},
    ]
    
    product_ids = {}
    for product in products:
        product_id = db.add_product(product["name"], product["price"], product["description"], product["category_id"], product["photo_url"])
        product_ids[product["name"]] = product_id
        print(f"Added product: {product['name']} (ID: {product_id})")
    
    # Add Services
    print("\nAdding services...")
    services = [
        # تعمیرات
        {"name": "عیب‌یابی و تعمیر آنتن", "price": 850000, "description": "خدمات عیب‌یابی و تعمیر انواع آنتن‌های رادیویی و تلویزیونی", "category_id": level1_ids["تعمیرات"], "photo_url": "static/uploads/antenna_repair.jpg"},
        {"name": "تعمیر فرستنده رادیویی", "price": 1500000, "description": "خدمات تعمیر و نگهداری انواع فرستنده‌های رادیویی با قطعات اصلی", "category_id": level1_ids["تعمیرات"], "photo_url": "static/uploads/transmitter_repair.jpg"},
        
        # نصب و راه‌اندازی
        {"name": "نصب آنتن مرکزی", "price": 1200000, "description": "خدمات نصب و راه‌اندازی آنتن مرکزی برای ساختمان‌ها، شامل نصب آنتن، تقویت‌کننده و سیم‌کشی", "category_id": level2_ids["نصب آنتن"], "photo_url": "static/uploads/antenna_install.jpg"},
        {"name": "نصب و راه‌اندازی فرستنده", "price": 2500000, "description": "خدمات نصب و راه‌اندازی انواع فرستنده‌های رادیویی با تنظیمات دقیق", "category_id": level2_ids["نصب فرستنده"], "photo_url": "static/uploads/transmitter_install.jpg"},
        
        # طراحی سیستم
        {"name": "طراحی سیستم پخش رادیویی", "price": 7500000, "description": "خدمات طراحی سیستم‌های پخش رادیویی شامل فرستنده، آنتن و تجهیزات جانبی", "category_id": level1_ids["طراحی سیستم"], "photo_url": "static/uploads/system_design.jpg"},
        {"name": "طراحی شبکه بی‌سیم", "price": 5500000, "description": "خدمات طراحی شبکه‌های بی‌سیم با پوشش گسترده و پایداری بالا", "category_id": level1_ids["طراحی سیستم"], "photo_url": "static/uploads/wireless_design.jpg"},
        
        # مشاوره تخصصی
        {"name": "مشاوره انتخاب تجهیزات", "price": 1500000, "description": "خدمات مشاوره تخصصی برای انتخاب تجهیزات مناسب برای پروژه‌های رادیویی و مخابراتی", "category_id": level1_ids["مشاوره تخصصی"], "photo_url": "static/uploads/consultation.jpg"},
        {"name": "مشاوره اخذ مجوزهای فرکانسی", "price": 3500000, "description": "خدمات مشاوره و راهنمایی برای اخذ مجوزهای فرکانسی از سازمان تنظیم مقررات", "category_id": level1_ids["مشاوره تخصصی"], "photo_url": "static/uploads/license_consult.jpg"},
        
        # آموزش
        {"name": "دوره آموزشی مبانی رادیو", "price": 2800000, "description": "دوره آموزشی جامع مبانی رادیو، شامل اصول انتشار امواج، مدولاسیون و دمدولاسیون", "category_id": level1_ids["آموزش"], "photo_url": "static/uploads/radio_course.jpg"},
        {"name": "کارگاه عملی تعمیر آنتن", "price": 3200000, "description": "کارگاه عملی آموزش تعمیر انواع آنتن، شامل عیب‌یابی و رفع خرابی‌های رایج", "category_id": level1_ids["آموزش"], "photo_url": "static/uploads/antenna_workshop.jpg"},
        
        # تعمیر آنتن‌های یاگی
        {"name": "تعمیر و تنظیم آنتن یاگی", "price": 950000, "description": "خدمات تعمیر، تنظیم و بهینه‌سازی آنتن‌های یاگی با تجهیزات پیشرفته", "category_id": level3_ids["تعمیر آنتن‌های یاگی"], "photo_url": "static/uploads/yagi_repair.jpg"},
        {"name": "بازسازی آنتن یاگی", "price": 1250000, "description": "خدمات بازسازی کامل آنتن‌های یاگی آسیب‌دیده شامل تعویض المان‌ها و بوم اصلی", "category_id": level3_ids["تعمیر آنتن‌های یاگی"], "photo_url": "static/uploads/yagi_restore.jpg"},
        
        # تعمیر فرستنده‌های FM
        {"name": "تعمیر فرستنده FM کم‌توان", "price": 1800000, "description": "خدمات تعمیر فرستنده‌های FM تا توان 100 وات با قطعات اصلی", "category_id": level4_ids["تعمیر فرستنده FM تا ۱۰۰ وات"], "photo_url": "static/uploads/fm_repair_low.jpg"},
        {"name": "تعمیر فرستنده FM پرتوان", "price": 2500000, "description": "خدمات تعمیر فرستنده‌های FM با توان بالای 100 وات با استفاده از قطعات اصلی", "category_id": level4_ids["تعمیر فرستنده FM بالای ۱۰۰ وات"], "photo_url": "static/uploads/fm_repair_high.jpg"},
    ]
    
    service_ids = {}
    for service in services:
        service_id = db.add_service(service["name"], service["price"], service["description"], service["category_id"], service["photo_url"])
        service_ids[service["name"]] = service_id
        print(f"Added service: {service['name']} (ID: {service_id})")
    
    # Add product media
    print("\nAdding product media...")
    product_media_items = [
        {"product_id": product_ids["آنتن مرکزی UHF/VHF"], "file_id": "static/uploads/antenna1_detail1.jpg", "file_type": "photo"},
        {"product_id": product_ids["آنتن مرکزی UHF/VHF"], "file_id": "static/uploads/antenna1_detail2.jpg", "file_type": "photo"},
        {"product_id": product_ids["آنتن مرکزی UHF/VHF"], "file_id": "static/uploads/antenna1_video.mp4", "file_type": "video"},
        
        {"product_id": product_ids["فرستنده FM 150 وات"], "file_id": "static/uploads/transmitter1_detail1.jpg", "file_type": "photo"},
        {"product_id": product_ids["فرستنده FM 150 وات"], "file_id": "static/uploads/transmitter1_detail2.jpg", "file_type": "photo"},
        
        {"product_id": product_ids["آنتن یاگی 10 المانی"], "file_id": "static/uploads/yagi1_detail1.jpg", "file_type": "photo"},
        {"product_id": product_ids["آنتن یاگی 10 المانی"], "file_id": "static/uploads/yagi1_detail2.jpg", "file_type": "photo"},
        {"product_id": product_ids["آنتن یاگی 10 المانی"], "file_id": "static/uploads/yagi1_video.mp4", "file_type": "video"},
        
        {"product_id": product_ids["اسیلوسکوپ دیجیتال 100MHz"], "file_id": "static/uploads/oscilloscope_detail1.jpg", "file_type": "photo"},
        {"product_id": product_ids["اسیلوسکوپ دیجیتال 100MHz"], "file_id": "static/uploads/oscilloscope_detail2.jpg", "file_type": "photo"},
        {"product_id": product_ids["اسیلوسکوپ دیجیتال 100MHz"], "file_id": "static/uploads/oscilloscope_video.mp4", "file_type": "video"},
    ]
    
    for media in product_media_items:
        media_id = db.add_product_media(media["product_id"], media["file_id"], media["file_type"])
        print(f"Added product media ID: {media_id} for product ID: {media['product_id']}")
    
    # Add service media
    print("\nAdding service media...")
    service_media_items = [
        {"service_id": service_ids["عیب‌یابی و تعمیر آنتن"], "file_id": "static/uploads/antenna_repair_detail1.jpg", "file_type": "photo"},
        {"service_id": service_ids["عیب‌یابی و تعمیر آنتن"], "file_id": "static/uploads/antenna_repair_detail2.jpg", "file_type": "photo"},
        {"service_id": service_ids["عیب‌یابی و تعمیر آنتن"], "file_id": "static/uploads/antenna_repair_video.mp4", "file_type": "video"},
        
        {"service_id": service_ids["نصب آنتن مرکزی"], "file_id": "static/uploads/antenna_install_detail1.jpg", "file_type": "photo"},
        {"service_id": service_ids["نصب آنتن مرکزی"], "file_id": "static/uploads/antenna_install_detail2.jpg", "file_type": "photo"},
        {"service_id": service_ids["نصب آنتن مرکزی"], "file_id": "static/uploads/antenna_install_video.mp4", "file_type": "video"},
        
        {"service_id": service_ids["طراحی سیستم پخش رادیویی"], "file_id": "static/uploads/system_design_detail1.jpg", "file_type": "photo"},
        {"service_id": service_ids["طراحی سیستم پخش رادیویی"], "file_id": "static/uploads/system_design_detail2.jpg", "file_type": "photo"},
        
        {"service_id": service_ids["دوره آموزشی مبانی رادیو"], "file_id": "static/uploads/radio_course_detail1.jpg", "file_type": "photo"},
        {"service_id": service_ids["دوره آموزشی مبانی رادیو"], "file_id": "static/uploads/radio_course_detail2.jpg", "file_type": "photo"},
        {"service_id": service_ids["دوره آموزشی مبانی رادیو"], "file_id": "static/uploads/radio_course_video.mp4", "file_type": "video"},
    ]
    
    for media in service_media_items:
        media_id = db.add_service_media(media["service_id"], media["file_id"], media["file_type"])
        print(f"Added service media ID: {media_id} for service ID: {media['service_id']}")
    
    # Add inquiries
    print("\nAdding inquiries...")
    inquiries = [
        {"user_id": 123456789, "name": "محمد احمدی", "phone": "09123456789", "description": "استعلام قیمت آنتن یاگی برای نصب در منطقه کوهستانی", "product_id": product_ids["آنتن یاگی 10 المانی"], "product_type": "product"},
        {"user_id": 234567890, "name": "علی محمدی", "phone": "09234567890", "description": "درخواست اطلاعات بیشتر در مورد فرستنده FM 150 وات و نحوه نصب آن", "product_id": product_ids["فرستنده FM 150 وات"], "product_type": "product"},
        {"user_id": 345678901, "name": "زهرا کریمی", "phone": "09345678901", "description": "درخواست مشاوره برای انتخاب آنتن مناسب برای دریافت کانال‌های دیجیتال", "product_id": product_ids["آنتن مرکزی UHF/VHF"], "product_type": "product"},
        {"user_id": 456789012, "name": "رضا رضایی", "phone": "09456789012", "description": "استعلام هزینه نصب آنتن مرکزی برای یک ساختمان 5 طبقه", "product_id": service_ids["نصب آنتن مرکزی"], "product_type": "service"},
        {"user_id": 567890123, "name": "مریم حسینی", "phone": "09567890123", "description": "درخواست اطلاعات بیشتر در مورد دوره آموزشی مبانی رادیو", "product_id": service_ids["دوره آموزشی مبانی رادیو"], "product_type": "service"},
        
        {"user_id": 678901234, "name": "امیر نجفی", "phone": "09678901234", "description": "استعلام قیمت و زمان تحویل 5 عدد آنتن یاگی برای یک پروژه", "product_id": product_ids["آنتن یاگی 10 المانی"], "product_type": "product"},
        {"user_id": 789012345, "name": "سارا میرزایی", "phone": "09789012345", "description": "درخواست بازدید و عیب‌یابی آنتن مرکزی ساختمان", "product_id": service_ids["عیب‌یابی و تعمیر آنتن"], "product_type": "service"},
        {"user_id": 890123456, "name": "حسن قاسمی", "phone": "09890123456", "description": "استعلام قیمت طراحی و پیاده‌سازی یک سیستم رادیویی محلی", "product_id": service_ids["طراحی سیستم پخش رادیویی"], "product_type": "service"},
        {"user_id": 901234567, "name": "فاطمه عباسی", "phone": "09901234567", "description": "درخواست اطلاعات فنی بیشتر در مورد اسیلوسکوپ دیجیتال", "product_id": product_ids["اسیلوسکوپ دیجیتال 100MHz"], "product_type": "product"},
        {"user_id": 123123123, "name": "علیرضا صادقی", "phone": "09123123123", "description": "استعلام قیمت برای خرید عمده مقاومت‌های کربنی", "product_id": product_ids["مقاومت کربنی 10 کیلواهم"], "product_type": "product"},
        
        {"user_id": 234234234, "name": "مهدی جعفری", "phone": "09234234234", "description": "درخواست مشاوره برای راه‌اندازی یک ایستگاه رادیویی کوچک", "product_id": service_ids["مشاوره انتخاب تجهیزات"], "product_type": "service"},
        {"user_id": 345345345, "name": "نرگس حیدری", "phone": "09345345345", "description": "استعلام هزینه تعمیر فرستنده FM دچار مشکل مدولاسیون", "product_id": service_ids["تعمیر فرستنده FM کم‌توان"], "product_type": "service"},
        {"user_id": 456456456, "name": "کامران نوری", "phone": "09456456456", "description": "درخواست اطلاعات بیشتر در مورد برد آردوینو و قابلیت‌های آن", "product_id": product_ids["برد آردوینو UNO"], "product_type": "product"},
        {"user_id": 567567567, "name": "پریسا مرادی", "phone": "09567567567", "description": "استعلام قیمت و مشخصات فرستنده‌های FM با توان بالاتر", "product_id": product_ids["فرستنده FM 150 وات"], "product_type": "product"},
        {"user_id": 678678678, "name": "سعید رضوی", "phone": "09678678678", "description": "درخواست مشاوره برای ارتقای شبکه بی‌سیم یک شرکت", "product_id": service_ids["طراحی شبکه بی‌سیم"], "product_type": "service"},
        
        {"user_id": 789789789, "name": "لیلا کرمی", "phone": "09789789789", "description": "استعلام قیمت و زمان برگزاری کارگاه عملی تعمیر آنتن", "product_id": service_ids["کارگاه عملی تعمیر آنتن"], "product_type": "service"},
        {"user_id": 890890890, "name": "بهزاد فرهادی", "phone": "09890890890", "description": "درخواست بازدید برای نصب آنتن شبکه وای‌فای بلندبرد", "product_id": product_ids["آنتن شبکه وای‌فای بلندبرد"], "product_type": "product"},
        {"user_id": 901901901, "name": "ندا سلطانی", "phone": "09901901901", "description": "استعلام قیمت تعمیر آنتن پارابولیک آسیب‌دیده", "product_id": service_ids["بازسازی آنتن یاگی"], "product_type": "service"},
        {"user_id": 112233445, "name": "مجید امینی", "phone": "09112233445", "description": "درخواست مشاوره برای خرید تجهیزات رادیویی آماتوری", "product_id": service_ids["مشاوره انتخاب تجهیزات"], "product_type": "service"},
        {"user_id": 223344556, "name": "شیرین رحمانی", "phone": "09223344556", "description": "استعلام هزینه و زمان برای تعمیر روتر بی‌سیم آسیب‌دیده", "product_id": product_ids["روتر بی‌سیم N300"], "product_type": "product"},
    ]
    
    for i, inquiry in enumerate(inquiries):
        date = datetime.now()
        with db.conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO inquiries (user_id, name, phone, description, product_id, product_type, date) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id',
                (inquiry["user_id"], inquiry["name"], inquiry["phone"], inquiry["description"], 
                 inquiry["product_id"], inquiry["product_type"], date)
            )
            inquiry_id = cursor.fetchone()[0]
            print(f"Added inquiry: {inquiry_id} from {inquiry['name']}")
    
    # Add educational content
    print("\nAdding educational content...")
    edu_contents = [
        {"title": "مبانی فرکانس و طول موج", "content": "در این مقاله با مفاهیم پایه‌ای فرکانس و طول موج آشنا می‌شوید. فرکانس نشان‌دهنده تعداد تکرار یک موج در یک ثانیه است و با واحد هرتز (Hz) اندازه‌گیری می‌شود. طول موج نیز فاصله بین دو نقطه متوالی با فاز مشابه در موج است.", "category": "آموزش مبانی رادیو", "type": "article"},
        {"title": "انواع آنتن‌ها و کاربردهای آن‌ها", "content": "در این مقاله انواع مختلف آنتن‌ها از جمله آنتن‌های یاگی، پارابولیک، دایپل و... معرفی شده و کاربردهای هر یک در زمینه‌های مختلف مخابراتی توضیح داده می‌شود.", "category": "آموزش مبانی رادیو", "type": "article"},
        {"title": "مدولاسیون AM و FM", "content": "این مقاله به بررسی انواع مدولاسیون دامنه (AM) و فرکانس (FM) می‌پردازد. مدولاسیون فرآیندی است که در آن سیگنال اصلی (پیام) روی یک سیگنال حامل سوار می‌شود تا امکان انتقال آن فراهم گردد.", "category": "آموزش مبانی رادیو", "type": "article"},
        {"title": "اصول عملکرد فرستنده‌های رادیویی", "content": "در این مقاله با اصول عملکرد فرستنده‌های رادیویی آشنا می‌شوید. یک فرستنده رادیویی از بخش‌های مختلفی مانند اسیلاتور، مدولاتور، تقویت‌کننده و آنتن تشکیل شده است.", "category": "فرستنده‌ها", "type": "article"},
        {"title": "نحوه طراحی آنتن یاگی", "content": "این مقاله به آموزش نحوه طراحی آنتن‌های یاگی می‌پردازد. در طراحی آنتن یاگی، عواملی مانند تعداد المان‌ها، فاصله بین آن‌ها و طول هر المان در عملکرد نهایی آنتن تأثیرگذار هستند.", "category": "آنتن‌ها", "type": "tutorial"},
        
        {"title": "چگونگی عیب‌یابی آنتن", "content": "در این آموزش با روش‌های عیب‌یابی آنتن آشنا می‌شوید. مشکلات رایج آنتن‌ها شامل اتصالات ضعیف، آسیب‌های فیزیکی، تنظیم نادرست و تداخل سیگنال می‌باشد.", "category": "تعمیرات", "type": "tutorial"},
        {"title": "راه‌اندازی یک ایستگاه رادیویی کوچک", "content": "این راهنما شما را با مراحل راه‌اندازی یک ایستگاه رادیویی کوچک آشنا می‌کند. از انتخاب تجهیزات مناسب تا تنظیمات نهایی و اخذ مجوزهای لازم.", "category": "فرستنده‌ها", "type": "guide"},
        {"title": "محاسبه برد پوشش فرستنده", "content": "در این مقاله با نحوه محاسبه برد پوشش فرستنده‌های رادیویی آشنا می‌شوید. عواملی مانند توان فرستنده، بهره آنتن، ارتفاع نصب و شرایط جغرافیایی در محاسبه برد پوشش تأثیرگذار هستند.", "category": "فرستنده‌ها", "type": "article"},
        {"title": "تنظیم دقیق فرستنده FM", "content": "این آموزش به نحوه تنظیم دقیق پارامترهای فرستنده FM می‌پردازد. تنظیماتی مانند فرکانس کاری، میزان انحراف فرکانس، توان خروجی و امپدانس خروجی.", "category": "فرستنده‌ها", "type": "tutorial"},
        {"title": "آشنایی با قوانین و مقررات ارتباطات رادیویی", "content": "در این مقاله با قوانین و مقررات مربوط به ارتباطات رادیویی در ایران آشنا می‌شوید. موضوعاتی مانند تخصیص فرکانس، مجوزهای لازم و محدودیت‌های قانونی.", "category": "مقررات و قوانین", "type": "article"},
        
        {"title": "نحوه استفاده از اسیلوسکوپ", "content": "این آموزش به نحوه استفاده صحیح از اسیلوسکوپ می‌پردازد. از تنظیمات اولیه تا روش‌های اندازه‌گیری پارامترهای مختلف سیگنال مانند دامنه، فرکانس و فاز.", "category": "ابزار اندازه‌گیری", "type": "tutorial"},
        {"title": "اصول عملکرد آنالایزر اسپکتروم", "content": "در این مقاله با اصول عملکرد دستگاه آنالایزر اسپکتروم آشنا می‌شوید. این دستگاه برای تحلیل فرکانسی سیگنال‌ها و مشاهده طیف فرکانسی استفاده می‌شود.", "category": "ابزار اندازه‌گیری", "type": "article"},
        {"title": "چگونگی اندازه‌گیری SWR آنتن", "content": "این آموزش به نحوه اندازه‌گیری نسبت موج ایستاده (SWR) در آنتن‌ها می‌پردازد. SWR مناسب نشان‌دهنده تطبیق امپدانس مناسب بین خط انتقال و آنتن است.", "category": "آنتن‌ها", "type": "tutorial"},
        {"title": "اصول طراحی شبکه‌های بی‌سیم", "content": "در این مقاله با اصول طراحی شبکه‌های بی‌سیم آشنا می‌شوید. موضوعاتی مانند انتخاب فرکانس، نحوه چیدمان تجهیزات، پوشش سیگنال و امنیت شبکه.", "category": "شبکه‌های بی‌سیم", "type": "article"},
        {"title": "آشنایی با مدارات الکترونیکی پایه", "content": "این آموزش به معرفی مدارات الکترونیکی پایه می‌پردازد. از مدارهای ساده مانند مقسم ولتاژ تا مدارهای پیچیده‌تر مانند تقویت‌کننده‌ها و فیلترها.", "category": "الکترونیک", "type": "tutorial"},
        
        {"title": "نحوه محاسبه بودجه لینک رادیویی", "content": "در این مقاله با نحوه محاسبه بودجه لینک (Link Budget) در سیستم‌های رادیویی آشنا می‌شوید. عواملی مانند توان فرستنده، بهره آنتن‌ها، افت مسیر و حساسیت گیرنده در محاسبات بودجه لینک تأثیرگذار هستند.", "category": "مهندسی رادیو", "type": "article"},
        {"title": "کاربردهای آردوینو در پروژه‌های رادیویی", "content": "این آموزش به معرفی کاربردهای برد آردوینو در پروژه‌های رادیویی می‌پردازد. از کنترل فرستنده‌ها تا ساخت گیرنده‌های ساده و سیستم‌های پایش.", "category": "الکترونیک", "type": "tutorial"},
        {"title": "نحوه تست و عیب‌یابی فرستنده‌های رادیویی", "content": "در این آموزش با روش‌های تست و عیب‌یابی فرستنده‌های رادیویی آشنا می‌شوید. از ابزارهای مورد نیاز تا مراحل منظم عیب‌یابی و رفع مشکلات رایج.", "category": "تعمیرات", "type": "tutorial"},
        {"title": "آشنایی با باندهای فرکانسی و کاربردهای آن‌ها", "content": "این مقاله به معرفی باندهای مختلف فرکانسی و کاربردهای هر یک می‌پردازد. از فرکانس‌های پایین (LF) تا فرکانس‌های خیلی بالا (UHF) و ماکروویو.", "category": "آموزش مبانی رادیو", "type": "article"},
        {"title": "اصول حفاظت از تجهیزات رادیویی", "content": "در این آموزش با اصول حفاظت از تجهیزات رادیویی در برابر آسیب‌های محیطی، الکتریکی و فیزیکی آشنا می‌شوید. از روش‌های ارت‌گذاری تا حفاظت در برابر صاعقه و نوسانات برق.", "category": "نگهداری و تعمیرات", "type": "guide"},
    ]
    
    for edu in edu_contents:
        with db.conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO educational_content (title, content, category, type) VALUES (%s, %s, %s, %s) RETURNING id',
                (edu["title"], edu["content"], edu["category"], edu["type"])
            )
            edu_id = cursor.fetchone()[0]
            print(f"Added educational content: {edu['title']} (ID: {edu_id})")
    
    print("\nSample data added successfully!")

if __name__ == "__main__":
    print("Starting database improvements and sample data addition...")
    
    # First improve the database methods to handle NULL values
    improve_database_methods()
    
    # Then add sample data
    add_sample_data()
    
    print("All tasks completed successfully!")