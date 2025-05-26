#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
پر کردن سریع دیتابیس با اطلاعات کامل
"""

import os
import sys
from database import Database
from PIL import Image, ImageDraw, ImageFont
import random

def create_sample_image(filename, text, width=800, height=600):
    """ساخت تصویر نمونه"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    image = Image.new('RGB', (width, height), (240, 240, 240))
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    # محاسبه موقعیت متن
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    else:
        text_width = len(text) * 8
        text_height = 16
    
    x = max(0, (width - text_width) // 2)
    y = max(0, (height - text_height) // 2)
    
    draw.text((x, y), text, fill=(100, 100, 100), font=font)
    image.save(filename)

def seed_all_data():
    """پر کردن کامل دیتابیس"""
    print("🚀 شروع پر کردن دیتابیس...")
    
    db = Database()
    
    try:
        # استفاده از متد های موجود database
        print("📁 ایجاد دسته‌بندی‌ها...")
        
        # دسته‌بندی محصولات
        product_categories = [
            ("اسیلوسکوپ", "دستگاه‌های اسیلوسکوپ آنالوگ و دیجیتال"),
            ("اسپکتروم آنالایزر", "تحلیل‌گرهای طیف فرکانسی"),
            ("سیگنال ژنراتور", "تولیدکننده‌های سیگنال"),
            ("نتورک آنالایزر", "تحلیل‌گرهای شبکه"),
            ("پاور متر", "اندازه‌گیری توان RF"),
            ("رادیوتستر", "تستر رادیوهای دوطرفه")
        ]
        
        # اضافه کردن دسته‌بندی‌ها
        for name, desc in product_categories:
            try:
                db.add_category(name, "products", desc)
                print(f"✅ دسته‌بندی {name} اضافه شد")
            except Exception as e:
                print(f"⚠️ {name}: {e}")
        
        # محصولات
        print("\n🛠️ ایجاد محصولات...")
        
        products = [
            {
                "name": "اسیلوسکوپ دیجیتال Keysight DSOX3024T",
                "description": "اسیلوسکوپ دیجیتال 4 کاناله 200MHz با صفحه نمایش لمسی",
                "price": 850000000,
                "model": "DSOX3024T",
                "manufacturer": "Keysight",
                "category": "اسیلوسکوپ",
                "tags": "4-channel,200MHz,digital"
            },
            {
                "name": "اسپکتروم آنالایزر Keysight N9020A",
                "description": "اسپکتروم آنالایزر حرفه‌ای تا 26.5GHz",
                "price": 2500000000,
                "model": "N9020A", 
                "manufacturer": "Keysight",
                "category": "اسپکتروم آنالایزر",
                "tags": "26.5GHz,professional"
            },
            {
                "name": "سیگنال ژنراتور Rigol DG4062",
                "description": "فانکشن ژنراتور دو کاناله 60MHz",
                "price": 95000000,
                "model": "DG4062",
                "manufacturer": "Rigol", 
                "category": "سیگنال ژنراتور",
                "tags": "dual-channel,60MHz"
            },
            {
                "name": "نتورک آنالایزر Keysight E5071C",
                "description": "نتورک آنالایزر 4 پورت تا 20GHz",
                "price": 1800000000,
                "model": "E5071C",
                "manufacturer": "Keysight",
                "category": "نتورک آنالایزر", 
                "tags": "4-port,20GHz"
            },
            {
                "name": "پاور متر Keysight E4417A",
                "description": "پاور متر دو کاناله با دقت بالا",
                "price": 320000000,
                "model": "E4417A",
                "manufacturer": "Keysight",
                "category": "پاور متر",
                "tags": "dual-channel,high-accuracy"
            },
            {
                "name": "رادیوتستر Aeroflex 3920B",
                "description": "رادیوتستر دیجیتال با پشتیبانی DMR, TETRA",
                "price": 1200000000,
                "model": "3920B",
                "manufacturer": "Aeroflex",
                "category": "رادیوتستر",
                "tags": "digital,DMR,TETRA"
            }
        ]
        
        for product in products:
            try:
                # دریافت category_id
                category_id = db.get_category_id(product["category"], "products")
                if category_id:
                    product_id = db.add_product(
                        name=product["name"],
                        description=product["description"], 
                        price=product["price"],
                        model=product["model"],
                        manufacturer=product["manufacturer"],
                        category_id=category_id,
                        tags=product["tags"]
                    )
                    
                    # ایجاد تصویر
                    image_path = f"static/uploads/products/product_{product_id}.jpg"
                    create_sample_image(
                        image_path,
                        f"{product['model']}\n{product['manufacturer']}"
                    )
                    
                    # اضافه کردن media
                    db.add_product_media(product_id, image_path, "image", True)
                    
                    print(f"✅ {product['name']}")
                    
            except Exception as e:
                print(f"⚠️ خطا در {product['name']}: {e}")
        
        # خدمات
        print("\n🔧 ایجاد خدمات...")
        
        # دسته‌بندی خدمات
        service_categories = [
            ("کالیبراسیون", "کالیبراسیون تجهیزات اندازه‌گیری"),
            ("تعمیرات", "تعمیر و نگهداری تجهیزات"),
            ("آموزش", "دوره‌های آموزشی تخصصی")
        ]
        
        for name, desc in service_categories:
            try:
                db.add_category(name, "services", desc)
                print(f"✅ دسته‌بندی خدمات {name}")
            except:
                pass
        
        services = [
            {
                "name": "کالیبراسیون اسیلوسکوپ",
                "description": "کالیبراسیون دقیق اسیلوسکوپ طبق استانداردهای ملی",
                "price": 12000000,
                "duration": "3-5 روز کاری",
                "category": "کالیبراسیون"
            },
            {
                "name": "تعمیر تجهیزات RF",
                "description": "تعمیر انواع تجهیزات اندازه‌گیری RF",
                "price": 25000000,
                "duration": "7-14 روز کاری", 
                "category": "تعمیرات"
            },
            {
                "name": "آموزش کار با اسیلوسکوپ",
                "description": "دوره جامع آموزش اسیلوسکوپ از مبتدی تا پیشرفته",
                "price": 8000000,
                "duration": "16 ساعت",
                "category": "آموزش"
            }
        ]
        
        for service in services:
            try:
                category_id = db.get_category_id(service["category"], "services")
                if category_id:
                    service_id = db.add_service(
                        name=service["name"],
                        description=service["description"],
                        price=service["price"],
                        duration=service["duration"],
                        category_id=category_id
                    )
                    
                    # ایجاد تصویر
                    image_path = f"static/uploads/services/service_{service_id}.jpg"
                    create_sample_image(
                        image_path,
                        f"خدمات {service['category']}\n{service['name'][:20]}"
                    )
                    
                    db.add_service_media(service_id, image_path, "image", True)
                    print(f"✅ {service['name']}")
                    
            except Exception as e:
                print(f"⚠️ خطا در {service['name']}: {e}")
        
        # محتوای آموزشی
        print("\n📚 ایجاد محتوای آموزشی...")
        
        # دسته‌بندی آموزشی
        edu_categories = [
            ("مبانی اندازه‌گیری", "اصول پایه اندازه‌گیری RF"),
            ("کار با دستگاه‌ها", "آموزش کار با تجهیزات")
        ]
        
        for name, desc in edu_categories:
            try:
                db.add_category(name, "educational", desc)
                print(f"✅ دسته‌بندی آموزشی {name}")
            except:
                pass
        
        educational_content = [
            {
                "title": "مقدمه‌ای بر اندازه‌گیری RF",
                "content": """
اندازه‌گیری در حوزه رادیو فرکانس یکی از مهم‌ترین بخش‌های مهندسی مخابرات است.

## مفاهیم کلیدی

### فرکانس
فرکانس تعداد نوسانات در واحد زمان است.

### توان  
توان انرژی منتقل شده در واحد زمان است.

## تجهیزات اساسی
1. اسیلوسکوپ
2. اسپکتروم آنالایزر
3. پاور متر
4. نتورک آنالایزر
                """,
                "reading_time": 8,
                "difficulty": "مبتدی",
                "category": "مبانی اندازه‌گیری"
            },
            {
                "title": "کار با اسیلوسکوپ",
                "content": """
اسیلوسکوپ ابزار اساسی برای مشاهده شکل موج است.

## کنترل‌های اصلی

### کنترل عمودی
- Volts/Div: حساسیت عمودی
- Position: جابجایی عمودی

### کنترل افقی  
- Time/Div: مقیاس زمانی
- Position: جابجایی افقی

## تنظیمات Trigger
تریگر تعیین می‌کند چه زمانی نمایش شروع شود.
                """,
                "reading_time": 12,
                "difficulty": "متوسط", 
                "category": "کار با دستگاه‌ها"
            }
        ]
        
        for content in educational_content:
            try:
                category_id = db.get_category_id(content["category"], "educational")
                if category_id:
                    content_id = db.add_educational_content(
                        title=content["title"],
                        content=content["content"],
                        reading_time=content["reading_time"],
                        difficulty=content["difficulty"],
                        category_id=category_id
                    )
                    
                    # ایجاد تصویر
                    image_path = f"static/uploads/educational/content_{content_id}.jpg"
                    create_sample_image(
                        image_path,
                        f"آموزش\n{content['title'][:25]}"
                    )
                    
                    db.add_educational_media(content_id, image_path, "image", True)
                    print(f"✅ {content['title']}")
                    
            except Exception as e:
                print(f"⚠️ خطا در {content['title']}: {e}")
        
        # استعلام‌های قیمت
        print("\n💬 ایجاد استعلام‌های قیمت...")
        
        inquiries = [
            {
                "name": "احمد رضایی",
                "phone": "09121234567",
                "email": "ahmad@example.com",
                "product_name": "اسیلوسکوپ دیجیتال",
                "message": "قیمت اسیلوسکوپ دیجیتال 100MHz اعلام کنید"
            },
            {
                "name": "مهندس حسینی", 
                "phone": "09135678901",
                "email": "hosseini@company.ir",
                "product_name": "کالیبراسیون پاور متر",
                "message": "نیاز به کالیبراسیون پاور متر HP داریم"
            },
            {
                "name": "دکتر زارعی",
                "phone": "09156789012", 
                "email": "zarei@university.ac.ir",
                "product_name": "بسته آموزشی RF",
                "message": "برای دانشگاه بسته تجهیزات آموزشی نیاز داریم"
            }
        ]
        
        for inquiry in inquiries:
            try:
                db.add_inquiry(
                    name=inquiry["name"],
                    phone=inquiry["phone"],
                    email=inquiry["email"],
                    product_name=inquiry["product_name"],
                    message=inquiry["message"]
                )
                print(f"✅ استعلام {inquiry['name']}")
            except Exception as e:
                print(f"⚠️ خطا در استعلام {inquiry['name']}: {e}")
        
        print("\n🎉 دیتابیس با موفقیت پر شد!")
        print("✅ محصولات، خدمات، محتوای آموزشی و استعلام‌ها اضافه شدند")
        
    except Exception as e:
        print(f"❌ خطای کلی: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    seed_all_data()