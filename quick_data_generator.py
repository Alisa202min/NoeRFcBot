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
            cur.execute("SELECT COUNT(*) FROM educational_categories")
            if cur.fetchone()[0] == 0:
                print("❌ دسته‌بندی‌ها وجود ندارن! ابتدا seed_categories.py اجرا کنید")
                return
            
            # === ایجاد 5 محصول ===
            print("📦 ایجاد 5 محصول با تصاویر...")
            
            # دریافت ID دسته محصولات
            cur.execute("SELECT id FROM product_categories LIMIT 1")
            product_cat_result = cur.fetchone()
            if product_cat_result:
                product_cat_id = product_cat_result[0]
                
                products_data = [
                    ("اسیلوسکوپ Rigol DS1054Z", 22000000, "Rigol"),
                    ("اسیلوسکوپ Keysight DSOX2002A", 45000000, "Keysight"),
                    ("اسیلوسکوپ Tektronix TBS1102B", 12000000, "Tektronix"),
                    ("اسیلوسکوپ Hantek DSO2C10", 3500000, "Hantek"),
                    ("اسیلوسکوپ Fluke ScopeMeter", 78000000, "Fluke")
                ]
                
                for i, (name, price, brand) in enumerate(products_data, 1):
                    # ایجاد محصول
                    cur.execute("""
                        INSERT INTO products (name, description, price, category_id, brand, model, tags, in_stock, featured, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """, (name, f"تجهیز پیشرفته اسیلوسکوپ از برند {brand}", price, product_cat_id,
                          brand, f"QUICK-{i:03d}", f"اسیلوسکوپ,{brand},تجهیزات", True, i <= 2, datetime.now()))
                    
                    product_id = cur.fetchone()[0]
                    
                    # ایجاد پوشه محصول
                    product_dir = f"static/uploads/products/{product_id}"
                    os.makedirs(product_dir, exist_ok=True)
                    
                    # ایجاد تصویر اصلی
                    img_path = f"{product_dir}/main.jpg"
                    create_quick_image(img_path, f"محصول {i}")
                    
                    # ایجاد رسانه
                    cur.execute("""
                        INSERT INTO product_media (product_id, file_id, file_type) 
                        VALUES (%s, %s, %s)
                    """, (product_id, f"uploads/products/{product_id}/main.jpg", "photo"))
                
                print("✅ 5 محصول با تصاویر ایجاد شد")
            
            # === ایجاد 5 خدمات ===
            print("🔧 ایجاد 5 خدمات با تصاویر...")
            
            # دریافت ID دسته خدمات
            cur.execute("SELECT id FROM service_categories WHERE name = 'کالیبراسیون' LIMIT 1")
            service_cat_result = cur.fetchone()
            if service_cat_result:
                service_cat_id = service_cat_result[0]
                
                services_data = [
                    ("کالیبراسیون اسیلوسکوپ", 3500000),
                    ("کالیبراسیون اسپکتروم آنالایزر", 4500000),
                    ("کالیبراسیون سیگنال ژنراتور", 4000000),
                    ("کالیبراسیون نتورک آنالایزر", 5500000),
                    ("کالیبراسیون پاورمتر", 2500000)
                ]
                
                for i, (name, price) in enumerate(services_data, 1):
                    # ایجاد خدمت
                    cur.execute("""
                        INSERT INTO services (name, description, price, category_id, tags, featured, available, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """, (name, f"خدمات تخصصی {name} توسط متخصصان RFTEST", price, service_cat_id,
                          f"کالیبراسیون,RFTEST,خدمات", i <= 2, True, datetime.now()))
                    
                    service_id = cur.fetchone()[0]
                    
                    # ایجاد پوشه خدمت
                    service_dir = f"static/uploads/services/{service_id}"
                    os.makedirs(service_dir, exist_ok=True)
                    
                    # ایجاد تصویر
                    img_path = f"{service_dir}/main.jpg"
                    create_quick_image(img_path, f"خدمات {i}")
                    
                    # ایجاد رسانه
                    cur.execute("""
                        INSERT INTO service_media (service_id, file_id, file_type, local_path) 
                        VALUES (%s, %s, %s, %s)
                    """, (service_id, f"uploads/services/{service_id}/main.jpg", "photo", f"./static/uploads/services/{service_id}/main.jpg"))
                
                print("✅ 5 خدمات با تصاویر ایجاد شد")
            
            # === ایجاد 5 مطلب آموزشی ===
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
            
            print("✅ 5 مطلب آموزشی با تصاویر ایجاد شد")
            
            db.conn.commit()
            
            # گزارش نهایی
            cur.execute('SELECT COUNT(*) FROM products')
            products_count = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM services')
            services_count = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM educational_content')
            edu_count = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM product_media')
            product_media_count = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM service_media')
            service_media_count = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM educational_content_media')
            edu_media_count = cur.fetchone()[0]
            
            print(f"\n🎉 تولید دیتا تکمیل شد!")
            print(f"✅ {products_count} محصول")
            print(f"✅ {services_count} خدمات")
            print(f"✅ {edu_count} مطلب آموزشی")
            print(f"🖼️ {product_media_count} تصویر محصولات")
            print(f"🖼️ {service_media_count} تصویر خدمات")
            print(f"🖼️ {edu_media_count} تصویر آموزشی")
            print("🚀 سیستم کامل آماده تست!")

    except Exception as e:
        print(f"❌ خطا: {e}")
        return False
    
    finally:
        if 'db' in locals() and hasattr(db, 'connection') and db.connection:
            db.connection.close()
    
    return True

if __name__ == "__main__":
    main()