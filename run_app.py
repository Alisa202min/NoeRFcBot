#!/usr/bin/env python3
"""
راه‌انداز ساده برای برنامه Flask
"""

import os
import sys

# اضافه کردن مسیر src به Python path
if 'src' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # تلاش برای import از src
    from src.web.app import app
    print("✅ App imported successfully from src")
except ImportError:
    try:
        # تلاش برای import از فایل اصلی
        from app import app
        print("✅ App imported successfully from root")
    except ImportError as e:
        print(f"❌ Error importing app: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # تنظیمات برای development
    app.config['DEBUG'] = True
    
    print("🚀 Starting Flask application...")
    print("📍 Available at: http://0.0.0.0:5000")
    
    # راه‌اندازی سرور
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )