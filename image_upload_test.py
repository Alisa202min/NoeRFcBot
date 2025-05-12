"""
اسکریپت تست برای بررسی مشکلات آپلود تصویر
این اسکریپت عملیات آپلود فایل را شبیه‌سازی می‌کند تا مشکلات احتمالی را پیدا کند
"""

import os
import sys
import time
import traceback
import logging
import shutil
from werkzeug.datastructures import FileStorage
from debug_logger import function_logger, log_error, log_media_operations

# تنظیم لاگر اختصاصی برای عملیات رسانه‌ای
media_logger = log_media_operations()

# مسیرهای مختلف برای تست
TEST_DIRS = [
    './static/uploads/',
    './static/media/',
    './static/images/',
    './static/products/',
    './attached_assets/'
]

# فایل‌های تست
TEST_FILES = [
    './attached_assets/show.jpg',
    './attached_assets/image_1746918726396.png',
    './attached_assets/photo_2025-05-11_12-20-03.jpg',
]

@function_logger
def ensure_directories():
    """اطمینان از وجود مسیرهای آپلود"""
    for directory in TEST_DIRS:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                media_logger.info(f"Created directory: {directory}")
            except Exception as e:
                log_error(e, f"Could not create directory {directory}")

@function_logger
def test_file_permissions():
    """بررسی دسترسی‌های فایل‌های تست"""
    for test_file in TEST_FILES:
        if os.path.exists(test_file):
            try:
                # بررسی امکان خواندن فایل
                with open(test_file, 'rb') as f:
                    data = f.read(100)  # خواندن 100 بایت اول
                media_logger.info(f"Successfully read from {test_file}")
                
                # بررسی اندازه و اطلاعات فایل
                file_size = os.path.getsize(test_file)
                file_stats = os.stat(test_file)
                media_logger.info(f"File {test_file} - Size: {file_size} bytes, "
                                 f"Permissions: {oct(file_stats.st_mode)}")
            except Exception as e:
                log_error(e, f"Error reading {test_file}")
        else:
            media_logger.warning(f"Test file does not exist: {test_file}")

@function_logger
def test_copy_files():
    """تست کپی فایل‌ها به مسیرهای مختلف"""
    test_files_copied = []
    
    for test_file in TEST_FILES:
        if os.path.exists(test_file):
            for dest_dir in TEST_DIRS:
                if os.path.exists(dest_dir):
                    try:
                        filename = os.path.basename(test_file)
                        dest_path = os.path.join(dest_dir, f"test_{filename}")
                        
                        # کپی فایل
                        shutil.copy2(test_file, dest_path)
                        media_logger.info(f"Successfully copied {test_file} to {dest_path}")
                        test_files_copied.append(dest_path)
                        
                        # تست خواندن فایل کپی شده
                        with open(dest_path, 'rb') as f:
                            data = f.read(100)
                        media_logger.info(f"Successfully read from copied file: {dest_path}")
                    except Exception as e:
                        log_error(e, f"Error copying {test_file} to {dest_dir}")
    
    return test_files_copied

@function_logger
def test_file_storage_save():
    """تست ذخیره فایل با کلاس FileStorage"""
    test_results = []
    
    for test_file in TEST_FILES:
        if os.path.exists(test_file):
            try:
                with open(test_file, 'rb') as f:
                    file_content = f.read()
                
                # شبیه‌سازی FileStorage
                file_name = os.path.basename(test_file)
                file_storage = FileStorage(
                    stream=open(test_file, 'rb'),
                    filename=file_name,
                    content_type="image/jpeg" if file_name.endswith(('.jpg', '.jpeg')) else "image/png"
                )
                
                for dest_dir in TEST_DIRS:
                    if os.path.exists(dest_dir):
                        try:
                            dest_path = os.path.join(dest_dir, f"filestorage_{file_name}")
                            
                            # ذخیره فایل
                            start_time = time.time()
                            file_storage.save(dest_path)
                            save_time = time.time() - start_time
                            
                            media_logger.info(f"FileStorage.save to {dest_path} completed in {save_time:.4f}s")
                            test_results.append((dest_path, True, save_time))
                            
                            # بازگرداندن اشاره‌گر فایل به ابتدا برای عملیات بعدی
                            file_storage.stream.seek(0)
                        except Exception as e:
                            log_error(e, f"Error in FileStorage.save to {dest_dir}")
                            test_results.append((dest_dir, False, str(e)))
                
                # بستن فایل اصلی
                file_storage.stream.close()
            except Exception as e:
                log_error(e, f"Error creating FileStorage for {test_file}")
                test_results.append((test_file, False, str(e)))
    
    return test_results

@function_logger
def verify_test_files(test_files):
    """تأیید فایل‌های کپی شده"""
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                file_size = os.path.getsize(file_path)
                media_logger.info(f"Verified {file_path} exists, size: {file_size} bytes")
                
                # تلاش برای باز کردن و خواندن فایل
                with open(file_path, 'rb') as f:
                    data_size = len(f.read())
                media_logger.info(f"Successfully read {data_size} bytes from {file_path}")
            except Exception as e:
                log_error(e, f"Error verifying {file_path}")
        else:
            media_logger.error(f"Test file does not exist after copy: {file_path}")

@function_logger
def cleanup_test_files(test_files):
    """پاکسازی فایل‌های تست شده"""
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                media_logger.info(f"Removed test file: {file_path}")
            except Exception as e:
                log_error(e, f"Error removing {file_path}")

@function_logger
def run_image_upload_tests():
    """اجرای همه تست‌های آپلود تصویر"""
    media_logger.info("=== STARTING IMAGE UPLOAD TESTS ===")
    
    try:
        # اطمینان از وجود دایرکتوری‌ها
        ensure_directories()
        
        # بررسی دسترسی‌های فایل
        test_file_permissions()
        
        # تست کپی فایل‌ها
        media_logger.info("--- Testing file copying ---")
        copied_files = test_copy_files()
        verify_test_files(copied_files)
        
        # تست ذخیره FileStorage
        media_logger.info("--- Testing FileStorage save ---")
        storage_results = test_file_storage_save()
        
        # گزارش نتایج تست FileStorage
        for dest_path, success, info in storage_results:
            if success:
                media_logger.info(f"FileStorage test passed for {dest_path} in {info:.4f}s")
            else:
                media_logger.error(f"FileStorage test failed for {dest_path}: {info}")
        
        # پاکسازی فایل‌های تست
        success_files = [path for path, success, _ in storage_results if success and isinstance(path, str)]
        cleanup_test_files(copied_files + success_files)
        
        media_logger.info("=== IMAGE UPLOAD TESTS COMPLETED ===")
        return True
    except Exception as e:
        log_error(e, "Error in image upload test suite")
        media_logger.error("=== IMAGE UPLOAD TESTS FAILED ===")
        return False

if __name__ == "__main__":
    run_image_upload_tests()