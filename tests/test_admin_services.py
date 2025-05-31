"""
تست مدیریت خدمات در پنل ادمین
"""

import os
import pytest
from flask import url_for
import json
from src.web.app import app
from models import db, Service, ServiceCategory, ServiceMedia

@pytest.fixture
def admin_client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()

def test_admin_services_page(admin_client):
    """تست نمایش صفحه مدیریت خدمات"""
    response = admin_client.get('/admin/services')
    assert response.status_code == 200
    assert b'\xd9\x85\xd8\xaf\xdb\x8c\xd8\xb1\xdb\x8c\xd8\xaa \xd8\xae\xd8\xaf\xd9\x85\xd8\xa7\xd8\xaa' in response.data  # مدیریت خدمات

def test_service_category_listing(admin_client):
    """تست نمایش دسته‌بندی‌های خدمات"""
    with app.app_context():
        # ایجاد یک دسته‌بندی خدمات
        category = ServiceCategory(name="دسته‌بندی تست خدمات", description="توضیحات تست")
        db.session.add(category)
        db.session.commit()
        
        response = admin_client.get('/admin/service_categories')
        assert response.status_code == 200
        assert b'\xd8\xaf\xd8\xb3\xd8\xaa\xd9\x87\xe2\x80\x8c\xd8\xa8\xd9\x86\xd8\xaf\xdb\x8c \xd8\xaa\xd8\xb3\xd8\xaa \xd8\xae\xd8\xaf\xd9\x85\xd8\xa7\xd8\xaa' in response.data  # دسته‌بندی تست خدمات

def test_add_service(admin_client):
    """تست افزودن خدمات جدید"""
    with app.app_context():
        # ایجاد یک دسته‌بندی خدمات
        category = ServiceCategory(name="دسته‌بندی تست", description="توضیحات تست")
        db.session.add(category)
        db.session.commit()
        
        service_data = {
            'name': 'خدمات تست',
            'description': 'توضیحات خدمات تست',
            'price': 1000000,
            'category_id': category.id
        }
        
        response = admin_client.post('/admin/services/add', data=service_data, follow_redirects=True)
        assert response.status_code == 200
        
        # بررسی اضافه شدن خدمات به دیتابیس
        added_service = Service.query.filter_by(name='خدمات تست').first()
        assert added_service is not None
        assert added_service.price == 1000000
        assert added_service.category_id == category.id

def test_edit_service(admin_client):
    """تست ویرایش خدمات"""
    with app.app_context():
        # ایجاد یک دسته‌بندی خدمات
        category = ServiceCategory(name="دسته‌بندی تست", description="توضیحات تست")
        db.session.add(category)
        
        # ایجاد یک خدمات
        service = Service(
            name="خدمات اصلی",
            description="توضیحات خدمات اصلی",
            price=1000000,
            category_id=None  # فعلاً بدون دسته‌بندی
        )
        db.session.add(service)
        db.session.commit()
        
        # ویرایش خدمات
        edit_data = {
            'name': 'خدمات ویرایش شده',
            'description': 'توضیحات جدید',
            'price': 2000000,
            'category_id': category.id
        }
        
        response = admin_client.post(f'/admin/services/edit/{service.id}', data=edit_data, follow_redirects=True)
        assert response.status_code == 200
        
        # بررسی اعمال تغییرات
        edited_service = Service.query.get(service.id)
        assert edited_service.name == 'خدمات ویرایش شده'
        assert edited_service.price == 2000000
        assert edited_service.category_id == category.id

def test_delete_service(admin_client):
    """تست حذف خدمات"""
    with app.app_context():
        # ایجاد یک خدمات
        service = Service(
            name="خدمات قابل حذف",
            description="این خدمات برای تست حذف است",
            price=500000
        )
        db.session.add(service)
        db.session.commit()
        
        service_id = service.id
        
        # حذف خدمات
        response = admin_client.get(f'/admin/services/delete/{service_id}', follow_redirects=True)
        assert response.status_code == 200
        
        # بررسی حذف خدمات
        deleted_service = Service.query.get(service_id)
        assert deleted_service is None