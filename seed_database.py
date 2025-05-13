#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
اسکریپت برای ایجاد داده‌های نمونه در پایگاه داده
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# تنظیم مسیر برای پیدا کردن ماژول‌ها
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# واردسازی مدل‌های دیتابیس
from src.web.app import db
from src.models.models import User, Category, Product, Service, Inquiry, EducationalContent

# تنظیم لاگر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_database():
    """ایجاد داده‌های نمونه در پایگاه داده"""
    
    try:
        # بررسی وجود کاربر ادمین
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                phone='09123456789',
                is_admin=True
            )
            admin.set_password('admin12345')
            db.session.add(admin)
            logger.info("کاربر ادمین ایجاد شد")
        
        # ایجاد دسته‌بندی‌ها
        categories = {
            'product': [
                'تجهیزات رادیویی',
                'آنتن‌ها',
                'مالتی پلکسرها',
                'تقویت‌کننده‌ها',
                'تجهیزات تست و اندازه‌گیری'
            ],
            'service': [
                'خدمات نصب و راه‌اندازی',
                'تعمیر و نگهداری',
                'مشاوره فنی',
                'طراحی سیستم‌های مخابراتی',
                'خدمات پشتیبانی'
            ]
        }
        
        # ایجاد دسته‌بندی‌های محصول
        for cat_name in categories['product']:
            if not Category.query.filter_by(name=cat_name, cat_type='product').first():
                cat = Category(name=cat_name, cat_type='product')
                db.session.add(cat)
                logger.info(f"دسته‌بندی محصول '{cat_name}' ایجاد شد")
        
        # ایجاد دسته‌بندی‌های خدمات
        for cat_name in categories['service']:
            if not Category.query.filter_by(name=cat_name, cat_type='service').first():
                cat = Category(name=cat_name, cat_type='service')
                db.session.add(cat)
                logger.info(f"دسته‌بندی خدمت '{cat_name}' ایجاد شد")
        
        db.session.commit()
        
        # دریافت دسته‌بندی‌های ایجاد شده
        product_categories = Category.query.filter_by(cat_type='product').all()
        service_categories = Category.query.filter_by(cat_type='service').all()
        
        # ایجاد محصولات نمونه
        products = [
            {
                'name': 'آنتن دو بانده RF-2300',
                'price': 2500000,
                'description': 'آنتن دو بانده با قابلیت دریافت فرکانس‌های 2.4 و 5 گیگاهرتز، مناسب برای سیستم‌های مخابراتی نظامی و غیرنظامی',
                'category': product_categories[1],  # آنتن‌ها
                'featured': True,
                'brand': 'RF Systems',
                'model': 'RF-2300',
                'in_stock': True
            },
            {
                'name': 'رادیو SDR مدل RAD-4500',
                'price': 15000000,
                'description': 'رادیو نرم‌افزاری (SDR) با قابلیت برنامه‌ریزی برای فرکانس‌های مختلف، دارای پورت‌های I/O متنوع',
                'category': product_categories[0],  # تجهیزات رادیویی
                'featured': True,
                'brand': 'Advanced Radio Systems',
                'model': 'RAD-4500',
                'in_stock': True
            },
            {
                'name': 'تقویت‌کننده قدرت RF مدل AMP-150',
                'price': 8700000,
                'description': 'تقویت‌کننده قدرت RF با خروجی 150 وات، مناسب برای سیستم‌های پخش رادیویی و ارتباطات نظامی',
                'category': product_categories[3],  # تقویت‌کننده‌ها
                'featured': False,
                'brand': 'Power RF',
                'model': 'AMP-150',
                'in_stock': True
            },
            {
                'name': 'آنالایزر طیف فرکانسی SA-3500',
                'price': 32000000,
                'description': 'دستگاه آنالایزر طیف فرکانسی با دقت بالا و رنج فرکانسی 9 کیلوهرتز تا 20 گیگاهرتز',
                'category': product_categories[4],  # تجهیزات تست و اندازه‌گیری
                'featured': True,
                'brand': 'RF Test Solutions',
                'model': 'SA-3500',
                'in_stock': False
            },
            {
                'name': 'مالتی پلکسر 16 کاناله دیجیتال',
                'price': 12500000,
                'description': 'مالتی پلکسر دیجیتال 16 کاناله با قابلیت کدگذاری و رمزنگاری، مناسب برای سیستم‌های مخابراتی چندکاناله',
                'category': product_categories[2],  # مالتی پلکسرها
                'featured': False,
                'brand': 'Comm Systems',
                'model': 'MUX-16D',
                'in_stock': True
            }
        ]
        
        # ایجاد خدمات نمونه
        services = [
            {
                'name': 'نصب و راه‌اندازی سیستم‌های مخابراتی',
                'price': 5000000,
                'description': 'خدمات نصب و راه‌اندازی انواع سیستم‌های مخابراتی شامل آنتن‌ها، رادیوها و تجهیزات جانبی با گارانتی 12 ماهه',
                'category': service_categories[0],  # خدمات نصب و راه‌اندازی
                'featured': True
            },
            {
                'name': 'تعمیر تخصصی تجهیزات RF',
                'price': 2800000,
                'description': 'تعمیر انواع تجهیزات RF شامل رادیوها، آنتن‌ها و تقویت‌کننده‌ها توسط کارشناسان مجرب با 15 سال سابقه',
                'category': service_categories[1],  # تعمیر و نگهداری
                'featured': True
            },
            {
                'name': 'طراحی و پیاده‌سازی شبکه‌های بی‌سیم',
                'price': 15000000,
                'description': 'طراحی و پیاده‌سازی شبکه‌های بی‌سیم با تضمین پوشش و کیفیت مناسب برای سازمان‌ها و صنایع مختلف',
                'category': service_categories[3],  # طراحی سیستم‌های مخابراتی
                'featured': True
            },
            {
                'name': 'مشاوره فنی در زمینه انتخاب تجهیزات مخابراتی',
                'price': 3500000,
                'description': 'ارائه مشاوره تخصصی برای انتخاب بهترین تجهیزات مخابراتی مناسب با نیازهای مشتری و بودجه در نظر گرفته شده',
                'category': service_categories[2],  # مشاوره فنی
                'featured': False
            },
            {
                'name': 'قرارداد پشتیبانی سالانه تجهیزات مخابراتی',
                'price': 7500000,
                'description': 'قرارداد پشتیبانی سالانه شامل بازدیدهای دوره‌ای، تعمیرات، به‌روزرسانی نرم‌افزار و پشتیبانی 24/7',
                'category': service_categories[4],  # خدمات پشتیبانی
                'featured': False
            },
            {
                'name': 'آموزش تخصصی کار با تجهیزات رادیویی',
                'price': 4200000,
                'description': 'دوره‌های آموزشی تخصصی برای کار با تجهیزات رادیویی و مخابراتی برای کارکنان و متخصصان صنایع مختلف',
                'category': service_categories[2],  # مشاوره فنی (به عنوان آموزش)
                'featured': True
            }
        ]
        
        # افزودن محصولات
        for p_data in products:
            if not Product.query.filter_by(name=p_data['name']).first():
                product = Product(
                    name=p_data['name'],
                    price=p_data['price'],
                    description=p_data['description'],
                    category_id=p_data['category'].id,
                    featured=p_data['featured'],
                    brand=p_data['brand'],
                    model=p_data['model'],
                    in_stock=p_data['in_stock']
                )
                db.session.add(product)
                logger.info(f"محصول '{p_data['name']}' ایجاد شد")
        
        # افزودن خدمات
        for s_data in services:
            if not Service.query.filter_by(name=s_data['name']).first():
                service = Service(
                    name=s_data['name'],
                    price=s_data['price'],
                    description=s_data['description'],
                    category_id=s_data['category'].id,
                    featured=s_data['featured'],
                )
                db.session.add(service)
                logger.info(f"خدمت '{s_data['name']}' ایجاد شد")
        
        db.session.commit()
        
        # ایجاد استعلام‌های نمونه
        
        # دریافت محصولات و خدمات
        products_db = Product.query.all()
        services_db = Service.query.all()
        
        if products_db and services_db:
            inquiries = [
                {
                    'user_id': 123456789,  # شناسه تلگرام کاربر
                    'name': 'علی محمدی',
                    'phone': '09111234567',
                    'description': 'درخواست استعلام قیمت برای خرید 5 دستگاه آنتن دو بانده RF-2300 به همراه نصب و راه‌اندازی',
                    'product': products_db[0],  # آنتن دو بانده RF-2300
                    'service': None,
                    'status': 'pending'
                },
                {
                    'user_id': 987654321,
                    'name': 'رضا کریمی',
                    'phone': '09122345678',
                    'description': 'نیاز به مشاوره برای طراحی شبکه بی‌سیم برای یک سازمان دولتی با 500 کاربر',
                    'product': None,
                    'service': services_db[2],  # طراحی و پیاده‌سازی شبکه‌های بی‌سیم
                    'status': 'in_progress'
                },
                {
                    'user_id': 246813579,
                    'name': 'فاطمه حسینی',
                    'phone': '09133456789',
                    'description': 'استعلام قیمت تعمیر 3 دستگاه رادیو SDR مدل RAD-4500 خریداری شده در سال گذشته که دچار مشکل شده‌اند',
                    'product': products_db[1],  # رادیو SDR مدل RAD-4500
                    'service': None,
                    'status': 'completed'
                },
                {
                    'user_id': 135792468,
                    'name': 'محمد احمدی',
                    'phone': '09144567890',
                    'description': 'درخواست طرح قرارداد پشتیبانی سالانه برای تجهیزات مخابراتی شرکت ما که شامل 15 دستگاه رادیو و 20 آنتن می‌شود',
                    'product': None,
                    'service': services_db[4],  # قرارداد پشتیبانی سالانه تجهیزات مخابراتی
                    'status': 'pending'
                }
            ]
            
            for i_data in inquiries:
                # بررسی وجود استعلام مشابه برای جلوگیری از ثبت تکراری
                existing_inquiry = Inquiry.query.filter_by(
                    user_id=i_data['user_id'], 
                    phone=i_data['phone']
                ).first()
                
                if not existing_inquiry:
                    # دریافت زمان فعلی
                    now = datetime.now()
                    
                    # ساخت استعلام با فیلدهای مورد نیاز
                    inquiry = Inquiry(
                        user_id=i_data['user_id'],
                        name=i_data['name'],
                        phone=i_data['phone'],
                        description=i_data['description'],
                        product_id=i_data['product'].id if i_data['product'] else None,
                        service_id=i_data['service'].id if i_data['service'] else None,
                        status=i_data['status'],
                        date=now  # فیلد date را که در دیتابیس وجود دارد ولی در مدل نیست، به صورت دستی تنظیم می‌کنیم
                    )
                    db.session.add(inquiry)
                    logger.info(f"استعلام برای {i_data['name']} ایجاد شد")
        
        # افزودن محتوای آموزشی
        educational_contents = [
            {
                'title': 'اصول کار با آنتن‌های دو بانده',
                'content': 'آنتن‌های دو بانده قابلیت کار در دو محدوده فرکانسی مختلف را دارند. در این مقاله اصول کار با این آنتن‌ها و تنظیمات مورد نیاز برای عملکرد بهینه توضیح داده شده است.',
                'category': 'آنتن‌ها',
                'content_type': 'article'
            },
            {
                'title': 'اصول سیگنال‌های رادیویی و کاربردهای آن',
                'content': 'سیگنال‌های رادیویی یکی از مهم‌ترین روش‌های انتقال اطلاعات در دنیای امروز هستند. در این محتوا به بررسی اصول فیزیکی سیگنال‌های رادیویی و کاربردهای مهم آن‌ها می‌پردازیم.',
                'category': 'مبانی ارتباطات رادیویی',
                'content_type': 'article'
            },
            {
                'title': 'نحوه عیب‌یابی تجهیزات RF',
                'content': 'عیب‌یابی تجهیزات RF نیازمند دانش تخصصی و ابزارهای مناسب است. در این آموزش مراحل استاندارد عیب‌یابی تجهیزات RF و نکات کلیدی که باید رعایت شوند، تشریح شده است.',
                'category': 'تعمیر و نگهداری',
                'content_type': 'tutorial'
            }
        ]
        
        for ec_data in educational_contents:
            if not EducationalContent.query.filter_by(title=ec_data['title']).first():
                ec = EducationalContent(
                    title=ec_data['title'],
                    content=ec_data['content'],
                    category=ec_data['category'],
                    content_type=ec_data['content_type'],
                    type=ec_data['content_type']  # type is a duplicate of content_type for backward compatibility
                )
                db.session.add(ec)
                logger.info(f"محتوای آموزشی '{ec_data['title']}' ایجاد شد")
        
        db.session.commit()
        logger.info("فرآیند اضافه کردن داده‌های نمونه با موفقیت انجام شد")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"خطا در افزودن داده‌های نمونه: {str(e)}")
        return False

if __name__ == "__main__":
    # اجرای اسکریپت
    from src.web.app import app
    with app.app_context():
        success = seed_database()
        if success:
            print("داده‌های نمونه با موفقیت به پایگاه داده اضافه شدند.")
        else:
            print("خطا در افزودن داده‌های نمونه!")