#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست اتوماتیک سیستم استعلام قیمت ربات تلگرام
این اسکریپت بخش استعلام قیمت ربات را تست می‌کند
"""

import sys
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

class TestInquirySystem(unittest.TestCase):
    
    def test_database_models(self):
        """تست مدل‌های دیتابیس"""
        print("\n===== تست مدل‌های دیتابیس =====")
        
        with app.app_context():
            # Test User model
            users = User.query.all()
            print(f"تعداد کاربران: {len(users)}")
            if users:
                print(f"نام کاربری کاربر اول: {users[0].username}")
            
            # Test Product model
            products = Product.query.filter_by(product_type="product").all()
            print(f"تعداد محصولات: {len(products)}")
            if products:
                print(f"نام اولین محصول: {products[0].name}")
                print(f"قیمت اولین محصول: {products[0].price}")
            
            # Test Category model
            categories = Category.query.all()
            print(f"تعداد دسته‌بندی‌ها: {len(categories)}")
            if categories:
                print(f"نام اولین دسته‌بندی: {categories[0].name}")
            
            # Test Inquiry model
            inquiries = Inquiry.query.all()
            print(f"تعداد استعلام‌ها: {len(inquiries)}")
            if inquiries:
                print(f"نام مشتری در اولین استعلام: {inquiries[0].name}")
                print(f"شماره تلفن در اولین استعلام: {inquiries[0].phone}")
                print(f"وضعیت اولین استعلام: {inquiries[0].status}")
            
            print("✓ تست مدل‌های دیتابیس با موفقیت انجام شد")
    
    def test_inquiry_creation(self):
        """تست ایجاد استعلام جدید"""
        print("\n===== تست ایجاد استعلام جدید =====")
        
        with app.app_context():
            # Count initial inquiries
            initial_count = Inquiry.query.count()
            print(f"تعداد استعلام‌های اولیه: {initial_count}")
            
            # Get a test product
            product = Product.query.filter_by(product_type="product").first()
            if not product:
                self.skipTest("هیچ محصولی در دیتابیس یافت نشد")
                return
            
            # Create a new inquiry
            new_inquiry = Inquiry(
                user_id=1,  # فرض می‌کنیم کاربر با شناسه 1 وجود دارد
                name="کاربر تست",
                phone="09123456789",
                description="این یک استعلام تستی است",
                product_id=product.id,
                product_type="product",
                status="new"
            )
            
            # Add to database
            db.session.add(new_inquiry)
            db.session.commit()
            
            # Check if inquiry was created
            new_count = Inquiry.query.count()
            print(f"تعداد استعلام‌های جدید: {new_count}")
            self.assertEqual(new_count, initial_count + 1)
            
            # Get the created inquiry
            created_inquiry = Inquiry.query.order_by(Inquiry.id.desc()).first()
            self.assertEqual(created_inquiry.name, "کاربر تست")
            self.assertEqual(created_inquiry.phone, "09123456789")
            
            print(f"✓ استعلام جدید با موفقیت ایجاد شد (ID: {created_inquiry.id})")
            
            # Clean up - delete the created inquiry
            db.session.delete(created_inquiry)
            db.session.commit()
            
            # Verify deletion
            final_count = Inquiry.query.count()
            self.assertEqual(final_count, initial_count)
            print("✓ استعلام ایجاد شده با موفقیت حذف شد")

if __name__ == "__main__":
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    unittest.main()