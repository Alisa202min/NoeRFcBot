"""
اسکریپت اصلی برای اجرای تست‌ها
"""

from src.tests.run_tests import run_all_tests
import sys

if __name__ == "__main__":
    sys.exit(run_all_tests())