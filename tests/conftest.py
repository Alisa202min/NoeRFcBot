"""
فایل conftest.py برای تعریف فیکسچرهای مورد نیاز تست‌ها
"""

import os
import sys
import pytest
import tempfile
from PIL import Image
import io
import shutil
from werkzeug.datastructures import FileStorage

# اضافه کردن مسیر پروژه به سیستم
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ایمپورت کلاس Database
from database import Database

# ایجاد مسیر آپلود موقت برای تست
@pytest.fixture
def app_upload_folder():
    """ایجاد پوشه آپلود موقت برای تست"""
    temp_dir = tempfile.mkdtemp()
    uploads_dir = os.path.join(temp_dir, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    yield uploads_dir
    # پاک کردن فایل‌ها بعد از تست
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_image():
    """ایجاد یک تصویر نمونه برای تست"""
    # ایجاد یک تصویر ساده برای تست
    img = Image.new('RGB', (100, 100), color=(73, 109, 137))
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    
    return img_io

@pytest.fixture
def invalid_file():
    """ایجاد یک فایل نامعتبر (غیر تصویری) برای تست"""
    file_content = b"This is not an image file"
    return io.BytesIO(file_content)

@pytest.fixture
def sample_image_file(sample_image):
    """ایجاد یک آبجکت FileStorage از تصویر نمونه"""
    return FileStorage(
        stream=sample_image,
        filename='test_image.jpg',
        content_type='image/jpeg'
    )

@pytest.fixture
def large_image_file():
    """ایجاد یک تصویر بزرگ برای تست محدودیت سایز"""
    # ایجاد یک تصویر بزرگ (6MB)
    img = Image.new('RGB', (2000, 1500), color=(73, 109, 137))
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG', quality=100)
    
    # تکرار داده‌ها برای رسیدن به سایز مورد نظر
    data = img_io.getvalue()
    while len(data) < 6 * 1024 * 1024:  # 6MB
        data += data
    
    large_io = io.BytesIO(data[:6 * 1024 * 1024])
    large_io.seek(0)
    
    return FileStorage(
        stream=large_io,
        filename='large_image.jpg',
        content_type='image/jpeg'
    )

@pytest.fixture
def invalid_file_storage():
    """ایجاد یک آبجکت FileStorage از فایل نامعتبر"""
    return FileStorage(
        stream=io.BytesIO(b"This is not an image file"),
        filename='test_document.pdf',
        content_type='application/pdf'
    )

@pytest.fixture
def db():
    """اتصال به دیتابیس"""
    # استفاده از دیتابیس تست جدا از دیتابیس اصلی
    os.environ['TEST_MODE'] = 'True'
    
    # ایجاد کانکشن دیتابیس
    database = Database()
    
    yield database
    
    # پاکسازی دیتابیس تست بعد از اتمام تست‌ها
    try:
        print("Test database cleaned up successfully")
    except Exception as e:
        print(f"Error cleaning up test database: {e}")
    finally:
        os.environ.pop('TEST_MODE', None)

@pytest.fixture
def test_db():
    """اتصال به دیتابیس - نام متفاوت برای سازگاری با تست‌های قبلی"""
    # استفاده از دیتابیس تست جدا از دیتابیس اصلی
    os.environ['TEST_MODE'] = 'True'
    
    # ایجاد کانکشن دیتابیس
    database = Database()
    
    yield database
    
    # پاکسازی دیتابیس تست بعد از اتمام تست‌ها
    try:
        print("Test database cleaned up successfully")
    except Exception as e:
        print(f"Error cleaning up test database: {e}")
    finally:
        os.environ.pop('TEST_MODE', None)

@pytest.fixture
def flask_client():
    """کلاینت Flask برای تست‌های API"""
    try:
        # ابتدا تلاش می‌کنیم app را به صورت عادی import کنیم
        from app import app
    except Exception as e:
        print(f"Error importing app: {e}")
        # اگر در import اصلی مشکلی وجود داشت، تلاش می‌کنیم از flask یک نمونه جدید بسازیم
        from flask import Flask
        app = Flask(__name__)
        print("Created a new Flask app instance for testing")
    
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost.localdomain'
    
    # تنظیم مسیر آپلود برای تست
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static/test_uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # ثبت route های ساده برای تست
    @app.route('/test')
    def test_route():
        return 'Test route works!'
    
    # اضافه کردن app context برای تست‌ها
    app_context = app.app_context()
    app_context.push()
    
    with app.test_client() as client:
        print("Flask test client created successfully")
        yield client
    
    # خروج از app context
    app_context.pop()
    
    # پاکسازی فایل‌های آپلود شده
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        try:
            for file in os.listdir(app.config['UPLOAD_FOLDER']):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            print("Test upload folder cleaned up")
        except Exception as e:
            print(f"Error cleaning up test files: {e}")

@pytest.fixture
def admin_flask_client(flask_client):
    """کلاینت Flask با لاگین ادمین برای تست‌های نیازمند احراز هویت"""
    # شبیه‌سازی لاگین ادمین
    with flask_client.session_transaction() as session:
        session['admin_logged_in'] = True
        session['admin_username'] = 'test_admin'
        session['admin_id'] = 1  # شناسه ادمین برای تست‌ها
    
    # ایجاد دایرکتوری آپلود برای تست
    from app import app
    upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
    if upload_folder and not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
    
    return flask_client