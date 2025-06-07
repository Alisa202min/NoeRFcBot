"""
تست‌های مربوط به API و مسیرهای وب
"""

import unittest
import json
from flask_testing import TestCase
from src.web.app import app


class ApiRoutesTests(TestCase):
    """
    تست‌های مسیرهای API
    """
    
    def create_app(self):
        app.config['TESTING'] = True
        app.config['CSRF_ENABLED'] = False
        app.config['WTF_CSRF_ENABLED'] = False
        return app
    
    def test_api_categories_response(self):
        """تست پاسخ API دسته‌بندی‌ها"""
        response = self.client.get('/api/categories')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
    
    def test_api_products_response(self):
        """تست پاسخ API محصولات"""
        response = self.client.get('/api/products')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
    
    def test_api_services_response(self):
        """تست پاسخ API خدمات"""
        response = self.client.get('/api/services')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
    
    def test_api_educational_response(self):
        """تست پاسخ API محتوای آموزشی"""
        response = self.client.get('/api/educational')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
    
    def test_api_logs_json_response(self):
        """تست پاسخ JSON مسیر لاگ‌ها"""
        # استفاده از هدر مناسب برای درخواست JSON
        response = self.client.get('/logs', headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(response.status_code, 302)  # 302 for redirect to login
        
        # اگر بعدا احراز هویت اضافه کردیم، می‌توان تست دقیق‌تری نوشت
        # with self.client.session_transaction() as session:
        #     session['user_id'] = 1  # فرض کنید کاربر با ID=1 وجود دارد
        # response = self.client.get('/logs', headers={'X-Requested-With': 'XMLHttpRequest'})
        # self.assertEqual(response.status_code, 200)
        # self.assertTrue(response.is_json)
        # self.assertIn('logs', response.json)


class WebRoutesTests(TestCase):
    """
    تست‌های مسیرهای وب
    """
    
    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    def test_index_page(self):
        """تست صفحه اصلی"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_products_page(self):
        """تست صفحه محصولات"""
        response = self.client.get('/products')
        self.assertEqual(response.status_code, 200)
    
    def test_services_page(self):
        """تست صفحه خدمات"""
        response = self.client.get('/services')
        self.assertEqual(response.status_code, 200)
    
    def test_educational_page(self):
        """تست صفحه محتوای آموزشی"""
        response = self.client.get('/educational')
        self.assertEqual(response.status_code, 200)
    
    def test_login_page(self):
        """تست صفحه ورود"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
    
    def test_logs_page_redirect(self):
        """تست هدایت مجدد صفحه لاگ‌ها برای کاربران غیرمجاز"""
        response = self.client.get('/logs')
        self.assertEqual(response.status_code, 302)  # 302 for redirect to login


if __name__ == '__main__':
    unittest.main()