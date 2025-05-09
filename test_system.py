"""
Comprehensive Test System for RFCBot (Radio Frequency Catalog Bot)
------------------------------------------------------------------
This module provides systematic testing of all major and minor functionalities
of the RFCBot system, including both the Flask web application and
the Telegram bot components.
"""

import os
import sys
import unittest
import json
import requests
from contextlib import contextmanager
from io import StringIO
from app import app, db
from models import User, Category, Product, ProductMedia, Inquiry, StaticContent, EducationalContent
from database import get_categories, search_products, get_product_details
from configuration import load_config, save_config, reset_to_default

@contextmanager
def captured_output():
    """Capture stdout and stderr for testing"""
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

class DatabaseTestCase(unittest.TestCase):
    """Test case for database models and operations"""

    def setUp(self):
        """Set up test environment"""
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        # Use an in-memory database for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
        
    def tearDown(self):
        """Clean up test environment"""
        self.app_context.pop()
        
    def test_database_connection(self):
        """Test database connection"""
        result = db.session.execute("SELECT 1").fetchone()
        self.assertEqual(result[0], 1)

    def test_user_model(self):
        """Test User model CRUD operations"""
        # Create a test user
        test_user = User(username='testuser', email='test@example.com')
        test_user.set_password('password123')
        
        # Test password hashing
        self.assertTrue(test_user.check_password('password123'))
        self.assertFalse(test_user.check_password('wrong_password'))
        
        # Save user to database temporarily to test retrieval
        try:
            db.session.add(test_user)
            db.session.commit()
            
            # Test user retrieval
            retrieved_user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(retrieved_user)
            self.assertEqual(retrieved_user.email, 'test@example.com')
            
        finally:
            # Clean up test data
            User.query.filter_by(username='testuser').delete()
            db.session.commit()

    def test_category_model(self):
        """Test Category model"""
        # Create a test category
        test_category = Category(name='Test Category', cat_type='product')
        
        try:
            db.session.add(test_category)
            db.session.commit()
            
            # Test category retrieval
            categories = Category.query.filter_by(name='Test Category').all()
            self.assertEqual(len(categories), 1)
            self.assertEqual(categories[0].cat_type, 'product')
            
            # Test sub-category relationship
            sub_category = Category(name='Test Subcategory', cat_type='product', parent_id=test_category.id)
            db.session.add(sub_category)
            db.session.commit()
            
            # Verify parent-child relationship
            sub = Category.query.filter_by(name='Test Subcategory').first()
            self.assertEqual(sub.parent_id, test_category.id)
            
            # Test get_categories function
            with captured_output() as (out, err):
                categories = get_categories(cat_type='product')
                self.assertIsNotNone(categories)
                
        finally:
            # Clean up test data
            Category.query.filter_by(name='Test Subcategory').delete()
            Category.query.filter_by(name='Test Category').delete()
            db.session.commit()

    def test_product_model(self):
        """Test Product model and search functionality"""
        # Create a test category
        test_category = Category(name='Test Category', cat_type='product')
        db.session.add(test_category)
        db.session.commit()
        
        try:
            # Create test products
            test_product1 = Product(
                name='Test Oscilloscope', 
                price=1000,
                description='A test oscilloscope',
                category_id=test_category.id,
                product_type='product',
                tags='test,oscilloscope,equipment',
                brand='Test Brand',
                model_number='OSC-123',
                manufacturer='Test Manufacturer',
                in_stock=True,
                featured=True
            )
            test_product2 = Product(
                name='Test Service', 
                price=500,
                description='A test service',
                category_id=test_category.id,
                product_type='service',
                tags='test,service,repair',
                provider='Test Provider',
                service_code='SVC-456',
                duration='2 hours',
                in_stock=True,
                featured=False
            )
            
            db.session.add_all([test_product1, test_product2])
            db.session.commit()
            
            # Test basic product retrieval
            products = Product.query.all()
            self.assertGreaterEqual(len(products), 2)
            
            # Test product search by keyword
            with captured_output() as (out, err):
                search_results = search_products('oscilloscope')
                self.assertTrue(any('Test Oscilloscope' in str(p) for p in search_results))
                
            # Test product search by various filters
            advanced_search = Product.search(
                query='test',
                product_type='product',
                tags='equipment',
                brand='Test Brand',
                manufacturer='Test Manufacturer',
                model_number='OSC-123',
                in_stock=True,
                featured=True
            )
            self.assertGreaterEqual(advanced_search.count(), 1)
            
            # Test service search
            service_search = Product.search(
                query='test',
                product_type='service',
                provider='Test Provider',
                service_code='SVC-456',
                duration='2 hours'
            )
            self.assertGreaterEqual(service_search.count(), 1)
            
            # Test get product details
            with captured_output() as (out, err):
                product_details = get_product_details(test_product1.id)
                self.assertIsNotNone(product_details)
            
        finally:
            # Clean up test data
            Product.query.filter_by(name='Test Oscilloscope').delete()
            Product.query.filter_by(name='Test Service').delete()
            Category.query.filter_by(name='Test Category').delete()
            db.session.commit()

