"""
این ماژول برای مدیریت ارتباط با پایگاه داده و بازیابی خودکار از خطاهای ارتباطی طراحی شده است.
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from functools import wraps

def connect_database(database_url=None):
    """
    ایجاد اتصال پایگاه داده با تنظیمات بهینه برای پایداری اتصال
    
    Args:
        database_url: آدرس اتصال به پایگاه داده (اختیاری، به صورت پیش‌فرض از محیط گرفته می‌شود)
        
    Returns:
        اتصال پایگاه داده پیکربندی شده
    """
    if not database_url:
        database_url = os.environ.get('DATABASE_URL')
        
    if not database_url:
        raise ValueError("DATABASE_URL not provided")
    
    logging.info("Establishing new database connection")
    connection = psycopg2.connect(
        database_url,
        # تنظیمات اضافی برای بهبود مقاومت ارتباط
        connect_timeout=10,  # زمان برقراری اتصال - 10 ثانیه
        keepalives=1,        # فعال کردن keepalive
        keepalives_idle=30,  # بعد از 30 ثانیه idle، بسته keepalive ارسال شود
        keepalives_interval=10,  # هر 10 ثانیه بسته keepalive ارسال شود
        keepalives_count=5   # حداکثر 5 تلاش مجدد قبل از خطا
    )
    connection.autocommit = True
    logging.info("Database connection established successfully")
    return connection

def test_connection(connection):
    """
    تست اتصال با اجرای یک کوئری ساده
    
    Args:
        connection: اتصال به پایگاه داده
        
    Returns:
        True اگر اتصال برقرار باشد، False در غیر این صورت
    """
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        return True
    except Exception as e:
        logging.error(f"Database connection test failed: {str(e)}")
        return False

def reconnect_if_needed(connection, database_url=None):
    """
    بررسی اتصال و برقراری مجدد در صورت نیاز
    
    Args:
        connection: اتصال به پایگاه داده
        database_url: آدرس اتصال به پایگاه داده (اختیاری)
        
    Returns:
        اتصال جدید یا موجود به پایگاه داده
    """
    if test_connection(connection):
        return connection
    
    logging.warning("Database connection lost. Attempting to reconnect...")
    try:
        connection.close()
    except:
        pass
    
    return connect_database(database_url)

def with_reconnect(func):
    """
    دکوراتور برای تابع‌هایی که با پایگاه داده کار می‌کنند
    در صورت قطع ارتباط، اتصال مجدد برقرار می‌کند و تابع را دوباره اجرا می‌کند.
    
    Args:
        func: تابعی که باید با این قابلیت بازآوری اجرا شود
        
    Returns:
        تابع بسته‌بندی شده با قابلیت بازیابی اتصال
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # فرض می‌کنیم آبجکت کلاس Database اولین پارامتر است
        db_instance = args[0]
        max_retries = 3
        attempts = 0
        
        while attempts < max_retries:
            try:
                try:
                    cursor = db_instance.conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute("SELECT 1")
                    cursor.close()
                except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                    # اتصال مجدد در صورت قطع شدن
                    logging.warning(f"Database connection lost. Reconnecting... Error: {str(e)}")
                    try:
                        db_instance.conn.close()
                    except:
                        pass
                    db_instance.conn = connect_database(db_instance.database_url)
                
                # اجرای تابع اصلی
                return func(*args, **kwargs)
                
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                attempts += 1
                logging.warning(f"Database operation failed (attempt {attempts}/{max_retries}): {str(e)}")
                
                if attempts >= max_retries:
                    logging.error(f"Maximum retries reached. Database operation failed permanently.")
                    raise
                
                # سعی مجدد با اتصال جدید
                try:
                    db_instance.conn.close()
                except:
                    pass
                db_instance.conn = connect_database(db_instance.database_url)
    
    return wrapper