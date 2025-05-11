import pytest
import asyncio
from unittest.mock import MagicMock
import logging
from database import Database

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestDatabase:
    """Test cases for database functionality"""
    
    def test_db_connection(self, test_db):
        """Test database connection"""
        assert test_db is not None, "Database connection failed"
    
    def test_category_operations(self, test_db):
        """Test CRUD operations for categories"""
        # Create a test category
        category_name = "Test Category"
        parent_id = None
        cat_type = "product"
        
        # Test add category
        category_id = test_db.add_category(category_name, parent_id, cat_type)
        assert category_id > 0, "Failed to add category"
        
        # Test get category
        category = test_db.get_category(category_id)
        assert category is not None, "Failed to get category"
        assert category["name"] == category_name, "Category name doesn't match"
        assert category["type"] == cat_type, "Category type doesn't match"
        
        # Test update category
        new_name = "Updated Test Category"
        updated = test_db.update_category(category_id, new_name, parent_id, cat_type)
        assert updated, "Failed to update category"
        
        # Verify the update
        updated_category = test_db.get_category(category_id)
        assert updated_category["name"] == new_name, "Category name wasn't updated"
        
        # Test add subcategory
        subcategory_name = "Test Subcategory"
        subcategory_id = test_db.add_category(subcategory_name, category_id, cat_type)
        assert subcategory_id > 0, "Failed to add subcategory"
        
        # Test get categories
        categories = test_db.get_categories(parent_id=category_id)
        assert len(categories) >= 1, "Failed to get subcategories"
        assert any(cat["name"] == subcategory_name for cat in categories), "Subcategory not found"
        
        # Test delete subcategory
        deleted = test_db.delete_category(subcategory_id)
        assert deleted, "Failed to delete subcategory"
        
        # Verify the subcategory was deleted
        subcategories = test_db.get_categories(parent_id=category_id)
        assert not any(cat["id"] == subcategory_id for cat in subcategories), "Subcategory wasn't deleted"
        
        # Test delete category
        deleted = test_db.delete_category(category_id)
        assert deleted, "Failed to delete category"
        
        # Verify the category was deleted
        category = test_db.get_category(category_id)
        assert category is None, "Category wasn't deleted"
    
    def test_product_operations(self, test_db):
        """Test CRUD operations for products"""
        # Create a test category for products
        category_name = "Test Product Category"
        category_id = test_db.add_category(category_name, parent_id=None, cat_type="product")
        
        # Test add product
        product_name = "Test Product"
        product_price = 1000000
        product_description = "This is a test product"
        
        product_id = test_db.add_product(
            name=product_name,
            price=product_price,
            description=product_description,
            category_id=category_id,
            photo_url=None,
            brand="Test Brand",
            model="Test Model",
            in_stock=True,
            tags="test,product",
            featured=False
        )
        assert product_id > 0, "Failed to add product"
        
        # Test get product
        product = test_db.get_product(product_id)
        assert product is not None, "Failed to get product"
        assert product["name"] == product_name, "Product name doesn't match"
        assert product["price"] == product_price, "Product price doesn't match"
        assert product["description"] == product_description, "Product description doesn't match"
        
        # Test update product
        new_price = 1500000
        updated = test_db.update_product(product_id, price=new_price)
        assert updated, "Failed to update product"
        
        # Verify the update
        updated_product = test_db.get_product(product_id)
        assert updated_product["price"] == new_price, "Product price wasn't updated"
        
        # Test add product media
        file_id = "test_file_id"
        file_type = "photo"
        media_id = test_db.add_product_media(product_id, file_id, file_type)
        assert media_id > 0, "Failed to add product media"
        
        # Test get product media
        media = test_db.get_product_media(product_id)
        assert len(media) > 0, "Failed to get product media"
        assert media[0]["file_id"] == file_id, "Media file_id doesn't match"
        
        # Test get media by id
        media_item = test_db.get_media_by_id(media_id)
        assert media_item is not None, "Failed to get media by id"
        assert media_item["file_id"] == file_id, "Media file_id doesn't match"
        
        # Test get product by media id
        product_by_media = test_db.get_product_by_media_id(media_id)
        assert product_by_media is not None, "Failed to get product by media id"
        assert product_by_media["id"] == product_id, "Product id doesn't match"
        
        # Test delete product media
        deleted = test_db.delete_product_media(media_id)
        assert deleted, "Failed to delete product media"
        
        # Verify the media was deleted
        media = test_db.get_product_media(product_id)
        assert not any(m["id"] == media_id for m in media), "Media wasn't deleted"
        
        # Test get products by category
        products = test_db.get_products_by_category(category_id)
        assert len(products) > 0, "Failed to get products by category"
        assert any(p["id"] == product_id for p in products), "Product not found in category"
        
        # Test search products
        search_results = test_db.search_products(query="Test", cat_type="product")
        assert len(search_results) > 0, "Failed to search products"
        assert any(p["id"] == product_id for p in search_results), "Product not found in search results"
        
        # Test filter products
        filter_results = test_db.search_products(brand="Test Brand")
        assert len(filter_results) > 0, "Failed to filter products"
        assert any(p["id"] == product_id for p in filter_results), "Product not found in filter results"
        
        # Test delete product
        deleted = test_db.delete_product(product_id)
        assert deleted, "Failed to delete product"
        
        # Verify the product was deleted
        product = test_db.get_product(product_id)
        assert product is None, "Product wasn't deleted"
        
        # Clean up
        test_db.delete_category(category_id)
    
    def test_service_operations(self, test_db):
        """Test CRUD operations for services"""
        # Create a test category for services
        category_name = "Test Service Category"
        category_id = test_db.add_category(category_name, parent_id=None, cat_type="service")
        
        # Test add service
        service_name = "Test Service"
        service_price = 500000
        service_description = "This is a test service"
        
        service_id = test_db.add_service(
            name=service_name,
            price=service_price,
            description=service_description,
            category_id=category_id,
            photo_url=None,
            featured=True,
            tags="test,service"
        )
        assert service_id > 0, "Failed to add service"
        
        # Test get service
        service = test_db.get_service(service_id)
        assert service is not None, "Failed to get service"
        assert service["name"] == service_name, "Service name doesn't match"
        assert service["price"] == service_price, "Service price doesn't match"
        
        # Test delete service
        deleted = test_db.delete_service(service_id)
        assert deleted, "Failed to delete service"
        
        # Verify the service was deleted
        service = test_db.get_service(service_id)
        assert service is None, "Service wasn't deleted"
        
        # Clean up
        test_db.delete_category(category_id)
    
    def test_inquiry_operations(self, test_db):
        """Test CRUD operations for inquiries"""
        # Create test category and product for inquiry
        category_id = test_db.add_category("Test Inquiry Category", cat_type="product")
        product_id = test_db.add_product(
            name="Test Inquiry Product",
            price=1000000,
            description="Product for inquiry test",
            category_id=category_id
        )
        
        # Test add inquiry
        user_id = 123456789
        name = "Test User"
        phone = "09123456789"
        description = "This is a test inquiry"
        
        inquiry_id = test_db.add_inquiry(
            user_id=user_id,
            name=name,
            phone=phone,
            description=description,
            product_id=product_id
        )
        assert inquiry_id > 0, "Failed to add inquiry"
        
        # Test get inquiry
        inquiry = test_db.get_inquiry(inquiry_id)
        assert inquiry is not None, "Failed to get inquiry"
        assert inquiry["name"] == name, "Inquiry name doesn't match"
        assert inquiry["phone"] == phone, "Inquiry phone doesn't match"
        
        # Test get inquiries
        inquiries = test_db.get_inquiries(product_id=product_id)
        assert len(inquiries) > 0, "Failed to get inquiries"
        assert any(i["id"] == inquiry_id for i in inquiries), "Inquiry not found"
        
        # Test delete inquiry
        deleted = test_db.delete_inquiry(inquiry_id)
        assert deleted, "Failed to delete inquiry"
        
        # Verify the inquiry was deleted
        inquiry = test_db.get_inquiry(inquiry_id)
        assert inquiry is None, "Inquiry wasn't deleted"
        
        # Clean up
        test_db.delete_product(product_id)
        test_db.delete_category(category_id)
    
    def test_educational_content_operations(self, test_db):
        """Test CRUD operations for educational content"""
        # Test add educational content
        title = "Test Educational Content"
        content = "This is a test educational content"
        category = "Test Category"
        content_type = "article"
        
        content_id = test_db.add_educational_content(
            title=title,
            content=content,
            category=category,
            content_type=content_type
        )
        assert content_id > 0, "Failed to add educational content"
        
        # Test get educational content
        edu_content = test_db.get_educational_content(content_id)
        assert edu_content is not None, "Failed to get educational content"
        assert edu_content["title"] == title, "Educational content title doesn't match"
        assert edu_content["content"] == content, "Educational content doesn't match"
        
        # Test get all educational content
        all_content = test_db.get_all_educational_content()
        assert len(all_content) > 0, "Failed to get all educational content"
        assert any(c["id"] == content_id for c in all_content), "Educational content not found"
        
        # Test get educational content by category
        category_content = test_db.get_all_educational_content(category=category)
        assert len(category_content) > 0, "Failed to get educational content by category"
        assert any(c["id"] == content_id for c in category_content), "Educational content not found in category"
        
        # Test get educational categories
        categories = test_db.get_educational_categories()
        assert len(categories) > 0, "Failed to get educational categories"
        assert category in categories, "Category not found"
        
        # Test update educational content
        new_title = "Updated Test Educational Content"
        updated = test_db.update_educational_content(content_id, title=new_title)
        assert updated, "Failed to update educational content"
        
        # Verify the update
        updated_content = test_db.get_educational_content(content_id)
        assert updated_content["title"] == new_title, "Educational content title wasn't updated"
        
        # Test delete educational content
        deleted = test_db.delete_educational_content(content_id)
        assert deleted, "Failed to delete educational content"
        
        # Verify the educational content was deleted
        edu_content = test_db.get_educational_content(content_id)
        assert edu_content is None, "Educational content wasn't deleted"
    
    def test_static_content_operations(self, test_db):
        """Test CRUD operations for static content"""
        # Test update static content
        content_type = "test_static"
        content = "This is a test static content"
        
        updated = test_db.update_static_content(content_type, content)
        assert updated, "Failed to update static content"
        
        # Test get static content
        static_content = test_db.get_static_content(content_type)
        assert static_content == content, "Static content doesn't match"