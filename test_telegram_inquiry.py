#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import unittest
import logging
from unittest.mock import MagicMock, patch

# تنظیم لاگ برای دیباگ
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# کلاس‌های موک برای تست‌های ربات تلگرام
class MockUser:
    def __init__(self, user_id=123456, first_name="کاربر تست"):
        self.id = user_id
        self.first_name = first_name

class MockChat:
    def __init__(self, chat_id=123456):
        self.id = chat_id

class MockMessage:
    def __init__(self, message_id=1, text="", chat=None, from_user=None):
        self.message_id = message_id
        self.text = text
        self.chat = chat or MockChat()
        self.from_user = from_user or MockUser()
        self.answer_called = False
        self.reply_markup = None
    
    async def answer(self, text, reply_markup=None):
        print(f"Mock message answer: {text}")
        self.answer_called = True
        self.answer_text = text
        self.reply_markup = reply_markup
        return True

class MockCallbackQuery:
    def __init__(self, data="", from_user=None, message=None):
        self.data = data
        self.from_user = from_user or MockUser()
        self.message = message or MockMessage()
        self.answer_called = False
    
    async def answer(self, text=""):
        print(f"Mock callback answer: {text}")
        self.answer_called = True
        return True

class MockFSMContext:
    def __init__(self, initial_data=None):
        self.data = initial_data or {}
        self.state = None
    
    async def update_data(self, **kwargs):
        self.data.update(kwargs)
    
    async def get_data(self):
        return self.data
    
    async def set_state(self, state):
        self.state = state
    
    async def clear(self):
        self.data = {}
        self.state = None

class MockDatabase:
    def __init__(self):
        self.products = {
            1: {
                'id': 1,
                'name': 'محصول تست',
                'price': 1000000,
                'description': 'توضیحات محصول تست',
                'category_id': 1
            }
        }
        
        self.services = {
            1: {
                'id': 1,
                'name': 'خدمت تست',
                'price': 500000,
                'description': 'توضیحات خدمت تست',
                'category_id': 2
            }
        }
        
        self.inquiries = {}
        self.next_inquiry_id = 1
    
    def get_product(self, product_id):
        return self.products.get(product_id)
    
    def get_service(self, service_id):
        return self.services.get(service_id)
    
    def add_inquiry(self, user_id, name, phone, description, product_id=None, service_id=None):
        inquiry_id = self.next_inquiry_id
        self.next_inquiry_id += 1
        
        inquiry = {
            'id': inquiry_id,
            'user_id': user_id,
            'name': name,
            'phone': phone,
            'description': description,
            'product_id': product_id,
            'service_id': service_id
        }
        
        self.inquiries[inquiry_id] = inquiry
        return inquiry_id

