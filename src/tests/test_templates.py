"""
تست‌های مربوط به قالب‌های HTML
"""

import os
import unittest
from flask import render_template_string, template_rendered
from contextlib import contextmanager
from flask_testing import TestCase
from src.web.app import app


@contextmanager
def captured_templates(app):
    """
    کانتکست منیجر برای گرفتن قالب‌های رندر شده
    """
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


class TemplateStyleTests(TestCase):
    """
    تست‌های اطمینان از درستی استایل‌ها و هماهنگی قالب‌ها
    """
    
    def create_app(self):
        app.config['TESTING'] = True
        app.config['CSRF_ENABLED'] = False
        app.config['WTF_CSRF_ENABLED'] = False
        return app
    
    def test_html_dir_rtl(self):
        """تست اینکه تمام قالب‌ها دارای ویژگی dir="rtl" در تگ HTML هستند"""
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
        for filename in os.listdir(templates_dir):
            if filename.endswith('.html'):
                with open(os.path.join(templates_dir, filename), 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.assertIn('dir="rtl"', content, f"Template {filename} doesn't have dir=\"rtl\" attribute")
    
    def test_dark_theme_attribute(self):
        """تست اینکه قالب‌های اصلی دارای data-bs-theme=\"dark\" هستند"""
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
        base_templates = ['base.html', 'layout.html', 'admin_layout.html']
        
        for filename in base_templates:
            template_path = os.path.join(templates_dir, filename)
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.assertIn('data-bs-theme="dark"', content, 
                                 f"Base template {filename} doesn't have data-bs-theme=\"dark\" attribute")


if __name__ == '__main__':
    unittest.main()