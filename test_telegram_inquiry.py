#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import unittest
import logging
import re
from unittest.mock import MagicMock, patch

# تنظیم لاگ برای دیباگ
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# کلاس‌های موک برای تست‌های ربات تلگرام
class MockUser:
    def __init__(self, user_id=123456, first_name="کاربر تست", username="test_user"):
        self.id = user_id
        self.first_name = first_name
        self.username = username

class MockChat:
    def __init__(self, chat_id=123456, type="private"):
        self.id = chat_id
        self.type = type

class MockInlineKeyboardButton:
    def __init__(self, text, callback_data=None, url=None):
        self.text = text
        self.callback_data = callback_data
        self.url = url

class MockInlineKeyboardMarkup:
    def __init__(self, inline_keyboard=None):
        self.inline_keyboard = inline_keyboard or []

class MockMessage:
    def __init__(self, message_id=1, text="", chat=None, from_user=None, reply_markup=None):
        self.message_id = message_id
        self.text = text
        self.chat = chat or MockChat()
        self.from_user = from_user or MockUser()
        self.reply_markup = reply_markup
        self.answer_called = False
        self.answer_text = ""
        self.answer_history = []
    
    async def answer(self, text, reply_markup=None, parse_mode=None):
        print(f"Mock message answer: {text}")
        self.answer_called = True
        self.answer_text = text
        self.reply_markup = reply_markup
        self.answer_history.append({
            'text': text,
            'reply_markup': reply_markup,
            'parse_mode': parse_mode
        })
        return True

class MockCallbackQuery:
    def __init__(self, data="", from_user=None, message=None):
        self.data = data
        self.from_user = from_user or MockUser()
        self.message = message or MockMessage()
        self.answer_called = False
        self.answer_text = ""
    
    async def answer(self, text=""):
        print(f"Mock callback answer: {text}")
        self.answer_called = True
        self.answer_text = text
        return True

class MockFSMContext:
    def __init__(self, initial_data=None):
        self.data = initial_data or {}
        self.state = None
    
    async def update_data(self, **kwargs):
        self.data.update(kwargs)
        return self.data
    
    async def get_data(self):
        return self.data
    
    async def set_state(self, state):
        self.state = state
        return self.state
    
    async def get_state(self):
        return self.state
    
    async def clear(self):
        self.data = {}
        self.state = None

class MockBot:
    def __init__(self):
        self.sent_messages = []
    
    async def send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
        message = MockMessage(
            message_id=len(self.sent_messages) + 1,
            text=text,
            chat=MockChat(chat_id=chat_id),
            reply_markup=reply_markup
        )
        self.sent_messages.append({
            'chat_id': chat_id,
            'text': text,
            'reply_markup': reply_markup,
            'parse_mode': parse_mode
        })
        return message

