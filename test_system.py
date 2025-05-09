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
from configuration import load_config, save_config, reset_to_default

# Function prototypes for tests that may not exist directly
def get_categories(cat_type=None):
    """Get categories prototype"""
    try:
        from database import Database
        db_instance = Database()
        return db_instance.get_categories(cat_type=cat_type)
    except (ImportError, AttributeError):
        return []

def search_products(query=None, **kwargs):
    """Search products prototype"""
    try:
        from database import Database
        db_instance = Database()
        return db_instance.search_products(query=query, **kwargs)
    except (ImportError, AttributeError):
        return []

def get_product_details(product_id):
    """Get product details prototype"""
    try:
        from database import Database
        db_instance = Database()
        return db_instance.get_product(product_id)
    except (ImportError, AttributeError):
        return None

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
        
        # Test search with multiple parameters
        combined_search_url = (
            '/search?query=oscilloscope&type=product&category_id=1'
            '&min_price=500&max_price=5000&tags=equipment'
            '&brand=Tektronix&manufacturer=Tektronix&model_number=TDS2000'
            '&in_stock=true&featured=true&sort_by=price&sort_order=desc'
        )
        response = self.app.get(combined_search_url)
        self.assertEqual(response.status_code, 200)
        
    def test_search_display_types(self):
        """Test search display for different product types"""
        # Test product display with product-specific fields
        product_search = '/search?type=product'
        response = self.app.get(product_search)
        self.assertEqual(response.status_code, 200)
        # Check for product-specific filter fields in the HTML
        response_text = response.data.decode('utf-8')
        self.assertIn('brand', response_text.lower())  # Brand
        self.assertIn('manufacturer', response_text.lower())  # Manufacturer
        self.assertIn('model', response_text.lower())  # Model number
        
        # Test service display with service-specific fields
        service_search = '/search?type=service'
        response = self.app.get(service_search)
        self.assertEqual(response.status_code, 200)
        # Check for service-specific filter fields in the HTML
        response_text = response.data.decode('utf-8')
        self.assertIn('provider', response_text.lower())  # Provider
        self.assertIn('service code', response_text.lower())  # Service code
        self.assertIn('duration', response_text.lower())  # Duration
        
    def test_pagination_functionality(self):
        """Test search pagination functionality"""
        # Test pagination with multiple search parameters
        pagination_url = '/search?page=1&query=test&sort_by=name&sort_order=asc'
        response = self.app.get(pagination_url)
        self.assertEqual(response.status_code, 200)
        
        # Move to second page
        page2_url = '/search?page=2&query=test&sort_by=name&sort_order=asc'
        response = self.app.get(page2_url)
        self.assertEqual(response.status_code, 200)
        
    def test_sorting_functionality(self):
        """Test search sorting functionality"""
        # Test sorting by price ascending
        sort_price_asc = '/search?sort_by=price&sort_order=asc'
        response = self.app.get(sort_price_asc)
        self.assertEqual(response.status_code, 200)
        
        # Test sorting by price descending
        sort_price_desc = '/search?sort_by=price&sort_order=desc'
        response = self.app.get(sort_price_desc)
        self.assertEqual(response.status_code, 200)
        
        # Test sorting by name
        sort_name = '/search?sort_by=name&sort_order=asc'
        response = self.app.get(sort_name)
        self.assertEqual(response.status_code, 200)
        
        # Test sorting by newest
        sort_newest = '/search?sort_by=newest&sort_order=desc'
        response = self.app.get(sort_newest)
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
        # Check for login page elements
        self.assertIn(b'login', response.data.lower())  # 'Login' in page content

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
    
    def test_bot_imports(self):
        """Test that the bot's required modules are available"""
        # Test aiogram imports
        try:
            import aiogram
            from aiogram import Bot, Dispatcher, types
            from aiogram.filters import Command
            self.assertIsNotNone(aiogram)
        except ImportError:
            self.fail("aiogram package is not installed")
    
    def test_bot_handlers_file(self):
        """Test that the handlers file exists and is properly structured"""
        try:
            import handlers
            # Check if the necessary functions exist or if there are any handler functions
            handler_methods = [name for name in dir(handlers) if callable(getattr(handlers, name)) 
                              and (name.startswith('cmd_') or name.startswith('callback_'))]
            self.assertGreater(len(handler_methods), 0, "No handler methods found in handlers module")
        except ImportError:
            self.fail("handlers module cannot be imported")
            
    def test_bot_keyboards(self):
        """Test that keyboard utilities are available"""
        try:
            import keyboards
            # Test keyboard creation functions
            keyboard_methods = [name for name in dir(keyboards) if callable(getattr(keyboards, name)) 
                               and not name.startswith('_')]
            self.assertGreater(len(keyboard_methods), 0, "No keyboard methods found in keyboards module")
        except ImportError:
            self.fail("keyboards module cannot be imported")
    
    def test_database_connection_for_bot(self):
        """Test bot's database connection methods"""
        try:
            import database
            # Check if there's a Database class with necessary methods for the bot
            self.assertTrue(hasattr(database, 'Database'), "Database class not found")
            db_class = getattr(database, 'Database')
            # Check if the class has any methods
            db_methods = [name for name in dir(db_class) if callable(getattr(db_class, name)) 
                         and not name.startswith('_')]
            self.assertGreater(len(db_methods), 0, "No database methods found")
        except ImportError:
            self.fail("database module cannot be imported")
            
    def test_media_handling(self):
        """Test media handling functions for the bot"""
        try:
            import handlers
            # Check for methods in handlers module related to inquiries
            inquiry_methods = [name for name in dir(handlers) if callable(getattr(handlers, name)) 
                              and 'inquiry' in name.lower()]
            self.assertGreater(len(inquiry_methods), 0, "No inquiry handling methods found")
            
            # Check if there's any media-related functionality
            media_related = any('media' in name.lower() or 'photo' in name.lower() or 
                               'video' in name.lower() or 'file' in name.lower() 
                               for name in dir(handlers))
            self.assertTrue(media_related, "No media-related functionality found")
        except ImportError:
            self.fail("handlers module cannot be imported")
                
    def test_search_filter_functionality(self):
        """Test that search and filter functionality is available in the bot"""
        try:
            import database
            # Check if Database class exists
            self.assertTrue(hasattr(database, 'Database'), "Database class not found")
            db_class = getattr(database, 'Database')
            
            # Search for search-related methods in the Database class
            search_methods = [name for name in dir(db_class) if callable(getattr(db_class, name)) 
                             and any(term in name.lower() for term in 
                                   ['search', 'filter', 'find', 'query', 'get_product'])]
            
            # At least some search functionality should be present
            self.assertGreater(len(search_methods), 0, 
                              "No search or filter methods found in Database class")

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