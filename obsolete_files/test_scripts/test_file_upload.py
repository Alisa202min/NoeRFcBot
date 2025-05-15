"""
تست آپلود فایل در سیستم
"""

import os
import time
import shutil
import logging
from io import BytesIO
from PIL import Image
from debug_logger import function_logger, log_error, measure_time

# تنظیم لاگر
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# مسیرهای آپلود برای تست
TEST_UPLOAD_DIRS = [
    './static/uploads/test_upload',
    './static/uploads/products/999',
    './static/media/test_upload',
    './static/images/test_upload',
]

# اندازه‌های مختلف فایل برای تست
FILE_SIZES = [
    (100, 100),      # تصویر کوچک
    (500, 500),      # تصویر متوسط
    (1000, 1000),    # تصویر بزرگ
    (2000, 2000),    # تصویر خیلی بزرگ
]

@function_logger
def create_test_image(size=(100, 100), format='JPEG', color=(255, 0, 0)):
    """ایجاد تصویر تست با سایز مشخص"""
    image = Image.new('RGB', size, color=color)
    img_io = BytesIO()
    image.save(img_io, format=format)
    img_io.seek(0)
    return img_io

@function_logger
def create_test_dirs():
    """ایجاد مسیرهای تست"""
    for dir_path in TEST_UPLOAD_DIRS:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created test directory: {dir_path}")

@function_logger
def cleanup_test_dirs():
    """پاکسازی مسیرهای تست"""
    for dir_path in TEST_UPLOAD_DIRS:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                logger.info(f"Removed test directory: {dir_path}")
            except Exception as e:
                logger.error(f"Error removing directory {dir_path}: {e}")

@measure_time
def test_direct_file_save():
    """تست ذخیره مستقیم فایل بدون استفاده از utils_upload"""
    create_test_dirs()
    results = []
    
    for size in FILE_SIZES:
        img_io = create_test_image(size=size)
        img_data = img_io.read()  # خواندن داده‌های تصویر
        
        for upload_dir in TEST_UPLOAD_DIRS:
            filename = f"test_image_{size[0]}x{size[1]}.jpg"
            file_path = os.path.join(upload_dir, filename)
            
            # اندازه‌گیری زمان ذخیره فایل
            start_time = time.time()
            try:
                with open(file_path, 'wb') as f:
                    f.write(img_data)
                execution_time = time.time() - start_time
                file_size = os.path.getsize(file_path)
                success = True
                logger.info(f"Saved file {file_path} ({file_size} bytes) in {execution_time:.4f}s")
            except Exception as e:
                execution_time = time.time() - start_time
                file_size = 0
                success = False
                logger.error(f"Failed to save file {file_path}: {e}")
                
            results.append({
                'size': size,
                'path': file_path,
                'time': execution_time,
                'success': success,
                'file_size': file_size
            })
            
            # بازگرداندن اشاره‌گر به ابتدای فایل
            img_io.seek(0)
            
    return results

@measure_time
def simulate_flask_file_upload():
    """شبیه‌سازی آپلود فایل در فلسک"""
    from werkzeug.datastructures import FileStorage
    
    create_test_dirs()
    results = []
    
    for size in FILE_SIZES:
        img_io = create_test_image(size=size)
        
        # ایجاد شی FileStorage
        file_storage = FileStorage(
            stream=img_io,
            filename=f"test_image_{size[0]}x{size[1]}.jpg",
            content_type="image/jpeg"
        )
        
        for upload_dir in TEST_UPLOAD_DIRS:
            filename = f"fs_test_image_{size[0]}x{size[1]}.jpg"
            file_path = os.path.join(upload_dir, filename)
            
            # اندازه‌گیری زمان ذخیره فایل با FileStorage
            start_time = time.time()
            try:
                file_storage.save(file_path)
                execution_time = time.time() - start_time
                file_size = os.path.getsize(file_path)
                success = True
                logger.info(f"Saved FileStorage to {file_path} ({file_size} bytes) in {execution_time:.4f}s")
            except Exception as e:
                execution_time = time.time() - start_time
                file_size = 0
                success = False
                logger.error(f"Failed to save FileStorage to {file_path}: {e}")
                
            results.append({
                'size': size,
                'path': file_path,
                'time': execution_time,
                'success': success,
                'file_size': file_size,
                'method': 'FileStorage'
            })
            
            # بازگرداندن اشاره‌گر به ابتدای فایل
            file_storage.stream.seek(0)
            
    return results

@measure_time
def run_upload_tests():
    """اجرای تمام تست‌های آپلود فایل"""
    logger.info("=== Starting file upload tests ===")
    
    # تست ذخیره مستقیم فایل
    logger.info("--- Testing direct file save ---")
    direct_results = test_direct_file_save()
    
    # تست شبیه‌سازی آپلود فلسک
    logger.info("--- Testing Flask file upload simulation ---")
    flask_results = simulate_flask_file_upload()
    
    # پاکسازی مسیرهای تست
    cleanup_test_dirs()
    
    # گزارش نتایج
    logger.info("=== File upload test results ===")
    logger.info("Direct save results:")
    for result in direct_results:
        logger.info(f"Size: {result['size']}, Time: {result['time']:.4f}s, Success: {result['success']}, File size: {result['file_size']} bytes")
        
    logger.info("Flask FileStorage results:")
    for result in flask_results:
        logger.info(f"Size: {result['size']}, Time: {result['time']:.4f}s, Success: {result['success']}, File size: {result['file_size']} bytes")
    
    return direct_results, flask_results

if __name__ == "__main__":
    run_upload_tests()