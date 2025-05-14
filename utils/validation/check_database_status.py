#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بررسی وضعیت دیتابیس و مدل‌های موجود
"""

import os
import sys
import logging
from app import app
from models import User, Category, Product, ProductMedia, Inquiry, EducationalContent, StaticContent

# تنظیم لاگر
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_status():
    """بررسی وضعیت دیتابیس و مدل‌های موجود"""
    try:
        with app.app_context():
            print("\n===== وضعیت پایگاه داده =====")
            print(f"• کاربران: {User.query.count()}")
            print(f"• دسته‌بندی‌ها: {Category.query.count()}")
            print(f"• محصولات: {Product.query.filter_by(product_type='product').count()}")
            print(f"• خدمات: {Product.query.filter_by(product_type='service').count()}")
            print(f"• رسانه‌ها: {ProductMedia.query.count()}")
            print(f"• استعلام‌ها: {Inquiry.query.count()}")
            # ممکن است ساختار جدول با مدل مطابقت نداشته باشد
            try:
                print(f"• محتوای آموزشی: {EducationalContent.query.count()}")
            except Exception as e:
                print(f"• محتوای آموزشی: [خطا: {str(e)}]")
                
            try:
                print(f"• محتوای ثابت: {StaticContent.query.count()}")
            except Exception as e:
                print(f"• محتوای ثابت: [خطا: {str(e)}]")
            print("=============================\n")
            
            # بررسی هر کدام از جداول به صورت جداگانه
            try:
                if Inquiry.query.count() > 0:
                    inquiry = Inquiry.query.first()
                    print("نمونه استعلام قیمت:")
                    for column, value in inquiry.__dict__.items():
                        if not column.startswith('_'):
                            print(f"  {column}: {value}")
            except Exception as e:
                print(f"خطا در نمایش نمونه استعلام: {e}")
            
            return True
    except Exception as e:
        logger.error(f"خطا در بررسی وضعیت دیتابیس: {e}")
        return False

if __name__ == "__main__":
    if check_database_status():
        sys.exit(0)
    else:
        sys.exit(1)