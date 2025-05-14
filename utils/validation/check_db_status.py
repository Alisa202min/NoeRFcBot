#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بررسی وضعیت دیتابیس بعد از سیدینگ
"""

from app import app, db
from models import User, Category, Product, ProductMedia, Inquiry, EducationalContent, StaticContent

def check_database():
    """بررسی وضعیت دیتابیس"""
    with app.app_context():
        print('===== وضعیت پایگاه داده =====')
        print(f'• کاربران: {User.query.count()}')
        print(f'• دسته‌بندی‌ها: {Category.query.count()}')
        print(f'• محصولات: {Product.query.filter_by(product_type="product").count()}')
        print(f'• خدمات: {Product.query.filter_by(product_type="service").count()}')
        print(f'• رسانه‌ها: {ProductMedia.query.count()}')
        print(f'• استعلام‌ها: {Inquiry.query.count()}')
        print(f'• محتوای آموزشی: {EducationalContent.query.count()}')
        print(f'• محتوای ثابت: {StaticContent.query.count()}')
        print('=============================')

if __name__ == "__main__":
    check_database()