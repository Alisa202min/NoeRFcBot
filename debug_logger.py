"""
کتابخانه لاگینگ پیشرفته برای دیباگ مشکلات
"""

import logging
import inspect
import os
import traceback
import sys
import time
from datetime import datetime
from functools import wraps

# تنظیم فرمت لاگ
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s"
DEBUG_LOG_FILE = "debug.log"

# تنظیم لاگر اصلی
logging.basicConfig(
    level=logging.DEBUG,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(DEBUG_LOG_FILE, 'a', 'utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("debug_logger")

def function_logger(func):
    """دکوراتور برای ثبت ورود و خروج به توابع همراه با پارامترها و مقدار برگشتی"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        file_name = inspect.getfile(func)
        line_no = inspect.getsourcelines(func)[1]
        
        # ثبت ورود به تابع
        args_str = ", ".join([str(arg) for arg in args])
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        params = f"{args_str}, {kwargs_str}" if args_str and kwargs_str else args_str or kwargs_str
        
        logger.debug(f"ENTER {func_name} in {file_name}:{line_no} with params: {params}")
        
        start_time = time.time()
        try:
            # اجرای تابع اصلی
            result = func(*args, **kwargs)
            
            # ثبت زمان اجرا و مقدار برگشتی
            execution_time = time.time() - start_time
            result_str = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
            logger.debug(f"EXIT {func_name} in {execution_time:.4f}s - returned: {result_str}")
            
            return result
        except Exception as e:
            # ثبت خطا
            execution_time = time.time() - start_time
            logger.error(f"ERROR in {func_name} after {execution_time:.4f}s: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    return wrapper

def log_error(e, context=""):
    """ثبت خطا با جزئیات کامل"""
    error_msg = f"ERROR {context}: {str(e)}"
    logger.error(error_msg)
    logger.error(traceback.format_exc())
    return error_msg

def measure_time(func):
    """دکوراتور برای اندازه‌گیری زمان اجرای توابع"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(f"Function {func.__name__} executed in {execution_time:.4f} seconds")
        return result
    return wrapper

def log_media_operations():
    """تنظیم لاگر ویژه برای عملیات رسانه‌ای"""
    media_logger = logging.getLogger("media_logger")
    media_logger.setLevel(logging.DEBUG)
    
    # ایجاد فایل لاگ ویژه برای عملیات رسانه‌ای
    media_log_file = f"media_operations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(media_log_file, 'a', 'utf-8')
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    # افزودن هندلر برای نمایش در کنسول
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    media_logger.addHandler(file_handler)
    media_logger.addHandler(console_handler)
    
    return media_logger

def log_api_call(api_name, params=None, response=None, error=None):
    """ثبت درخواست‌های API با پارامترها و پاسخ"""
    if params:
        logger.debug(f"API CALL {api_name} with params: {params}")
    else:
        logger.debug(f"API CALL {api_name}")
        
    if error:
        logger.error(f"API ERROR {api_name}: {error}")
    elif response:
        response_str = str(response)[:200] + "..." if len(str(response)) > 200 else str(response)
        logger.debug(f"API RESPONSE {api_name}: {response_str}")

def memory_usage():
    """بررسی مصرف حافظه فرآیند فعلی"""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        logger.info(f"Memory usage: {mem_info.rss / 1024 / 1024:.2f} MB")
        return mem_info.rss / 1024 / 1024
    except ImportError:
        logger.warning("psutil not installed, memory usage monitoring not available")
        return -1