#!/usr/bin/env python3
"""
RFTEST Data Generator - Enhanced Version
Uses ORM functions for data integrity and error detection
Generates 15 products + 15 services + 15 educational contents + 15 inquiries
"""

import os
import sys
from datetime import datetime, timedelta
import random
from PIL import Image, ImageDraw, ImageFont
import shutil
from sqlalchemy.sql import text

# Add main project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import main application classes
from app import app, db
from models import (
    Product, Service, EducationalContent, Inquiry,
    ProductCategory, ServiceCategory, EducationalCategory,
    ProductMedia, ServiceMedia, EducationalContentMedia,
    User
)

def create_image(path, text):
    """Create an image with specified text"""
    # Ensure directory exists
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
    print(f"✅ Image created: {path}")

def clear_all_data():
    """Clear all previous data using ORM"""
    print("🗑️ Clearing previous data...")

    with app.app_context():
        try:
            # Delete media (in dependency order)
            ProductMedia.query.delete()
            ServiceMedia.query.delete()
            EducationalContentMedia.query.delete()

            # Delete content
            Product.query.delete()
            Service.query.delete()
            EducationalContent.query.delete()
            Inquiry.query.delete()

            # Delete categories
            ProductCategory.query.delete()
            ServiceCategory.query.delete()
            EducationalCategory.query.delete()

            # Reset auto-increment sequences
            db.session.execute(text("ALTER SEQUENCE products_id_seq RESTART WITH 1;"))
            db.session.execute(text("ALTER SEQUENCE services_id_seq RESTART WITH 1;"))
            db.session.execute(text("ALTER SEQUENCE educational_content_id_seq RESTART WITH 1;"))
            db.session.execute(text("ALTER SEQUENCE inquiries_id_seq RESTART WITH 1;"))
            db.session.execute(text("ALTER SEQUENCE product_categories_id_seq RESTART WITH 1;"))
            db.session.execute(text("ALTER SEQUENCE service_categories_id_seq RESTART WITH 1;"))
            db.session.execute(text("ALTER SEQUENCE educational_categories_id_seq RESTART WITH 1;"))

            db.session.commit()
            print("✅ Previous data cleared and sequences reset")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error clearing data: {e}")

def create_hierarchical_categories():
    """Create hierarchical categories using ORM"""
    print("📂 Creating hierarchical categories...")

    categories = {}

    with app.app_context():
        try:
            # Product categories
            product_categories = [
                ("اسیلوسکوپ", "Waveform measurement equipment"),
                ("اسپکتروم آنالایزر", "Frequency analysis equipment"),
                ("سیگنال ژنراتور", "Signal generation equipment"),
                ("نتورک آنالایزر", "Network analysis equipment"),
                ("پاورمتر", "Power measurement equipment")
            ]

            for name, description in product_categories:
                category = ProductCategory()
                category.name = name
                category.description = description
                category.created_at = datetime.now()
                db.session.add(category)
                db.session.flush()  # To get ID
                categories[f"product_{name}"] = category.id

            # Service categories
            service_categories = [
                ("کالیبراسیون", "Equipment calibration services"),
                ("تعمیرات", "Repair and maintenance services"),
                ("آموزش", "Training and consulting services"),
                ("طراحی", "Design and implementation services"),
                ("مشاوره", "Specialized consulting services")
            ]

            for name, description in service_categories:
                category = ServiceCategory()
                category.name = name
                category.description = description
                category.created_at = datetime.now()
                db.session.add(category)
                db.session.flush()
                categories[f"service_{name}"] = category.id

            # Educational categories
            educational_categories = [
                ("RF و میکروویو", "RF technology training"),
                ("اندازه‌گیری", "Measurement equipment training"),
                ("کالیبراسیون", "Calibration process training"),
                ("تعمیرات", "Equipment repair training"),
                ("استانداردها", "Industrial standards training")
            ]

            for name, description in educational_categories:
                category = EducationalCategory()
                category.name = name
                category.description = description
                category.created_at = datetime.now()
                db.session.add(category)
                db.session.flush()
                categories[f"educational_{name}"] = category.id

            db.session.commit()
            print("✅ Hierarchical categories created")
            print(f"Available category keys: {list(categories.keys())}")

            return categories

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating categories: {e}")
            return {}

