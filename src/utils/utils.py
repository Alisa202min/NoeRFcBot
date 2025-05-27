"""
توابع کمکی متنوع
این ماژول توابع کمکی عمومی برای استفاده در جاهای مختلف برنامه را فراهم می‌کند.
"""

import os
import re
import logging
from typing import Tuple, Optional
from werkzeug.utils import secure_filename

# تنظیم لاگر
logger = logging.getLogger(__name__)

# پسوندهای فایل مجاز
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}

def validate_phone_number(phone: str) -> bool:
    """
    بررسی اعتبار شماره تلفن
    
    Args:
        phone: شماره تلفن برای بررسی
        
    Returns:
        True اگر شماره تلفن معتبر باشد، False در غیر این صورت
    """
    # الگوی شماره موبایل ایران (09XXXXXXXXX)
    pattern = r'^09\d{9}$'
    
    # بررسی تطابق با الگو
    if re.match(pattern, phone):
        return True
    return False

def format_price(price: int) -> str:
    """
    قالب‌بندی قیمت به صورت رشته با جداکننده هزارگان
    
    Args:
        price: قیمت به تومان
        
    Returns:
        رشته قالب‌بندی شده قیمت
    """
    return f"{price:,} تومان"

def allowed_file(filename: str) -> bool:
    """
    بررسی مجاز بودن پسوند فایل
    
    Args:
        filename: نام فایل برای بررسی
        
    Returns:
        True اگر پسوند فایل مجاز باشد، False در غیر این صورت
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_directory(path: str) -> bool:
    """
    ایجاد دایرکتوری اگر وجود نداشته باشد
    
    Args:
        path: مسیر دایرکتوری
        
    Returns:
        True در صورت موفقیت، False در صورت شکست
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"خطا در ایجاد دایرکتوری {path}: {e}")
        return False

def save_uploaded_file(file, upload_folder: str, filename: Optional[str] = None) -> Tuple[bool, str]:
    """
    ذخیره فایل آپلود شده
    
    Args:
        file: شیء فایل آپلود شده
        upload_folder: پوشه برای ذخیره‌سازی
        filename: نام فایل سفارشی (اختیاری)
        
    Returns:
        (موفقیت، مسیر فایل) - موفقیت: True/False، مسیر فایل: مسیر کامل یا خالی
    """
    try:
        if file and allowed_file(file.filename):
            # استفاده از نام فایل سفارشی یا نام اصلی
            if filename:
                safe_filename = secure_filename(filename)
            else:
                safe_filename = secure_filename(file.filename)
            
            # تعیین مسیر کامل برای ذخیره‌سازی فایل
            full_path = ''
            if upload_folder == 'educational':
                # برای محتوای آموزشی، استفاده از مسیر استاندارد
                full_path = os.path.join('static', 'uploads', 'educational')
                create_directory(full_path)
                file_path = os.path.join('media', 'educational', safe_filename)
            else:
                # برای سایر محتوا، استفاده از مسیر ارسالی
                full_path = upload_folder
                create_directory(full_path)
                file_path = os.path.join(upload_folder, safe_filename)
            
            # ذخیره فایل
            file.save(os.path.join('static', file_path))
            
            return True, file_path
        
        return False, ""
    except Exception as e:
        logger.error(f"خطا در ذخیره فایل: {e}")
        return False, ""