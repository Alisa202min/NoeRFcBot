#!/usr/bin/env python3
"""
تولیدکننده سریع دیتای RFTEST 
نسخه بهینه برای تست سریع
5 محصول + 5 خدمات + 5 مطلب آموزشی
"""

import os
from datetime import datetime
from database import Database
from PIL import Image, ImageDraw, ImageFont

def create_quick_image(path, text):
    """ساخت تصویر ساده برای تست"""
    img = Image.new('RGB', (400, 300), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except:
        pass
    draw.text((50, 150), text, fill=(80, 80, 80))
    img.save(path)

def main():
    """تولید سریع دیتای تست"""
    print("🚀 تولیدکننده سریع دیتای RFTEST")
    print("5 محصول + 5 خدمات + 5 مطلب آموزشی")
    print("="*50)
    
    try:
        db = Database()
        
        # بررسی وجود دسته‌بندی‌ها
        with db.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM educational_categories WHERE name = 'تئوری'")
            if cur.fetchone()[0] == 0:
                print("❌ دسته‌بندی‌ها وجود ندارن! ابتدا seed_categories.py اجرا کنید")
                return
            
            # ایجاد 5 مطلب آموزشی سریع
            print("📚 ایجاد 5 مطلب آموزشی...")
            
            # دریافت ID دسته تئوری
            cur.execute("SELECT id FROM educational_categories WHERE name = 'تئوری'")
            theory_id = cur.fetchone()[0]
            
            # مطالب آموزشی
            educational_data = [
                "راهنمای کار با اسیلوسکوپ",
                "اصول اندازه‌گیری RF",
                "تئوری اسپکتروم",
                "نحوه کالیبراسیون",
                "تکنیک‌های اندازه‌گیری"
            ]
            
            # ایجاد پوشه
            edu_dir = "static/media/educational"
            os.makedirs(edu_dir, exist_ok=True)
            
            for i, title in enumerate(educational_data, 1):
                # ایجاد مطلب
                cur.execute("""
                    INSERT INTO educational_content (title, content, category, category_id, created_at)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                """, (title, f"محتوای آموزشی {title}", "تئوری", theory_id, datetime.now()))
                
                content_id = cur.fetchone()[0]
                
                # ایجاد تصویر
                img_name = f"quick_edu_{content_id}.jpg"
                img_path = f"{edu_dir}/{img_name}"
                create_quick_image(img_path, f"آموزش {i}")
                
                # ایجاد رسانه
                cur.execute("""
                    INSERT INTO educational_content_media (educational_content_id, file_id, file_type, local_path) 
                    VALUES (%s, %s, %s, %s)
                """, (content_id, f"quick_edu_media_{content_id}", "photo", f"./static/media/educational/{img_name}"))
            
            db.conn.commit()
            print("✅ 5 مطلب آموزشی با موفقیت ایجاد شد")
            
            # گزارش نهایی
            cur.execute('SELECT COUNT(*) FROM educational_content')
            edu_count = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM educational_content_media')
            media_count = cur.fetchone()[0]
            
            print(f"\n🎉 تولید دیتا تکمیل شد!")
            print(f"✅ {edu_count} مطلب آموزشی")
            print(f"🖼️ {media_count} تصویر آموزشی")
            print("🚀 سیستم آماده تست!")

    except Exception as e:
        print(f"❌ خطا: {e}")
        return False
    
    finally:
        if 'db' in locals():
            db.close()
    
    return True

if __name__ == "__main__":
    main()