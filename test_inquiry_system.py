#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import sys
import json
import logging
from datetime import datetime
from unittest.mock import MagicMock, patch
from flask import Flask, session
from flask_testing import TestCase

# تنظیم لاگ برای دیباگ
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# اضافه کردن مسیر فعلی به سیستم
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ایمپورت ماژول‌های مورد نیاز
from database import Database
from models import Inquiry
from app import db, app
import main

# تست‌های مربوط به قابلیت استعلام قیمت در ربات تلگرام
class TelegramInquiryTests(unittest.TestCase):
    """تست‌های مربوط به بخش استعلام قیمت ربات تلگرام"""
    
    def setUp(self):
        """تنظیمات قبل از هر تست"""
        self.db = MagicMock(spec=Database)
        
        # ایجاد محصول و سرویس نمونه برای تست
        self.sample_product = {
            'id': 1,
            'name': 'محصول تست',
            'price': 1000000,
            'description': 'توضیحات محصول تست',
            'category_id': 1
        }
        
        self.sample_service = {
            'id': 1,
            'name': 'خدمت تست',
            'price': 500000,
            'description': 'توضیحات خدمت تست',
            'category_id': 2
        }
        
        # تنظیم پاسخ‌های mock برای متدهای دیتابیس
        self.db.get_product.return_value = self.sample_product
        self.db.get_service.return_value = self.sample_service
        self.db.add_inquiry.return_value = 1  # شناسه استعلام قیمت ایجاد شده
        
    @patch('handlers.db')
    async def test_inquiry_product_flow(self, mock_db):
        """تست جریان کامل استعلام قیمت برای محصول"""
        from aiogram.types import Message, CallbackQuery, Chat, User
        from aiogram.fsm.context import FSMContext
        from handlers import callback_inquiry, process_inquiry_name, process_inquiry_phone, process_inquiry_description, callback_confirm_inquiry
        
        # جایگزینی با mock database
        mock_db.get_product.return_value = self.sample_product
        mock_db.add_inquiry.return_value = 1
        
        # ایجاد موک‌های لازم
        chat = MagicMock(spec=Chat)
        chat.id = 12345
        
        user = MagicMock(spec=User)
        user.id = 67890
        user.first_name = "کاربر تست"
        
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "inquiry:product:1"
        callback.from_user = user
        callback.message.chat = chat
        
        state = MagicMock(spec=FSMContext)
        data = {}
        
        # مک‌کردن update_data و get_data 
        async def mock_update_data(**kwargs):
            data.update(kwargs)
        
        async def mock_get_data():
            return data
            
        state.update_data = mock_update_data
        state.get_data = mock_get_data
        
        # اجرای مراحل جریان استعلام قیمت
        # 1. کلیک روی دکمه استعلام قیمت
        await callback_inquiry(callback, state)
        self.assertEqual(data.get('product_id'), 1)
        self.assertIsNone(data.get('service_id'))
        
        # 2. وارد کردن نام
        message = MagicMock(spec=Message)
        message.text = "علی رضایی"
        await process_inquiry_name(message, state)
        self.assertEqual(data.get('name'), "علی رضایی")
        
        # 3. وارد کردن شماره تماس
        message.text = "09123456789"
        await process_inquiry_phone(message, state)
        self.assertEqual(data.get('phone'), "09123456789")
        
        # 4. وارد کردن توضیحات
        message.text = "لطفا قیمت دقیق را اعلام کنید"
        await process_inquiry_description(message, state)
        self.assertEqual(data.get('description'), "لطفا قیمت دقیق را اعلام کنید")
        
        # 5. تایید استعلام قیمت
        callback.data = "confirm_inquiry"
        callback.message = message
        await callback_confirm_inquiry(callback, state)
        
        # بررسی اینکه آیا استعلام قیمت در دیتابیس ثبت شده است
        mock_db.add_inquiry.assert_called_once()
        
    @patch('handlers.db')
    async def test_inquiry_service_flow(self, mock_db):
        """تست جریان کامل استعلام قیمت برای خدمات"""
        from aiogram.types import Message, CallbackQuery, Chat, User
        from aiogram.fsm.context import FSMContext
        from handlers import callback_inquiry, process_inquiry_name, process_inquiry_phone, process_inquiry_description, callback_confirm_inquiry
        
        # جایگزینی با mock database
        mock_db.get_service.return_value = self.sample_service
        mock_db.add_inquiry.return_value = 2
        
        # ایجاد موک‌های لازم
        chat = MagicMock(spec=Chat)
        chat.id = 12345
        
        user = MagicMock(spec=User)
        user.id = 67890
        user.first_name = "کاربر تست"
        
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "inquiry:service:1"
        callback.from_user = user
        callback.message.chat = chat
        
        state = MagicMock(spec=FSMContext)
        data = {}
        
        # مک‌کردن update_data و get_data 
        async def mock_update_data(**kwargs):
            data.update(kwargs)
        
        async def mock_get_data():
            return data
            
        state.update_data = mock_update_data
        state.get_data = mock_get_data
        
        # اجرای مراحل جریان استعلام قیمت
        # 1. کلیک روی دکمه استعلام قیمت
        await callback_inquiry(callback, state)
        self.assertEqual(data.get('service_id'), 1)
        self.assertIsNone(data.get('product_id'))
        
        # 2. وارد کردن نام
        message = MagicMock(spec=Message)
        message.text = "محمد جعفری"
        await process_inquiry_name(message, state)
        self.assertEqual(data.get('name'), "محمد جعفری")
        
        # 3. وارد کردن شماره تماس
        message.text = "09187654321"
        await process_inquiry_phone(message, state)
        self.assertEqual(data.get('phone'), "09187654321")
        
        # 4. وارد کردن توضیحات
        message.text = "نیاز به نصب در محل داریم"
        await process_inquiry_description(message, state)
        self.assertEqual(data.get('description'), "نیاز به نصب در محل داریم")
        
        # 5. تایید استعلام قیمت
        callback.data = "confirm_inquiry"
        callback.message = message
        await callback_confirm_inquiry(callback, state)
        
        # بررسی اینکه آیا استعلام قیمت در دیتابیس ثبت شده است
        mock_db.add_inquiry.assert_called_once()
        
    @patch('handlers.db')
    async def test_inquiry_error_handling(self, mock_db):
        """تست مدیریت خطا در جریان استعلام قیمت"""
        from aiogram.types import Message, CallbackQuery, Chat, User
        from aiogram.fsm.context import FSMContext
        from handlers import callback_inquiry, process_inquiry_phone
        
        # جایگزینی با mock database
        mock_db.get_product.return_value = self.sample_product
        
        # ایجاد موک‌های لازم
        chat = MagicMock(spec=Chat)
        chat.id = 12345
        
        user = MagicMock(spec=User)
        user.id = 67890
        user.first_name = "کاربر تست"
        
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "inquiry:product:1"
        callback.from_user = user
        callback.message.chat = chat
        
        state = MagicMock(spec=FSMContext)
        data = {}
        
        # مک‌کردن update_data و get_data 
        async def mock_update_data(**kwargs):
            data.update(kwargs)
        
        async def mock_get_data():
            return data
            
        state.update_data = mock_update_data
        state.get_data = mock_get_data
        
        # تست مدیریت خطا در وارد کردن شماره تلفن نامعتبر
        message = MagicMock(spec=Message)
        message.text = "شماره نامعتبر"
        await process_inquiry_phone(message, state)
        self.assertNotIn('phone', data)  # شماره تلفن نباید ذخیره شده باشد


