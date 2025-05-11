import pytest
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from database import Database
from unittest.mock import patch, MagicMock


class TestDatabase:
    """
    Test database interactions to ensure category hierarchy is properly maintained
    and queries are returning the expected data structures
    """

    @pytest.fixture
    def test_db(self, test_db_url):
        """Create a test database instance"""
        # Save the current DATABASE_URL
        original_db_url = os.environ.get('DATABASE_URL')
        
        # Set the test database URL for the duration of the test
        os.environ['DATABASE_URL'] = test_db_url
        
        # Create the database instance
        db = Database()
        
        # Yield the database to the test
        yield db
        
        # Restore the original DATABASE_URL
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        else:
            os.environ.pop('DATABASE_URL', None)

    def test_get_categories_hierarchy(self, test_db):
        """Test retrieving categories with parent-child relationships intact"""
        # Get all product categories
        product_categories = test_db.get_categories(cat_type='product')
        
        # Verify we got some categories
        assert len(product_categories) > 0
        
        # Check that the hierarchy is properly represented
        # Level 1 categories should have parent_id = None
        level1_categories = [cat for cat in product_categories if cat['parent_id'] is None]
        assert len(level1_categories) > 0
        
        # Get a level 1 category to test with
        test_level1 = level1_categories[0]
        
        # Get level 2 categories under the test level 1 category
        level2_categories = test_db.get_categories(parent_id=test_level1['id'], cat_type='product')
        assert len(level2_categories) > 0
        
        # All level 2 categories should have the level 1 category as parent
        for cat in level2_categories:
            assert cat['parent_id'] == test_level1['id']
        
        # Get a level 2 category to test with
        test_level2 = level2_categories[0]
        
        # Get level 3 categories under the test level 2 category
        level3_categories = test_db.get_categories(parent_id=test_level2['id'], cat_type='product')
        
        # If there are level 3 categories, test level 4
        if level3_categories:
            test_level3 = level3_categories[0]
            level4_categories = test_db.get_categories(parent_id=test_level3['id'], cat_type='product')
            
            # Level 4 categories should be leaf nodes with no children
            if level4_categories:
                test_level4 = level4_categories[0]
                leaf_categories = test_db.get_categories(parent_id=test_level4['id'], cat_type='product')
                assert len(leaf_categories) == 0, "Level 4 categories should be leaf nodes with no children"

    def test_add_and_retrieve_category(self, test_db):
        """Test adding a new category and retrieving it with the correct hierarchy"""
        # Add a new level 1 category
        new_level1_name = "دسته‌بندی تست"
        new_level1_id = test_db.add_category(name=new_level1_name, cat_type='product')
        
        # Verify it was added
        category = test_db.get_category(new_level1_id)
        assert category is not None
        assert category['name'] == new_level1_name
        assert category['parent_id'] is None
        
        # Add a level 2 category under it
        new_level2_name = "زیردسته تست"
        new_level2_id = test_db.add_category(name=new_level2_name, parent_id=new_level1_id, cat_type='product')
        
        # Verify the level 2 category
        level2_category = test_db.get_category(new_level2_id)
        assert level2_category is not None
        assert level2_category['name'] == new_level2_name
        assert level2_category['parent_id'] == new_level1_id
        
        # Add a level 3 category
        new_level3_name = "زیردسته تست سطح ۳"
        new_level3_id = test_db.add_category(name=new_level3_name, parent_id=new_level2_id, cat_type='product')
        
        # Verify the level 3 category
        level3_category = test_db.get_category(new_level3_id)
        assert level3_category is not None
        assert level3_category['name'] == new_level3_name
        assert level3_category['parent_id'] == new_level2_id
        
        # Add a level 4 category (leaf node)
        new_level4_name = "زیردسته تست سطح ۴"
        new_level4_id = test_db.add_category(name=new_level4_name, parent_id=new_level3_id, cat_type='product')
        
        # Verify the level 4 category
        level4_category = test_db.get_category(new_level4_id)
        assert level4_category is not None
        assert level4_category['name'] == new_level4_name
        assert level4_category['parent_id'] == new_level3_id
        
        # Verify that getting subcategories of level 4 returns empty (leaf node)
        level5_categories = test_db.get_categories(parent_id=new_level4_id, cat_type='product')
        assert len(level5_categories) == 0, "Level 4 categories should be leaf nodes with no children"
        
        # Retrieve all categories and check the hierarchy
        all_categories = test_db.get_categories(cat_type='product')
        
        # Find our test categories in the result
        level1_found = False
        level2_found = False
        level3_found = False
        level4_found = False
        
        for cat in all_categories:
            if cat['id'] == new_level1_id:
                level1_found = True
                assert cat['parent_id'] is None
            elif cat['id'] == new_level2_id:
                level2_found = True
                assert cat['parent_id'] == new_level1_id
            elif cat['id'] == new_level3_id:
                level3_found = True
                assert cat['parent_id'] == new_level2_id
            elif cat['id'] == new_level4_id:
                level4_found = True
                assert cat['parent_id'] == new_level3_id
        
        # Verify all categories were found
        assert level1_found, "Level 1 category not found in results"
        assert level2_found, "Level 2 category not found in results"
        assert level3_found, "Level 3 category not found in results"
        assert level4_found, "Level 4 category not found in results"

    def test_add_and_retrieve_products(self, test_db):
        """Test adding products to a leaf category and retrieving them"""
        # First create a 4-level category hierarchy
        level1_id = test_db.add_category(name="محصولات تست", cat_type='product')
        level2_id = test_db.add_category(name="زیردسته تست", parent_id=level1_id, cat_type='product')
        level3_id = test_db.add_category(name="زیردسته تست سطح ۳", parent_id=level2_id, cat_type='product')
        level4_id = test_db.add_category(name="زیردسته تست سطح ۴", parent_id=level3_id, cat_type='product')
        
        # Add a product to the level 4 (leaf) category
        product_name = "محصول تست"
        product_price = 1000000
        product_description = "توضیحات محصول تست"
        
        product_id = test_db.add_product(
            name=product_name,
            price=product_price,
            description=product_description,
            category_id=level4_id
        )
        
        # Verify the product was added
        product = test_db.get_product(product_id)
        assert product is not None
        assert product['name'] == product_name
        assert product['price'] == product_price
        assert product['description'] == product_description
        assert product['category_id'] == level4_id
        
        # Retrieve products by category
        products_in_category = test_db.get_products_by_category(level4_id)
        assert len(products_in_category) == 1
        assert products_in_category[0]['id'] == product_id
        assert products_in_category[0]['name'] == product_name

    def test_service_category_operations(self, test_db):
        """Test operations on service categories to ensure they follow the same hierarchy rules"""
        # Add service categories with a 4-level hierarchy
        service_level1_id = test_db.add_category(name="خدمات تست", cat_type='service')
        service_level2_id = test_db.add_category(name="خدمات تست سطح ۲", parent_id=service_level1_id, cat_type='service')
        service_level3_id = test_db.add_category(name="خدمات تست سطح ۳", parent_id=service_level2_id, cat_type='service')
        service_level4_id = test_db.add_category(name="خدمات تست سطح ۴", parent_id=service_level3_id, cat_type='service')
        
        # Verify service categories were added correctly
        service_level1 = test_db.get_category(service_level1_id)
        assert service_level1['cat_type'] == 'service'
        assert service_level1['parent_id'] is None
        
        # Get service categories
        service_categories = test_db.get_categories(cat_type='service')
        assert len(service_categories) > 0
        
        # Verify the hierarchy is maintained for services
        level2_services = test_db.get_categories(parent_id=service_level1_id, cat_type='service')
        assert len(level2_services) > 0
        assert level2_services[0]['id'] == service_level2_id
        
        level3_services = test_db.get_categories(parent_id=service_level2_id, cat_type='service')
        assert len(level3_services) > 0
        assert level3_services[0]['id'] == service_level3_id
        
        level4_services = test_db.get_categories(parent_id=service_level3_id, cat_type='service')
        assert len(level4_services) > 0
        assert level4_services[0]['id'] == service_level4_id
        
        # Level 4 should be a leaf node
        level5_services = test_db.get_categories(parent_id=service_level4_id, cat_type='service')
        assert len(level5_services) == 0

    def test_search_functionality(self, test_db):
        """Test search functionality to ensure it properly filters by category hierarchy"""
        # Create a test category hierarchy
        parent_cat_id = test_db.add_category(name="دسته‌بندی جستجو", cat_type='product')
        child_cat_id = test_db.add_category(name="زیردسته جستجو", parent_id=parent_cat_id, cat_type='product')
        
        # Add products to test with
        product1_id = test_db.add_product(
            name="محصول تست جستجو ۱",
            price=1000000,
            description="محصول برای تست جستجو",
            category_id=parent_cat_id,
            tags="تست,جستجو"
        )
        
        product2_id = test_db.add_product(
            name="محصول تست جستجو ۲",
            price=2000000,
            description="محصول دیگر برای تست جستجو",
            category_id=child_cat_id,
            tags="تست,جستجو,ویژه"
        )
        
        # Search for products with "جستجو" in their name or description
        search_results = test_db.search_products(query="جستجو")
        assert len(search_results) == 2
        
        # Filter by category
        category_results = test_db.search_products(category_id=child_cat_id)
        assert len(category_results) == 1
        assert category_results[0]['id'] == product2_id
        
        # Filter by price range
        price_results = test_db.search_products(min_price=1500000)
        assert len(price_results) == 1
        assert price_results[0]['id'] == product2_id
        
        # Filter by tags
        tag_results = test_db.search_products(tags="ویژه")
        assert len(tag_results) == 1
        assert tag_results[0]['id'] == product2_id

    def test_update_category(self, test_db):
        """Test updating category information"""
        # Create a test category
        category_id = test_db.add_category(name="دسته‌بندی قبل از بروزرسانی", cat_type='product')
        
        # Update the category
        new_name = "دسته‌بندی بعد از بروزرسانی"
        success = test_db.update_category(category_id, name=new_name)
        
        # Verify the update was successful
        assert success, "Category update failed"
        
        # Verify the changes were saved
        updated_category = test_db.get_category(category_id)
        assert updated_category['name'] == new_name

    def test_delete_category_cascade(self, test_db):
        """Test deleting a category cascades to its subcategories and products"""
        # Create a category hierarchy
        parent_id = test_db.add_category(name="دسته‌بندی حذف", cat_type='product')
        child_id = test_db.add_category(name="زیردسته حذف", parent_id=parent_id, cat_type='product')
        
        # Add a product to the child category
        product_id = test_db.add_product(
            name="محصول تست حذف",
            price=1000000,
            description="محصول برای تست حذف",
            category_id=child_id
        )
        
        # Verify everything was created
        assert test_db.get_category(parent_id) is not None
        assert test_db.get_category(child_id) is not None
        assert test_db.get_product(product_id) is not None
        
        # Delete the parent category
        success = test_db.delete_category(parent_id)
        assert success, "Category deletion failed"
        
        # Verify the parent category was deleted
        assert test_db.get_category(parent_id) is None
        
        # Verify the child category was also deleted (cascade)
        assert test_db.get_category(child_id) is None
        
        # Verify the product was also deleted (cascade)
        assert test_db.get_product(product_id) is None