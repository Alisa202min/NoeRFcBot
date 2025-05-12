"""
تست‌های مربوط به آپلود، ذخیره، و نمایش تصاویر در RFCBot
"""

import os
import pytest
import io
from PIL import Image
from werkzeug.datastructures import FileStorage
import sys
import logging

# اضافه کردن مسیر پروژه به سیستم
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ایمپورت ماژول‌های مورد نیاز
from utils_upload import is_valid_image, save_uploaded_file
from database import Database
from image_logger import log_upload_start, log_upload_success, log_upload_error

# تنظیم لاگر
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

class TestImageUpload:
    """تست‌های مربوط به آپلود تصاویر"""
    
    def test_valid_image_validation(self, sample_image_file):
        """تست اعتبارسنجی تصویر معتبر"""
        assert is_valid_image(sample_image_file) == True
    
    def test_invalid_image_validation(self, invalid_file_storage):
        """تست اعتبارسنجی فایل نامعتبر"""
        assert is_valid_image(invalid_file_storage) == False
    
    def test_large_image_validation(self, large_image_file):
        """تست اعتبارسنجی تصویر بزرگتر از حد مجاز"""
        # فرض می‌کنیم حداکثر سایز 5MB است
        max_size = 5 * 1024 * 1024
        large_image_file.seek(0, os.SEEK_END)
        file_size = large_image_file.tell()
        large_image_file.seek(0)
        
        assert file_size > max_size
        assert is_valid_image(large_image_file, max_size=max_size) == False

    def test_save_uploaded_file(self, sample_image_file, app_upload_folder):
        """تست ذخیره فایل آپلودی"""
        log_upload_start(sample_image_file.filename, len(sample_image_file.read()), sample_image_file.content_type)
        sample_image_file.seek(0)  # بازگرداندن اشاره‌گر فایل به ابتدا
        
        filename = save_uploaded_file(sample_image_file, app_upload_folder)
        
        # بررسی نتیجه ذخیره فایل
        assert filename is not None
        assert os.path.exists(os.path.join(app_upload_folder, filename))
        
        log_upload_success(sample_image_file.filename, os.path.join(app_upload_folder, filename))

    def test_save_invalid_file(self, invalid_file_storage, app_upload_folder):
        """تست ذخیره فایل نامعتبر"""
        try:
            log_upload_start(invalid_file_storage.filename, len(invalid_file_storage.read()), invalid_file_storage.content_type)
            invalid_file_storage.seek(0)  # بازگرداندن اشاره‌گر فایل به ابتدا
            
            filename = save_uploaded_file(invalid_file_storage, app_upload_folder, validate=True)
            assert filename is None, "Invalid file should not be saved"
        except Exception as e:
            log_upload_error(invalid_file_storage.filename, str(e))
            assert "Invalid file format" in str(e) or "File validation failed" in str(e)