# تست‌های مربوط به قابلیت استعلام قیمت در پنل مدیریت
class AdminInquiryTests(TestCase):
    """تست‌های مربوط به بخش استعلام قیمت پنل مدیریت"""
    
    def create_app(self):
        """ایجاد اپلیکیشن فلسک برای تست"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app
        
    def setUp(self):
        """تنظیمات قبل از هر تست"""
        db.create_all()
        
        # ایجاد یک کاربر ادمین برای تست
        from models import User
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('adminpassword')
        db.session.add(admin)
        
        # اضافه کردن چند استعلام قیمت نمونه
        from models import Inquiry, Product, Service
        
        # ایجاد دسته‌بندی
        from models import Category
        product_category = Category(name='دسته محصول تست', cat_type='product')
        service_category = Category(name='دسته خدمت تست', cat_type='service')
        db.session.add(product_category)
        db.session.add(service_category)
        db.session.commit()
        
        # ایجاد محصول و سرویس
        product = Product(name='محصول تست', price=1000000, description='توضیحات محصول تست', 
                         category_id=product_category.id, product_type='product')
        service = Product(name='خدمت تست', price=500000, description='توضیحات خدمت تست', 
                         category_id=service_category.id, product_type='service')
        db.session.add(product)
        db.session.add(service)
        db.session.commit()
        
        # ایجاد استعلام قیمت برای محصول
        product_inquiry = Inquiry(user_id=12345, name='علی رضایی', 
                                 phone='09123456789', description='استعلام قیمت محصول',
                                 product_id=product.id, product_type='product', 
                                 created_at=datetime.now())
        
        # ایجاد استعلام قیمت برای خدمت
        service_inquiry = Inquiry(user_id=67890, name='محمد جعفری', 
                                  phone='09187654321', description='استعلام قیمت خدمات',
                                  product_id=service.id, product_type='service', 
                                  created_at=datetime.now())
        
        db.session.add(product_inquiry)
        db.session.add(service_inquiry)
        db.session.commit()
        
    def tearDown(self):
        """پاکسازی بعد از هر تست"""
        db.session.remove()
        db.drop_all()
    
    def login(self, username, password):
        """ورود کاربر ادمین"""
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
    
    def logout(self):
        """خروج کاربر"""
        return self.client.get('/logout', follow_redirects=True)
    
    def test_inquiry_list_page(self):
        """تست صفحه لیست استعلام قیمت‌ها"""
        # ورود کاربر ادمین
        response = self.login('admin', 'adminpassword')
        self.assertIn(b'خوش آمدید', response.data)
        
        # درخواست صفحه لیست استعلام‌ها
        response = self.client.get('/admin/inquiries')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xd8\xa7\xd8\xb3\xd8\xaa\xd8\xb9\xd9\x84\xd8\xa7\xd9\x85 \xd9\x82\xdb\x8c\xd9\x85\xd8\xaa \xd9\x85\xd8\xad\xd8\xb5\xd9\x88\xd9\x84', response.data)  # استعلام قیمت محصول
        self.assertIn(b'\xd8\xa7\xd8\xb3\xd8\xaa\xd8\xb9\xd9\x84\xd8\xa7\xd9\x85 \xd9\x82\xdb\x8c\xd9\x85\xd8\xaa \xd8\xae\xd8\xaf\xd9\x85\xd8\xa7\xd8\xaa', response.data)  # استعلام قیمت خدمات
    
    def test_inquiry_details(self):
        """تست صفحه جزئیات استعلام قیمت"""
        # ورود کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # پیدا کردن یک استعلام قیمت
        inquiry = Inquiry.query.first()
        
        # درخواست صفحه جزئیات استعلام
        response = self.client.get(f'/admin/inquiry/{inquiry.id}')
        self.assertEqual(response.status_code, 200)
        
        if inquiry.product_type == 'product':
            self.assertIn(b'\xd9\x85\xd8\xad\xd8\xb5\xd9\x88\xd9\x84 \xd8\xaa\xd8\xb3\xd8\xaa', response.data)  # محصول تست
        else:
            self.assertIn(b'\xd8\xae\xd8\xaf\xd9\x85\xd8\xaa \xd8\xaa\xd8\xb3\xd8\xaa', response.data)  # خدمت تست
    
    def test_inquiry_delete(self):
        """تست حذف استعلام قیمت"""
        # ورود کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # پیدا کردن یک استعلام قیمت
        inquiry = Inquiry.query.first()
        inquiry_id = inquiry.id
        
        # درخواست حذف استعلام
        response = self.client.post(f'/admin/inquiry/delete/{inquiry_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # بررسی حذف شدن استعلام
        deleted_inquiry = Inquiry.query.get(inquiry_id)
        self.assertIsNone(deleted_inquiry)
    
    def test_inquiry_filter(self):
        """تست فیلتر استعلام قیمت‌ها"""
        # ورود کاربر ادمین
        self.login('admin', 'adminpassword')
        
        # فیلتر بر اساس نوع محصول
        response = self.client.get('/admin/inquiries?type=product')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xd8\xa7\xd8\xb3\xd8\xaa\xd8\xb9\xd9\x84\xd8\xa7\xd9\x85 \xd9\x82\xdb\x8c\xd9\x85\xd8\xaa \xd9\x85\xd8\xad\xd8\xb5\xd9\x88\xd9\x84', response.data)  # استعلام قیمت محصول
        
        # فیلتر بر اساس نوع خدمت
        response = self.client.get('/admin/inquiries?type=service')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xd8\xa7\xd8\xb3\xd8\xaa\xd8\xb9\xd9\x84\xd8\xa7\xd9\x85 \xd9\x82\xdb\x8c\xd9\x85\xd8\xaa \xd8\xae\xd8\xaf\xd9\x85\xd8\xa7\xd8\xaa', response.data)  # استعلام قیمت خدمات
    
    def test_unauthenticated_access(self):
        """تست دسترسی بدون احراز هویت"""
        # بدون ورود به سیستم، تلاش برای دسترسی به صفحه استعلام‌ها
        response = self.client.get('/admin/inquiries', follow_redirects=True)
        self.assertIn(b'login', response.data.lower())  # باید به صفحه ورود هدایت شود

    def test_non_admin_access(self):
        """تست دسترسی با کاربر غیر ادمین"""
        # ایجاد کاربر غیر ادمین
        from models import User
        user = User(username='user', email='user@example.com', is_admin=False)
        user.set_password('userpassword')
        db.session.add(user)
        db.session.commit()
        
        # ورود با کاربر غیر ادمین
        self.login('user', 'userpassword')
        
        # تلاش برای دسترسی به صفحه استعلام‌ها
        response = self.client.get('/admin/inquiries', follow_redirects=True)
        self.assertIn(b'\xd8\xb4\xd9\x85\xd8\xa7 \xd8\xaf\xd8\xb3\xd8\xaa\xd8\xb1\xd8\xb3\xdb\x8c \xd9\x85\xd8\xaf\xdb\x8c\xd8\xb1\xdb\x8c\xd8\xaa\xdb\x8c \xd9\x86\xd8\xaf\xd8\xa7\xd8\xb1\xdb\x8c\xd8\xaf', response.data)  # شما دسترسی مدیریتی ندارید


# اجرای تست‌ها
if __name__ == '__main__':
    unittest.main()