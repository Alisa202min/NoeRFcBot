#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست ارتباطات بین جداول
"""

import sys
from app import app, db
from models import Category, Product, ProductMedia

def test_relationships():
    """تست ارتباطات بین جداول"""
    success = True
    
    with app.app_context():
        try:
            # تست ارتباط بین محصولات و دسته‌بندی‌ها
            category = Category.query.first()
            
            if category:
                print(f"✓ دسته‌بندی یافت شد: {category.name}")
                
                # بررسی محصولات مرتبط با این دسته‌بندی
                products = Product.query.filter_by(category_id=category.id).all()
                
                if products:
                    print(f"✓ {len(products)} محصول در دسته‌بندی {category.name} یافت شد")
                    
                    # بررسی رابطه دو طرفه
                    for product in products[:3]:  # فقط ۳ مورد اول را بررسی می‌کنیم
                        print(f"  • محصول: {product.name}")
                        print(f"    - دسته‌بندی محصول: {product.category.name}")
                        
                        if product.category.id == category.id:
                            print("    ✓ ارتباط دو طرفه بین محصول و دسته‌بندی صحیح است")
                        else:
                            print("    ✗ ارتباط دو طرفه بین محصول و دسته‌بندی صحیح نیست")
                            success = False
                        
                        # بررسی رسانه‌های محصول
                        media_items = ProductMedia.query.filter_by(product_id=product.id).all()
                        
                        if media_items:
                            print(f"    ✓ {len(media_items)} رسانه برای محصول {product.name} یافت شد")
                            
                            # بررسی ارتباط دو طرفه محصول و رسانه
                            for media in media_items[:2]:  # فقط ۲ مورد اول را بررسی می‌کنیم
                                print(f"      • نوع رسانه: {media.file_type}")
                                print(f"        - محصول مرتبط: {media.product.name}")
                                
                                if media.product.id == product.id:
                                    print("        ✓ ارتباط دو طرفه بین محصول و رسانه صحیح است")
                                else:
                                    print("        ✗ ارتباط دو طرفه بین محصول و رسانه صحیح نیست")
                                    success = False
                        else:
                            print(f"    ℹ هیچ رسانه‌ای برای محصول {product.name} یافت نشد")
                else:
                    print(f"ℹ هیچ محصولی در دسته‌بندی {category.name} یافت نشد")
            else:
                print("✗ هیچ دسته‌بندی‌ای یافت نشد")
                success = False
            
            # تست دسته‌بندی‌های درختی (چند سطحی)
            parent_categories = Category.query.filter_by(parent_id=None).all()
            
            if parent_categories:
                print(f"\n✓ {len(parent_categories)} دسته‌بندی اصلی (بدون والد) یافت شد")
                
                # بررسی زیردسته‌ها
                for parent in parent_categories[:2]:  # فقط ۲ مورد اول را بررسی می‌کنیم
                    print(f"  • دسته‌بندی اصلی: {parent.name}")
                    
                    if parent.subcategories:
                        print(f"    ✓ {len(parent.subcategories)} زیردسته برای {parent.name} یافت شد")
                        
                        # بررسی ارتباط زیردسته‌ها با والد
                        for child in parent.subcategories[:2]:  # فقط ۲ مورد اول را بررسی می‌کنیم
                            print(f"      • زیردسته: {child.name}")
                            
                            if child.parent and child.parent.id == parent.id:
                                print("        ✓ ارتباط دو طرفه بین والد و زیردسته صحیح است")
                            else:
                                print("        ✗ ارتباط دو طرفه بین والد و زیردسته صحیح نیست")
                                success = False
                    else:
                        print(f"    ℹ هیچ زیردسته‌ای برای {parent.name} یافت نشد")
            else:
                print("ℹ هیچ دسته‌بندی اصلی‌ای یافت نشد")
        except Exception as e:
            print(f"✗ خطا در تست ارتباطات: {str(e)}")
            db.session.rollback()
            success = False
    
    return success

if __name__ == "__main__":
    print("===== تست ارتباطات بین جداول =====")
    success = test_relationships()
    print("==================================")
    
    if success:
        print("تست با موفقیت انجام شد!")
        sys.exit(0)
    else:
        print("تست ناموفق بود!")
        sys.exit(1)