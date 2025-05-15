"""
ماژول اختصاصی برای لاگ‌گذاری عملیات تصاویر و فایل‌ها
"""

import logging
import os
import sys
from datetime import datetime

# تنظیم فرمت لاگ
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
IMAGE_LOG_FILE = "logs/image_operations.log"

# اطمینان از وجود دایرکتوری لاگ
if not os.path.exists("logs"):
    os.makedirs("logs")

# ایجاد لاگر ویژه برای عملیات تصاویر
image_logger = logging.getLogger("image_logger")
image_logger.setLevel(logging.DEBUG)

# حذف هندلرهای قبلی برای جلوگیری از تکرار لاگ
if image_logger.handlers:
    image_logger.handlers.clear()

# تنظیم هندلرها
file_handler = logging.FileHandler(IMAGE_LOG_FILE, 'a', 'utf-8')
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

image_logger.addHandler(file_handler)
image_logger.addHandler(console_handler)

def log_upload_start(filename, file_size, file_type, user_id=None):
    """ثبت شروع آپلود فایل"""
    user_info = f" - User ID: {user_id}" if user_id else ""
    image_logger.info(f"Upload started - File: {filename} - Size: {file_size/1024:.2f} KB - Type: {file_type}{user_info}")

def log_upload_success(filename, destination_path, entity_type="product", entity_id=None):
    """ثبت آپلود موفق فایل"""
    entity_info = f" - {entity_type.capitalize()} ID: {entity_id}" if entity_id else ""
    image_logger.info(f"Upload successful - File: {filename} - Saved to: {destination_path}{entity_info}")

def log_upload_error(filename, error_message, error_type=None):
    """ثبت خطای آپلود فایل"""
    type_info = f" - Error type: {error_type}" if error_type else ""
    image_logger.error(f"Upload failed - File: {filename}{type_info} - Error: {error_message}")

def log_file_validation(filename, is_valid, validation_message=None):
    """ثبت نتیجه اعتبارسنجی فایل"""
    result = "passed" if is_valid else "failed"
    message = f" - Details: {validation_message}" if validation_message else ""
    image_logger.info(f"File validation {result} - File: {filename}{message}")

def log_image_processing(filename, operation, params=None):
    """ثبت عملیات پردازش تصویر"""
    params_info = f" - Parameters: {params}" if params else ""
    image_logger.info(f"Image processing - Operation: {operation} - File: {filename}{params_info}")

def log_database_image_operation(operation, entity_type, entity_id, image_field=None, image_path=None):
    """ثبت عملیات مرتبط با تصویر در پایگاه داده"""
    field_info = f" - Field: {image_field}" if image_field else ""
    path_info = f" - Path: {image_path}" if image_path else ""
    image_logger.info(f"Database {operation} - {entity_type.capitalize()} ID: {entity_id}{field_info}{path_info}")

def log_image_display(image_path, template, context=None):
    """ثبت نمایش تصویر در قالب"""
    context_info = f" - Context: {context}" if context else ""
    image_logger.debug(f"Image display - Path: {image_path} - Template: {template}{context_info}")

def log_file_not_found(image_path, template=None, entity_type=None, entity_id=None):
    """ثبت خطای عدم وجود فایل"""
    template_info = f" - Template: {template}" if template else ""
    entity_info = f" - {entity_type.capitalize()} ID: {entity_id}" if entity_type and entity_id else ""
    image_logger.warning(f"File not found - Path: {image_path}{template_info}{entity_info}")