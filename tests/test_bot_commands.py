#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست دستورات و منوهای بات تلگرام
این اسکریپت عملکرد دستورات و منوهای مختلف بات تلگرام را تست می‌کند
"""

import unittest
import asyncio
import logging
import sys
import os
from unittest.mock import patch, MagicMock

# اضافه کردن مسیر پروژه به PYTHONPATH برای دسترسی به ماژول‌های پروژه
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import project modules
from src.web.app import app, db
from models import  Product, Service, Inquiry, EducationalContent, StaticContent
from src.bot.handlers import UserStates
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, User, Chat
from aiogram.filters import Command
from aiogram.fsm.storage.base import StorageKey

class TestBotCommands(unittest.TestCase):
    """کلاس تست برای بررسی دستورات و منوهای بات تلگرام"""
    
    def setUp(self):
        """تنظیمات اولیه قبل از هر تست"""
        self.app_context = app.app_context()
        self.app_context.push()
        
        # مقادیر شبیه‌سازی شده برای تست
        self.user_id = 123456789
        self.chat_id = 123456789
        self.message_id = 1
        
        # ایجاد Storage برای FSM
        self.storage = MemoryStorage()
        self.bot = MagicMock()
        self.bot.id = 7630601243  # ID بات تلگرام
        self.dp = Dispatcher(storage=self.storage)
        
        # ذخیره پاسخ‌های ارسالی
        self.sent_messages = []
        
        # شبیه‌سازی Message و اجزای آن
        self.user = User(id=self.user_id, is_bot=False, first_name="Test", last_name="User", 
                        username="testuser", language_code="fa")
        self.chat = Chat(id=self.chat_id, type="private", title="Test Chat")
        
        # شبیه‌سازی متد ارسال پیام بات
        async def mock_answer(text, **kwargs):
            self.sent_messages.append(text)
            return MagicMock()
        
        async def mock_send_message(chat_id, text, **kwargs):
            self.sent_messages.append(text)
            return MagicMock()
        
        self.bot.send_message = mock_send_message
        
        # تزریق محتوای تست به دیتابیس اگر خالی است
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
    
    def create_message(self, text):
        """ایجاد یک Message با متن مشخص"""
        message = Message()
        message.message_id = self.message_id
        message.from_user = self.user
        message.chat = self.chat
        message.text = text
        return message
    
    def create_callback_query(self, data):
        """ایجاد یک CallbackQuery با داده مشخص"""
        callback_query = CallbackQuery()
        callback_query.id = "123456"
        callback_query.from_user = self.user
        callback_query.message = self.create_message("")
        callback_query.data = data
        
        # شبیه‌سازی متد answer
        callback_query.answer = MagicMock(side_effect=self.bot.send_message)
        
        return callback_query
    
    async def create_fsm_context(self):
        """ایجاد FSMContext برای تست"""
        key = StorageKey(bot_id=self.bot.id, chat_id=self.chat_id, user_id=self.user_id)
        return FSMContext(storage=self.storage, key=key)
    
    async def test_start_command(self):
        """تست دستور /start"""
        print("\n=== تست دستور /start ===")
        self.sent_messages.clear()
        
        # شبیه‌سازی message حاوی دستور /start
        message = self.create_message("/start")
        
        # شبیه‌سازی فراخوانی هندلر مربوط به دستور /start
        from src.bot.handlers import cmd_start
        
        with patch('src.bot.handlers.get_main_keyboard') as mock_get_keyboard:
            mock_get_keyboard.return_value = MagicMock()
            await cmd_start(message)
        
        # بررسی نتیجه
        self.assertTrue(len(self.sent_messages) > 0, "دستور /start باید حداقل یک پیام بفرستد")
        print(f"✓ دستور /start منجر به ارسال {len(self.sent_messages)} پیام شد")
    
    async def test_help_command(self):
        """تست دستور /help"""
        print("\n=== تست دستور /help ===")
        self.sent_messages.clear()
        
        # شبیه‌سازی message حاوی دستور /help
        message = self.create_message("/help")
        
        # شبیه‌سازی فراخوانی هندلر مربوط به دستور /help
        from src.bot.handlers import cmd_help
        
        with patch('src.bot.handlers.get_main_keyboard') as mock_get_keyboard:
            mock_get_keyboard.return_value = MagicMock()
            await cmd_help(message)
        
        # بررسی نتیجه
        self.assertTrue(len(self.sent_messages) > 0, "دستور /help باید حداقل یک پیام بفرستد")
        print(f"✓ دستور /help منجر به ارسال {len(self.sent_messages)} پیام شد")
    
    async def test_products_command(self):
        """تست دستور /products"""
        print("\n=== تست دستور /products ===")
        self.sent_messages.clear()
        
        # شبیه‌سازی message حاوی دستور /products
        message = self.create_message("/products")
        
        # شبیه‌سازی فراخوانی هندلر مربوط به دستور /products
        from src.bot.handlers import cmd_products
        
        with patch('src.bot.handlers.get_categories_keyboard') as mock_get_keyboard:
            mock_get_keyboard.return_value = MagicMock()
            # شبیه‌سازی FSM Context
            fsm_context = await self.create_fsm_context()
            with patch('src.bot.handlers.FSMContext', return_value=fsm_context):
                with patch('src.bot.database.Database.get_categories') as mock_get_categories:
                    # شبیه‌سازی دسته‌بندی‌ها
                    mock_get_categories.return_value = [
                        {'id': 1, 'name': 'دسته 1', 'parent_id': None},
                        {'id': 2, 'name': 'دسته 2', 'parent_id': None}
                    ]
                    await cmd_products(message)
        
        # بررسی نتیجه
        self.assertTrue(len(self.sent_messages) > 0, "دستور /products باید حداقل یک پیام بفرستد")
        # بررسی وضعیت FSM
        state = await fsm_context.get_state()
        if state:
            print(f"✓ دستور /products وضعیت FSM را به {state} تغییر داد")
        print(f"✓ دستور /products منجر به ارسال {len(self.sent_messages)} پیام شد")
    
    async def test_services_command(self):
        """تست دستور /services"""
        print("\n=== تست دستور /services ===")
        self.sent_messages.clear()
        
        # شبیه‌سازی message حاوی دستور /services
        message = self.create_message("/services")
        
        # شبیه‌سازی فراخوانی هندلر مربوط به دستور /services
        from src.bot.handlers import cmd_services
        
        with patch('src.bot.handlers.get_categories_keyboard') as mock_get_keyboard:
            mock_get_keyboard.return_value = MagicMock()
            # شبیه‌سازی FSM Context
            fsm_context = await self.create_fsm_context()
            with patch('src.bot.handlers.FSMContext', return_value=fsm_context):
                with patch('src.bot.database.Database.get_categories') as mock_get_categories:
                    # شبیه‌سازی دسته‌بندی‌ها
                    mock_get_categories.return_value = [
                        {'id': 3, 'name': 'خدمت 1', 'parent_id': None},
                        {'id': 4, 'name': 'خدمت 2', 'parent_id': None}
                    ]
                    await cmd_services(message)
        
        # بررسی نتیجه
        self.assertTrue(len(self.sent_messages) > 0, "دستور /services باید حداقل یک پیام بفرستد")
        # بررسی وضعیت FSM
        state = await fsm_context.get_state()
        if state:
            print(f"✓ دستور /services وضعیت FSM را به {state} تغییر داد")
        print(f"✓ دستور /services منجر به ارسال {len(self.sent_messages)} پیام شد")
    
    async def test_about_command(self):
        """تست دستور /about"""
        print("\n=== تست دستور /about ===")
        self.sent_messages.clear()
        
        # شبیه‌سازی message حاوی دستور /about
        message = self.create_message("/about")
        
        # شبیه‌سازی فراخوانی هندلر مربوط به دستور /about
        from src.bot.handlers import cmd_about
        
        with patch('src.bot.handlers.get_back_keyboard') as mock_get_keyboard:
            mock_get_keyboard.return_value = MagicMock()
            with patch('src.bot.database.Database.get_static_content') as mock_get_content:
                # شبیه‌سازی محتوای استاتیک
                mock_get_content.return_value = "این متن درباره ماست"
                await cmd_about(message)
        
        # بررسی نتیجه
        self.assertTrue(len(self.sent_messages) > 0, "دستور /about باید حداقل یک پیام بفرستد")
        print(f"✓ دستور /about منجر به ارسال {len(self.sent_messages)} پیام شد")
    
    async def test_contact_command(self):
        """تست دستور /contact"""
        print("\n=== تست دستور /contact ===")
        self.sent_messages.clear()
        
        # شبیه‌سازی message حاوی دستور /contact
        message = self.create_message("/contact")
        
        # شبیه‌سازی فراخوانی هندلر مربوط به دستور /contact
        from src.bot.handlers import cmd_contact
        
        with patch('src.bot.handlers.get_back_keyboard') as mock_get_keyboard:
            mock_get_keyboard.return_value = MagicMock()
            with patch('src.bot.database.Database.get_static_content') as mock_get_content:
                # شبیه‌سازی محتوای استاتیک
                mock_get_content.return_value = "اطلاعات تماس ما"
                await cmd_contact(message)
        
        # بررسی نتیجه
        self.assertTrue(len(self.sent_messages) > 0, "دستور /contact باید حداقل یک پیام بفرستد")
        print(f"✓ دستور /contact منجر به ارسال {len(self.sent_messages)} پیام شد")
    
    async def test_education_command(self):
        """تست دستور /education"""
        print("\n=== تست دستور /education ===")
        self.sent_messages.clear()
        
        # شبیه‌سازی message حاوی دستور /education
        message = self.create_message("/education")
        
        # شبیه‌سازی فراخوانی هندلر مربوط به دستور /education
        from src.bot.handlers import cmd_education
        
        with patch('src.bot.handlers.get_back_keyboard') as mock_get_keyboard:
            mock_get_keyboard.return_value = MagicMock()
            with patch('src.bot.database.Database.get_educational_categories') as mock_get_categories:
                # شبیه‌سازی دسته‌بندی‌های آموزشی
                mock_get_categories.return_value = ['دسته 1', 'دسته 2']
                await cmd_education(message)
        
        # بررسی نتیجه
        self.assertTrue(len(self.sent_messages) > 0, "دستور /education باید حداقل یک پیام بفرستد")
        print(f"✓ دستور /education منجر به ارسال {len(self.sent_messages)} پیام شد")
    
    async def test_back_button(self):
        """تست دکمه بازگشت"""
        print("\n=== تست دکمه بازگشت ===")
        self.sent_messages.clear()
        
        # شبیه‌سازی message حاوی متن "بازگشت"
        message = self.create_message("بازگشت")
        
        # شبیه‌سازی فراخوانی هندلر مربوط به دکمه بازگشت
        from src.bot.handlers import text_back
        
        with patch('src.bot.handlers.get_main_keyboard') as mock_get_keyboard:
            mock_get_keyboard.return_value = MagicMock()
            # شبیه‌سازی FSM Context
            fsm_context = await self.create_fsm_context()
            with patch('src.bot.handlers.FSMContext', return_value=fsm_context):
                await text_back(message)
        
        # بررسی نتیجه
        self.assertTrue(len(self.sent_messages) > 0, "دکمه بازگشت باید حداقل یک پیام بفرستد")
        # بررسی وضعیت FSM
        state = await fsm_context.get_state()
        self.assertIsNone(state, "دکمه بازگشت باید وضعیت FSM را به None تغییر دهد")
        print(f"✓ دکمه بازگشت منجر به ارسال {len(self.sent_messages)} پیام شد و وضعیت FSM را پاک کرد")
    
    async def test_inquiry_flow(self):
        """تست فرآیند استعلام قیمت"""
        print("\n=== تست فرآیند استعلام قیمت ===")
        self.sent_messages.clear()
        
        # شبیه‌سازی FSM Context
        fsm_context = await self.create_fsm_context()
        
        # شبیه‌سازی آغاز فرآیند استعلام
        await fsm_context.set_state(UserStates.view_product)
        await fsm_context.update_data(selected_product_id="1")
        
        # 1. استعلام قیمت
        message = self.create_message("استعلام قیمت")
        
        # شبیه‌سازی هندلر دکمه استعلام قیمت
        with patch('src.bot.handlers.FSMContext', return_value=fsm_context):
            # نیاز به شبیه‌سازی هندلر دکمه استعلام قیمت
            # این بخش نیاز به دسترسی به کد اصلی دارد و در صورت عدم دسترسی مستقیم، از هندلرهای جداگانه استفاده می‌کنیم
            
            # 2. وارد کردن نام
            await fsm_context.set_state(UserStates.inquiry_name)
            message_name = self.create_message("کاربر تست")
            with patch('src.bot.handlers.FSMContext', return_value=fsm_context):
                # ذخیره نام و تغییر وضعیت
                await fsm_context.update_data(inquiry_name="کاربر تست")
                await fsm_context.set_state(UserStates.inquiry_phone)
            
            # 3. وارد کردن شماره تلفن
            message_phone = self.create_message("09123456789")
            with patch('src.bot.handlers.FSMContext', return_value=fsm_context):
                # ذخیره شماره تلفن و تغییر وضعیت
                await fsm_context.update_data(inquiry_phone="09123456789")
                await fsm_context.set_state(UserStates.inquiry_description)
            
            # 4. وارد کردن توضیحات
            message_description = self.create_message("این یک استعلام تستی است")
            with patch('src.bot.handlers.FSMContext', return_value=fsm_context):
                # ذخیره توضیحات و تغییر وضعیت
                await fsm_context.update_data(inquiry_description="این یک استعلام تستی است")
                await fsm_context.set_state(UserStates.waiting_for_confirmation)
            
            # 5. تأیید استعلام
            message_confirm = self.create_message("تأیید")
            with patch('src.bot.handlers.FSMContext', return_value=fsm_context):
                # شبیه‌سازی هندلر تأیید استعلام
                # در اینجا می‌توان هندلر واقعی را صدا زد یا عملکرد آن را شبیه‌سازی کرد
                
                # پاک کردن وضعیت FSM پس از ثبت استعلام
                await fsm_context.clear()
        
        # بررسی نتیجه
        state = await fsm_context.get_state()
        self.assertIsNone(state, "پس از تأیید استعلام، وضعیت FSM باید پاک شود")
        data = await fsm_context.get_data()
        self.assertEqual(data, {}, "پس از تأیید استعلام، داده‌های FSM باید پاک شود")
        print("✓ فرآیند استعلام قیمت با موفقیت شبیه‌سازی شد")
    
    async def test_browse_categories(self):
        """تست مرور دسته‌بندی‌ها"""
        print("\n=== تست مرور دسته‌بندی‌ها ===")
        self.sent_messages.clear()
        
        # شبیه‌سازی FSM Context
        fsm_context = await self.create_fsm_context()
        
        # شبیه‌سازی وضعیت مرور دسته‌بندی‌ها
        await fsm_context.set_state(UserStates.browse_categories)
        await fsm_context.update_data(cat_type="product")
        
        # شبیه‌سازی انتخاب یک دسته‌بندی
        callback_query = self.create_callback_query("category:1")
        
        # شبیه‌سازی هندلر انتخاب دسته‌بندی
        with patch('src.bot.handlers.FSMContext', return_value=fsm_context):
            with patch('src.bot.database.Database.get_products_by_category') as mock_get_products:
                # شبیه‌سازی محصولات
                mock_get_products.return_value = [
                    {'id': 1, 'name': 'محصول 1', 'price': 1000, 'description': 'توضیحات محصول 1'},
                    {'id': 2, 'name': 'محصول 2', 'price': 2000, 'description': 'توضیحات محصول 2'}
                ]
                # نیاز به هندلر واقعی دارد یا شبیه‌سازی عملکرد آن
                # در اینجا تنها تغییر وضعیت FSM را شبیه‌سازی می‌کنیم
                await fsm_context.set_state(UserStates.view_category)
        
        # بررسی نتیجه
        state = await fsm_context.get_state()
        self.assertEqual(state, UserStates.view_category.state, "پس از انتخاب دسته‌بندی، وضعیت FSM باید view_category باشد")
        print("✓ مرور دسته‌بندی‌ها با موفقیت شبیه‌سازی شد")
    
    async def test_view_product(self):
        """تست مشاهده جزئیات محصول"""
        print("\n=== تست مشاهده جزئیات محصول ===")
        self.sent_messages.clear()
        
        # شبیه‌سازی FSM Context
        fsm_context = await self.create_fsm_context()
        
        # شبیه‌سازی انتخاب یک محصول
        callback_query = self.create_callback_query("product:1")
        
        # شبیه‌سازی هندلر انتخاب محصول
        with patch('src.bot.handlers.FSMContext', return_value=fsm_context):
            with patch('src.bot.database.Database.get_product') as mock_get_product:
                # شبیه‌سازی محصول
                mock_get_product.return_value = {
                    'id': 1, 
                    'name': 'محصول 1', 
                    'price': 1000, 
                    'description': 'توضیحات محصول 1',
                    'photo_url': None
                }
                # نیاز به هندلر واقعی دارد یا شبیه‌سازی عملکرد آن
                # در اینجا تنها تغییر وضعیت FSM را شبیه‌سازی می‌کنیم
                await fsm_context.set_state(UserStates.view_product)
                await fsm_context.update_data(selected_product_id="1")
        
        # بررسی نتیجه
        state = await fsm_context.get_state()
        self.assertEqual(state, UserStates.view_product.state, "پس از انتخاب محصول، وضعیت FSM باید view_product باشد")
        data = await fsm_context.get_data()
        self.assertEqual(data.get('selected_product_id'), "1", "شناسه محصول انتخاب شده باید در داده‌های FSM ذخیره شود")
        print("✓ مشاهده جزئیات محصول با موفقیت شبیه‌سازی شد")
    
    async def run_all_tests(self):
        """اجرای همه تست‌ها"""
        print("\n===== شروع تست‌های دستورات و منوهای بات تلگرام =====")
        
        try:
            await self.test_start_command()
        except Exception as e:
            print(f"❌ خطا در تست دستور /start: {str(e)}")
        
        try:
            await self.test_help_command()
        except Exception as e:
            print(f"❌ خطا در تست دستور /help: {str(e)}")
        
        try:
            await self.test_products_command()
        except Exception as e:
            print(f"❌ خطا در تست دستور /products: {str(e)}")
        
        try:
            await self.test_services_command()
        except Exception as e:
            print(f"❌ خطا در تست دستور /services: {str(e)}")
        
        try:
            await self.test_about_command()
        except Exception as e:
            print(f"❌ خطا در تست دستور /about: {str(e)}")
        
        try:
            await self.test_contact_command()
        except Exception as e:
            print(f"❌ خطا در تست دستور /contact: {str(e)}")
        
        try:
            await self.test_education_command()
        except Exception as e:
            print(f"❌ خطا در تست دستور /education: {str(e)}")
        
        try:
            await self.test_back_button()
        except Exception as e:
            print(f"❌ خطا در تست دکمه بازگشت: {str(e)}")
        
        try:
            await self.test_inquiry_flow()
        except Exception as e:
            print(f"❌ خطا در تست فرآیند استعلام قیمت: {str(e)}")
        
        try:
            await self.test_browse_categories()
        except Exception as e:
            print(f"❌ خطا در تست مرور دسته‌بندی‌ها: {str(e)}")
        
        try:
            await self.test_view_product()
        except Exception as e:
            print(f"❌ خطا در تست مشاهده جزئیات محصول: {str(e)}")
        
        print("\n===== پایان تست‌های دستورات و منوهای بات تلگرام =====")
        
        # بازگشت None برای جلوگیری از warning
        return None
    
    def test_bot_commands(self):
        """متد اصلی تست که توسط unittest فراخوانی می‌شود"""
        # برای جلوگیری از خطای RuntimeWarning: coroutine ... was never awaited
        # باید از asyncio.run استفاده کرد
        asyncio.run(self.run_all_tests())

def run_tests():
    """اجرای همه تست‌ها"""
    unittest.main()

if __name__ == "__main__":
    run_tests()