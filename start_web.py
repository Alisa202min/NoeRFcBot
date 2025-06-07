#!/usr/bin/env python3
"""
راه‌انداز سرور وب برای workflow
"""

import os
import sys

# اضافه کردن مسیر فعلی به path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    print("Starting web server on 0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
except Exception as e:
    print(f"Error starting web server: {e}")
    sys.exit(1)