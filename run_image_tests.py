#!/usr/bin/env python
"""
اسکریپت اجرای تست‌های مربوط به تصاویر در RFCBot
"""

import os
import sys
import argparse
import pytest
import shutil

def setup_test_environment():
    """تنظیم محیط تست"""
    # ایجاد دایرکتوری‌های مورد نیاز
    os.makedirs('logs', exist_ok=True)
    os.makedirs('static/test_uploads', exist_ok=True)
    os.makedirs('tests/fixtures/images', exist_ok=True)
    
    # ایجاد تصاویر نمونه برای تست
    create_sample_images()
    
    print("Test environment setup completed.")


def create_sample_images():
    """ایجاد تصاویر نمونه برای تست‌ها"""
    from PIL import Image, ImageDraw, ImageFont
    
    fixtures_dir = 'tests/fixtures/images'
    
    # ایجاد تصویر JPG
    img = Image.new('RGB', (400, 300), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    d.text((10, 10), "Sample JPEG Image", fill=(255, 255, 255))
    img.save(os.path.join(fixtures_dir, 'sample.jpg'), 'JPEG')
    
    # ایجاد تصویر PNG
    img = Image.new('RGBA', (400, 300), color=(73, 109, 137, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 10), "Sample PNG Image", fill=(255, 255, 255))
    img.save(os.path.join(fixtures_dir, 'sample.png'), 'PNG')
    
    # ایجاد فایل نامعتبر
    with open(os.path.join(fixtures_dir, 'invalid.pdf'), 'w') as f:
        f.write("This is not a valid image file.")
    
    print(f"Sample images created in {fixtures_dir}")


def run_tests(verbose=False, xml_report=False, coverage=False):
    """اجرای تست‌ها"""
    args = ['tests/test_images.py']
    
    if verbose:
        args.append('-v')
    
    if xml_report:
        args.append('--junitxml=test_results/image_tests.xml')
        os.makedirs('test_results', exist_ok=True)
    
    if coverage:
        args = ['-m', 'pytest', '--cov=.', '--cov-report=html:test_results/coverage'] + args
        os.makedirs('test_results/coverage', exist_ok=True)
    
    print(f"Running tests with args: {args}")
    
    if coverage:
        import subprocess
        result = subprocess.run([sys.executable] + args, capture_output=False)
        return result.returncode
    else:
        return pytest.main(args)


def cleanup_test_environment():
    """پاکسازی محیط تست"""
    # حذف فایل‌های موقت
    if os.path.exists('static/test_uploads'):
        shutil.rmtree('static/test_uploads')
    
    print("Test environment cleanup completed.")


def main():
    """تابع اصلی"""
    parser = argparse.ArgumentParser(description="Run image-related tests for RFCBot")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose test output")
    parser.add_argument('--xml', action='store_true', help="Generate XML test report")
    parser.add_argument('--coverage', action='store_true', help="Generate coverage report")
    parser.add_argument('--no-setup', action='store_true', help="Skip test environment setup")
    parser.add_argument('--no-cleanup', action='store_true', help="Skip test environment cleanup")
    
    args = parser.parse_args()
    
    # تنظیم محیط تست
    if not args.no_setup:
        setup_test_environment()
    
    # اجرای تست‌ها
    result = run_tests(args.verbose, args.xml, args.coverage)
    
    # پاکسازی محیط تست
    if not args.no_cleanup:
        cleanup_test_environment()
    
    # نمایش گزارش
    if args.xml:
        print(f"XML report generated in test_results/image_tests.xml")
    
    if args.coverage:
        print(f"Coverage report generated in test_results/coverage")
    
    print(f"Test run completed with exit code {result}")
    sys.exit(result)


if __name__ == "__main__":
    main()