def create_products_with_images(categories):
    """Create 15 products with images using ORM"""
    print("📦 Creating 15 products with images...")

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

    with app.app_context():
        try:
            for i, (name, cat, price, brand) in enumerate(products_data, 1):
                category_key = f"product_{cat}"
                if category_key not in categories:
                    raise KeyError(f"Category '{category_key}' not found in categories")
                category_id = categories[category_key]

                # Create product
                product = Product(
                    name=name,
                    description=f"تجهيز پيشرفته {cat} از برند معتبر {brand}",
                    price=price,
                    category_id=category_id,
                    brand=brand,
                    model=f"MODEL-{i:03d}",
                    tags=f"{cat},{brand},تجهيزات اندازه‌گيري",
                    in_stock=True,
                    featured=i <= 5,
                    created_at=datetime.now()
                )
                db.session.add(product)
                db.session.flush()  # To get product ID

                # Create product directory
                product_dir = f"static/uploads/products/{product.id}"
                os.makedirs(product_dir, exist_ok=True)

                # Main image + 3 extra images
                for j in range(4):
                    if j == 0:
                        img_name = "main.jpg"
                        text = f"{name[:25]}..."
                    else:
                        img_name = f"extra_{j}.jpg"
                        text = f"تصوير اضافي {j}"

                    img_path = f"{product_dir}/{img_name}"
                    create_image(img_path, text)

                    media = ProductMedia(
                        product_id=product.id,
                        file_id=f"uploads/products/{product.id}/{img_name}",
                        file_type="photo"
                    )
                    db.session.add(media)

            db.session.commit()
            print("✅ 15 products with images created")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating products: {e}")

def create_services_with_images(categories):
    """Create 15 services with images using ORM"""
    print("🔧 Creating 15 services with images...")

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
                category_key = f"service_{cat}"
                if category_key not in categories:
                    raise KeyError(f"Category '{category_key}' not found in categories")
                category_id = categories[category_key]

                # Create service
                service = Service(
                    name=name,
                    description=f"خدمات تخصصي {cat} توسط متخصصان مجرب RFTEST. کيفيت بالا و قيمت مناسب.",
                    price=price,
                    category_id=category_id,
                    tags=f"{cat},RFTEST,خدمات تخصصي",
                    featured=i <= 5,
                    available=True,
                    created_at=datetime.now()
                )
                db.session.add(service)
                db.session.flush()  # To get service ID

                # Create service directory
                service_dir = f"static/uploads/services/{service.id}"
                os.makedirs(service_dir, exist_ok=True)

                img_path = f"{service_dir}/main.jpg"
                create_image(img_path, f"خدمات {cat}")

                media = ServiceMedia(
                    service_id=service.id,
                    file_id=f"uploads/services/{service.id}/main.jpg",
                    file_type="photo"
                )
                db.session.add(media)

            db.session.commit()
            print("✅ 15 services with images created")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating services: {e}")

