#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست ساده ربات تلگرام
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
from models import User, Product, Category, Inquiry

class SimpleTest(unittest.TestCase):
    
    def test_database_access(self):
        """Test database access"""
        print("\n===== Testing Database Access =====")
        
        with app.app_context():
            # Test User table
            users_count = User.query.count()
            print(f"Users count: {users_count}")
            
            # Test Product table
            products_count = Product.query.count()
            print(f"Products count: {products_count}")
            
            # Test Category table
            categories_count = Category.query.count()
            print(f"Categories count: {categories_count}")
            
            # Test Inquiry table
            inquiries_count = Inquiry.query.count()
            print(f"Inquiries count: {inquiries_count}")
            
            print("✓ Database access test passed")
            
if __name__ == "__main__":
    unittest.main()