# تست‌های استعلام قیمت ربات تلگرام
class TestTelegramInquiry(unittest.TestCase):
    async def test_product_inquiry_flow(self):
        """تست جریان کامل استعلام قیمت یک محصول"""
        with patch('handlers.db', new=MockDatabase()):
            from handlers import callback_inquiry, process_inquiry_name, process_inquiry_phone, process_inquiry_description, callback_confirm_inquiry
            
            # ایجاد موک‌های مورد نیاز
            user = MockUser()
            chat = MockChat()
            message = MockMessage(text="", chat=chat, from_user=user)
            
            # 1. کلیک روی دکمه استعلام قیمت
            callback = MockCallbackQuery(data="inquiry:product:1", from_user=user, message=message)
            state = MockFSMContext()
            
            await callback_inquiry(callback, state)
            self.assertEqual(state.data.get('product_id'), 1)
            self.assertIsNone(state.data.get('service_id'))
            
            # 2. وارد کردن نام
            message.text = "علی رضایی"
            await process_inquiry_name(message, state)
            self.assertEqual(state.data.get('name'), "علی رضایی")
            
            # 3. وارد کردن شماره تماس
            message.text = "09123456789"
            await process_inquiry_phone(message, state)
            self.assertEqual(state.data.get('phone'), "09123456789")
            
            # 4. وارد کردن توضیحات
            message.text = "لطفا قیمت دقیق محصول را اعلام کنید"
            await process_inquiry_description(message, state)
            self.assertEqual(state.data.get('description'), "لطفا قیمت دقیق محصول را اعلام کنید")
            self.assertTrue(message.answer_called)
            
            # 5. تایید استعلام
            confirm_callback = MockCallbackQuery(data="confirm_inquiry", from_user=user, message=message)
            await callback_confirm_inquiry(confirm_callback, state)
            
            # بررسی داده‌های ذخیره شده در دیتابیس
            from handlers import db
            inquiry_id = max(db.inquiries.keys())
            inquiry = db.inquiries[inquiry_id]
            
            self.assertEqual(inquiry['user_id'], user.id)
            self.assertEqual(inquiry['name'], "علی رضایی")
            self.assertEqual(inquiry['phone'], "09123456789")
            self.assertEqual(inquiry['description'], "لطفا قیمت دقیق محصول را اعلام کنید")
            self.assertEqual(inquiry['product_id'], 1)
            self.assertIsNone(inquiry['service_id'])
    
    async def test_service_inquiry_flow(self):
        """تست جریان کامل استعلام قیمت یک خدمت"""
        with patch('handlers.db', new=MockDatabase()):
            from handlers import callback_inquiry, process_inquiry_name, process_inquiry_phone, process_inquiry_description, callback_confirm_inquiry
            
            # ایجاد موک‌های مورد نیاز
            user = MockUser()
            chat = MockChat()
            message = MockMessage(text="", chat=chat, from_user=user)
            
            # 1. کلیک روی دکمه استعلام قیمت
            callback = MockCallbackQuery(data="inquiry:service:1", from_user=user, message=message)
            state = MockFSMContext()
            
            await callback_inquiry(callback, state)
            self.assertEqual(state.data.get('service_id'), 1)
            self.assertIsNone(state.data.get('product_id'))
            
            # 2. وارد کردن نام
            message.text = "محمد جعفری"
            await process_inquiry_name(message, state)
            self.assertEqual(state.data.get('name'), "محمد جعفری")
            
            # 3. وارد کردن شماره تماس
            message.text = "09187654321"
            await process_inquiry_phone(message, state)
            self.assertEqual(state.data.get('phone'), "09187654321")
            
            # 4. وارد کردن توضیحات
            message.text = "نیاز به نصب در محل داریم"
            await process_inquiry_description(message, state)
            self.assertEqual(state.data.get('description'), "نیاز به نصب در محل داریم")
            self.assertTrue(message.answer_called)
            
            # 5. تایید استعلام
            confirm_callback = MockCallbackQuery(data="confirm_inquiry", from_user=user, message=message)
            await callback_confirm_inquiry(confirm_callback, state)
            
            # بررسی داده‌های ذخیره شده در دیتابیس
            from handlers import db
            inquiry_id = max(db.inquiries.keys())
            inquiry = db.inquiries[inquiry_id]
            
            self.assertEqual(inquiry['user_id'], user.id)
            self.assertEqual(inquiry['name'], "محمد جعفری")
            self.assertEqual(inquiry['phone'], "09187654321")
            self.assertEqual(inquiry['description'], "نیاز به نصب در محل داریم")
            self.assertEqual(inquiry['service_id'], 1)
            self.assertIsNone(inquiry['product_id'])

    async def test_invalid_phone_handling(self):
        """تست مدیریت شماره تلفن نامعتبر"""
        with patch('handlers.db', new=MockDatabase()):
            from handlers import process_inquiry_phone
            
            # ایجاد موک‌های مورد نیاز
            user = MockUser()
            chat = MockChat()
            message = MockMessage(text="شماره نامعتبر", chat=chat, from_user=user)
            state = MockFSMContext({'name': 'کاربر تست'})
            
            # وارد کردن شماره تلفن نامعتبر
            await process_inquiry_phone(message, state)
            
            # شماره تلفن نباید ذخیره شده باشد
            self.assertNotIn('phone', state.data)
            self.assertTrue(message.answer_called)
            # پیام خطا باید نمایش داده شود
            self.assertIn('معتبر', message.answer_text)

    async def test_inquiry_cancel(self):
        """تست لغو استعلام قیمت"""
        with patch('handlers.db', new=MockDatabase()):
            from handlers import callback_cancel_inquiry
            
            # ایجاد موک‌های مورد نیاز
            user = MockUser()
            chat = MockChat()
            message = MockMessage(text="", chat=chat, from_user=user)
            callback = MockCallbackQuery(data="cancel_inquiry", from_user=user, message=message)
            
            # وضعیت اولیه
            state = MockFSMContext({
                'name': 'کاربر تست',
                'phone': '09123456789',
                'description': 'توضیحات تست'
            })
            
            # لغو استعلام
            await callback_cancel_inquiry(callback, state)
            
            # state باید پاک شده باشد
            self.assertEqual(state.data, {})
            self.assertIsNone(state.state)
            
            # پیام لغو باید نمایش داده شود - بررسی پیام اول
            self.assertTrue(message.answer_called)
            
            # اطمینان از درستی اجرای تست - باید به فرم زیر باشد
            # در اولین فراخوانی answer باید پیام لغو باشد
            # در دومین فراخوانی answer باید پیام منو باشد
            self.assertEqual(message.answer_text, "می‌توانید به استفاده از ربات ادامه دهید:")

# اجرای تست‌ها
def run_test():
    """اجرای همه تست‌ها"""
    # تبدیل تست‌های async به sync برای unittest
    def async_test(coro):
        def wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(coro(*args, **kwargs))
        return wrapper
    
    # اعمال دکوریتور async_test به همه متدهای تست
    for attr in dir(TestTelegramInquiry):
        if attr.startswith('test_'):
            setattr(TestTelegramInquiry, attr, async_test(getattr(TestTelegramInquiry, attr)))
    
    # اجرای تست‌ها
    unittest.main()

if __name__ == "__main__":
    run_test()