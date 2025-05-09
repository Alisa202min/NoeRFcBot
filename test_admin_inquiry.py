#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest
import tempfile
from datetime import datetime, timedelta
from flask_testing import TestCase

# افزودن مسیر فعلی به پایتون پث
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ایمپورت ماژول‌های مورد نیاز
from app import app, db
from models import User, Inquiry, Product, Category

class AdminInquiryTest(TestCase):
    """تست‌های مربوط به مدیریت استعلام قیمت در پنل ادمین"""
    
    def create_app(self):
        """ایجاد نمونه اپلیکیشن برای تست"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app
    
    def setUp(self):
        """تنظیمات قبل از اجرای هر تست"""
        db.create_all()
        self._create_test_data()
    
    def tearDown(self):
        """پاکسازی پس از اجرای هر تست"""
        db.session.remove()
        db.drop_all()
    
    def _create_test_data(self):
        """ایجاد داده‌های آزمایشی برای تست"""
        # ایجاد کاربر ادمین
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('adminpassword')
        db.session.add(admin)
        
        # ایجاد کاربر عادی
        user = User(username='user', email='user@example.com', is_admin=False)
        user.set_password('userpassword')
        db.session.add(user)
        
        # ایجاد دسته‌بندی‌ها
        product_category = Category(name='دسته محصول تست', cat_type='product')
        service_category = Category(name='دسته خدمت تست', cat_type='service')
        db.session.add(product_category)
        db.session.add(service_category)
        db.session.commit()
        
        # ایجاد محصولات
        product1 = Product(
            name='محصول تست 1',
            price=1000000,
            description='توضیحات محصول تست 1',
            category_id=product_category.id,
            product_type='product',
            featured=True,
            tags='رادیویی,مخابراتی'
        )
        
        product2 = Product(
            name='محصول تست 2',
            price=2000000, 
            description='توضیحات محصول تست 2',
            category_id=product_category.id,
            product_type='product',
            featured=False,
            tags='رادیویی,تست'
        )
        
        # ایجاد خدمات
        service1 = Product(
            name='خدمت تست 1',
            price=500000,
            description='توضیحات خدمت تست 1',
            category_id=service_category.id,
            product_type='service',
            featured=True,
            tags='نصب,راه‌اندازی'
        )
        
        service2 = Product(
            name='خدمت تست 2',
            price=750000,
            description='توضیحات خدمت تست 2',
            category_id=service_category.id,
            product_type='service',
            featured=False,
            tags='تعمیر,نگهداری'
        )
        
        db.session.add_all([product1, product2, service1, service2])
        db.session.commit()
        
        # ایجاد استعلام‌های قیمت
        now = datetime.now()
        
        # استعلام برای محصول 1
        inquiry1 = Inquiry(
            user_id=12345,
            name='علی رضایی',
            phone='09123456789',
            description='استعلام قیمت محصول تست 1',
            product_id=product1.id,
            product_type='product',
            created_at=now - timedelta(days=1)
        )
        
        # استعلام برای محصول 2
        inquiry2 = Inquiry(
            user_id=23456,
            name='رضا احمدی',
            phone='09123456790',
            description='استعلام قیمت محصول تست 2',
            product_id=product2.id,
            product_type='product',
            created_at=now - timedelta(hours=12)
        )
        
        # استعلام برای خدمت 1
        inquiry3 = Inquiry(
            user_id=34567,
            name='محمد جعفری',
            phone='09123456791',
            description='استعلام قیمت خدمت تست 1',
            product_id=service1.id,
            product_type='service',
            created_at=now - timedelta(hours=6)
        )
        
        # استعلام برای خدمت 2
        inquiry4 = Inquiry(
            user_id=45678,
            name='محسن کریمی',
            phone='09123456792',
            description='استعلام قیمت خدمت تست 2',
            product_id=service2.id,
            product_type='service',
            created_at=now - timedelta(hours=2)
        )
        
        db.session.add_all([inquiry1, inquiry2, inquiry3, inquiry4])
        db.session.commit()
    
    def login(self, username, password):
        """ورود کاربر"""
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
    
    def logout(self):
        """خروج کاربر"""
        return self.client.get('/logout', follow_redirects=True)
    
    def test_admin_login_access(self):
        """تست دسترسی ادمین به صفحه استعلام‌ها"""
        # ورود با کاربر ادمین
        response = self.login('admin', 'adminpassword')
        self.assertIn(b'welcome', response.data.lower())
        
        # دسترسی به صفحه لیست استعلام‌ها
        response = self.client.get('/admin/inquiries')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود نام استعلام‌کنندگان در صفحه
        self.assertIn(b'\xd8\xb9\xd9\x84\xdb\x8c \xd8\xb1\xd8\xb6\xd8\xa7\xdb\x8c\xdb\x8c', response.data)  # علی رضایی
        self.assertIn(b'\xd8\xb1\xd8\xb6\xd8\xa7 \xd8\xa7\xd8\xad\xd9\x85\xd8\xaf\xdb\x8c', response.data)  # رضا احمدی
        self.assertIn(b'\xd9\x85\xd8\xad\xd9\x85\xd8\xaf \xd8\xac\xd8\xb9\xd9\x81\xd8\xb1\xdb\x8c', response.data)  # محمد جعفری
    
    def test_non_admin_blocked(self):
        """تست محدودیت دسترسی کاربر غیر ادمین"""
        # ورود با کاربر عادی
        response = self.login('user', 'userpassword')
        self.assertIn(b'welcome', response.data.lower())
        
        # تلاش برای دسترسی به صفحه لیست استعلام‌ها
        response = self.client.get('/admin/inquiries', follow_redirects=True)
        
        # کاربر باید به یک صفحه خطا هدایت شود
        self.assertIn(b'\xd8\xb4\xd9\x85\xd8\xa7 \xd8\xaf\xd8\xb3\xd8\xaa\xd8\xb1\xd8\xb3\xdb\x8c \xd9\x85\xd8\xaf\xdb\x8c\xd8\xb1\xdb\x8c\xd8\xaa\xdb\x8c \xd9\x86\xd8\xaf\xd8\xa7\xd8\xb1\xdb\x8c\xd8\xaf', response.data)  # شما دسترسی مدیریتی ندارید
    
    def test_guest_blocked(self):
        """تست محدودیت دسترسی کاربر مهمان"""
        # بدون ورود، تلاش برای دسترسی به صفحه لیست استعلام‌ها
        response = self.client.get('/admin/inquiries', follow_redirects=True)
        
        # کاربر باید به صفحه ورود هدایت شود
        self.assertIn(b'login', response.data.lower())
    
    def test_inquiry_detail_page(self):
        """تست صفحه جزئیات استعلام قیمت"""
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # پیدا کردن استعلام محصول اول
        inquiry = Inquiry.query.filter_by(name='علی رضایی').first()
        
        # دسترسی به صفحه جزئیات استعلام
        response = self.client.get(f'/admin/inquiry/{inquiry.id}')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود اطلاعات استعلام در صفحه
        self.assertIn(b'\xd8\xb9\xd9\x84\xdb\x8c \xd8\xb1\xd8\xb6\xd8\xa7\xdb\x8c\xdb\x8c', response.data)  # علی رضایی
        self.assertIn(b'09123456789', response.data)
        self.assertIn(b'\xd8\xa7\xd8\xb3\xd8\xaa\xd8\xb9\xd9\x84\xd8\xa7\xd9\x85 \xd9\x82\xdb\x8c\xd9\x85\xd8\xaa \xd9\x85\xd8\xad\xd8\xb5\xd9\x88\xd9\x84 \xd8\xaa\xd8\xb3\xd8\xaa 1', response.data)  # استعلام قیمت محصول تست 1
    
    def test_filter_by_product_type(self):
        """تست فیلتر استعلام‌ها بر اساس نوع محصول"""
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # فیلتر استعلام‌های محصول
        response = self.client.get('/admin/inquiries?type=product')
        self.assertEqual(response.status_code, 200)
        
        # باید شامل استعلام‌های محصول باشد
        self.assertIn(b'\xd8\xb9\xd9\x84\xdb\x8c \xd8\xb1\xd8\xb6\xd8\xa7\xdb\x8c\xdb\x8c', response.data)  # علی رضایی
        self.assertIn(b'\xd8\xb1\xd8\xb6\xd8\xa7 \xd8\xa7\xd8\xad\xd9\x85\xd8\xaf\xdb\x8c', response.data)  # رضا احمدی
        
        # نباید شامل استعلام‌های خدمات باشد
        self.assertNotIn(b'\xd9\x85\xd8\xad\xd9\x85\xd8\xaf \xd8\xac\xd8\xb9\xd9\x81\xd8\xb1\xdb\x8c', response.data)  # محمد جعفری
    
    def test_filter_by_service_type(self):
        """تست فیلتر استعلام‌ها بر اساس نوع خدمت"""
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # فیلتر استعلام‌های خدمت
        response = self.client.get('/admin/inquiries?type=service')
        self.assertEqual(response.status_code, 200)
        
        # باید شامل استعلام‌های خدمت باشد
        self.assertIn(b'\xd9\x85\xd8\xad\xd9\x85\xd8\xaf \xd8\xac\xd8\xb9\xd9\x81\xd8\xb1\xdb\x8c', response.data)  # محمد جعفری
        self.assertIn(b'\xd9\x85\xd8\xad\xd8\xb3\xd9\x86 \xda\xa9\xd8\xb1\xdb\x8c\xd9\x85\xdb\x8c', response.data)  # محسن کریمی
        
        # نباید شامل استعلام‌های محصول باشد
        self.assertNotIn(b'\xd8\xb9\xd9\x84\xdb\x8c \xd8\xb1\xd8\xb6\xd8\xa7\xdb\x8c\xdb\x8c', response.data)  # علی رضایی
    
    def test_filter_by_date(self):
        """تست فیلتر استعلام‌ها بر اساس تاریخ"""
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # تاریخ امروز
        today = datetime.now().strftime('%Y-%m-%d')
        
        # فیلتر استعلام‌های امروز
        response = self.client.get(f'/admin/inquiries?date={today}')
        self.assertEqual(response.status_code, 200)
        
        # استعلام‌های امروز باید نمایش داده شوند
        self.assertIn(b'\xd8\xb1\xd8\xb6\xd8\xa7 \xd8\xa7\xd8\xad\xd9\x85\xd8\xaf\xdb\x8c', response.data)  # رضا احمدی
        self.assertIn(b'\xd9\x85\xd8\xad\xd9\x85\xd8\xaf \xd8\xac\xd8\xb9\xd9\x81\xd8\xb1\xdb\x8c', response.data)  # محمد جعفری
        
        # استعلام‌های قدیمی‌تر (دیروز) نباید نمایش داده شوند
        self.assertNotIn(b'\xd8\xb9\xd9\x84\xdb\x8c \xd8\xb1\xd8\xb6\xd8\xa7\xdb\x8c\xdb\x8c', response.data)  # علی رضایی
    
    def test_inquiry_delete(self):
        """تست حذف استعلام قیمت"""
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # پیدا کردن استعلام اول
        inquiry = Inquiry.query.filter_by(name='علی رضایی').first()
        inquiry_id = inquiry.id
        
        # حذف استعلام
        response = self.client.post(f'/admin/inquiry/delete/{inquiry_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # بررسی حذف شدن استعلام از دیتابیس
        inquiry = Inquiry.query.get(inquiry_id)
        self.assertIsNone(inquiry)
        
        # بررسی نمایش پیام موفقیت
        self.assertIn(b'success', response.data.lower())
    
    def test_inquiry_export(self):
        """تست خروجی گرفتن از استعلام‌ها"""
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # درخواست خروجی CSV
        response = self.client.get('/admin/inquiries/export')
        self.assertEqual(response.status_code, 200)
        
        # بررسی هدر های CSV
        self.assertEqual(response.content_type, 'text/csv')
        self.assertIn('attachment; filename=', response.headers['Content-Disposition'])
        
        # بررسی محتوای فایل CSV
        csv_data = response.data.decode('utf-8')
        self.assertIn('علی رضایی', csv_data)
        self.assertIn('09123456789', csv_data)
        self.assertIn('رضا احمدی', csv_data)
        self.assertIn('محمد جعفری', csv_data)


if __name__ == '__main__':
    unittest.main()