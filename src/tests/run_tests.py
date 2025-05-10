"""
اسکریپت اجرای تمام تست‌ها
"""

import unittest
import sys
import os


def run_all_tests():
    """اجرای تمام تست‌های پروژه"""
    # اضافه کردن مسیر اصلی پروژه به سیستم تا import ها درست کار کنند
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    
    # یافتن و اجرای تمام تست‌ها
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(tests_dir, pattern="test_*.py")
    
    # اجرای تست ها و نمایش نتایج
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # برگرداندن کد متناسب با نتیجه تست برای استفاده در CI/CD
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())