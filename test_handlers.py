#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست اتوماتیک برای توابع handlers ربات تلگرام
این اسکریپت توابع handlers را با استفاده از اشیاء مجازی (mock) تست می‌کند
"""

import unittest
import asyncio
import logging
from datetime import datetime

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import project modules
from app import app, db
from models import Product, Inquiry, User, Category
from aiogram.types import Message, CallbackQuery, Chat, User as TelegramUser
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# کلاس‌های Mock برای آزمایش
class MockFSMContext:
    """کلاس مجازی برای FSMContext"""
    def __init__(self):
        self.data = {}
        self.state = None
        
    async def get_state(self):
        return self.state
        
    async def set_state(self, state):
        self.state = state
        logger.info(f"State set to: {state}")
        return True
        
    async def update_data(self, **kwargs):
        logger.info(f"Updating data with: {kwargs}")
        self.data.update(kwargs)
        return True
        
    async def get_data(self):
        return self.data
        
    async def clear(self):
        self.data = {}
        self.state = None
        logger.info("State cleared")
        return True

class TestHandlerFunctions(unittest.TestCase):
    
    def setUp(self):
        """آماده‌سازی محیط تست"""
        # ایجاد آبجکت‌های مجازی
        self.state_context = MockFSMContext()
        
        # وارد کردن ماژول handlers
        import handlers
        self.handlers = handlers
    
    async def test_start_command(self):
        """تست دستور /start"""
        print("\n=== تست دستور /start ===")
        
        # ایجاد یک پیام تلگرامی مجازی
        message = Message(
            message_id=1,
            date=datetime.now(),
            chat=Chat(id=123456789, type="private"),
            from_user=TelegramUser(id=123456789, is_bot=False, first_name="Test User"),
            text="/start"
        )
        
        # فراخوانی تابع cmd_start
        await self.handlers.cmd_start(message, self.state_context)
        
        # بررسی نتیجه
        state = await self.state_context.get_state()
        self.assertIsNone(state, "حالت FSM باید بعد از دستور /start پاک شود")
        print("✓ تست دستور /start با موفقیت انجام شد")
    
    async def test_products_command(self):
        """تست دستور /products"""
        print("\n=== تست دستور /products ===")
        
        # ایجاد یک پیام تلگرامی مجازی
        message = Message(
            message_id=1,
            date=datetime.now(),
            chat=Chat(id=123456789, type="private"),
            from_user=TelegramUser(id=123456789, is_bot=False, first_name="Test User"),
            text="/products"
        )
        
        # فراخوانی تابع cmd_products
        await self.handlers.cmd_products(message, self.state_context)
        
        # بررسی نتیجه
        state = await self.state_context.get_state()
        self.assertEqual(state, "UserStates:browse_categories", "حالت باید به browse_categories تغییر کند")
        
        # بررسی داده‌های ذخیره شده
        data = await self.state_context.get_data()
        self.assertEqual(data.get('cat_type'), 'product', "نوع دسته‌بندی باید 'product' باشد")
        print("✓ تست دستور /products با موفقیت انجام شد")
    
    async def test_services_command(self):
        """تست دستور /services"""
        print("\n=== تست دستور /services ===")
        
        # ایجاد یک پیام تلگرامی مجازی
        message = Message(
            message_id=1,
            date=datetime.now(),
            chat=Chat(id=123456789, type="private"),
            from_user=TelegramUser(id=123456789, is_bot=False, first_name="Test User"),
            text="/services"
        )
        
        # فراخوانی تابع cmd_services
        await self.handlers.cmd_services(message, self.state_context)
        
        # بررسی نتیجه
        state = await self.state_context.get_state()
        self.assertEqual(state, "UserStates:browse_categories", "حالت باید به browse_categories تغییر کند")
        
        # بررسی داده‌های ذخیره شده
        data = await self.state_context.get_data()
        self.assertEqual(data.get('cat_type'), 'service', "نوع دسته‌بندی باید 'service' باشد")
        print("✓ تست دستور /services با موفقیت انجام شد")

    async def test_menu_command(self):
        """تست دستور /menu"""
        print("\n=== تست دستور /menu ===")
        
        # ایجاد یک پیام تلگرامی مجازی
        message = Message(
            message_id=1,
            date=datetime.now(),
            chat=Chat(id=123456789, type="private"),
            from_user=TelegramUser(id=123456789, is_bot=False, first_name="Test User"),
            text="/menu"
        )
        
        # فراخوانی تابع cmd_menu
        await self.handlers.cmd_menu(message, self.state_context)
        
        # بررسی نتیجه - حالت باید پاک شود
        state = await self.state_context.get_state()
        self.assertIsNone(state, "حالت FSM باید بعد از دستور /menu پاک شود")
        print("✓ تست دستور /menu با موفقیت انجام شد")
    
    async def run_all_tests(self):
        """اجرای تمام تست‌ها"""
        await self.test_start_command()
        await self.test_menu_command()
        await self.test_products_command()
        await self.test_services_command()
    
    def test_handlers(self):
        """متد اصلی تست که توسط unittest فراخوانی می‌شود"""
        print("\n===== شروع تست توابع handlers =====")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.run_all_tests())
        print("\n===== پایان تست توابع handlers =====")

if __name__ == "__main__":
    unittest.main()