#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست API و مسیرهای وب‌سایت
این اسکریپت مسیرهای مختلف وب‌سایت و API را تست می‌کند
"""

import unittest
import json
import sys
import os
import logging
from urllib.parse import urlencode
# Import project modules
from src.web.app import app, db
from models import User,  Product, Service, Inquiry, EducationalContent, StaticContent

# اضافه کردن مسیر پروژه به PYTHONPATH برای دسترسی به ماژول‌های پروژه
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestAPIEndpoints(unittest.TestCase):
    """کلاس تست برای بررسی مسیرهای API و وب‌سایت"""
    
    def setUp(self):
        """تنظیمات اولیه قبل از هر تست"""
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # اضافه کردن داده‌های تست اگر نیاز است
        with app.app_context():
            # اطمینان از وجود محتوای استاتیک در دیتابیس برای تست
            if not StaticContent.query.filter_by(content_type='about').first():
                about_content = StaticContent(content_type='about', 
                                            content='این متن درباره ماست')
                db.session.add(about_content)
                
            if not StaticContent.query.filter_by(content_type='contact').first():
                contact_content = StaticContent(content_type='contact', 
                                               content='اطلاعات تماس ما')
                db.session.add(contact_content)
                
            db.session.commit()
    
    def tearDown(self):
        """نظافت بعد از اتمام هر تست"""
        self.app_context.pop()
    
    def test_home_page(self):
        """تست صفحه اصلی"""
        print("\n=== تست صفحه اصلی ===")
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200, "صفحه اصلی باید قابل دسترسی باشد")
        self.assertIn(b'<!DOCTYPE html>', response.data, "صفحه اصلی باید HTML باشد")
        print("✓ صفحه اصلی با موفقیت لود شد")
    
    def test_admin_login_page(self):
        """تست صفحه ورود ادمین"""
        print("\n=== تست صفحه ورود ادمین ===")
        response = self.client.get('/admin/login')
        self.assertEqual(response.status_code, 200, "صفحه ورود ادمین باید قابل دسترسی باشد")
        self.assertIn(b'<!DOCTYPE html>', response.data, "صفحه ورود باید HTML باشد")
        self.assertIn(b'login', response.data.lower(), "صفحه باید شامل فرم ورود باشد")
        print("✓ صفحه ورود ادمین با موفقیت لود شد")
    
    def test_admin_without_auth(self):
        """تست صفحات ادمین بدون احراز هویت"""
        print("\n=== تست صفحات ادمین بدون احراز هویت ===")
        admin_pages = [
            '/admin/',
            '/admin/dashboard',
            '/admin/categories',
            '/admin/products',
            '/admin/services',
            '/admin/inquiries',
            '/admin/educational',
            '/admin/content'
        ]
        
        for page in admin_pages:
            response = self.client.get(page)
            self.assertIn(response.status_code, [302, 401, 403], 
                         f"صفحه {page} باید کاربر را به صفحه ورود ریدایرکت کند")
            print(f"✓ صفحه {page} بدون احراز هویت به درستی رد شد")
    
    def test_admin_login(self):
        """تست ورود به پنل ادمین"""
        print("\n=== تست ورود به پنل ادمین ===")
        response = self.client.post('/admin/login', data={
            'username': 'admin',
            'password': 'password123'
        }, follow_redirects=True)
        
        # بررسی وضعیت ورود (موفق یا ناموفق)
        if response.status_code == 200 and b'dashboard' in response.data.lower():
            print("✓ ورود به پنل ادمین موفق بود")
        else:
            print("× ورود به پنل ادمین موفق نبود (احتمالاً به دلیل نام کاربری یا رمز عبور نادرست)")
    
    def test_about_page(self):
        """تست صفحه درباره ما"""
        print("\n=== تست صفحه درباره ما ===")
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200, "صفحه درباره ما باید قابل دسترسی باشد")
        # بررسی وجود محتوای استاتیک درباره ما
        about_content = StaticContent.query.filter_by(content_type='about').first()
        if about_content:
            # تنها بخشی از محتوا را بررسی می‌کنیم چون ممکن است با HTML ترکیب شده باشد
            content_snippet = about_content.content[:20].encode('utf-8')
            self.assertIn(content_snippet, response.data, "محتوای درباره ما باید در صفحه نمایش داده شود")
        print("✓ صفحه درباره ما با موفقیت لود شد")
    
    def test_contact_page(self):
        """تست صفحه تماس با ما"""
        print("\n=== تست صفحه تماس با ما ===")
        response = self.client.get('/contact')
        self.assertEqual(response.status_code, 200, "صفحه تماس با ما باید قابل دسترسی باشد")
        # بررسی وجود محتوای استاتیک تماس با ما
        contact_content = StaticContent.query.filter_by(content_type='contact').first()
        if contact_content:
            # تنها بخشی از محتوا را بررسی می‌کنیم چون ممکن است با HTML ترکیب شده باشد
            content_snippet = contact_content.content[:20].encode('utf-8')
            self.assertIn(content_snippet, response.data, "محتوای تماس با ما باید در صفحه نمایش داده شود")
        print("✓ صفحه تماس با ما با موفقیت لود شد")
    
    def test_products_page(self):
        """تست صفحه محصولات"""
        print("\n=== تست صفحه محصولات ===")
        response = self.client.get('/products')
        self.assertEqual(response.status_code, 200, "صفحه محصولات باید قابل دسترسی باشد")
        
        # بررسی وجود محصولات در دیتابیس
        products_count = Product.query.count()
        print(f"تعداد محصولات در دیتابیس: {products_count}")
        
        # تست گرفتن محصولات دسته‌بندی خاص
        categories = Category.query.filter_by(cat_type='product').all()
        if categories:
            category = categories[0]
            response = self.client.get(f'/products?category_id={category.id}')
            self.assertEqual(response.status_code, 200, f"صفحه محصولات دسته {category.name} باید قابل دسترسی باشد")
            print(f"✓ صفحه محصولات دسته {category.name} با موفقیت لود شد")
        
        print("✓ صفحه محصولات با موفقیت لود شد")
    
    def test_services_page(self):
        """تست صفحه خدمات"""
        print("\n=== تست صفحه خدمات ===")
        response = self.client.get('/services')
        self.assertEqual(response.status_code, 200, "صفحه خدمات باید قابل دسترسی باشد")
        
        # بررسی وجود خدمات در دیتابیس
        services_count = Service.query.count()
        print(f"تعداد خدمات در دیتابیس: {services_count}")
        
        # تست گرفتن خدمات دسته‌بندی خاص
        categories = Category.query.filter_by(cat_type='service').all()
        if categories:
            category = categories[0]
            response = self.client.get(f'/services?category_id={category.id}')
            self.assertEqual(response.status_code, 200, f"صفحه خدمات دسته {category.name} باید قابل دسترسی باشد")
            print(f"✓ صفحه خدمات دسته {category.name} با موفقیت لود شد")
        
        print("✓ صفحه خدمات با موفقیت لود شد")
    
    def test_educational_content_page(self):
        """تست صفحه محتوای آموزشی"""
        print("\n=== تست صفحه محتوای آموزشی ===")
        response = self.client.get('/educational')
        self.assertEqual(response.status_code, 200, "صفحه محتوای آموزشی باید قابل دسترسی باشد")
        
        # بررسی وجود محتوای آموزشی در دیتابیس
        content_count = EducationalContent.query.count()
        print(f"تعداد محتوای آموزشی در دیتابیس: {content_count}")
        
        # تست گرفتن محتوای آموزشی دسته خاص
        categories = db.session.query(EducationalContent.category).distinct().all()
        if categories:
            category = categories[0][0]
            response = self.client.get(f'/educational?category={category}')
            self.assertEqual(response.status_code, 200, f"صفحه محتوای آموزشی دسته {category} باید قابل دسترسی باشد")
            print(f"✓ صفحه محتوای آموزشی دسته {category} با موفقیت لود شد")
        
        print("✓ صفحه محتوای آموزشی با موفقیت لود شد")
    
    def test_product_detail_page(self):
        """تست صفحه جزئیات محصول"""
        print("\n=== تست صفحه جزئیات محصول ===")
        # یافتن یک محصول برای تست
        product = Product.query.first()
        if product:
            response = self.client.get(f'/product/{product.id}')
            self.assertEqual(response.status_code, 200, f"صفحه جزئیات محصول {product.name} باید قابل دسترسی باشد")
            self.assertIn(product.name.encode('utf-8'), response.data, "نام محصول باید در صفحه نمایش داده شود")
            print(f"✓ صفحه جزئیات محصول {product.name} با موفقیت لود شد")
        else:
            print("× هیچ محصولی در دیتابیس یافت نشد")
    
    def test_service_detail_page(self):
        """تست صفحه جزئیات خدمت"""
        print("\n=== تست صفحه جزئیات خدمت ===")
        # یافتن یک خدمت برای تست
        service = Service.query.first()
        if service:
            response = self.client.get(f'/service/{service.id}')
            self.assertEqual(response.status_code, 200, f"صفحه جزئیات خدمت {service.name} باید قابل دسترسی باشد")
            self.assertIn(service.name.encode('utf-8'), response.data, "نام خدمت باید در صفحه نمایش داده شود")
            print(f"✓ صفحه جزئیات خدمت {service.name} با موفقیت لود شد")
        else:
            print("× هیچ خدمتی در دیتابیس یافت نشد")
    
    def test_educational_content_detail_page(self):
        """تست صفحه جزئیات محتوای آموزشی"""
        print("\n=== تست صفحه جزئیات محتوای آموزشی ===")
        # یافتن یک محتوای آموزشی برای تست
        content = EducationalContent.query.first()
        if content:
            response = self.client.get(f'/educational/{content.id}')
            self.assertEqual(response.status_code, 200, f"صفحه جزئیات محتوای آموزشی {content.title} باید قابل دسترسی باشد")
            self.assertIn(content.title.encode('utf-8'), response.data, "عنوان محتوای آموزشی باید در صفحه نمایش داده شود")
            print(f"✓ صفحه جزئیات محتوای آموزشی {content.title} با موفقیت لود شد")
        else:
            print("× هیچ محتوای آموزشی در دیتابیس یافت نشد")
    
    def test_search_page(self):
        """تست صفحه جستجو"""
        print("\n=== تست صفحه جستجو ===")
        # تست جستجوی ساده
        response = self.client.get('/search?q=تست')
        self.assertEqual(response.status_code, 200, "صفحه جستجو باید قابل دسترسی باشد")
        print("✓ صفحه جستجوی ساده با موفقیت لود شد")
        
        # تست جستجوی پیشرفته
        search_params = {
            'q': 'تست',
            'category_id': '1',
            'min_price': '1000',
            'max_price': '100000',
            'product_type': 'product'
        }
        response = self.client.get(f'/search?{urlencode(search_params)}')
        self.assertEqual(response.status_code, 200, "صفحه جستجوی پیشرفته باید قابل دسترسی باشد")
        print("✓ صفحه جستجوی پیشرفته با موفقیت لود شد")
    
    def test_nonexistent_page(self):
        """تست صفحه‌ای که وجود ندارد"""
        print("\n=== تست صفحه‌ای که وجود ندارد ===")
        response = self.client.get('/nonexistent_page')
        self.assertEqual(response.status_code, 404, "صفحه‌ای که وجود ندارد باید کد 404 برگرداند")
        print("✓ صفحه‌ای که وجود ندارد به درستی کد 404 برگرداند")
    
    def test_api_categories(self):
        """تست API دسته‌بندی‌ها"""
        print("\n=== تست API دسته‌بندی‌ها ===")
        # تست API دسته‌بندی‌های محصولات
        response = self.client.get('/api/categories?type=product')
        self.assertEqual(response.status_code, 200, "API دسته‌بندی‌های محصولات باید قابل دسترسی باشد")
        try:
            data = json.loads(response.data)
            self.assertIsInstance(data, list, "خروجی API باید یک لیست باشد")
            print(f"✓ API دسته‌بندی‌های محصولات {len(data)} دسته‌بندی برگرداند")
        except json.JSONDecodeError:
            self.fail("خروجی API باید JSON معتبر باشد")
        
        # تست API دسته‌بندی‌های خدمات
        response = self.client.get('/api/categories?type=service')
        self.assertEqual(response.status_code, 200, "API دسته‌بندی‌های خدمات باید قابل دسترسی باشد")
        try:
            data = json.loads(response.data)
            self.assertIsInstance(data, list, "خروجی API باید یک لیست باشد")
            print(f"✓ API دسته‌بندی‌های خدمات {len(data)} دسته‌بندی برگرداند")
        except json.JSONDecodeError:
            self.fail("خروجی API باید JSON معتبر باشد")
    
    def test_api_products(self):
        """تست API محصولات"""
        print("\n=== تست API محصولات ===")
        response = self.client.get('/api/products')
        self.assertEqual(response.status_code, 200, "API محصولات باید قابل دسترسی باشد")
        try:
            data = json.loads(response.data)
            self.assertIsInstance(data, list, "خروجی API باید یک لیست باشد")
            print(f"✓ API محصولات {len(data)} محصول برگرداند")
        except json.JSONDecodeError:
            self.fail("خروجی API باید JSON معتبر باشد")
        
        # تست API محصولات با دسته‌بندی خاص
        categories = Category.query.filter_by(cat_type='product').all()
        if categories:
            category = categories[0]
            response = self.client.get(f'/api/products?category_id={category.id}')
            self.assertEqual(response.status_code, 200, f"API محصولات دسته {category.name} باید قابل دسترسی باشد")
            try:
                data = json.loads(response.data)
                self.assertIsInstance(data, list, "خروجی API باید یک لیست باشد")
                print(f"✓ API محصولات دسته {category.name} با {len(data)} محصول برگرداند")
            except json.JSONDecodeError:
                self.fail("خروجی API باید JSON معتبر باشد")
    
    def test_api_services(self):
        """تست API خدمات"""
        print("\n=== تست API خدمات ===")
        response = self.client.get('/api/services')
        self.assertEqual(response.status_code, 200, "API خدمات باید قابل دسترسی باشد")
        try:
            data = json.loads(response.data)
            self.assertIsInstance(data, list, "خروجی API باید یک لیست باشد")
            print(f"✓ API خدمات {len(data)} خدمت برگرداند")
        except json.JSONDecodeError:
            self.fail("خروجی API باید JSON معتبر باشد")
        
        # تست API خدمات با دسته‌بندی خاص
        categories = Category.query.filter_by(cat_type='service').all()
        if categories:
            category = categories[0]
            response = self.client.get(f'/api/services?category_id={category.id}')
            self.assertEqual(response.status_code, 200, f"API خدمات دسته {category.name} باید قابل دسترسی باشد")
            try:
                data = json.loads(response.data)
                self.assertIsInstance(data, list, "خروجی API باید یک لیست باشد")
                print(f"✓ API خدمات دسته {category.name} با {len(data)} خدمت برگرداند")
            except json.JSONDecodeError:
                self.fail("خروجی API باید JSON معتبر باشد")
    
    def test_api_educational(self):
        """تست API محتوای آموزشی"""
        print("\n=== تست API محتوای آموزشی ===")
        response = self.client.get('/api/educational')
        self.assertEqual(response.status_code, 200, "API محتوای آموزشی باید قابل دسترسی باشد")
        try:
            data = json.loads(response.data)
            self.assertIsInstance(data, list, "خروجی API باید یک لیست باشد")
            print(f"✓ API محتوای آموزشی {len(data)} محتوا برگرداند")
        except json.JSONDecodeError:
            self.fail("خروجی API باید JSON معتبر باشد")
        
        # تست API محتوای آموزشی با دسته خاص
        categories = db.session.query(EducationalContent.category).distinct().all()
        if categories:
            category = categories[0][0]
            response = self.client.get(f'/api/educational?category={category}')
            self.assertEqual(response.status_code, 200, f"API محتوای آموزشی دسته {category} باید قابل دسترسی باشد")
            try:
                data = json.loads(response.data)
                self.assertIsInstance(data, list, "خروجی API باید یک لیست باشد")
                print(f"✓ API محتوای آموزشی دسته {category} با {len(data)} محتوا برگرداند")
            except json.JSONDecodeError:
                self.fail("خروجی API باید JSON معتبر باشد")

def run_tests():
    """اجرای همه تست‌ها"""
    unittest.main()

if __name__ == "__main__":
    run_tests()