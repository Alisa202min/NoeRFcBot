#!/usr/bin/env python3
"""
راه‌انداز سرور وب برای workflow
"""

from app import app

if __name__ == '__main__':
    print("Starting web server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)