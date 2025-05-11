import pytest
import json
from flask import url_for
from unittest.mock import patch, MagicMock
from models import Category, Product, EducationalContent, StaticContent
from src.web.app import db


class TestAdminPanel:
    """
    Test admin panel functionality, particularly for managing categories
    and ensuring changes are immediately visible to the bot
    """

    def test_admin_login(self, flask_test_client):
        """Test admin login functionality"""
        # First logout to ensure we're starting fresh
        flask_test_client.get('/logout', follow_redirects=True)
        
        # Test login with valid credentials
        response = flask_test_client.post('/login', data={
            'username': 'admin_test',
            'password': 'test123'
        }, follow_redirects=True)
        
        # Should redirect to admin dashboard on success
        assert response.status_code == 200
        assert b'داشبورد مدیریت' in response.data
        
        # Test login with invalid credentials
        flask_test_client.get('/logout', follow_redirects=True)
        response = flask_test_client.post('/login', data={
            'username': 'wrong_username',
            'password': 'wrong_password'
        }, follow_redirects=True)
        
        # Should show error message
        assert b'نام کاربری یا رمز عبور نادرست است' in response.data

    def test_category_management(self, auth_flask_test_client):
        """Test category management in admin panel"""
        # Get the category management page
        response = auth_flask_test_client.get('/admin/categories')
        assert response.status_code == 200
        assert b'مدیریت دسته‌بندی‌ها' in response.data
        
        # Add a new product category
        response = auth_flask_test_client.post('/admin/product_categories/add', data={
            'name': 'دسته‌بندی تست',
            'parent_id': ''  # No parent (level 1)
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'دسته‌بندی با موفقیت اضافه شد' in response.data
        
        # Verify the category was added to the database
        with auth_flask_test_client.application.app_context():
            category = Category.query.filter_by(name='دسته‌بندی تست', cat_type='product').first()
            assert category is not None
            assert category.parent_id is None
            
            # Now add a subcategory (level 2)
            response = auth_flask_test_client.post('/admin/product_categories/add', data={
                'name': 'زیردسته تست',
                'parent_id': category.id
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'دسته‌بندی با موفقیت اضافه شد' in response.data
            
            # Verify the subcategory was added
            subcategory = Category.query.filter_by(name='زیردسته تست', cat_type='product').first()
            assert subcategory is not None
            assert subcategory.parent_id == category.id
            
            # Edit the subcategory
            response = auth_flask_test_client.post(f'/admin/product_categories/edit/{subcategory.id}', data={
                'name': 'زیردسته ویرایش شده',
                'parent_id': category.id
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'دسته‌بندی با موفقیت ویرایش شد' in response.data
            
            # Verify the change
            edited_subcategory = Category.query.get(subcategory.id)
            assert edited_subcategory.name == 'زیردسته ویرایش شده'
            
            # Delete the subcategory
            response = auth_flask_test_client.get(f'/admin/product_categories/delete/{subcategory.id}', 
                                              follow_redirects=True)
            
            assert response.status_code == 200
            assert b'دسته‌بندی با موفقیت حذف شد' in response.data
            
            # Verify it was deleted
            deleted_subcategory = Category.query.get(subcategory.id)
            assert deleted_subcategory is None
            
            # Clean up - delete the main category
            auth_flask_test_client.get(f'/admin/product_categories/delete/{category.id}', 
                                   follow_redirects=True)

    def test_service_category_management(self, auth_flask_test_client):
        """Test service category management in admin panel"""
        # Get the category management page
        response = auth_flask_test_client.get('/admin/categories')
        assert response.status_code == 200
        
        # Add a new service category
        response = auth_flask_test_client.post('/admin/service_categories/add', data={
            'name': 'خدمات تست',
            'parent_id': ''  # No parent (level 1)
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'دسته‌بندی با موفقیت اضافه شد' in response.data
        
        # Verify the category was added to the database
        with auth_flask_test_client.application.app_context():
            category = Category.query.filter_by(name='خدمات تست', cat_type='service').first()
            assert category is not None
            assert category.parent_id is None
            
            # Clean up
            auth_flask_test_client.get(f'/admin/service_categories/delete/{category.id}', 
                                   follow_redirects=True)

    def test_four_level_category_hierarchy(self, auth_flask_test_client):
        """Test creating a full four-level category hierarchy in the admin panel"""
        # Create level 1 category
        response = auth_flask_test_client.post('/admin/product_categories/add', data={
            'name': 'سطح ۱ تست',
            'parent_id': ''
        }, follow_redirects=True)
        
        with auth_flask_test_client.application.app_context():
            # Get the level 1 category
            level1 = Category.query.filter_by(name='سطح ۱ تست', cat_type='product').first()
            assert level1 is not None
            
            # Create level 2 category
            response = auth_flask_test_client.post('/admin/product_categories/add', data={
                'name': 'سطح ۲ تست',
                'parent_id': level1.id
            }, follow_redirects=True)
            
            level2 = Category.query.filter_by(name='سطح ۲ تست', cat_type='product').first()
            assert level2 is not None
            assert level2.parent_id == level1.id
            
            # Create level 3 category
            response = auth_flask_test_client.post('/admin/product_categories/add', data={
                'name': 'سطح ۳ تست',
                'parent_id': level2.id
            }, follow_redirects=True)
            
            level3 = Category.query.filter_by(name='سطح ۳ تست', cat_type='product').first()
            assert level3 is not None
            assert level3.parent_id == level2.id
            
            # Create level 4 category (leaf node)
            response = auth_flask_test_client.post('/admin/product_categories/add', data={
                'name': 'سطح ۴ تست',
                'parent_id': level3.id
            }, follow_redirects=True)
            
            level4 = Category.query.filter_by(name='سطح ۴ تست', cat_type='product').first()
            assert level4 is not None
            assert level4.parent_id == level3.id
            
            # Verify the full hierarchy
            # Level 1 should have level 2 as child
            level1_children = Category.query.filter_by(parent_id=level1.id, cat_type='product').all()
            assert any(child.id == level2.id for child in level1_children)
            
            # Level 2 should have level 3 as child
            level2_children = Category.query.filter_by(parent_id=level2.id, cat_type='product').all()
            assert any(child.id == level3.id for child in level2_children)
            
            # Level 3 should have level 4 as child
            level3_children = Category.query.filter_by(parent_id=level3.id, cat_type='product').all()
            assert any(child.id == level4.id for child in level3_children)
            
            # Level 4 should have no children (leaf node)
            level4_children = Category.query.filter_by(parent_id=level4.id, cat_type='product').all()
            assert len(level4_children) == 0
            
            # Clean up - delete the top level category (should cascade)
            auth_flask_test_client.get(f'/admin/product_categories/delete/{level1.id}', 
                                   follow_redirects=True)
            
            # Verify everything was deleted
            assert Category.query.get(level1.id) is None
            assert Category.query.get(level2.id) is None
            assert Category.query.get(level3.id) is None
            assert Category.query.get(level4.id) is None

    def test_product_management(self, auth_flask_test_client):
        """Test product management in admin panel"""
        # First create a category for the product
        response = auth_flask_test_client.post('/admin/product_categories/add', data={
            'name': 'دسته محصول تست',
            'parent_id': ''
        }, follow_redirects=True)
        
        with auth_flask_test_client.application.app_context():
            # Get the category
            category = Category.query.filter_by(name='دسته محصول تست', cat_type='product').first()
            assert category is not None
            
            # Add a new product
            response = auth_flask_test_client.post('/admin/products/add', data={
                'name': 'محصول تست',
                'price': '1000000',
                'description': 'توضیحات محصول تست',
                'category_id': category.id,
                'product_type': 'product',
                'brand': 'برند تست',
                'tags': 'تست,محصول',
                'in_stock': 'true'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'محصول با موفقیت اضافه شد' in response.data
            
            # Verify the product was added
            product = Product.query.filter_by(name='محصول تست').first()
            assert product is not None
            assert product.category_id == category.id
            assert product.price == 1000000
            
            # Edit the product
            response = auth_flask_test_client.post(f'/admin/products/edit/{product.id}', data={
                'name': 'محصول ویرایش شده',
                'price': '1500000',
                'description': 'توضیحات بروز شده',
                'category_id': category.id,
                'product_type': 'product',
                'brand': 'برند تست',
                'tags': 'تست,محصول,ویرایش',
                'in_stock': 'true'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'محصول با موفقیت ویرایش شد' in response.data
            
            # Verify the changes
            edited_product = Product.query.get(product.id)
            assert edited_product.name == 'محصول ویرایش شده'
            assert edited_product.price == 1500000
            
            # Delete the product
            response = auth_flask_test_client.get(f'/admin/products/delete/{product.id}', 
                                             follow_redirects=True)
            
            assert response.status_code == 200
            assert b'محصول با موفقیت حذف شد' in response.data
            
            # Verify it was deleted
            deleted_product = Product.query.get(product.id)
            assert deleted_product is None
            
            # Clean up - delete the category
            auth_flask_test_client.get(f'/admin/product_categories/delete/{category.id}', 
                                   follow_redirects=True)

    def test_bot_visibility_of_admin_changes(self, auth_flask_test_client):
        """
        Test that changes made in the admin panel are immediately visible to the bot
        This test simulates the database queries that would be made by the bot
        """
        # Create a test category in admin panel
        response = auth_flask_test_client.post('/admin/product_categories/add', data={
            'name': 'دسته تست ربات',
            'parent_id': ''
        }, follow_redirects=True)
        
        with auth_flask_test_client.application.app_context():
            # Get the category
            category = Category.query.filter_by(name='دسته تست ربات', cat_type='product').first()
            assert category is not None
            
            # Simulate bot query to get categories
            from database import Database
            db_instance = Database()
            
            # Check if the category is visible to the bot
            bot_categories = db_instance.get_categories(cat_type='product')
            bot_category_ids = [cat['id'] for cat in bot_categories]
            assert category.id in bot_category_ids
            
            # Add a product to the category
            response = auth_flask_test_client.post('/admin/products/add', data={
                'name': 'محصول تست ربات',
                'price': '1000000',
                'description': 'توضیحات محصول تست',
                'category_id': category.id,
                'product_type': 'product',
                'in_stock': 'true'
            }, follow_redirects=True)
            
            # Get the product
            product = Product.query.filter_by(name='محصول تست ربات').first()
            assert product is not None
            
            # Simulate bot query to get products in this category
            bot_products = db_instance.get_products_by_category(category.id)
            bot_product_ids = [p['id'] for p in bot_products]
            assert product.id in bot_product_ids
            
            # Edit the category
            response = auth_flask_test_client.post(f'/admin/product_categories/edit/{category.id}', data={
                'name': 'دسته ربات ویرایش شده',
                'parent_id': ''
            }, follow_redirects=True)
            
            # Verify the bot sees the updated name
            updated_category = db_instance.get_category(category.id)
            assert updated_category['name'] == 'دسته ربات ویرایش شده'
            
            # Clean up
            auth_flask_test_client.get(f'/admin/products/delete/{product.id}', follow_redirects=True)
            auth_flask_test_client.get(f'/admin/product_categories/delete/{category.id}', follow_redirects=True)

    def test_educational_content_management(self, auth_flask_test_client):
        """Test educational content management in admin panel"""
        # Add educational content
        response = auth_flask_test_client.post('/admin/education/add', data={
            'title': 'محتوای آموزشی تست',
            'content': 'متن محتوای آموزشی تست',
            'category': 'دسته آموزشی تست',
            'content_type': 'text'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'محتوای آموزشی با موفقیت اضافه شد' in response.data
        
        with auth_flask_test_client.application.app_context():
            # Verify content was added
            content = EducationalContent.query.filter_by(title='محتوای آموزشی تست').first()
            assert content is not None
            assert content.category == 'دسته آموزشی تست'
            
            # Edit the content
            response = auth_flask_test_client.post(f'/admin/education/edit/{content.id}', data={
                'title': 'محتوای آموزشی ویرایش شده',
                'content': 'متن بروز شده',
                'category': 'دسته آموزشی تست',
                'content_type': 'text'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'محتوای آموزشی با موفقیت ویرایش شد' in response.data
            
            # Verify changes
            edited_content = EducationalContent.query.get(content.id)
            assert edited_content.title == 'محتوای آموزشی ویرایش شده'
            
            # Delete the content
            response = auth_flask_test_client.get(f'/admin/education/delete/{content.id}', 
                                             follow_redirects=True)
            
            assert response.status_code == 200
            assert b'محتوای آموزشی با موفقیت حذف شد' in response.data
            
            # Verify deletion
            deleted_content = EducationalContent.query.get(content.id)
            assert deleted_content is None

    def test_static_content_management(self, auth_flask_test_client):
        """Test static content (about/contact) management in admin panel"""
        # Check existing static content
        with auth_flask_test_client.application.app_context():
            about_content = StaticContent.query.filter_by(content_type='about').first()
            contact_content = StaticContent.query.filter_by(content_type='contact').first()
            
            # Update about content
            if about_content:
                response = auth_flask_test_client.post('/admin/static-content/update', data={
                    'content_type': 'about',
                    'content': 'متن درباره ما بروز شده برای تست'
                }, follow_redirects=True)
                
                assert response.status_code == 200
                assert b'محتوای ثابت با موفقیت بروز شد' in response.data
                
                # Verify changes
                updated_about = StaticContent.query.filter_by(content_type='about').first()
                assert updated_about.content == 'متن درباره ما بروز شده برای تست'
            
            # Update contact content
            if contact_content:
                response = auth_flask_test_client.post('/admin/static-content/update', data={
                    'content_type': 'contact',
                    'content': 'اطلاعات تماس بروز شده برای تست'
                }, follow_redirects=True)
                
                assert response.status_code == 200
                assert b'محتوای ثابت با موفقیت بروز شد' in response.data
                
                # Verify changes
                updated_contact = StaticContent.query.filter_by(content_type='contact').first()
                assert updated_contact.content == 'اطلاعات تماس بروز شده برای تست'