class MockDatabase:
    def __init__(self):
        self.products = {
            1: {
                'id': 1,
                'name': 'محصول تست',
                'price': 1000000,
                'description': 'توضیحات محصول تست',
                'category_id': 1,
                'photo_url': None,
                'product_type': 'product',
                'brand': 'برند تست',
                'model': 'مدل تست',
                'in_stock': True,
                'tags': 'رادیویی,مخابراتی'
            }
        }
        
        self.services = {
            1: {
                'id': 1,
                'name': 'خدمت تست',
                'price': 500000,
                'description': 'توضیحات خدمت تست',
                'category_id': 2,
                'photo_url': None,
                'product_type': 'service',
                'tags': 'نصب,راه‌اندازی'
            }
        }
        
        self.inquiries = {}
        self.next_inquiry_id = 1
    
    def get_product(self, product_id):
        return self.products.get(int(product_id))
    
    def get_service(self, service_id):
        return self.services.get(int(service_id))
    
    def add_inquiry(self, user_id, name, phone, description, product_id=None, service_id=None, product_type=None):
        inquiry_id = self.next_inquiry_id
        self.next_inquiry_id += 1
        
        if product_id is not None:
            product_id = int(product_id)
        
        if service_id is not None:
            service_id = int(service_id)
        
        inquiry = {
            'id': inquiry_id,
            'user_id': user_id,
            'name': name,
            'phone': phone,
            'description': description,
            'product_id': product_id,
            'product_type': product_type or ('product' if product_id else ('service' if service_id else 'general'))
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
            
            # 1. کلیک روی دکمه استعلام قیمت محصول
            callback = MockCallbackQuery(data="inquiry:product:1", from_user=user, message=message)
            state = MockFSMContext()
            
            await callback_inquiry(callback, state)
            
            # بررسی ذخیره شدن شناسه محصول
            self.assertEqual(state.data.get('product_id'), 1)
            self.assertEqual(state.data.get('product_type'), 'product')
            self.assertIsNone(state.data.get('service_id'))
            
            # بررسی نمایش پیام منتظر نام
            self.assertTrue(message.answer_called)
            self.assertIn('نام', message.answer_text)
            
            # 2. وارد کردن نام
            message.text = "علی رضایی"
            await process_inquiry_name(message, state)
            
            # بررسی ذخیره شدن نام
            self.assertEqual(state.data.get('name'), "علی رضایی")
            
            # بررسی نمایش پیام منتظر شماره تماس
            self.assertIn('شماره تماس', message.answer_text)
            
            # 3. وارد کردن شماره تماس
            message.text = "09123456789"
            await process_inquiry_phone(message, state)
            
            # بررسی ذخیره شدن شماره تماس
            self.assertEqual(state.data.get('phone'), "09123456789")
            
            # بررسی نمایش پیام منتظر توضیحات
            self.assertIn('توضیحات', message.answer_text)
            
            # 4. وارد کردن توضیحات
            message.text = "لطفا قیمت دقیق محصول را اعلام کنید"
            await process_inquiry_description(message, state)
            
            # بررسی ذخیره شدن توضیحات
            self.assertEqual(state.data.get('description'), "لطفا قیمت دقیق محصول را اعلام کنید")
            
            # بررسی نمایش خلاصه استعلام و دکمه‌های تایید/لغو
            self.assertTrue(any('تأیید' in answer['text'] for answer in message.answer_history))
            
            # وجود دکمه‌های تایید و لغو را بررسی کنیم
            last_reply_markup = message.reply_markup
            self.assertIsNotNone(last_reply_markup)
            
            # 5. تایید استعلام
            confirm_callback = MockCallbackQuery(data="confirm_inquiry", from_user=user, message=message)
            await callback_confirm_inquiry(confirm_callback, state)
            
            # بررسی نمایش پیام موفقیت
            self.assertTrue(confirm_callback.answer_called)
            self.assertIn('موفقیت', message.answer_text)
            
            # بررسی داده‌های ذخیره شده در دیتابیس
            from handlers import db
            inquiry_id = max(db.inquiries.keys())
            inquiry = db.inquiries[inquiry_id]
            
            self.assertEqual(inquiry['user_id'], user.id)
            self.assertEqual(inquiry['name'], "علی رضایی")
            self.assertEqual(inquiry['phone'], "09123456789")
            self.assertEqual(inquiry['description'], "لطفا قیمت دقیق محصول را اعلام کنید")
            self.assertEqual(inquiry['product_id'], 1)
            self.assertEqual(inquiry['product_type'], 'product')
    
    async def test_service_inquiry_flow(self):
        """تست جریان کامل استعلام قیمت یک خدمت"""
        with patch('handlers.db', new=MockDatabase()):
            from handlers import callback_inquiry, process_inquiry_name, process_inquiry_phone, process_inquiry_description, callback_confirm_inquiry
            
            # ایجاد موک‌های مورد نیاز
            user = MockUser()
            chat = MockChat()
            message = MockMessage(text="", chat=chat, from_user=user)
            
            # 1. کلیک روی دکمه استعلام قیمت خدمت
            callback = MockCallbackQuery(data="inquiry:service:1", from_user=user, message=message)
            state = MockFSMContext()
            
            await callback_inquiry(callback, state)
            
            # بررسی ذخیره شدن شناسه خدمت
            self.assertEqual(state.data.get('product_id'), 1)
            self.assertEqual(state.data.get('product_type'), 'service')
            
            # بررسی نمایش پیام منتظر نام
            self.assertTrue(message.answer_called)
            self.assertIn('نام', message.answer_text)
            
            # 2. وارد کردن نام
            message.text = "محمد جعفری"
            await process_inquiry_name(message, state)
            
            # بررسی ذخیره شدن نام
            self.assertEqual(state.data.get('name'), "محمد جعفری")
            
            # بررسی نمایش پیام منتظر شماره تماس
            self.assertIn('شماره تماس', message.answer_text)
            
            # 3. وارد کردن شماره تماس
            message.text = "09187654321"
            await process_inquiry_phone(message, state)
            
            # بررسی ذخیره شدن شماره تماس
            self.assertEqual(state.data.get('phone'), "09187654321")
            
            # بررسی نمایش پیام منتظر توضیحات
            self.assertIn('توضیحات', message.answer_text)
            
            # 4. وارد کردن توضیحات
            message.text = "نیاز به نصب در محل داریم"
            await process_inquiry_description(message, state)
            
            # بررسی ذخیره شدن توضیحات
            self.assertEqual(state.data.get('description'), "نیاز به نصب در محل داریم")
            
            # بررسی نمایش خلاصه استعلام و دکمه‌های تایید/لغو
            self.assertTrue(any('تأیید' in answer['text'] for answer in message.answer_history))
            
            # وجود دکمه‌های تایید و لغو را بررسی کنیم
            last_reply_markup = message.reply_markup
            self.assertIsNotNone(last_reply_markup)
            
            # 5. تایید استعلام
            confirm_callback = MockCallbackQuery(data="confirm_inquiry", from_user=user, message=message)
            await callback_confirm_inquiry(confirm_callback, state)
            
            # بررسی نمایش پیام موفقیت
            self.assertTrue(confirm_callback.answer_called)
            self.assertIn('موفقیت', message.answer_text)
            
            # بررسی داده‌های ذخیره شده در دیتابیس
            from handlers import db
            inquiry_id = max(db.inquiries.keys())
            inquiry = db.inquiries[inquiry_id]
            
            self.assertEqual(inquiry['user_id'], user.id)
            self.assertEqual(inquiry['name'], "محمد جعفری")
            self.assertEqual(inquiry['phone'], "09187654321")
            self.assertEqual(inquiry['description'], "نیاز به نصب در محل داریم")
            self.assertEqual(inquiry['product_id'], 1)
            self.assertEqual(inquiry['product_type'], 'service')

    async def test_general_inquiry_flow(self):
        """تست جریان استعلام قیمت عمومی (بدون محصول/خدمت خاص)"""
        with patch('handlers.db', new=MockDatabase()):
            from handlers import callback_general_inquiry, process_inquiry_name, process_inquiry_phone, process_inquiry_description, callback_confirm_inquiry
            
            # ایجاد موک‌های مورد نیاز
            user = MockUser()
            chat = MockChat()
            message = MockMessage(text="", chat=chat, from_user=user)
            
            # 1. کلیک روی دکمه استعلام قیمت عمومی
            callback = MockCallbackQuery(data="general_inquiry", from_user=user, message=message)
            state = MockFSMContext()
            
            await callback_general_inquiry(callback, state)
            
            # بررسی تنظیم نوع استعلام به عمومی
            self.assertEqual(state.data.get('product_type'), 'general')
            self.assertIsNone(state.data.get('product_id'))
            
            # بررسی نمایش پیام منتظر نام
            self.assertTrue(message.answer_called)
            self.assertIn('نام', message.answer_text)
            
            # 2. وارد کردن نام
            message.text = "حسین محمدی"
            await process_inquiry_name(message, state)
            
            # بررسی ذخیره شدن نام
            self.assertEqual(state.data.get('name'), "حسین محمدی")
            
            # 3. وارد کردن شماره تماس
            message.text = "09123789456"
            await process_inquiry_phone(message, state)
            
            # بررسی ذخیره شدن شماره تماس
            self.assertEqual(state.data.get('phone'), "09123789456")
            
            # 4. وارد کردن توضیحات
            message.text = "نیاز به اطلاعات در مورد محصولات رادیویی جدید"
            await process_inquiry_description(message, state)
            
            # بررسی ذخیره شدن توضیحات
            self.assertEqual(state.data.get('description'), "نیاز به اطلاعات در مورد محصولات رادیویی جدید")
            
            # 5. تایید استعلام
            confirm_callback = MockCallbackQuery(data="confirm_inquiry", from_user=user, message=message)
            await callback_confirm_inquiry(confirm_callback, state)
            
            # بررسی نمایش پیام موفقیت
            self.assertTrue(confirm_callback.answer_called)
            self.assertIn('موفقیت', message.answer_text)
            
            # بررسی داده‌های ذخیره شده در دیتابیس
            from handlers import db
            inquiry_id = max(db.inquiries.keys())
            inquiry = db.inquiries[inquiry_id]
            
            self.assertEqual(inquiry['user_id'], user.id)
            self.assertEqual(inquiry['name'], "حسین محمدی")
            self.assertEqual(inquiry['phone'], "09123789456")
            self.assertEqual(inquiry['description'], "نیاز به اطلاعات در مورد محصولات رادیویی جدید")
            self.assertEqual(inquiry['product_type'], 'general')
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
            
            # آزمایش شماره‌های مختلف
            invalid_numbers = [
                "123", 
                "09", 
                "۰۹۱۲۳۴۵۶۷۸۹",  # با اعداد فارسی
                "abcdefghij",
                "+989121234567"  # فرمت بین‌المللی (در بعضی سیستم‌ها معتبر است)
            ]
            
            for number in invalid_numbers:
                message.text = number
                message.answer_called = False
                await process_inquiry_phone(message, state)
                self.assertNotIn('phone', state.data)
                self.assertTrue(message.answer_called)
                self.assertIn('معتبر', message.answer_text)
            
            # آزمایش شماره صحیح
            message.text = "09123456789"
            message.answer_called = False
            await process_inquiry_phone(message, state)
            self.assertEqual(state.data.get('phone'), "09123456789")

    async def test_inquiry_cancel(self):
        """تست لغو استعلام قیمت"""
        with patch('handlers.db', new=MockDatabase()):
            from handlers import callback_cancel_inquiry
            
            # ایجاد موک‌های مورد نیاز
            user = MockUser()
            chat = MockChat()
            message = MockMessage(text="", chat=chat, from_user=user)
            callback = MockCallbackQuery(data="cancel_inquiry", from_user=user, message=message)
            
            # وضعیت اولیه: در حال استعلام قیمت محصول
            state = MockFSMContext({
                'product_id': 1,
                'product_type': 'product',
                'name': 'کاربر تست',
                'phone': '09123456789',
                'description': 'توضیحات تست'
            })
            
            # لغو استعلام
            await callback_cancel_inquiry(callback, state)
            
            # بررسی پاک شدن وضعیت
            self.assertEqual(state.data, {})
            self.assertIsNone(state.state)
            
            # بررسی نمایش پیام لغو و منو
            self.assertTrue(callback.answer_called)
            self.assertTrue(message.answer_called)
            
            # باید دو پیام نمایش داده شود: پیام لغو و پیام منو
            # پیامی که بررسی می‌کنیم مربوط به منو است (چون در واقع دو پیام جداگانه ارسال می‌شود)
            self.assertEqual(message.answer_text, "می‌توانید به استفاده از ربات ادامه دهید:")
            
            # بررسی کنیم که دکمه‌های منو وجود داشته باشند
            self.assertIsNotNone(message.reply_markup)

    async def test_phone_validation_pattern(self):
        """تست الگوی اعتبارسنجی شماره تلفن"""
        # بررسی الگوی اعتبارسنجی شماره تلفن که در کد استفاده می‌شود
        phone_pattern = re.compile(r'^09\d{9}$')
        
        # شماره‌های معتبر
        valid_numbers = [
            "09123456789",
            "09301234567",
            "09911234567",
            "09000000000",
            "09999999999"
        ]
        
        for number in valid_numbers:
            self.assertTrue(phone_pattern.match(number), f"شماره {number} باید معتبر باشد")
        
        # شماره‌های نامعتبر
        invalid_numbers = [
            "9123456789",    # بدون صفر ابتدایی
            "091234567890",  # بیش از 11 رقم
            "0912345678",    # کمتر از 11 رقم
            "09۱۲۳۴۵۶۷۸۹",   # با اعداد فارسی
            "+989123456789",  # فرمت بین‌المللی
            "09-123-45678",  # با خط تیره
            "0 9123456789",  # با فاصله
            "09ABCDEFGHI",   # با حروف
            "9876543210"     # فرمت نامعتبر
        ]
        
        for number in invalid_numbers:
            self.assertFalse(phone_pattern.match(number), f"شماره {number} باید نامعتبر باشد")

# اجرای تست‌ها
def run_test():
    """اجرای همه تست‌ها"""
    # تبدیل تست‌های async به sync برای unittest
    def async_test(coro):
        def wrapper(*args, **kwargs):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro(*args, **kwargs))
            finally:
                loop.close()
        return wrapper
    
    # اعمال دکوریتور async_test به همه متدهای تست
    for attr in dir(TestTelegramInquiry):
        if attr.startswith('test_'):
            setattr(TestTelegramInquiry, attr, async_test(getattr(TestTelegramInquiry, attr)))
    
    # اجرای تست‌ها
    unittest.main()

if __name__ == "__main__":
    run_test()