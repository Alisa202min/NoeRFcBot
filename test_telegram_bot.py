#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست عملکرد بات تلگرام
این اسکریپت عملکرد بات تلگرام را به صورت شبیه‌سازی شده تست می‌کند
"""

import unittest
import asyncio
import logging
import os
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# مسیر پروژه را به sys.path اضافه کنید تا ماژول‌ها قابل دسترسی باشند
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from handlers import cmd_start, cmd_help, cmd_products, cmd_services, cmd_contact, cmd_about
from handlers import callback_category, callback_product, callback_service, callback_inquiry
from handlers import process_inquiry_name, process_inquiry_phone, process_inquiry_description
from models import Category, Product, ProductMedia, Inquiry, User

# ساختن آبجکت‌های مورد نیاز برای شبیه‌سازی تلگرام
class MockMessage:
    """کلاس شبیه‌سازی پیام تلگرام"""
    def __init__(self, text=None, from_user=None, chat=None):
        self.text = text
        self.from_user = from_user
        self.chat = chat
        self.message_id = 1
        self.date = datetime.now()
    
    async def reply(self, text, reply_markup=None, parse_mode=None):
        """شبیه‌سازی پاسخ به پیام"""
        logger.info(f"Mock Reply: {text}")
        return MockMessage(text="Reply sent")
    
    async def answer(self, text, reply_markup=None, parse_mode=None):
        """شبیه‌سازی پاسخ به پیام"""
        logger.info(f"Mock Answer: {text}")
        return MockMessage(text="Answer sent")

class MockUser:
    """کلاس شبیه‌سازی کاربر تلگرام"""
    def __init__(self, id=1, first_name="Test", last_name="User", username="testuser"):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.is_bot = False
        self.language_code = "fa"

class MockChat:
    """کلاس شبیه‌سازی چت تلگرام"""
    def __init__(self, id=1, type="private", title=None, username=None, first_name="Test", last_name="User"):
        self.id = id
        self.type = type
        self.title = title
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

class MockCallbackQuery:
    """کلاس شبیه‌سازی کال‌بک کوئری تلگرام"""
    def __init__(self, data=None, from_user=None, message=None):
        self.data = data
        self.from_user = from_user
        self.message = message
        self.id = "1"
    
    async def answer(self, text=None, show_alert=False):
        """شبیه‌سازی پاسخ به کال‌بک"""
        logger.info(f"Mock Callback Answer: {text}")
        return True

class MockBot:
    """کلاس شبیه‌سازی بات تلگرام"""
    def __init__(self):
        self.id = 123456789
        self.username = "test_bot"
    
    async def send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
        """شبیه‌سازی ارسال پیام"""
        logger.info(f"Mock Send Message to {chat_id}: {text}")
        return MockMessage(text=text)
    
    async def send_photo(self, chat_id, photo, caption=None, reply_markup=None, parse_mode=None):
        """شبیه‌سازی ارسال عکس"""
        logger.info(f"Mock Send Photo to {chat_id}: {caption}")
        return MockMessage(text=caption)
    
    async def send_media_group(self, chat_id, media):
        """شبیه‌سازی ارسال گروه رسانه‌ای"""
        logger.info(f"Mock Send Media Group to {chat_id}: {len(media)} items")
        return [MockMessage(text="Media sent")]

class MockState:
    """کلاس شبیه‌سازی وضعیت FSM"""
    def __init__(self):
        self.state = None
        self.data = {}
    
    async def set_state(self, state):
        """تنظیم وضعیت"""
        self.state = state
        logger.info(f"Mock State set to: {state}")
    
    async def update_data(self, **kwargs):
        """به‌روزرسانی داده‌ها"""
        self.data.update(kwargs)
        logger.info(f"Mock State data updated: {kwargs}")
    
    async def get_data(self):
        """دریافت داده‌ها"""
        return self.data
    
    async def clear(self):
        """پاک کردن وضعیت"""
        self.state = None
        self.data = {}
        logger.info(f"Mock State cleared")

class MockFSMContext:
    """کلاس شبیه‌سازی کانتکست FSM"""
    def __init__(self):
        self.state = MockState()
    
    async def set_state(self, state):
        """تنظیم وضعیت"""
        await self.state.set_state(state)
    
    async def update_data(self, **kwargs):
        """به‌روزرسانی داده‌ها"""
        await self.state.update_data(**kwargs)
    
    async def get_data(self):
        """دریافت داده‌ها"""
        return await self.state.get_data()
    
    async def clear(self):
        """پاک کردن وضعیت"""
        await self.state.clear()

class TelegramBotTest(unittest.TestCase):
    """کلاس تست بات تلگرام"""
    
    @classmethod
    def setUpClass(cls):
        """تنظیمات اولیه برای کلاس تست"""
        # تنظیم کانتکست اپلیکیشن
        cls.app_context = app.app_context()
        cls.app_context.push()
        
        # اجرای سیدینگ دیتابیس اگر هنوز انجام نشده
        if Category.query.count() == 0:
            logger.info("Seeding database...")
            from seed_admin_data import main
            main()
    
    @classmethod
    def tearDownClass(cls):
        """عملیات پایانی بعد از اتمام تست‌ها"""
        # حذف کانتکست برنامه
        cls.app_context.pop()
    
    def setUp(self):
        """تنظیمات قبل از هر تست"""
        # ایجاد آبجکت‌های شبیه‌سازی شده
        self.bot = MockBot()
        self.user = MockUser()
        self.chat = MockChat()
        self.message = MockMessage(from_user=self.user, chat=self.chat)
        self.fsm_context = MockFSMContext()
        
        # اطمینان از وجود داده‌ها در دیتابیس
        self.ensure_test_data()
    
    def ensure_test_data(self):
        """اطمینان از وجود داده‌های تست در دیتابیس"""
        # بررسی وجود کاربر تلگرام
        telegram_user = User.query.filter_by(telegram_id=self.user.id).first()
        if not telegram_user:
            telegram_user = User(
                username=f"telegram_user_{self.user.id}",
                telegram_id=self.user.id,
                telegram_username=self.user.username,
                first_name=self.user.first_name,
                last_name=self.user.last_name
            )
            db.session.add(telegram_user)
            db.session.commit()
    
    def test_cmd_start(self):
        """تست دستور /start"""
        async def test_async():
            self.message.text = "/start"
            result = await cmd_start(self.message, self.fsm_context)
            return result
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_async())
        # موفقیت اگر به خطا نخورد
    
    def test_cmd_help(self):
        """تست دستور /help"""
        async def test_async():
            self.message.text = "/help"
            result = await cmd_help(self.message)
            return result
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_async())
        # موفقیت اگر به خطا نخورد
    
    def test_cmd_products(self):
        """تست دستور /products"""
        async def test_async():
            self.message.text = "/products"
            result = await cmd_products(self.message, self.fsm_context)
            return result
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_async())
        # موفقیت اگر به خطا نخورد
    
    def test_cmd_services(self):
        """تست دستور /services"""
        async def test_async():
            self.message.text = "/services"
            result = await cmd_services(self.message, self.fsm_context)
            return result
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_async())
        # موفقیت اگر به خطا نخورد
    
    def test_cmd_contact(self):
        """تست دستور /contact"""
        async def test_async():
            self.message.text = "/contact"
            result = await cmd_contact(self.message)
            return result
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_async())
        # موفقیت اگر به خطا نخورد
    
    def test_cmd_about(self):
        """تست دستور /about"""
        async def test_async():
            self.message.text = "/about"
            result = await cmd_about(self.message)
            return result
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_async())
        # موفقیت اگر به خطا نخورد
    
    def test_category_callback(self):
        """تست کال‌بک انتخاب دسته‌بندی"""
        # گرفتن یک دسته‌بندی از دیتابیس
        category = Category.query.filter_by(cat_type='product').first()
        
        async def test_async():
            # ساخت کال‌بک کوئری
            callback_data = f"category:{category.id}"
            callback_query = MockCallbackQuery(
                data=callback_data,
                from_user=self.user,
                message=self.message
            )
            
            # اجرای هندلر کال‌بک
            await callback_category(callback_query, self.fsm_context)
            
            # بررسی تنظیم داده‌ها در وضعیت FSM
            data = await self.fsm_context.get_data()
            self.assertIn('category_id', data)
            self.assertEqual(data['category_id'], str(category.id))
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_async())
    
    def test_product_callback(self):
        """تست کال‌بک انتخاب محصول"""
        # گرفتن یک محصول از دیتابیس
        product = Product.query.filter_by(product_type='product').first()
        
        async def test_async():
            # ساخت کال‌بک کوئری
            callback_data = f"product:{product.id}"
            callback_query = MockCallbackQuery(
                data=callback_data,
                from_user=self.user,
                message=self.message
            )
            
            # اجرای هندلر کال‌بک
            await callback_product(callback_query, self.fsm_context)
            
            # بررسی تنظیم داده‌ها در وضعیت FSM
            data = await self.fsm_context.get_data()
            self.assertIn('product_id', data)
            self.assertEqual(int(data['product_id']), product.id)
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_async())
    
    def test_service_callback(self):
        """تست کال‌بک انتخاب خدمت"""
        # گرفتن یک خدمت از دیتابیس
        service = Product.query.filter_by(product_type='service').first()
        
        async def test_async():
            # ساخت کال‌بک کوئری
            callback_data = f"service:{service.id}"
            callback_query = MockCallbackQuery(
                data=callback_data,
                from_user=self.user,
                message=self.message
            )
            
            # اجرای هندلر کال‌بک
            await callback_service(callback_query, self.fsm_context)
            
            # بررسی تنظیم داده‌ها در وضعیت FSM
            data = await self.fsm_context.get_data()
            self.assertIn('service_id', data)
            self.assertEqual(int(data['service_id']), service.id)
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_async())
    
    def test_inquiry_flow(self):
        """تست جریان کامل استعلام قیمت"""
        # گرفتن یک محصول از دیتابیس
        product = Product.query.filter_by(product_type='product').first()
        
        async def test_async():
            # ۱. شروع استعلام
            callback_data = f"inquiry:product:{product.id}"
            callback_query = MockCallbackQuery(
                data=callback_data,
                from_user=self.user,
                message=self.message
            )
            
            await callback_inquiry(callback_query, self.fsm_context)
            
            # ۲. وارد کردن نام
            self.message.text = "محمد حسینی"
            await process_inquiry_name(self.message, self.fsm_context)
            
            # ۳. وارد کردن شماره تلفن
            self.message.text = "09123456789"
            await process_inquiry_phone(self.message, self.fsm_context)
            
            # ۴. وارد کردن توضیحات
            self.message.text = "نیاز به استعلام قیمت برای خرید عمده داریم"
            await process_inquiry_description(self.message, self.fsm_context)
            
            # بررسی داده‌های ذخیره شده
            data = await self.fsm_context.get_data()
            self.assertEqual(data['name'], "محمد حسینی")
            self.assertEqual(data['phone'], "09123456789")
            self.assertEqual(data['description'], "نیاز به استعلام قیمت برای خرید عمده داریم")
            
            # بررسی وضعیت نهایی
            self.assertIsNotNone(self.fsm_context.state.state)
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_async())

# اجرای تست‌ها
if __name__ == '__main__':
    unittest.main()