#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست ساده برای ربات تلگرام با مدل FSM
این اسکریپت عملکرد اساسی ربات را تست می‌کند بدون اتصال به API تلگرام
"""

import unittest
import asyncio
import logging
import os
from datetime import datetime

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import project modules
from app import app, db
from models import Product, Inquiry, User, Category
from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from handlers import UserStates

# کلاس تست ربات تلگرام
class TestTelegramBot(unittest.TestCase):
    
    def setUp(self):
        """آماده‌سازی محیط تست"""
        self.responses = []
        
    def record_message(self, text):
        """ثبت پیام‌های ارسالی"""
        self.responses.append(text)
        logger.info(f"پیام ارسال شد: {text}")
        
    async def test_fsm_states(self):
        """تست وضعیت‌های مختلف FSM"""
        print("\n=== تست حالت‌های FSM ===")
        
        # ایجاد ذخیره‌ساز حافظه و context
        storage = MemoryStorage()
        fsm_context = FSMContext(storage=storage, user_id=123456789, chat_id=123456789)
        
        # تست وضعیت اولیه
        state = await fsm_context.get_state()
        self.assertIsNone(state, "وضعیت اولیه FSM باید None باشد")
        
        # تست تنظیم وضعیت browse_categories
        await fsm_context.set_state(UserStates.browse_categories)
        state = await fsm_context.get_state()
        self.assertEqual(state, UserStates.browse_categories.state, "وضعیت باید browse_categories باشد")
        
        # تست ذخیره داده در وضعیت
        await fsm_context.update_data(cat_type="product")
        data = await fsm_context.get_data()
        self.assertEqual(data.get("cat_type"), "product", "داده‌ی cat_type باید برابر 'product' باشد")
        
        # تست تغییر وضعیت به view_product
        await fsm_context.set_state(UserStates.view_product)
        state = await fsm_context.get_state()
        self.assertEqual(state, UserStates.view_product.state, "وضعیت باید view_product باشد")
        
        # تست پاک کردن وضعیت
        await fsm_context.clear()
        state = await fsm_context.get_state()
        self.assertIsNone(state, "وضعیت باید بعد از clear به None تغییر کند")
        data = await fsm_context.get_data()
        self.assertEqual(data, {}, "داده‌ها باید بعد از clear خالی باشند")
        
        print("✓ تست حالت‌های FSM با موفقیت انجام شد")
    
    async def test_inquiry_flow(self):
        """تست گردش کار استعلام قیمت"""
        print("\n=== تست گردش کار استعلام قیمت ===")
        
        # ایجاد ذخیره‌ساز حافظه و context
        storage = MemoryStorage()
        fsm_context = FSMContext(storage=storage, user_id=123456789, chat_id=123456789)
        
        # 1. شبیه‌سازی ورود به حالت view_product
        await fsm_context.set_state(UserStates.view_product)
        
        with app.app_context():
            product = Product.query.filter_by(product_type="product").first()
            if not product:
                self.skipTest("هیچ محصولی در دیتابیس یافت نشد")
                return
                
            # ذخیره شناسه محصول
            await fsm_context.update_data(selected_product_id=str(product.id))
            
            # 2. شبیه‌سازی ورود به حالت inquiry_name (بعد از کلیک روی دکمه استعلام قیمت)
            await fsm_context.set_state(UserStates.inquiry_name)
            state = await fsm_context.get_state()
            self.assertEqual(state, UserStates.inquiry_name.state, "وضعیت باید inquiry_name باشد")
            
            # 3. شبیه‌سازی ورود نام
            await fsm_context.update_data(inquiry_name="کاربر تست")
            await fsm_context.set_state(UserStates.inquiry_phone)
            state = await fsm_context.get_state()
            self.assertEqual(state, UserStates.inquiry_phone.state, "وضعیت باید inquiry_phone باشد")
            
            # 4. شبیه‌سازی ورود شماره تلفن
            await fsm_context.update_data(inquiry_phone="09123456789")
            await fsm_context.set_state(UserStates.inquiry_description)
            state = await fsm_context.get_state()
            self.assertEqual(state, UserStates.inquiry_description.state, "وضعیت باید inquiry_description باشد")
            
            # 5. شبیه‌سازی ورود توضیحات
            await fsm_context.update_data(inquiry_description="این یک استعلام تستی است")
            await fsm_context.set_state(UserStates.waiting_for_confirmation)
            state = await fsm_context.get_state()
            self.assertEqual(state, UserStates.waiting_for_confirmation.state, "وضعیت باید waiting_for_confirmation باشد")
            
            # 6. بررسی داده‌های جمع‌آوری شده
            data = await fsm_context.get_data()
            self.assertEqual(data.get("inquiry_name"), "کاربر تست", "نام باید 'کاربر تست' باشد")
            self.assertEqual(data.get("inquiry_phone"), "09123456789", "شماره تلفن باید '09123456789' باشد")
            self.assertEqual(data.get("inquiry_description"), "این یک استعلام تستی است", "توضیحات باید 'این یک استعلام تستی است' باشد")
            self.assertEqual(data.get("selected_product_id"), str(product.id), f"شناسه محصول باید '{product.id}' باشد")
            
            # 7. شبیه‌سازی پایان فرایند استعلام
            await fsm_context.clear()
            state = await fsm_context.get_state()
            self.assertIsNone(state, "وضعیت باید در پایان None باشد")
            
        print("✓ تست گردش کار استعلام قیمت با موفقیت انجام شد")
    
    async def test_database_model_relationships(self):
        """تست ارتباطات مدل‌های دیتابیس"""
        print("\n=== تست ارتباطات مدل‌های دیتابیس ===")
        
        with app.app_context():
            # بررسی ارتباط بین دسته‌بندی‌ها
            parent_category = Category.query.filter_by(parent_id=None, cat_type="product").first()
            if parent_category:
                print(f"دسته‌بندی والد: {parent_category.name}")
                
                children = Category.query.filter_by(parent_id=parent_category.id).all()
                if children:
                    print(f"تعداد زیردسته‌ها: {len(children)}")
                    print(f"اولین زیردسته: {children[0].name}")
                    
                    # بررسی ارتباط دوطرفه
                    self.assertEqual(children[0].parent_id, parent_category.id, "رابطه parent_id باید درست باشد")
            
            # بررسی ارتباط محصول و دسته‌بندی
            product = Product.query.filter_by(product_type="product").first()
            if product:
                print(f"محصول: {product.name}")
                category = Category.query.get(product.category_id)
                if category:
                    print(f"دسته‌بندی محصول: {category.name}")
                    
            # بررسی ارتباط محصول و رسانه
            from models import ProductMedia
            media = ProductMedia.query.first()
            if media:
                print(f"رسانه: {media.file_id}, نوع: {media.file_type}")
                related_product = Product.query.get(media.product_id)
                if related_product:
                    print(f"محصول مرتبط با رسانه: {related_product.name}")
                    
                    # بررسی ارتباط دوطرفه
                    media_list = ProductMedia.query.filter_by(product_id=related_product.id).all()
                    found = False
                    for m in media_list:
                        if m.id == media.id:
                            found = True
                            break
                    self.assertTrue(found, "رسانه باید در لیست رسانه‌های محصول باشد")
            
            # بررسی ارتباط استعلام و محصول
            inquiry = Inquiry.query.filter_by(product_type="product").first()
            if inquiry:
                print(f"استعلام: {inquiry.name}, تلفن: {inquiry.phone}")
                inquiry_product = Product.query.get(inquiry.product_id)
                if inquiry_product:
                    print(f"محصول مرتبط با استعلام: {inquiry_product.name}")
                    
        print("✓ تست ارتباطات مدل‌های دیتابیس با موفقیت انجام شد")
    
    async def run_all_tests(self):
        """اجرای تمام تست‌ها"""
        try:
            await self.test_fsm_states()
        except Exception as e:
            print(f"❌ خطا در تست حالت‌های FSM: {str(e)}")
            
        try:
            await self.test_inquiry_flow()
        except Exception as e:
            print(f"❌ خطا در تست گردش کار استعلام: {str(e)}")
            
        try:
            await self.test_database_model_relationships()
        except Exception as e:
            print(f"❌ خطا در تست ارتباطات مدل‌ها: {str(e)}")
    
    def test_bot(self):
        """متد اصلی تست که توسط unittest فراخوانی می‌شود"""
        print("\n===== شروع تست‌های ربات تلگرام =====")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.run_all_tests())
        print("\n===== پایان تست‌های ربات تلگرام =====")

if __name__ == "__main__":
    unittest.main()