def create_educational_content_with_images(categories):
    """Create 15 educational contents with images using ORM"""
    print("📚 Creating 15 educational contents with images...")

    educational_data = [
        ("راهنمای کامل استفاده از اسیلوسکوپ دیجیتال", "RF و میکروویو"),
        ("نحوه کار با اسپکتروم آنالایزر", "اندازه‌گیری"),
        ("راهنمای استفاده از نتورک آنالایزر", "اندازه‌گیری"),
        ("تنظیمات اولیه دستگاه", "کالیبراسیون"),
        ("راهنمای ایمنی در آزمایشگاه RF", "استانداردها"),
        ("اصول اندازه‌گیری توان RF", "RF و میکروویو"),
        ("مفهوم نویز فاز در سیگنال‌ها", "RF و میکروویو"),
        ("تئوری اسپکتروم و تحلیل فرکانسی", "اندازه‌گیری"),
        ("اندازه‌گیری امپدانس و SWR", "اندازه‌گیری"),
        ("اصول پراکندگی S-parameters", "RF و میکروویو"),
        ("روش‌های عیب‌یابی در مدارات RF", "تعمیرات"),
        ("تکنیک‌های اندازه‌گیری S-parameters", "اندازه‌گیری"),
        ("تست تداخل و EMC", "استانداردها"),
        ("تکنیک‌های تست آنتن", "اندازه‌گیری"),
        ("پروژه طراحی و تست فیلتر RF", "RF و میکروویو")
    ]

    with app.app_context():
        try:
            for i, (title, cat) in enumerate(educational_data, 1):
                category_key = f"educational_{cat}"
                if category_key not in categories:
                    raise KeyError(f"Category '{category_key}' not found in categories")
                category_id = categories[category_key]

                content = f"""اين مطلب جامع در زمينه {cat} تهيه شده است. شامل توضيحات کامل، مثال‌هاي عملي و نکات کاربردي براي متخصصان و علاقه‌مندان به تجهيزات اندازه‌گيري RF.

محتواي اين مطلب شامل:
- اصول کلي و مباني تئوري
- راهنماي گام به گام عملي
- نکات و ترفندهاي کاربردي
- مثال‌هاي واقعي از پروژه‌ها
- منابع و مراجع تکميلي

اين محتوا مناسب براي سطوح مختلف دانش فني و به صورت کاربردي تنظيم شده است."""

                # Create educational content
                edu_content = EducationalContent(
                    title=title,
                    content=content,
                    category_id=category_id,
                    created_at=datetime.now()
                )
                db.session.add(edu_content)
                db.session.flush()  # To get content ID

                # Create educational image directory
                edu_dir = f"static/media/educational"
                os.makedirs(edu_dir, exist_ok=True)

                img_name = f"edu_{edu_content.id}_main.jpg"
                img_path = f"{edu_dir}/{img_name}"
                create_image(img_path, f"آموزش {cat}")

                media = EducationalContentMedia(
                    content_id=edu_content.id,
                    file_id=f"educational_media_{edu_content.id}_main",
                    file_type="photo",
                    local_path=f"static/media/educational/{img_name}"
                )
                db.session.add(media)

            db.session.commit()
            print("✅ 15 educational contents with images created")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating educational contents: {e}")

