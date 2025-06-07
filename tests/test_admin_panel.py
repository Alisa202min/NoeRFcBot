#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست جامع ادمین پنل
این اسکریپت تمام قابلیت‌های ادمین پنل را تست می‌کند
"""

import unittest
import os
import sys
import json
from datetime import datetime, timedelta
from flask import url_for
from app import app, db
from models import User, Category, Product, ProductMedia, Inquiry, EducationalContent, StaticContent
from werkzeug.security import generate_password_hash
from werkzeug.datastructures import FileStorage
from io import BytesIO

class TestAdminPanel(unittest.TestCase):
    """کلاس تست جامع برای ادمین پنل"""

    @classmethod
    def setUpClass(cls):
        """تنظیمات اولیه برای کلاس تست"""
        # تنظیم حالت تست برای فلاسک
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # غیرفعال کردن CSRF برای تست‌ها
        app.config['SERVER_NAME'] = 'localhost:5000'  # تنظیم نام سرور برای تولید URL
        
        # ایجاد دیتابیس موقت برای تست
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
        
        # ایجاد کلاینت تست
        cls.client = app.test_client()
        
        # ایجاد کانتکست برنامه
        cls.app_context = app.app_context()
        cls.app_context.push()
        
        # اجرای اسکریپت سیدینگ دیتابیس
        from seed_admin_data import main
        main()
        
        # ایجاد سشن برای کاربر ادمین
        with cls.client.session_transaction() as session:
            user = User.query.filter_by(username='admin').first()
            session['user_id'] = user.id
            session['is_admin'] = True
    
    @classmethod
    def tearDownClass(cls):
        """عملیات پایانی بعد از اتمام تست‌ها"""
        # حذف کانتکست برنامه
        cls.app_context.pop()
    
    def setUp(self):
        """تنظیمات قبل از هر تست"""
        pass
    
    def tearDown(self):
        """عملیات بعد از هر تست"""
        pass
    
    # تست‌های مربوط به پنل ادمین
    
    def test_admin_login(self):
        """تست ورود به پنل ادمین"""
        # ابتدا از سیستم خارج می‌شویم
        self.client.get('/logout')
        
        # تلاش برای ورود با مشخصات نادرست
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'wrong_password'
        })
        self.assertIn(b'incorrect', response.data.lower())  # پیام خطای رمز نادرست
        
        # ورود با مشخصات درست
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertIn(b'welcome', response.data.lower())  # پیام خوش‌آمدگویی
        
        # بررسی دسترسی به صفحه ادمین
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)
    
    def test_admin_dashboard(self):
        """تست داشبورد ادمین"""
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود عناصر اصلی داشبورد
        self.assertIn(b'dashboard', response.data.lower())
        self.assertIn(b'recent', response.data.lower())  # استعلام‌های اخیر
        self.assertIn(b'statistics', response.data.lower())  # آمار
    
    # تست‌های مربوط به مدیریت دسته‌بندی‌ها
    
    def test_categories_list(self):
        """تست لیست دسته‌بندی‌ها"""
        response = self.client.get('/admin/categories')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود عناصر اصلی صفحه
        self.assertIn(b'categories', response.data.lower())
        self.assertIn(b'add', response.data.lower())  # دکمه افزودن دسته‌بندی جدید
        
        # بررسی وجود زبانه‌های محصولات و خدمات
        self.assertIn(b'product', response.data.lower())
        self.assertIn(b'service', response.data.lower())
        
        # بررسی وجود حداقل یک دسته‌بندی
        categories = Category.query.all()
        self.assertGreater(len(categories), 0)
        
        # بررسی وجود نام دسته‌بندی اول در صفحه
        self.assertIn(categories[0].name.encode(), response.data)
    
    def test_add_category(self):
        """تست افزودن دسته‌بندی جدید"""
        # تعداد دسته‌بندی‌ها قبل از افزودن
        categories_count_before = Category.query.count()
        
        # ارسال فرم افزودن دسته‌بندی
        response = self.client.post('/admin/categories/add', data={
            'name': 'دسته‌بندی تست',
            'cat_type': 'product',
            'parent_id': ''  # بدون والد
        }, follow_redirects=True)
        
        # بررسی موفقیت در افزودن
        self.assertEqual(response.status_code, 200)
        
        # بررسی افزایش تعداد دسته‌بندی‌ها
        categories_count_after = Category.query.count()
        self.assertEqual(categories_count_after, categories_count_before + 1)
        
        # بررسی وجود دسته‌بندی جدید در دیتابیس
        new_category = Category.query.filter_by(name='دسته‌بندی تست').first()
        self.assertIsNotNone(new_category)
        self.assertEqual(new_category.cat_type, 'product')
    
    def test_edit_category(self):
        """تست ویرایش دسته‌بندی"""
        # انتخاب یک دسته‌بندی موجود
        category = Category.query.first()
        
        # نام جدید برای دسته‌بندی
        new_name = f"{category.name} (ویرایش شده)"
        
        # ارسال فرم ویرایش دسته‌بندی
        response = self.client.post(f'/admin/categories/edit/{category.id}', data={
            'name': new_name,
            'cat_type': category.cat_type,
            'parent_id': str(category.parent_id) if category.parent_id else ''
        }, follow_redirects=True)
        
        # بررسی موفقیت در ویرایش
        self.assertEqual(response.status_code, 200)
        
        # بررسی اعمال تغییرات در دیتابیس
        updated_category = Category.query.get(category.id)
        self.assertEqual(updated_category.name, new_name)
    
    def test_delete_category(self):
        """تست حذف دسته‌بندی"""
        # ایجاد یک دسته‌بندی جدید برای حذف
        new_category = Category(
            name="دسته‌بندی برای حذف",
            cat_type="product"
        )
        db.session.add(new_category)
        db.session.commit()
        
        # تعداد دسته‌بندی‌ها قبل از حذف
        categories_count_before = Category.query.count()
        
        # حذف دسته‌بندی
        response = self.client.post(f'/admin/categories/delete/{new_category.id}', follow_redirects=True)
        
        # بررسی موفقیت در حذف
        self.assertEqual(response.status_code, 200)
        
        # بررسی کاهش تعداد دسته‌بندی‌ها
        categories_count_after = Category.query.count()
        self.assertEqual(categories_count_after, categories_count_before - 1)
        
        # بررسی عدم وجود دسته‌بندی حذف شده
        deleted_category = Category.query.get(new_category.id)
        self.assertIsNone(deleted_category)
    
    # تست‌های مربوط به مدیریت محصولات
    
    def test_products_list(self):
        """تست لیست محصولات"""
        response = self.client.get('/admin/products')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود عناصر اصلی صفحه
        self.assertIn(b'products', response.data.lower())
        self.assertIn(b'add', response.data.lower())  # دکمه افزودن محصول جدید
        
        # بررسی وجود حداقل یک محصول
        products = Product.query.filter_by(product_type='product').all()
        self.assertGreater(len(products), 0)
        
        # بررسی وجود نام محصول اول در صفحه
        self.assertIn(products[0].name.encode(), response.data)
    
    def test_add_product(self):
        """تست افزودن محصول جدید"""
        # تعداد محصولات قبل از افزودن
        products_count_before = Product.query.filter_by(product_type='product').count()
        
        # انتخاب یک دسته‌بندی برای محصول جدید
        category = Category.query.filter_by(cat_type='product').first()
        
        # ارسال فرم افزودن محصول
        response = self.client.post('/admin/products/add', data={
            'name': 'محصول تست',
            'description': 'توضیحات محصول تست',
            'price': '1500000',
            'category_id': category.id,
            'brand': 'برند تست',
            'model': 'مدل تست',
            'in_stock': 'true',
            'tags': 'تست,محصول,جدید',
            'featured': 'true'
        }, follow_redirects=True)
        
        # بررسی موفقیت در افزودن
        self.assertEqual(response.status_code, 200)
        
        # بررسی افزایش تعداد محصولات
        products_count_after = Product.query.filter_by(product_type='product').count()
        self.assertEqual(products_count_after, products_count_before + 1)
        
        # بررسی وجود محصول جدید در دیتابیس
        new_product = Product.query.filter_by(name='محصول تست').first()
        self.assertIsNotNone(new_product)
        self.assertEqual(new_product.product_type, 'product')
        self.assertEqual(new_product.price, 1500000)
    
    def test_edit_product(self):
        """تست ویرایش محصول"""
        # انتخاب یک محصول موجود
        product = Product.query.filter_by(product_type='product').first()
        
        # نام جدید برای محصول
        new_name = f"{product.name} (ویرایش شده)"
        new_price = product.price + 100000
        
        # ارسال فرم ویرایش محصول
        response = self.client.post(f'/admin/products/edit/{product.id}', data={
            'name': new_name,
            'description': product.description,
            'price': new_price,
            'category_id': product.category_id,
            'brand': product.brand,
            'model': product.model,
            'in_stock': 'true' if product.in_stock else 'false',
            'tags': product.tags,
            'featured': 'true' if product.featured else 'false'
        }, follow_redirects=True)
        
        # بررسی موفقیت در ویرایش
        self.assertEqual(response.status_code, 200)
        
        # بررسی اعمال تغییرات در دیتابیس
        updated_product = Product.query.get(product.id)
        self.assertEqual(updated_product.name, new_name)
        self.assertEqual(updated_product.price, new_price)
    
    def test_delete_product(self):
        """تست حذف محصول"""
        # ایجاد یک محصول جدید برای حذف
        category = Category.query.filter_by(cat_type='product').first()
        new_product = Product(
            name="محصول برای حذف",
            description="این محصول برای تست حذف ایجاد شده است",
            price=1000000,
            category_id=category.id,
            product_type="product",
            brand="برند تست",
            model="مدل تست",
            in_stock=True,
            tags="تست,حذف",
            featured=False
        )
        db.session.add(new_product)
        db.session.commit()
        
        # تعداد محصولات قبل از حذف
        products_count_before = Product.query.filter_by(product_type='product').count()
        
        # حذف محصول
        response = self.client.post(f'/admin/products/delete/{new_product.id}', follow_redirects=True)
        
        # بررسی موفقیت در حذف
        self.assertEqual(response.status_code, 200)
        
        # بررسی کاهش تعداد محصولات
        products_count_after = Product.query.filter_by(product_type='product').count()
        self.assertEqual(products_count_after, products_count_before - 1)
        
        # بررسی عدم وجود محصول حذف شده
        deleted_product = Product.query.get(new_product.id)
        self.assertIsNone(deleted_product)
    
    # تست‌های مربوط به مدیریت خدمات
    
    def test_services_list(self):
        """تست لیست خدمات"""
        response = self.client.get('/admin/services')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود عناصر اصلی صفحه
        self.assertIn(b'services', response.data.lower())
        self.assertIn(b'add', response.data.lower())  # دکمه افزودن خدمت جدید
        
        # بررسی وجود حداقل یک خدمت
        services = Product.query.filter_by(product_type='service').all()
        if services:
            # بررسی وجود نام خدمت اول در صفحه
            self.assertIn(services[0].name.encode(), response.data)
    
    def test_add_service(self):
        """تست افزودن خدمت جدید"""
        # تعداد خدمات قبل از افزودن
        services_count_before = Product.query.filter_by(product_type='service').count()
        
        # انتخاب یک دسته‌بندی برای خدمت جدید
        category = Category.query.filter_by(cat_type='service').first()
        
        # ارسال فرم افزودن خدمت
        response = self.client.post('/admin/services/add', data={
            'name': 'خدمت تست',
            'description': 'توضیحات خدمت تست',
            'price': '2500000',
            'category_id': category.id,
            'tags': 'خدمت,تست,جدید',
            'featured': 'true'
        }, follow_redirects=True)
        
        # بررسی موفقیت در افزودن
        self.assertEqual(response.status_code, 200)
        
        # بررسی افزایش تعداد خدمات
        services_count_after = Product.query.filter_by(product_type='service').count()
        self.assertEqual(services_count_after, services_count_before + 1)
        
        # بررسی وجود خدمت جدید در دیتابیس
        new_service = Product.query.filter_by(name='خدمت تست').first()
        self.assertIsNotNone(new_service)
        self.assertEqual(new_service.product_type, 'service')
        self.assertEqual(new_service.price, 2500000)
    
    # تست‌های مربوط به مدیریت استعلام‌های قیمت
    
    def test_inquiries_list(self):
        """تست لیست استعلام‌های قیمت"""
        response = self.client.get('/admin/inquiries')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود عناصر اصلی صفحه
        self.assertIn(b'inquiries', response.data.lower())
        
        # بررسی وجود حداقل یک استعلام
        inquiries = Inquiry.query.all()
        self.assertGreater(len(inquiries), 0)
    
    def test_inquiry_detail(self):
        """تست جزئیات استعلام قیمت"""
        # انتخاب یک استعلام موجود
        inquiry = Inquiry.query.first()
        
        # مشاهده جزئیات استعلام
        response = self.client.get(f'/admin/inquiries?action=view&id={inquiry.id}')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود اطلاعات استعلام در صفحه
        self.assertIn(inquiry.name.encode(), response.data)
        self.assertIn(inquiry.phone.encode(), response.data)
        self.assertIn(inquiry.description.encode(), response.data)
    
    def test_update_inquiry_status(self):
        """تست به‌روزرسانی وضعیت استعلام قیمت"""
        # انتخاب یک استعلام موجود
        inquiry = Inquiry.query.first()
        
        # وضعیت جدید
        new_status = 'in_progress' if inquiry.status != 'in_progress' else 'completed'
        
        # ارسال فرم به‌روزرسانی وضعیت
        response = self.client.post(f'/admin/inquiries?action=update_status&id={inquiry.id}', data={
            'status': new_status
        }, follow_redirects=True)
        
        # بررسی موفقیت در به‌روزرسانی
        self.assertEqual(response.status_code, 200)
        
        # بررسی اعمال تغییرات در دیتابیس
        updated_inquiry = Inquiry.query.get(inquiry.id)
        self.assertEqual(updated_inquiry.status, new_status)
    
    # تست‌های مربوط به مدیریت محتوای آموزشی
    
    def test_educational_content_list(self):
        """تست لیست محتوای آموزشی"""
        response = self.client.get('/admin/education')
        self.assertEqual(response.status_code, 200)
        
        # بررسی وجود عناصر اصلی صفحه
        self.assertIn(b'education', response.data.lower())
        self.assertIn(b'add', response.data.lower())  # دکمه افزودن محتوای جدید
        
        # بررسی وجود حداقل یک محتوای آموزشی
        contents = EducationalContent.query.all()
        self.assertGreater(len(contents), 0)
    
    def test_add_educational_content(self):
        """تست افزودن محتوای آموزشی جدید"""
        # تعداد محتواهای آموزشی قبل از افزودن
        contents_count_before = EducationalContent.query.count()
        
        # ارسال فرم افزودن محتوای آموزشی
        response = self.client.post('/admin/education?action=save', data={
            'title': 'محتوای آموزشی تست',
            'content': '<p>این یک محتوای آموزشی تست است.</p>',
            'category': 'دسته تست',
            'content_type': 'text'
        }, follow_redirects=True)
        
        # بررسی موفقیت در افزودن
        self.assertEqual(response.status_code, 200)
        
        # بررسی افزایش تعداد محتواهای آموزشی
        contents_count_after = EducationalContent.query.count()
        self.assertEqual(contents_count_after, contents_count_before + 1)
        
        # بررسی وجود محتوای آموزشی جدید در دیتابیس
        new_content = EducationalContent.query.filter_by(title='محتوای آموزشی تست').first()
        self.assertIsNotNone(new_content)
        self.assertEqual(new_content.category, 'دسته تست')
    
    def test_edit_educational_content(self):
        """تست ویرایش محتوای آموزشی"""
        # انتخاب یک محتوای آموزشی موجود
        content = EducationalContent.query.first()
        
        # عنوان جدید
        new_title = f"{content.title} (ویرایش شده)"
        
        # ارسال فرم ویرایش محتوا
        response = self.client.post(f'/admin/education/edit/{content.id}', data={
            'title': new_title,
            'content': content.content,
            'category': content.category,
            'content_type': content.content_type
        }, follow_redirects=True)
        
        # بررسی موفقیت در ویرایش
        self.assertEqual(response.status_code, 200)
        
        # بررسی اعمال تغییرات در دیتابیس
        updated_content = EducationalContent.query.get(content.id)
        self.assertEqual(updated_content.title, new_title)
    
    # تست‌های مربوط به مدیریت محتوای ثابت
    
    def test_static_content(self):
        """تست محتوای ثابت"""
        # بررسی محتوای "تماس با ما"
        response = self.client.get('/admin/content/contact')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'contact', response.data.lower())
        
        # بررسی محتوای "درباره ما"
        response = self.client.get('/admin/content/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'about', response.data.lower())
    
    def test_update_static_content(self):
        """تست به‌روزرسانی محتوای ثابت"""
        # محتوای جدید
        new_content = "<h2>محتوای تست جدید</h2><p>این محتوا برای تست به‌روزرسانی است.</p>"
        
        # ارسال فرم به‌روزرسانی محتوای تماس با ما
        response = self.client.post('/admin/content/contact', data={
            'content': new_content
        }, follow_redirects=True)
        
        # بررسی موفقیت در به‌روزرسانی
        self.assertEqual(response.status_code, 200)
        
        # بررسی اعمال تغییرات در دیتابیس
        updated_content = StaticContent.query.filter_by(content_type='contact').first()
        self.assertEqual(updated_content.content, new_content)

# اجرای تست‌ها
if __name__ == '__main__':
    unittest.main()