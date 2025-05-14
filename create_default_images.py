#!/usr/bin/env python3
"""
ساخت تصویر پیش‌فرض برای محصولات و خدمات
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_default_image(output_path, text, width=800, height=600, bg_color=(240, 240, 240), text_color=(100, 100, 100)):
    """ساخت تصویر پیش‌فرض با متن و رنگ مشخص"""
    # ایجاد تصویر
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # سعی در بارگذاری فونت
    try:
        # بارگذاری فونت فارسی اگر موجود باشد
        font = ImageFont.truetype('static/fonts/Vazir.ttf', 36)
    except IOError:
        # استفاده از فونت پیش‌فرض
        font = ImageFont.load_default()
    
    # محاسبه مختصات برای قرار دادن متن در مرکز
    text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (width//3, height//8)
    position = ((width - text_width) // 2, (height - text_height) // 2)
    
    # رسم متن
    draw.text(position, text, fill=text_color, font=font)
    
    # اطمینان از وجود مسیر
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # ذخیره تصویر
    img.save(output_path)
    print(f"تصویر در مسیر {output_path} ذخیره شد.")

def create_all_default_images():
    """ساخت تمام تصاویر پیش‌فرض"""
    # مسیر پایه برای تصاویر پیش‌فرض
    base_path = 'static/media'
    
    # اطمینان از وجود مسیرها
    os.makedirs(f"{base_path}/products", exist_ok=True)
    os.makedirs(f"{base_path}/services", exist_ok=True)
    
    # ساخت تصاویر پیش‌فرض برای چند محصول
    for product_id in range(712, 717):
        create_default_image(
            f"{base_path}/products/product_image_{product_id}_1.jpg",
            f"تصویر محصول {product_id}",
            bg_color=(230, 240, 255),
            text_color=(50, 50, 150)
        )
        create_default_image(
            f"{base_path}/products/product_image_{product_id}_2.jpg",
            f"تصویر دوم محصول {product_id}",
            bg_color=(220, 230, 255),
            text_color=(50, 50, 150)
        )
    
    # ساخت تصاویر پیش‌فرض برای چند خدمت
    for service_id in range(18, 24):
        create_default_image(
            f"{base_path}/services/service_image_{service_id}_1.jpg",
            f"تصویر خدمت {service_id}",
            bg_color=(255, 240, 230),
            text_color=(150, 50, 50)
        )
        create_default_image(
            f"{base_path}/services/service_image_{service_id}_2.jpg",
            f"تصویر دوم خدمت {service_id}",
            bg_color=(255, 230, 220),
            text_color=(150, 50, 50)
        )

if __name__ == "__main__":
    create_all_default_images()