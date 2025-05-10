#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست سریع ساختار ربات تلگرام
"""

import logging
from app import app
from models import User, Product, Category, Inquiry, ProductMedia
from handlers import UserStates

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_structure():
    """تست ساختار دیتابیس"""
    print("\n=== تست ساختار دیتابیس ===")
    
    with app.app_context():
        # تست جداول اصلی
        tables = {
            "User": User.query.count(),
            "Product": Product.query.count(),
            "Category": Category.query.count(),
            "Inquiry": Inquiry.query.count(),
            "ProductMedia": ProductMedia.query.count()
        }
        
        for table_name, count in tables.items():
            print(f"{table_name}: {count} رکورد")
            
        # تست رابطه محصول و دسته‌بندی
        product = Product.query.filter_by(product_type="product").first()
        if product:
            category = Category.query.get(product.category_id)
            print(f"\nمحصول '{product.name}' در دسته‌بندی '{category.name if category else 'نامشخص'}' قرار دارد")
            
        # تست رابطه محصول و رسانه
        media = ProductMedia.query.first()
        if media:
            media_product = Product.query.get(media.product_id)
            print(f"رسانه '{media.file_id}' مربوط به محصول '{media_product.name if media_product else 'نامشخص'}' است")
            
        # تست رابطه استعلام و محصول
        inquiry = Inquiry.query.first()
        if inquiry and inquiry.product_id:
            inquiry_product = Product.query.get(inquiry.product_id)
            print(f"استعلام '{inquiry.name}' مربوط به محصول '{inquiry_product.name if inquiry_product else 'نامشخص'}' است")
            
    print("✓ تست ساختار دیتابیس با موفقیت انجام شد")

def test_fsm_states():
    """تست حالت‌های ماشین وضعیت محدود (FSM)"""
    print("\n=== تست حالت‌های FSM ===")
    
    states = [
        UserStates.browse_categories,
        UserStates.view_product,
        UserStates.view_educational_content,
        UserStates.inquiry_name,
        UserStates.inquiry_phone,
        UserStates.inquiry_description,
        UserStates.waiting_for_confirmation
    ]
    
    for state in states:
        print(f"• {state.state}")
        
    print(f"\nتعداد کل حالت‌ها: {len(states)}")
    print("✓ تست حالت‌های FSM با موفقیت انجام شد")

def main():
    """تابع اصلی اجرای تست‌ها"""
    print("===== شروع تست‌های سریع ربات تلگرام =====")
    
    test_database_structure()
    test_fsm_states()
    
    print("\n===== پایان تست‌های سریع ربات تلگرام =====")
    print("تمام تست‌ها با موفقیت انجام شدند!")

if __name__ == "__main__":
    main()