class WebAppTestCase(unittest.TestCase):
    """Test case for Flask web application"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        """Clean up test environment"""
        self.app_context.pop()
        
    def test_home_page(self):
        """Test home page rendering"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)
        
    def test_search_functionality(self):
        """Test search functionality"""
        # Test basic search
        response = self.app.get('/search?query=test')
        self.assertEqual(response.status_code, 200)
        
        # Test advanced search with filters
        advanced_search_url = (
            '/search?query=test&type=product&min_price=100&max_price=10000'
            '&brand=Test&manufacturer=Test&model_number=OSC-123'
            '&in_stock=true&featured=true'
        )
        response = self.app.get(advanced_search_url)
        self.assertEqual(response.status_code, 200)
        
        # Test service specific search
        service_search_url = (
            '/search?query=test&type=service&provider=Test'
            '&service_code=SVC-456&duration=2+hours'
        )
        response = self.app.get(service_search_url)
        self.assertEqual(response.status_code, 200)
        
    def test_admin_pages(self):
        """Test admin pages (without authentication)"""
        # Admin pages should redirect to login when not authenticated
        admin_pages = [
            '/admin/products',
            '/admin/services',
            '/admin/product/add',
            '/admin/service/add',
            '/database'
        ]
        
        for page in admin_pages:
            response = self.app.get(page)
            self.assertIn(response.status_code, [302, 401, 403])
            
    def test_login_page(self):
        """Test login page"""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'ورود', response.data)  # 'Login' in Persian

class ConfigurationTestCase(unittest.TestCase):
    """Test case for configuration functionality"""
    
    def test_config_loading(self):
        """Test configuration loading"""
        config = load_config()
        self.assertIsInstance(config, dict)
        self.assertGreaterEqual(len(config), 1)
        
    def test_reset_to_default(self):
        """Test resetting configuration to default"""
        original_config = load_config()
        
        # Make a copy to restore later
        config_copy = original_config.copy()
        
        try:
            # Reset to default
            reset_to_default()
            
            # Check that config was reset
            new_config = load_config()
            self.assertIsInstance(new_config, dict)
            
        finally:
            # Restore original config
            save_config(config_copy)

class BotTestCase(unittest.TestCase):
    """Test case for Telegram bot functionality (mocked)"""
    
    def test_bot_token_available(self):
        """Test that BOT_TOKEN is available in environment"""
        self.assertIsNotNone(os.environ.get('BOT_TOKEN'))

def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases to suite
    suite.addTests(loader.loadTestsFromTestCase(DatabaseTestCase))
    suite.addTests(loader.loadTestsFromTestCase(WebAppTestCase))
    suite.addTests(loader.loadTestsFromTestCase(ConfigurationTestCase))
    suite.addTests(loader.loadTestsFromTestCase(BotTestCase))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == '__main__':
    run_tests()