class TestProductImageIntegration:
    """تست‌های یکپارچگی تصاویر محصولات"""
    
    def test_product_create_with_image(self, admin_flask_client, db, sample_image_file):
        """تست ایجاد محصول با تصویر"""
        # ابتدا یک دسته‌بندی ایجاد می‌کنیم
        category_id = db.add_category("تست دسته", cat_type="product")
        
        # آپلود محصول با تصویر
        response = admin_flask_client.post(
            '/admin/products?action=save',
            data={
                'name': 'محصول تست',
                'price': '1000',
                'description': 'توضیحات تست',
                'category_id': str(category_id),
                'photo': sample_image_file
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        # بررسی موفقیت‌آمیز بودن ریکوئست
        assert response.status_code == 200
        assert 'محصول با موفقیت ذخیره شد' in response.get_data(as_text=True)
        
        # بررسی ایجاد محصول در دیتابیس
        products = db.get_products_by_category(category_id)
        assert len(products) == 1
        assert products[0]['name'] == 'محصول تست'
        assert products[0]['photo_url'] is not None
        
        # بررسی وجود فایل
        assert os.path.exists(os.path.join('static', products[0]['photo_url']))
    
    def test_product_update_image(self, admin_flask_client, db, sample_image_file):
        """تست به‌روزرسانی تصویر محصول"""
        # ابتدا یک دسته‌بندی و محصول ایجاد می‌کنیم
        category_id = db.add_category("تست دسته", cat_type="product")
        product_id = db.add_product(
            name="محصول تست",
            price=1000,
            description="توضیحات تست",
            category_id=category_id
        )
        
        # به‌روزرسانی محصول با تصویر جدید
        response = admin_flask_client.post(
            '/admin/products?action=save',
            data={
                'id': str(product_id),
                'name': 'محصول تست ویرایش شده',
                'price': '1500',
                'description': 'توضیحات تست به‌روزرسانی شده',
                'category_id': str(category_id),
                'photo': sample_image_file
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        # بررسی موفقیت‌آمیز بودن ریکوئست
        assert response.status_code == 200
        assert 'محصول با موفقیت به‌روزرسانی شد' in response.get_data(as_text=True) or 'محصول با موفقیت ذخیره شد' in response.get_data(as_text=True)
        
        # بررسی به‌روزرسانی محصول در دیتابیس
        product = db.get_product(product_id)
        assert product['name'] == 'محصول تست ویرایش شده'
        assert product['photo_url'] is not None
        
        # بررسی وجود فایل
        assert os.path.exists(os.path.join('static', product['photo_url']))
    
    def test_invalid_image_upload(self, admin_flask_client, db, invalid_file_storage):
        """تست آپلود فایل نامعتبر برای محصول"""
        # ابتدا یک دسته‌بندی ایجاد می‌کنیم
        category_id = db.add_category("تست دسته", cat_type="product")
        
        # آپلود محصول با فایل نامعتبر
        response = admin_flask_client.post(
            '/admin/products?action=save',
            data={
                'name': 'محصول تست',
                'price': '1000',
                'description': 'توضیحات تست',
                'category_id': str(category_id),
                'photo': invalid_file_storage
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        # بررسی عدم موفقیت ریکوئست و نمایش پیام خطا
        assert response.status_code == 200
        response_text = response.get_data(as_text=True)
        assert 'فرمت فایل نامعتبر است' in response_text or 'تصویر نامعتبر است' in response_text or 'خطا در آپلود فایل' in response_text
    

class TestServiceImageIntegration:
    """تست‌های یکپارچگی تصاویر خدمات"""
    
    def test_service_create_with_image(self, admin_flask_client, db, sample_image_file):
        """تست ایجاد خدمت با تصویر"""
        # ابتدا یک دسته‌بندی ایجاد می‌کنیم
        category_id = db.add_category("تست دسته خدمات", cat_type="service")
        
        # آپلود خدمت با تصویر
        response = admin_flask_client.post(
            '/admin/services?action=save',
            data={
                'name': 'خدمت تست',
                'price': '2000',
                'description': 'توضیحات خدمت تست',
                'category_id': str(category_id),
                'photo': sample_image_file
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        # بررسی موفقیت‌آمیز بودن ریکوئست
        assert response.status_code == 200
        assert 'خدمت با موفقیت ذخیره شد' in response.get_data(as_text=True)
        
        # بررسی ایجاد خدمت در دیتابیس
        services = db.get_products_by_category(category_id, cat_type="service")
        assert len(services) == 1
        assert services[0]['name'] == 'خدمت تست'
        assert services[0]['photo_url'] is not None
        
        # بررسی وجود فایل
        assert os.path.exists(os.path.join('static', services[0]['photo_url']))


class TestAdditionalImagesIntegration:
    """تست‌های یکپارچگی تصاویر اضافی"""
    
    def test_add_product_media(self, admin_flask_client, db, sample_image_file):
        """تست افزودن مدیای اضافی به محصول"""
        # ابتدا یک دسته‌بندی و محصول ایجاد می‌کنیم
        category_id = db.add_category("تست دسته", cat_type="product")
        product_id = db.add_product(
            name="محصول تست",
            price=1000,
            description="توضیحات تست",
            category_id=category_id
        )
        
        # افزودن مدیای اضافی
        response = admin_flask_client.post(
            f'/admin/products/{product_id}/media/add',
            data={
                'file': sample_image_file,
                'file_type': 'photo'
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        # بررسی موفقیت‌آمیز بودن ریکوئست
        assert response.status_code == 200
        assert 'مدیا با موفقیت اضافه شد' in response.get_data(as_text=True)
        
        # بررسی افزودن مدیا در دیتابیس
        media_list = db.get_product_media(product_id)
        assert len(media_list) == 1
        
        # بررسی وجود فایل (تلگرام file_id یا مسیر محلی)
        if 'local_path' in media_list[0]:
            assert media_list[0]['local_path'] is not None
            if media_list[0]['local_path'].startswith('/'):
                assert os.path.exists(media_list[0]['local_path'][1:])  # حذف '/' از ابتدای مسیر
            else:
                assert os.path.exists(media_list[0]['local_path'])
    
    def test_delete_product_media(self, admin_flask_client, db, sample_image_file):
        """تست حذف مدیای محصول"""
        # ابتدا یک دسته‌بندی و محصول ایجاد می‌کنیم
        category_id = db.add_category("تست دسته", cat_type="product")
        product_id = db.add_product(
            name="محصول تست",
            price=1000,
            description="توضیحات تست",
            category_id=category_id
        )
        
        # افزودن مدیای اضافی
        sample_image_file.seek(0)
        response = admin_flask_client.post(
            f'/admin/products/{product_id}/media/add',
            data={
                'file': sample_image_file,
                'file_type': 'photo'
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        # دریافت لیست مدیا
        media_list = db.get_product_media(product_id)
        assert len(media_list) == 1
        media_id = media_list[0]['id']
        
        # حذف مدیا
        response = admin_flask_client.post(
            f'/admin/products/{product_id}/media/{media_id}/delete',
            follow_redirects=True
        )
        
        # بررسی موفقیت‌آمیز بودن ریکوئست
        assert response.status_code == 200
        assert 'مدیا با موفقیت حذف شد' in response.get_data(as_text=True)
        
        # بررسی حذف مدیا از دیتابیس
        media_list = db.get_product_media(product_id)
        assert len(media_list) == 0