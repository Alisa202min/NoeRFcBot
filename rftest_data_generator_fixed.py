#!/usr/bin/env python3
"""
تولیدکننده دیتای کامل RFTEST - ویرایش بهبود یافته
استفاده از توابع اصلی برنامه بجای SQL مستقیم برای حفظ یکپارچگی دیتا
"""

import os
import sys
from datetime import datetime, timedelta
import random
from PIL import Image, ImageDraw, ImageFont

# اضافه کردن مسیر اصلی برنامه
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# وارد کردن کلاس‌های اصلی برنامه
from src.web.app import app, db
from src.models.models import (
    Product, Service, EducationalContent, Inquiry,
    ProductCategory, ServiceCategory, EducationalCategory,
    ProductMedia, ServiceMedia, EducationalContentMedia,
    User
)

def create_image(path, text):
    """ساخت تصویر با متن مشخص"""
    # اطمینان از وجود پوشه
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    img = Image.new('RGB', (800, 600), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((300, 280), text, fill=(60, 60, 60), font=font)
    draw.text((50, 50), "RFTEST.IR", fill=(0, 102, 204), font=font)
    img.save(path)
    print(f"✅ تصویر ایجاد شد: {path}")

def clear_all_data():
    """پاک کردن تمام دیتای قبلی با استفاده از ORM"""
    print("🗑️ پاک کردن دیتای قبلی...")
    
    with app.app_context():
        try:
            # حذف رسانه‌ها
            ProductMedia.query.delete()
            ServiceMedia.query.delete()
            EducationalContentMedia.query.delete()
            
            # حذف محتوا
            Product.query.delete()
            Service.query.delete()
            EducationalContent.query.delete()
            Inquiry.query.delete()
            
            # حذف دسته‌بندی‌ها
            ProductCategory.query.delete()
            ServiceCategory.query.delete()
            EducationalCategory.query.delete()
            
            db.session.commit()
            print("✅ دیتای قبلی پاک شد")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطا در پاک کردن دیتا: {e}")

def create_hierarchical_categories():
    """ایجاد دسته‌بندی‌های سلسله مراتبی با استفاده از ORM"""
    print("📂 ایجاد دسته‌بندی‌های سلسله مراتبی...")
    
    categories = {}
    
    with app.app_context():
        try:
            # دسته‌بندی محصولات
            product_categories = [
                ("اسیلوسکوپ", "تجهیزات اندازه‌گیری شکل موج"),
                ("اسپکتروم آنالایزر", "تجهیزات آنالیز فرکانسی"),
                ("سیگنال ژنراتور", "تجهیزات تولید سیگنال"),
                ("نتورک آنالایزر", "تجهیزات آنالیز شبکه"),
                ("پاورمتر", "تجهیزات اندازه‌گیری توان")
            ]
            
            for name, description in product_categories:
                category = ProductCategory(name=name, description=description)
                db.session.add(category)
                db.session.flush()  # برای گرفتن ID
                categories[f"product_{name}"] = category.id
            
            # دسته‌بندی خدمات
            service_categories = [
                ("کالیبراسیون", "خدمات کالیبراسیون تجهیزات"),
                ("تعمیرات", "خدمات تعمیر و نگهداری"),
                ("آموزش", "خدمات آموزشی و مشاوره"),
                ("طراحی", "خدمات طراحی و پیاده‌سازی"),
                ("مشاوره", "خدمات مشاوره تخصصی")
            ]
            
            for name, description in service_categories:
                category = ServiceCategory(name=name, description=description)
                db.session.add(category)
                db.session.flush()
                categories[f"service_{name}"] = category.id
            
            # دسته‌بندی آموزشی
            educational_categories = [
                ("RF و میکروویو", "آموزش تکنولوژی RF"),
                ("اندازه‌گیری", "آموزش تجهیزات اندازه‌گیری"),
                ("کالیبراسیون", "آموزش فرآیندهای کالیبراسیون"),
                ("تعمیرات", "آموزش تعمیر تجهیزات"),
                ("استانداردها", "آموزش استانداردهای صنعتی")
            ]
            
            for name, description in educational_categories:
                category = EducationalCategory(name=name, description=description)
                db.session.add(category)
                db.session.flush()
                categories[f"educational_{name}"] = category.id
            
            db.session.commit()
            print("✅ دسته‌بندی‌های سلسله مراتبی ایجاد شد")
            return categories
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطا در ایجاد دسته‌بندی‌ها: {e}")
            return {}

def create_products_with_images(categories):
    """ایجاد محصولات با استفاده از ORM و توابع اصلی برنامه"""
    print("📦 ایجاد 15 محصول با تصاویر...")
    
    products_data = [
        ("اسیلوسکوپ Keysight DSOX2002A", "اسیلوسکوپ", 45000000, "Keysight", "DSO-X2002A"),
        ("اسیلوسکوپ Rigol DS1054Z", "اسیلوسکوپ", 22000000, "Rigol", "DS1054Z"),
        ("اسیلوسکوپ Tektronix TBS1102B", "اسیلوسکوپ", 12000000, "Tektronix", "TBS1102B"),
        ("اسیلوسکوپ Hantek DSO2C10", "اسیلوسکوپ", 3500000, "Hantek", "DSO2C10"),
        ("اسیلوسکوپ Fluke ScopeMeter", "اسیلوسکوپ", 78000000, "Fluke", "190-504"),
        ("اسپکتروم آنالایزر Rohde & Schwarz FSW50", "اسپکتروم آنالایزر", 850000000, "Rohde & Schwarz", "FSW50"),
        ("اسپکتروم آنالایزر Agilent E4402B", "اسپکتروم آنالایزر", 125000000, "Agilent", "E4402B"),
        ("اسپکتروم آنالایزر Keysight N9010A", "اسپکتروم آنالایزر", 285000000, "Keysight", "N9010A"),
        ("اسپکتروم آنالایزر Anritsu MS2720T", "اسپکتروم آنالایزر", 195000000, "Anritsu", "MS2720T"),
        ("اسپکتروم آنالایزر Rigol DSA832", "اسپکتروم آنالایزر", 45000000, "Rigol", "DSA832"),
        ("سیگنال ژنراتور Keysight E8257D", "سیگنال ژنراتور", 780000000, "Keysight", "E8257D"),
        ("سیگنال ژنراتور Agilent E4438C", "سیگنال ژنراتور", 185000000, "Agilent", "E4438C"),
        ("سیگنال ژنراتور Rohde & Schwarz SMB100A", "سیگنال ژنراتور", 125000000, "Rohde & Schwarz", "SMB100A"),
        ("فانکشن ژنراتور Rigol DG1062Z", "سیگنال ژنراتور", 15000000, "Rigol", "DG1062Z"),
        ("آربیتری ژنراتور Keysight 33622A", "سیگنال ژنراتور", 95000000, "Keysight", "33622A")
    ]
    
    with app.app_context():
        try:
            for i, (name, cat, price, brand, model) in enumerate(products_data, 1):
                category_id = categories.get(f"product_{cat}")
                if not category_id:
                    print(f"⚠️ دسته‌بندی {cat} یافت نشد")
                    continue
                
                # ایجاد محصول با استفاده از ORM
                product = Product(
                    name=name,
                    description=f"تجهیز پیشرفته {cat} از برند معتبر {brand}. کیفیت بالا و عملکرد قابل اعتماد.",
                    price=price,
                    category_id=category_id,
                    brand=brand,
                    model=model,
                    tags=f"{cat},{brand},تجهیزات اندازه‌گیری",
                    in_stock=True,
                    featured=(i <= 5),  # پنج محصول اول ویژه
                    created_at=datetime.now()
                )
                
                db.session.add(product)
                db.session.flush()  # برای گرفتن ID
                
                # ایجاد پوشه محصول
                product_dir = f"static/uploads/products/{product.id}"
                os.makedirs(product_dir, exist_ok=True)
                
                # ایجاد تصاویر
                image_types = ["main.jpg", "extra_1.jpg", "extra_2.jpg", "extra_3.jpg"]
                for j, img_name in enumerate(image_types):
                    img_path = f"{product_dir}/{img_name}"
                    
                    if j == 0:
                        text = f"{name[:25]}..."
                    else:
                        text = f"تصویر {j} - {brand}"
                    
                    create_image(img_path, text)
                    
                    # ایجاد رکورد رسانه با استفاده از ORM
                    media = ProductMedia(
                        product_id=product.id,
                        file_id=f"uploads/products/{product.id}/{img_name}",
                        file_type="photo"
                    )
                    db.session.add(media)
                
                print(f"✅ محصول ایجاد شد: {name}")
            
            db.session.commit()
            print("✅ همه محصولات با موفقیت ایجاد شد")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطا در ایجاد محصولات: {e}")

def create_services_with_images(categories):
    """ایجاد خدمات با استفاده از ORM"""
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
    
    with app.app_context():
        try:
            for i, (name, cat, price) in enumerate(services_data, 1):
                category_id = categories.get(f"service_{cat}")
                if not category_id:
                    print(f"⚠️ دسته‌بندی خدمت {cat} یافت نشد")
                    continue
                
                # ایجاد خدمت با استفاده از ORM
                service = Service(
                    name=name,
                    description=f"خدمات تخصصی {cat} توسط متخصصان مجرب RFTEST. کیفیت بالا و قیمت مناسب.",
                    price=price,
                    category_id=category_id,
                    tags=f"{cat},RFTEST,خدمات تخصصی",
                    featured=(i <= 5),
                    available=True,
                    created_at=datetime.now()
                )
                
                db.session.add(service)
                db.session.flush()
                
                # ایجاد پوشه خدمت
                service_dir = f"static/uploads/services/{service.id}"
                os.makedirs(service_dir, exist_ok=True)
                
                # ایجاد تصاویر خدمت
                image_types = ["main.jpg", "process.jpg"]
                for j, img_name in enumerate(image_types):
                    img_path = f"{service_dir}/{img_name}"
                    
                    if j == 0:
                        text = f"{name[:25]}..."
                    else:
                        text = f"فرآیند {cat}"
                    
                    create_image(img_path, text)
                    
                    # ایجاد رکورد رسانه
                    media = ServiceMedia(
                        service_id=service.id,
                        file_id=f"uploads/services/{service.id}/{img_name}",
                        file_type="photo"
                    )
                    db.session.add(media)
                
                print(f"✅ خدمت ایجاد شد: {name}")
            
            db.session.commit()
            print("✅ همه خدمات با موفقیت ایجاد شد")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطا در ایجاد خدمات: {e}")

def main():
    """تابع اصلی اجرای برنامه"""
    print("🚀 شروع تولید دیتای کامل RFTEST...")
    
    # پاک کردن دیتای قبلی
    clear_all_data()
    
    # ایجاد دسته‌بندی‌ها
    categories = create_hierarchical_categories()
    
    if not categories:
        print("❌ خطا در ایجاد دسته‌بندی‌ها. متوقف شد.")
        return
    
    # ایجاد محصولات
    create_products_with_images(categories)
    
    # ایجاد خدمات
    create_services_with_images(categories)
    
    print("🎉 تولید دیتای کامل RFTEST با موفقیت تکمیل شد!")

if __name__ == "__main__":
    main()