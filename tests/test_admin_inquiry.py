#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest
import io
import csv
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
            tags='رادیویی,مخابراتی',
            in_stock=True,
            brand='برند تست',
            model='مدل تست 1'
        )
        
        product2 = Product(
            name='محصول تست 2',
            price=2000000, 
            description='توضیحات محصول تست 2',
            category_id=product_category.id,
            product_type='product',
            featured=False,
            tags='رادیویی,تست',
            in_stock=True,
            brand='برند تست',
            model='مدل تست 2'
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
        
        # استعلام عمومی (بدون محصول/خدمت خاص)
        inquiry5 = Inquiry(
            user_id=56789,
            name='امیر محمدی',
            phone='09123456793',
            description='استعلام قیمت عمومی',
            product_type='general',
            created_at=now - timedelta(hours=1)
        )
        
        db.session.add_all([inquiry1, inquiry2, inquiry3, inquiry4, inquiry5])
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
        
        # دسترسی به صفحه داشبورد پنل مدیریت
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود منوی پنل مدیریت
        self.assertIn(b'\xd9\x85\xd8\xaf\xdb\x8c\xd8\xb1\xdb\x8c\xd8\xaa', response.data)  # "مدیریت" در منوی سایدبار
        
        # دسترسی به صفحه لیست استعلام‌ها از طریق پنل مدیریت
        response = self.client.get('/admin/inquiries')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود عناصر اصلی صفحه
        self.assertIn(b'\xd8\xa7\xd8\xb3\xd8\xaa\xd8\xb9\xd9\x84\xd8\xa7\xd9\x85\xe2\x80\x8c\xd9\x87\xd8\xa7\xdb\x8c \xd9\x82\xdb\x8c\xd9\x85\xd8\xaa', response.data)  # استعلام‌های قیمت
        self.assertIn(b'\xd8\xae\xd8\xb1\xd9\x88\xd8\xac\xdb\x8c \xd8\xa7\xda\xa9\xd8\xb3\xd9\x84', response.data)  # خروجی اکسل
        
        # بررسی وجود نام استعلام‌کنندگان در صفحه
        self.assertIn(b'\xd8\xb9\xd9\x84\xdb\x8c \xd8\xb1\xd8\xb6\xd8\xa7\xdb\x8c\xdb\x8c', response.data)  # علی رضایی
        self.assertIn(b'09123456789', response.data)  # شماره تلفن علی رضایی
    
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
    
    def test_filter_by_date_range(self):
        """تست فیلتر استعلام‌ها بر اساس محدوده تاریخ"""
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # تاریخ امروز و دیروز
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # فیلتر استعلام‌های از دیروز تا امروز
        response = self.client.get(f'/admin/inquiries?start_date={yesterday}&end_date={today}')
        self.assertEqual(response.status_code, 200)
        
        # باید تمام استعلام‌ها نمایش داده شوند
        self.assertIn(b'\xd8\xb9\xd9\x84\xdb\x8c \xd8\xb1\xd8\xb6\xd8\xa7\xdb\x8c\xdb\x8c', response.data)  # علی رضایی
        self.assertIn(b'\xd8\xb1\xd8\xb6\xd8\xa7 \xd8\xa7\xd8\xad\xd9\x85\xd8\xaf\xdb\x8c', response.data)  # رضا احمدی
        self.assertIn(b'\xd9\x85\xd8\xad\xd9\x85\xd8\xaf \xd8\xac\xd8\xb9\xd9\x81\xd8\xb1\xdb\x8c', response.data)  # محمد جعفری
    
    def test_filter_by_product_id(self):
        """تست فیلتر استعلام‌ها بر اساس محصول"""
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # پیدا کردن شناسه محصول اول
        product = Product.query.filter_by(name='محصول تست 1').first()
        
        # فیلتر استعلام‌های محصول اول
        response = self.client.get(f'/admin/inquiries?product_id={product.id}')
        self.assertEqual(response.status_code, 200)
        
        # باید فقط استعلام مربوط به محصول اول نمایش داده شود
        self.assertIn(b'\xd8\xb9\xd9\x84\xdb\x8c \xd8\xb1\xd8\xb6\xd8\xa7\xdb\x8c\xdb\x8c', response.data)  # علی رضایی
        
        # نباید استعلام‌های دیگر نمایش داده شوند
        self.assertNotIn(b'\xd8\xb1\xd8\xb6\xd8\xa7 \xd8\xa7\xd8\xad\xd9\x85\xd8\xaf\xdb\x8c', response.data)  # رضا احمدی
        self.assertNotIn(b'\xd9\x85\xd8\xad\xd9\x85\xd8\xaf \xd8\xac\xd8\xb9\xd9\x81\xd8\xb1\xdb\x8c', response.data)  # محمد جعفری
    
    def test_reset_filters(self):
        """تست حذف فیلترها"""
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # ابتدا یک فیلتر اعمال می‌کنیم
        product = Product.query.filter_by(name='محصول تست 1').first()
        response = self.client.get(f'/admin/inquiries?product_id={product.id}')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود دکمه حذف فیلتر
        self.assertIn(b'\xd8\xad\xd8\xb0\xd9\x81 \xd9\x81\xdb\x8c\xd9\x84\xd8\xaa\xd8\xb1', response.data)  # حذف فیلتر
        
        # کلیک روی دکمه حذف فیلتر
        response = self.client.get('/admin/inquiries')
        self.assertEqual(response.status_code, 200)
        
        # باید تمام استعلام‌ها نمایش داده شوند
        self.assertIn(b'\xd8\xb9\xd9\x84\xdb\x8c \xd8\xb1\xd8\xb6\xd8\xa7\xdb\x8c\xdb\x8c', response.data)  # علی رضایی
        self.assertIn(b'\xd8\xb1\xd8\xb6\xd8\xa7 \xd8\xa7\xd8\xad\xd9\x85\xd8\xaf\xdb\x8c', response.data)  # رضا احمدی
    
    def test_view_inquiry_description(self):
        """تست مشاهده توضیحات استعلام"""
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # دسترسی به صفحه لیست استعلام‌ها
        response = self.client.get('/admin/inquiries')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود دکمه مشاهده توضیحات
        self.assertIn(b'\xd9\x85\xd8\xb4\xd8\xa7\xd9\x87\xd8\xaf\xd9\x87 \xd8\xaa\xd9\x88\xd8\xb6\xdb\x8c\xd8\xad\xd8\xa7\xd8\xaa', response.data)  # مشاهده توضیحات
        
        # بررسی وجود محتوای مدال توضیحات
        self.assertIn(b'\xd8\xaa\xd9\x88\xd8\xb6\xdb\x8c\xd8\xad\xd8\xa7\xd8\xaa \xd8\xa7\xd8\xb3\xd8\xaa\xd8\xb9\xd9\x84\xd8\xa7\xd9\x85', response.data)  # توضیحات استعلام
        self.assertIn(b'\xd8\xa7\xd8\xb3\xd8\xaa\xd8\xb9\xd9\x84\xd8\xa7\xd9\x85 \xd9\x82\xdb\x8c\xd9\x85\xd8\xaa \xd9\x85\xd8\xad\xd8\xb5\xd9\x88\xd9\x84 \xd8\xaa\xd8\xb3\xd8\xaa', response.data)  # استعلام قیمت محصول تست
    
    def test_inquiry_delete(self):
        """تست حذف استعلام قیمت"""
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # پیدا کردن استعلام اول
        inquiry = Inquiry.query.filter_by(name='علی رضایی').first()
        inquiry_id = inquiry.id
        
        # ارسال درخواست حذف
        response = self.client.post('/admin/inquiry/delete', data={'inquiry_id': inquiry_id}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # بررسی حذف شدن استعلام از دیتابیس
        inquiry = Inquiry.query.get(inquiry_id)
        self.assertIsNone(inquiry)
        
        # بررسی نمایش پیام موفقیت
        self.assertIn(b'success', response.data.lower())
    
    def test_inquiry_delete_confirmation(self):
        """تست مدال تایید حذف استعلام"""
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # بررسی وجود دکمه حذف و مدال تایید
        response = self.client.get('/admin/inquiries')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود دکمه حذف
        self.assertIn(b'data-bs-target="#deleteModal', response.data)
        
        # بررسی وجود مدال تایید حذف
        self.assertIn(b'\xd8\xaa\xd8\xa3\xdb\x8c\xdb\x8c\xd8\xaf \xd8\xad\xd8\xb0\xd9\x81', response.data)  # تأیید حذف
        self.assertIn(b'\xd8\xa2\xdb\x8c\xd8\xa7 \xd8\xa7\xd8\xb2 \xd8\xad\xd8\xb0\xd9\x81 \xd8\xa7\xdb\x8c\xd9\x86 \xd8\xa7\xd8\xb3\xd8\xaa\xd8\xb9\xd9\x84\xd8\xa7\xd9\x85 \xd8\xa7\xd8\xb7\xd9\x85\xdb\x8c\xd9\x86\xd8\xa7\xd9\x86 \xd8\xaf\xd8\xa7\xd8\xb1\xdb\x8c\xd8\xaf\xd8\x9f', response.data)  # آیا از حذف این استعلام اطمینان دارید؟
        self.assertIn(b'\xd8\xa8\xd9\x84\xd9\x87\xd8\x8c \xd8\xad\xd8\xb0\xd9\x81 \xd8\xb4\xd9\x88\xd8\xaf', response.data)  # بله، حذف شود
    
    def test_inquiry_export_excel(self):
        """تست خروجی اکسل از استعلام‌ها"""
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # درخواست خروجی اکسل
        response = self.client.get('/admin/inquiries/export')
        self.assertEqual(response.status_code, 200)
        
        # بررسی هدر های فایل
        self.assertIn('attachment; filename=', response.headers['Content-Disposition'])
        self.assertIn('csv', response.headers['Content-Disposition'].lower())
        
        # بررسی محتوای فایل CSV
        content = response.data.decode('utf-8')
        self.assertIn('نام', content)
        self.assertIn('شماره تماس', content)
        self.assertIn('محصول', content)
        self.assertIn('علی رضایی', content)
        self.assertIn('09123456789', content)
    
    def test_pagination(self):
        """تست صفحه‌بندی استعلام‌ها"""
        # ایجاد تعداد بیشتری استعلام برای تست صفحه‌بندی
        now = datetime.now()
        
        # ایجاد 15 استعلام دیگر
        for i in range(15):
            inquiry = Inquiry(
                user_id=100000 + i,
                name=f'کاربر تست {i}',
                phone=f'09100000{i:03d}',
                description=f'استعلام قیمت تست {i}',
                product_type='general',
                created_at=now - timedelta(minutes=i)
            )
            db.session.add(inquiry)
        
        db.session.commit()
        
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # بررسی صفحه اول
        response = self.client.get('/admin/inquiries')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود ناوبری صفحه‌بندی
        self.assertIn(b'pagination', response.data)
        
        # بررسی وجود لینک صفحه بعدی
        self.assertIn(b'\xd8\xa8\xd8\xb9\xd8\xaf\xdb\x8c', response.data)  # بعدی
        
        # بررسی صفحه دوم
        response = self.client.get('/admin/inquiries?page=2')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود لینک صفحه قبلی
        self.assertIn(b'\xd9\x82\xd8\xa8\xd9\x84\xdb\x8c', response.data)  # قبلی
    
    def test_empty_inquiries(self):
        """تست نمایش پیام خالی بودن لیست استعلام‌ها"""
        # حذف تمام استعلام‌ها
        Inquiry.query.delete()
        db.session.commit()
        
        # ورود با کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # بررسی صفحه استعلام‌ها
        response = self.client.get('/admin/inquiries')
        self.assertEqual(response.status_code, 200)
        
        # بررسی نمایش پیام خالی بودن
        self.assertIn(b'\xd9\x87\xdb\x8c\xda\x86 \xd8\xa7\xd8\xb3\xd8\xaa\xd8\xb9\xd9\x84\xd8\xa7\xd9\x85\xdb\x8c \xdb\x8c\xd8\xa7\xd9\x81\xd8\xaa \xd9\x86\xd8\xb4\xd8\xaf', response.data)  # هیچ استعلامی یافت نشد


if __name__ == '__main__':
    unittest.main()