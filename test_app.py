#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اسکریپت بررسی دیتابیس و مسیرهای API
"""

import os
import sys
import logging
from app import app
from models import  Product, Service, Inquiry, EducationalContent, StaticContent

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database():
    """بررسی محتوای دیتابیس"""
    with app.app_context():
        print("\n=== بررسی دسته‌بندی‌ها ===")
        categories = Category.query.all()
        print(f"تعداد کل دسته‌بندی‌ها: {len(categories)}")
        
        for cat in categories:
            print(f"ID: {cat.id}, نام: {cat.name}, نوع: {cat.cat_type}, " +
                  f"والد: {cat.parent_id}")
        
        print("\n=== بررسی محصولات ===")
        products = Product.query.all()
        print(f"تعداد کل محصولات: {len(products)}")
        
        for prod in products[:5]:  # نمایش 5 محصول اول
            print(f"ID: {prod.id}, نام: {prod.name}, دسته: {prod.category_id}, " + 
                  f"قیمت: {prod.price}")
        
        print("\n=== بررسی خدمات ===")
        services = Service.query.all()
        print(f"تعداد کل خدمات: {len(services)}")
        
        for serv in services[:5]:  # نمایش 5 خدمت اول
            print(f"ID: {serv.id}, نام: {serv.name}, دسته: {serv.category_id}, " + 
                  f"قیمت: {serv.price}")
        
        print("\n=== بررسی استعلام‌ها ===")
        inquiries = Inquiry.query.all()
        print(f"تعداد کل استعلام‌ها: {len(inquiries)}")
        
        for inq in inquiries[:5]:  # نمایش 5 استعلام اول
            inquiry_type = "محصول" if inq.is_product_inquiry() else "خدمت" if inq.is_service_inquiry() else "عمومی"
            related_id = inq.product_id if inq.is_product_inquiry() else inq.service_id if inq.is_service_inquiry() else "N/A"
            print(f"ID: {inq.id}, نام: {inq.name}, تلفن: {inq.phone}, " + 
                  f"شناسه: {related_id} (نوع: {inquiry_type})")
        
        print("\n=== بررسی محتوای آموزشی ===")
        contents = EducationalContent.query.all()
        print(f"تعداد کل محتوای آموزشی: {len(contents)}")
        
        for content in contents[:5]:  # نمایش 5 محتوا اول
            print(f"ID: {content.id}, عنوان: {content.title}, دسته: {content.category}, " + 
                  f"نوع: {content.content_type}")
        
        print("\n=== بررسی محتوای استاتیک ===")
        static_contents = StaticContent.query.all()
        print(f"تعداد کل محتوای استاتیک: {len(static_contents)}")
        
        for static in static_contents:
            print(f"نوع: {static.content}, به‌روزرسانی: {static.updated_at}")

def check_api_routes():
    """بررسی مسیرهای API"""
    import requests
    
    base_url = "http://localhost:5000"
    
    print("\n=== بررسی API دسته‌بندی‌ها ===")
    response = requests.get(f"{base_url}/api/categories?type=product")
    print(f"وضعیت پاسخ: {response.status_code}")
    print(f"محتوای پاسخ: {response.text[:100]}...")
    
    print("\n=== بررسی API محصولات ===")
    response = requests.get(f"{base_url}/api/products")
    print(f"وضعیت پاسخ: {response.status_code}")
    print(f"محتوای پاسخ: {response.text[:100]}...")
    
    print("\n=== بررسی API خدمات ===")
    response = requests.get(f"{base_url}/api/services")
    print(f"وضعیت پاسخ: {response.status_code}")
    print(f"محتوای پاسخ: {response.text[:100]}...")
    
    print("\n=== بررسی API محتوای آموزشی ===")
    response = requests.get(f"{base_url}/api/educational")
    print(f"وضعیت پاسخ: {response.status_code}")
    print(f"محتوای پاسخ: {response.text[:100]}...")

def check_web_routes():
    """بررسی مسیرهای وب‌سایت"""
    import requests
    
    base_url = "http://localhost:5000"
    
    print("\n=== بررسی صفحه اصلی ===")
    response = requests.get(f"{base_url}/")
    print(f"وضعیت پاسخ: {response.status_code}")
    print(f"طول پاسخ: {len(response.text)} بایت")
    
    print("\n=== بررسی صفحه محصولات ===")
    response = requests.get(f"{base_url}/products")
    print(f"وضعیت پاسخ: {response.status_code}")
    print(f"طول پاسخ: {len(response.text)} بایت")
    
    print("\n=== بررسی صفحه خدمات ===")
    response = requests.get(f"{base_url}/services")
    print(f"وضعیت پاسخ: {response.status_code}")
    print(f"طول پاسخ: {len(response.text)} بایت")
    
    print("\n=== بررسی صفحه ورود ادمین ===")
    response = requests.get(f"{base_url}/admin/login")
    print(f"وضعیت پاسخ: {response.status_code}")
    print(f"طول پاسخ: {len(response.text)} بایت")
    
    # تست درخواست پنل ادمین بدون لاگین
    print("\n=== بررسی دسترسی به پنل ادمین بدون لاگین ===")
    response = requests.get(f"{base_url}/admin/", allow_redirects=False)
    print(f"وضعیت پاسخ: {response.status_code}")
    print(f"آدرس ریدایرکت: {response.headers.get('Location')}" if response.status_code in [301, 302, 303, 307, 308] else "بدون ریدایرکت")

def main():
    """تابع اصلی"""
    try:
        check_database()
        check_api_routes()
        check_web_routes()
    except Exception as e:
        logger.error(f"خطا در بررسی برنامه: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()