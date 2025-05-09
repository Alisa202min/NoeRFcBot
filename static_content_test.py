#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست فقط بخش محتوای ثابت
"""

import sys
from datetime import datetime
from app import app, db
from models import StaticContent

def test_static_content():
    """تست عملکرد محتوای ثابت"""
    success = True
    
    with app.app_context():
        try:
            # بررسی وجود داده‌های محتوای ثابت
            about_content = StaticContent.query.filter_by(content_type="about").first()
            contact_content = StaticContent.query.filter_by(content_type="contact").first()
            
            if about_content and contact_content:
                print("✓ رکوردهای محتوای ثابت یافت شدند")
                
                # بررسی مقادیر type
                print(f"  • محتوای about: type = {about_content.type}")
                print(f"  • محتوای contact: type = {contact_content.type}")
                
                # بررسی امکان به‌روزرسانی محتوا
                old_content = about_content.content
                old_updated_at = about_content.updated_at
                print(f"  • تاریخ به‌روزرسانی اولیه: {old_updated_at}")
                
                about_content.content = "Updated test content"
                about_content.updated_at = datetime.utcnow()  # به‌روزرسانی دستی
                db.session.commit()
                
                # بررسی به‌روزرسانی موفق
                refreshed_content = StaticContent.query.filter_by(content_type="about").first()
                print(f"  • محتوای جدید: {refreshed_content.content}")
                print(f"  • تاریخ به‌روزرسانی جدید: {refreshed_content.updated_at}")
                
                if refreshed_content.content == "Updated test content":
                    print("✓ به‌روزرسانی محتوا موفق بود")
                else:
                    print("✗ به‌روزرسانی محتوا موفق نبود")
                    success = False
                
                # بررسی به‌روزرسانی دستی updated_at
                if refreshed_content.updated_at > old_updated_at:
                    print("✓ فیلد updated_at به‌روز شد")
                else:
                    print("✗ فیلد updated_at به‌روز نشد")
                    success = False
                
                # بازگرداندن به حالت اولیه
                about_content.content = old_content
                db.session.commit()
                print("✓ محتوا به حالت اولیه بازگردانده شد")
            else:
                print("✗ رکوردهای محتوای ثابت یافت نشدند")
                success = False
        except Exception as e:
            print(f"✗ خطا در تست محتوای ثابت: {str(e)}")
            db.session.rollback()
            success = False
    
    return success

if __name__ == "__main__":
    print("===== تست بخش محتوای ثابت =====")
    success = test_static_content()
    print("================================")
    
    if success:
        print("تست با موفقیت انجام شد!")
        sys.exit(0)
    else:
        print("تست ناموفق بود!")
        sys.exit(1)