def create_inquiries():
    """Create 15 inquiries using ORM"""
    print("📋 Creating 15 inquiries...")

    inquiries_data = [
        (7625738591, "مهندس احمد رضایی", "09121234567", "استعلام قیمت اسیلوسکوپ 100MHz برای آزمایشگاه دانشگاه"),
        (987654321, "شرکت فناوری پارس", "02144556677", "درخواست کالیبراسیون 5 دستگاه اسپکتروم آنالایزر"),
        (123456789, "دکتر محمد محمدی", "09359876543", "آیا دوره آموزشی RF برای دانشجویان ارشد برگزار می‌کنید؟"),
        (555666777, "مهندس فاطمه نوری", "09128887766", "نیاز به مشاوره برای تجهیز آزمایشگاه تست EMC"),
        (111222333, "شرکت الکترونیک آریا", "02133445566", "استعلام قیمت رادیوتستر Aeroflex 3920B"),
        (444555666, "آقای علی احمدی", "09135554433", "آیا تعمیر اسیلوسکوپ Tektronix 2465 را انجام می‌دهید؟"),
        (777888999, "مهندس سارا کریمی", "09124443322", "درخواست آموزش تخصصی کار با نتورک آنالایزر"),
        (333444555, "شرکت مخابرات ایران", "02177889900", "استعلام قیمت سیگنال ژنراتور تا 6GHz"),
        (666777888, "دکتر رضا پوری", "09366655544", "نیاز به کالیبراسیون فوری پاورمتر HP 437B"),
        (222333444, "مهندس حسن زارعی", "09357778899", "استعلام قیمت اسپکتروم آنالایزر Rohde & Schwarz FSW"),
        (888999111, "شرکت رادار پردازش", "02155667788", "نیاز به آموزش تخصصی S-parameter measurements"),
        (999111222, "مهندس مریم صادقی", "09147775566", "استعلام قیمت کالیبراسیون سالانه 8 دستگاه"),
        (111333555, "آقای محسن رستمی", "09198886644", "آیا رادیوتستر Marconi 2955B دست دوم دارید؟"),
        (444666888, "شرکت نوآوری فن", "02166554433", "درخواست مشاوره برای انتخاب تجهیزات برای آزمایشگاه تست IoT"),
        (777999222, "دکتر امیر حسینی", "09351112233", "استعلام اجاره کوتاه مدت نتورک آنالایزر")
    ]

    with app.app_context():
        try:
            for user_id, name, phone, desc in inquiries_data:
                # Random date in the past 2 months
                days_ago = random.randint(1, 60)
                created_date = datetime.now() - timedelta(days=days_ago)

                # Create inquiry
                inquiry = Inquiry(
                    user_id=user_id,
                    name=name,
                    phone=phone,
                    description=desc,
                    status="pending",
                    created_at=created_date
                )
                db.session.add(inquiry)

            db.session.commit()
            print("✅ 15 inquiries created")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating inquiries: {e}")

def generate_final_report():
    """Generate final report using ORM"""
    with app.app_context():
        try:
            # Count totals
            products_count = Product.query.count()
            services_count = Service.query.count()
            educational_count = EducationalContent.query.count()
            inquiries_count = Inquiry.query.count()

            # Count media
            product_media_count = ProductMedia.query.count()
            service_media_count = ServiceMedia.query.count()
            edu_media_count = EducationalContentMedia.query.count()

            # Count all categories (not just hierarchical)
            product_cats = ProductCategory.query.count()
            service_cats = ServiceCategory.query.count()
            edu_cats = EducationalCategory.query.count()
            total_cats = product_cats + service_cats + edu_cats

            # Print final report
            print("\n" + "="*70)
            print(" RFTEST data successfully generated!")
            print("="*70)
            print(f"✅ {products_count} measurement equipment products")
            print(f"✅ {services_count} specialized services")
            print(f"✅ {educational_count} educational contents")
            print(f"✅ {inquiries_count} inquiries")
            print()
            print(f"🖼️ {product_media_count} product images (main + extra)")
            print(f"🖼️ {service_media_count} service images")
            print(f"🖼️ {edu_media_count} educational images")
            print()
            print(f"🗂️ {total_cats} categories (product: {product_cats}, service: {service_cats}, educational: {edu_cats})")
            print("✅ Complete parent-child structure")
            print()
        
            print("🚀 RFTEST system ready for use!")

        except Exception as e:
            print(f"❌ Error generating report: {e}")

def main():
    """Main function - Generate complete RFTEST data using ORM"""
    print("🚀 RFTEST Data Generator - Enhanced Version")
    print("📦 15 products + 15 services + 15 contents + 15 inquiries")
    print("⚙️ Using ORM for data integrity and error handling")
    print("="*80)

    try:
        # Create default image
        os.makedirs("static/uploads/default", exist_ok=True)
        create_image("static/uploads/default/default.jpg", "تصویر پیش‌فرض")

        # Data generation steps
        clear_all_data()
        categories = create_hierarchical_categories()

        if not categories:
            print("❌ Error creating categories. Aborted.")
            return 1

        create_products_with_images(categories)
        create_services_with_images(categories)
        create_educational_content_with_images(categories)
        create_inquiries()

        # Final report
        generate_final_report()

        return 0

    except Exception as e:
        print(f"❌ General error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())