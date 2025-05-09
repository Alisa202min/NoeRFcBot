#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سیدینگ دیتابیس برای تست‌های ادمین پنل
این اسکریپت داده‌های آزمایشی برای تمام بخش‌های سیستم مدیریت ایجاد می‌کند
"""

import os
import sys
import random
from datetime import datetime, timedelta
from app import app, db
from models import User, Category, Product, ProductMedia, Inquiry, EducationalContent, StaticContent
from werkzeug.security import generate_password_hash

def create_test_users():
    """ایجاد کاربران آزمایشی برای تست"""
    print("ایجاد کاربران آزمایشی...")
    
    # حذف کاربران قبلی
    User.query.delete()
    
    # ایجاد کاربر ادمین
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=generate_password_hash("admin123"),
        is_admin=True
    )
    
    # ایجاد کاربران عادی
    user1 = User(
        username="user1",
        email="user1@example.com",
        password_hash=generate_password_hash("user123"),
        is_admin=False
    )
    
    user2 = User(
        username="user2",
        email="user2@example.com",
        password_hash=generate_password_hash("user456"),
        is_admin=False
    )
    
    db.session.add_all([admin, user1, user2])
    db.session.commit()
    
    print(f"✓ {User.query.count()} کاربر ایجاد شد")
    return admin, user1, user2

def create_test_categories():
    """ایجاد دسته‌بندی‌های آزمایشی با ساختار درختی ۴ سطحی"""
    print("ایجاد دسته‌بندی‌های آزمایشی...")
    
    # حذف دسته‌بندی‌های قبلی
    Category.query.delete()
    
    # دسته‌بندی‌های محصولات (سطح ۱)
    cat_rf_equipment = Category(name="تجهیزات رادیویی", cat_type="product")
    cat_antennas = Category(name="آنتن‌های مخابراتی", cat_type="product")
    cat_cables = Category(name="کابل‌ها و اتصالات", cat_type="product")
    
    db.session.add_all([cat_rf_equipment, cat_antennas, cat_cables])
    db.session.flush()  # برای دریافت آی‌دی‌ها
    
    # زیردسته‌های تجهیزات رادیویی (سطح ۲)
    cat_transmitters = Category(name="فرستنده‌ها", parent_id=cat_rf_equipment.id, cat_type="product")
    cat_receivers = Category(name="گیرنده‌ها", parent_id=cat_rf_equipment.id, cat_type="product")
    cat_transceivers = Category(name="فرستنده-گیرنده‌ها", parent_id=cat_rf_equipment.id, cat_type="product")
    
    # زیردسته‌های آنتن‌ها (سطح ۲)
    cat_directional = Category(name="آنتن‌های جهت‌دار", parent_id=cat_antennas.id, cat_type="product")
    cat_omnidirectional = Category(name="آنتن‌های همه‌جهته", parent_id=cat_antennas.id, cat_type="product")
    
    # زیردسته‌های کابل‌ها (سطح ۲)
    cat_coaxial = Category(name="کابل‌های کواکسیال", parent_id=cat_cables.id, cat_type="product")
    cat_fiber = Category(name="فیبر نوری", parent_id=cat_cables.id, cat_type="product")
    
    db.session.add_all([
        cat_transmitters, cat_receivers, cat_transceivers,
        cat_directional, cat_omnidirectional,
        cat_coaxial, cat_fiber
    ])
    db.session.flush()
    
    # زیردسته‌های سطح ۳
    cat_low_power = Category(name="فرستنده‌های کم‌توان", parent_id=cat_transmitters.id, cat_type="product")
    cat_high_power = Category(name="فرستنده‌های پرقدرت", parent_id=cat_transmitters.id, cat_type="product")
    
    cat_yagi = Category(name="آنتن‌های یاگی", parent_id=cat_directional.id, cat_type="product")
    cat_dish = Category(name="آنتن‌های بشقابی", parent_id=cat_directional.id, cat_type="product")
    
    cat_rg6 = Category(name="کابل‌های RG-6", parent_id=cat_coaxial.id, cat_type="product")
    cat_rg11 = Category(name="کابل‌های RG-11", parent_id=cat_coaxial.id, cat_type="product")
    
    db.session.add_all([
        cat_low_power, cat_high_power,
        cat_yagi, cat_dish,
        cat_rg6, cat_rg11
    ])
    db.session.flush()
    
    # زیردسته‌های سطح ۴
    cat_fm_transmitters = Category(name="فرستنده‌های FM", parent_id=cat_low_power.id, cat_type="product")
    cat_am_transmitters = Category(name="فرستنده‌های AM", parent_id=cat_low_power.id, cat_type="product")
    
    cat_tv_antennas = Category(name="آنتن‌های تلویزیونی", parent_id=cat_yagi.id, cat_type="product")
    cat_wifi_antennas = Category(name="آنتن‌های وای‌فای", parent_id=cat_yagi.id, cat_type="product")
    
    db.session.add_all([
        cat_fm_transmitters, cat_am_transmitters,
        cat_tv_antennas, cat_wifi_antennas
    ])
    
    # دسته‌بندی‌های خدمات (سطح ۱)
    cat_installation = Category(name="نصب و راه‌اندازی", cat_type="service")
    cat_repair = Category(name="تعمیر و نگهداری", cat_type="service")
    cat_consultation = Category(name="مشاوره و طراحی", cat_type="service")
    
    db.session.add_all([cat_installation, cat_repair, cat_consultation])
    db.session.flush()
    
    # زیردسته‌های خدمات (سطح ۲)
    cat_install_transmitter = Category(name="نصب فرستنده", parent_id=cat_installation.id, cat_type="service")
    cat_install_antenna = Category(name="نصب آنتن", parent_id=cat_installation.id, cat_type="service")
    
    cat_repair_transmitter = Category(name="تعمیر فرستنده", parent_id=cat_repair.id, cat_type="service")
    cat_repair_antenna = Category(name="تعمیر آنتن", parent_id=cat_repair.id, cat_type="service")
    
    cat_network_design = Category(name="طراحی شبکه مخابراتی", parent_id=cat_consultation.id, cat_type="service")
    cat_frequency_planning = Category(name="برنامه‌ریزی فرکانسی", parent_id=cat_consultation.id, cat_type="service")
    
    db.session.add_all([
        cat_install_transmitter, cat_install_antenna,
        cat_repair_transmitter, cat_repair_antenna,
        cat_network_design, cat_frequency_planning
    ])
    
    db.session.commit()
    
    print(f"✓ {Category.query.count()} دسته‌بندی ایجاد شد")
    
    # لیست تمام دسته‌بندی‌ها برای استفاده در تولید محصولات و خدمات
    product_categories = Category.query.filter_by(cat_type="product").all()
    service_categories = Category.query.filter_by(cat_type="service").all()
    
    return product_categories, service_categories

def create_test_products(product_categories):
    """ایجاد محصولات آزمایشی برای دسته‌بندی‌های مختلف"""
    print("ایجاد محصولات آزمایشی...")
    
    # حذف محصولات قبلی
    Product.query.filter_by(product_type="product").delete()
    
    products = []
    
    # محصولات برای دسته‌بندی‌های مختلف
    brands = ["RF Pro", "TeleTech", "RFComm", "RadioMax", "AntennaPlus"]
    
    for i, category in enumerate(product_categories):
        # تعداد محصولات متفاوت برای هر دسته
        num_products = random.randint(2, 5)
        
        for j in range(num_products):
            brand = random.choice(brands)
            model = f"Model-{random.randint(100, 999)}"
            
            price = random.randint(1000000, 100000000)  # قیمت بین ۱ تا ۱۰۰ میلیون تومان
            
            product = Product(
                name=f"{category.name} {brand} {model}",
                description=f"توضیحات مفصل برای {category.name} {brand} {model}. این محصول دارای کیفیت بالا و قابلیت‌های پیشرفته است.",
                price=price,
                category_id=category.id,
                product_type="product",
                brand=brand,
                model=model,
                in_stock=random.choice([True, True, True, False]),  # ۷۵٪ موجود
                tags=f"{category.name},RF,{brand}",
                featured=random.choice([True, False, False, False])  # ۲۵٪ ویژه
            )
            
            products.append(product)
    
    db.session.add_all(products)
    db.session.commit()
    
    print(f"✓ {len(products)} محصول ایجاد شد")
    return products

def create_test_services(service_categories):
    """ایجاد خدمات آزمایشی برای دسته‌بندی‌های مختلف"""
    print("ایجاد خدمات آزمایشی...")
    
    # حذف خدمات قبلی
    Product.query.filter_by(product_type="service").delete()
    
    services = []
    
    for i, category in enumerate(service_categories):
        # تعداد خدمات متفاوت برای هر دسته
        num_services = random.randint(1, 3)
        
        for j in range(num_services):
            price = random.randint(500000, 10000000)  # قیمت بین ۵۰۰ هزار تا ۱۰ میلیون تومان
            
            service = Product(
                name=f"خدمات {category.name} پیشرفته",
                description=f"شرح کامل خدمات {category.name}. این خدمات شامل موارد زیر می‌شود: تحلیل اولیه، اجرا، تست و راه‌اندازی.",
                price=price,
                category_id=category.id,
                product_type="service",
                brand="",
                model="",
                in_stock=True,
                tags=f"{category.name},خدمات,نصب",
                featured=random.choice([True, False, False])  # ۳۳٪ ویژه
            )
            
            services.append(service)
    
    db.session.add_all(services)
    db.session.commit()
    
    print(f"✓ {len(services)} خدمت ایجاد شد")
    return services

def create_test_media(products, services):
    """ایجاد رسانه‌های آزمایشی برای محصولات و خدمات"""
    print("ایجاد رسانه‌های آزمایشی...")
    
    # حذف رسانه‌های قبلی
    ProductMedia.query.delete()
    
    media_items = []
    
    # فایل‌های رسانه برای محصولات
    for product in products:
        # هر محصول ۱ تا ۳ عکس دارد
        num_media = random.randint(1, 3)
        
        for i in range(num_media):
            media = ProductMedia(
                product_id=product.id,
                file_id=f"product_image_{product.id}_{i}",
                file_type="photo",
                file_path=f"/static/images/product_{product.id}_{i}.jpg",
                created_at=datetime.now()
            )
            
            media_items.append(media)
    
    # فایل‌های رسانه برای خدمات
    for service in services:
        # هر خدمت ۱ تا ۲ عکس دارد
        num_media = random.randint(1, 2)
        
        for i in range(num_media):
            media = ProductMedia(
                product_id=service.id,
                file_id=f"service_image_{service.id}_{i}",
                file_type="photo",
                file_path=f"/static/images/service_{service.id}_{i}.jpg",
                created_at=datetime.now()
            )
            
            media_items.append(media)
    
    db.session.add_all(media_items)
    db.session.commit()
    
    print(f"✓ {len(media_items)} رسانه ایجاد شد")
    return media_items

def create_test_inquiries(products, services, users):
    """ایجاد استعلام‌های قیمت آزمایشی"""
    print("ایجاد استعلام‌های قیمت آزمایشی...")
    
    # حذف استعلام‌های قبلی
    Inquiry.query.delete()
    
    inquiries = []
    
    # استعلام برای محصولات
    for _ in range(15):
        product = random.choice(products)
        user = random.choice(users)
        
        # تاریخ تصادفی در ۳۰ روز گذشته
        days_ago = random.randint(0, 30)
        created_at = datetime.now() - timedelta(days=days_ago)
        
        inquiry = Inquiry(
            user_id=user.id,
            product_id=product.id,
            product_type="product",
            name=f"{user.username} {random.choice(['علیزاده', 'محمدی', 'حسینی', 'احمدی'])}",
            phone=f"09{random.randint(10000000, 99999999)}",
            description=f"استعلام قیمت برای {product.name}. نیاز به {random.randint(1, 10)} دستگاه داریم.",
            status="new",
            created_at=created_at
        )
        
        inquiries.append(inquiry)
    
    # استعلام برای خدمات
    for _ in range(10):
        service = random.choice(services)
        user = random.choice(users)
        
        # تاریخ تصادفی در ۳۰ روز گذشته
        days_ago = random.randint(0, 30)
        created_at = datetime.now() - timedelta(days=days_ago)
        
        inquiry = Inquiry(
            user_id=user.id,
            product_id=service.id,
            product_type="service",
            name=f"{user.username} {random.choice(['کریمی', 'رحیمی', 'فرهادی', 'نجفی'])}",
            phone=f"09{random.randint(10000000, 99999999)}",
            description=f"استعلام قیمت برای {service.name}. نیاز به خدمات در منطقه {random.choice(['تهران', 'اصفهان', 'شیراز', 'مشهد'])} داریم.",
            status=random.choice(["new", "in_progress", "completed"]),
            created_at=created_at
        )
        
        inquiries.append(inquiry)
    
    db.session.add_all(inquiries)
    db.session.commit()
    
    print(f"✓ {len(inquiries)} استعلام قیمت ایجاد شد")
    return inquiries

def create_test_educational_content():
    """ایجاد محتوای آموزشی آزمایشی"""
    print("ایجاد محتوای آموزشی آزمایشی...")
    
    # حذف محتوای آموزشی قبلی
    EducationalContent.query.delete()
    
    contents = []
    
    # دسته‌بندی‌های محتوای آموزشی
    categories = ["آموزش عمومی", "آموزش فنی", "نکات کاربردی", "مقالات تخصصی", "ویدئوهای آموزشی"]
    
    # محتوای آموزشی متنی
    for i in range(8):
        category = random.choice(categories)
        
        days_ago = random.randint(0, 60)
        created_at = datetime.now() - timedelta(days=days_ago)
        
        content = EducationalContent(
            title=f"آموزش {i+1}: {category}",
            content=f"""<h2>محتوای آموزشی {i+1}</h2>
            <p>این یک محتوای آموزشی نمونه است که برای تست سیستم ایجاد شده است.</p>
            <h3>بخش اول: مقدمه</h3>
            <p>در این بخش به مفاهیم اولیه پرداخته می‌شود.</p>
            <h3>بخش دوم: جزئیات فنی</h3>
            <p>این بخش شامل اطلاعات فنی مهمی است که باید به آن توجه کنید.</p>
            <h3>نتیجه‌گیری</h3>
            <p>با رعایت نکات فوق، می‌توانید بهره‌وری را افزایش دهید.</p>""",
            category=category,
            content_type=random.choice(["text", "text", "text", "video", "image"]),
            created_at=created_at
        )
        
        contents.append(content)
    
    db.session.add_all(contents)
    db.session.commit()
    
    print(f"✓ {len(contents)} محتوای آموزشی ایجاد شد")
    return contents

def create_test_static_content():
    """ایجاد محتوای ثابت آزمایشی (تماس با ما، درباره ما)"""
    print("ایجاد محتوای ثابت آزمایشی...")
    
    # حذف محتوای ثابت قبلی
    StaticContent.query.delete()
    
    # محتوای تماس با ما
    contact_content = StaticContent(
        content_type="contact",
        content="""<h2>تماس با ما</h2>
        <p>شما می‌توانید از طریق راه‌های زیر با ما در ارتباط باشید:</p>
        <ul>
            <li><strong>آدرس:</strong> تهران، خیابان ولیعصر، پلاک ۱۲۳۴</li>
            <li><strong>تلفن:</strong> ۰۲۱-۸۸۷۸۶۵۴۳</li>
            <li><strong>ایمیل:</strong> info@rfcatalog.com</li>
        </ul>
        <h3>ساعات کاری:</h3>
        <p>شنبه تا چهارشنبه: ۹ الی ۱۸<br>پنجشنبه: ۹ الی ۱۳</p>
        """
    )
    
    # محتوای درباره ما
    about_content = StaticContent(
        content_type="about",
        content="""<h2>درباره ما</h2>
        <p>شرکت ما با بیش از ۱۵ سال سابقه در زمینه تجهیزات مخابراتی و رادیویی، یکی از معتبرترین شرکت‌های ارائه‌دهنده خدمات و محصولات RF در ایران است.</p>
        <h3>ماموریت ما</h3>
        <p>ماموریت ما ارائه بهترین محصولات و خدمات مخابراتی با کیفیت جهانی و قیمت رقابتی به مشتریان ایرانی است.</p>
        <h3>چشم‌انداز</h3>
        <p>در تلاشیم تا به عنوان پیشگام صنعت مخابرات و رادیویی در منطقه شناخته شویم.</p>
        """
    )
    
    db.session.add_all([contact_content, about_content])
    db.session.commit()
    
    print("✓ محتوای ثابت ایجاد شد")
    return contact_content, about_content

def main():
    """اجرای اصلی"""
    with app.app_context():
        try:
            # تولید کاربران
            admin, user1, user2 = create_test_users()
            users = [admin, user1, user2]
            
            # تولید دسته‌بندی‌ها
            product_categories, service_categories = create_test_categories()
            
            # تولید محصولات و خدمات
            products = create_test_products(product_categories)
            services = create_test_services(service_categories)
            
            # تولید رسانه‌های محصولات و خدمات
            media_items = create_test_media(products, services)
            
            # تولید استعلام‌های قیمت
            inquiries = create_test_inquiries(products, services, users)
            
            # تولید محتوای آموزشی
            educational_contents = create_test_educational_content()
            
            # تولید محتوای ثابت
            static_contents = create_test_static_content()
            
            print("\n✓ سیدینگ دیتابیس با موفقیت انجام شد!")
            print(f"  • {User.query.count()} کاربر")
            print(f"  • {Category.query.count()} دسته‌بندی")
            print(f"  • {Product.query.filter_by(product_type='product').count()} محصول")
            print(f"  • {Product.query.filter_by(product_type='service').count()} خدمت")
            print(f"  • {ProductMedia.query.count()} رسانه")
            print(f"  • {Inquiry.query.count()} استعلام قیمت")
            print(f"  • {EducationalContent.query.count()} محتوای آموزشی")
            print(f"  • {StaticContent.query.count()} محتوای ثابت")
        
        except Exception as e:
            print(f"خطا در سیدینگ دیتابیس: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        return 0

if __name__ == "__main__":
    sys.exit(main())