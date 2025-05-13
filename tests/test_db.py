"""
Tests for the database module
"""

import pytest
from database import Database


class TestDatabase:
    """Test cases for database operations"""

    def test_db_connection(self):
        """Test database connection"""
        db = Database()
        assert db is not None
        # بررسی اتصال به دیتابیس
        assert db.conn is not None

    def test_category_operations(self, test_db):
        """Test category CRUD operations"""
        # Create a category
        category_name = "Test Category"
        category_id = test_db.add_category(category_name, cat_type="product")
        assert category_id > 0

        # Get the category
        category = test_db.get_category(category_id)
        assert category is not None
        assert category["name"] == category_name
        assert category["cat_type"] == "product"

        # Update the category
        new_name = "Updated Test Category"
        success = test_db.update_category(category_id, new_name)
        assert success is True

        # Verify the update
        updated_category = test_db.get_category(category_id)
        assert updated_category["name"] == new_name

        # Delete the category
        success = test_db.delete_category(category_id)
        assert success is True

        # Verify the deletion
        deleted_category = test_db.get_category(category_id)
        assert deleted_category is None

    def test_product_operations(self, test_db):
        """Test product CRUD operations"""
        # Create a category first
        category_id = test_db.add_category("Test Product Category", cat_type="product")

        # Create a product
        product_name = "Test Product"
        product_price = 1000000
        product_description = "Test product description"
        product_id = test_db.add_product(
            name=product_name,
            price=product_price,
            description=product_description,
            category_id=category_id,
            brand="Test Brand",
            model="Test Model"
        )
        assert product_id > 0

        # Get the product
        product = test_db.get_product(product_id)
        assert product is not None
        assert product["name"] == product_name
        assert product["price"] == product_price
        assert product["description"] == product_description
        assert product["category_id"] == category_id

        # Update the product
        new_name = "Updated Test Product"
        new_price = 1500000
        success = test_db.update_product(
            product_id=product_id,
            name=new_name,
            price=new_price
        )
        assert success is True

        # Verify the update
        updated_product = test_db.get_product(product_id)
        assert updated_product["name"] == new_name
        assert updated_product["price"] == new_price

        # Delete the product
        success = test_db.delete_product(product_id)
        assert success is True

        # Verify the deletion
        deleted_product = test_db.get_product(product_id)
        assert deleted_product is None

        # Clean up the category
        test_db.delete_category(category_id)

    def test_service_operations(self, test_db):
        """Test service CRUD operations"""
        # Create a category first
        category_id = test_db.add_category("Test Service Category", cat_type="service")

        # Create a service
        service_name = "Test Service"
        service_price = 2000000
        service_description = "Test service description"
        service_id = test_db.add_service(
            name=service_name,
            price=service_price,
            description=service_description,
            category_id=category_id,
            tags="test, service"
        )
        assert service_id > 0

        # Get the service
        service = test_db.get_service(service_id)
        assert service is not None
        assert service["name"] == service_name
        assert service["price"] == service_price
        assert service["description"] == service_description
        assert service["category_id"] == category_id

        # Delete the service
        success = test_db.delete_service(service_id)
        assert success is True

        # Verify the deletion
        deleted_service = test_db.get_service(service_id)
        assert deleted_service is None

        # Clean up the category
        test_db.delete_category(category_id)

    def test_media_operations(self, test_db):
        """Test media operations for products and services"""
        # Create a category first
        category_id = test_db.add_category("Test Media Category", cat_type="product")

        # Create a product
        product_id = test_db.add_product(
            name="Test Media Product",
            price=1000000,
            description="Test product for media",
            category_id=category_id
        )

        # Add media to the product
        file_id = "test_file_id"
        file_type = "photo"
        media_id = test_db.add_product_media(product_id, file_id, file_type)
        assert media_id > 0

        # Get product media
        media_list = test_db.get_product_media(product_id)
        assert len(media_list) > 0
        assert media_list[0]["file_id"] == file_id
        assert media_list[0]["file_type"] == file_type

        # Get specific media by ID
        media = test_db.get_media_by_id(media_id)
        assert media is not None
        assert media["file_id"] == file_id
        assert media["file_type"] == file_type

        # Delete the media
        success = test_db.delete_product_media(media_id)
        assert success is True

        # Verify the deletion
        media_list_after = test_db.get_product_media(product_id)
        assert len(media_list_after) == 0

        # Clean up
        test_db.delete_product(product_id)
        test_db.delete_category(category_id)

    def test_inquiry_operations(self, test_db):
        """Test inquiry operations"""
        # Create a category first
        category_id = test_db.add_category("Test Inquiry Category", cat_type="product")

        # Create a product
        product_id = test_db.add_product(
            name="Test Inquiry Product",
            price=1000000,
            description="Test product for inquiry",
            category_id=category_id
        )

        # Create an inquiry
        user_id = 123456789
        name = "Test Customer"
        phone = "09123456789"
        description = "Test inquiry description"
        inquiry_id = test_db.add_inquiry(
            user_id=user_id,
            name=name,
            phone=phone,
            description=description,
            product_id=product_id
        )
        assert inquiry_id > 0

        # Get the inquiry
        inquiry = test_db.get_inquiry(inquiry_id)
        assert inquiry is not None
        assert inquiry["user_id"] == user_id
        assert inquiry["name"] == name
        assert inquiry["phone"] == phone
        assert inquiry["description"] == description
        assert inquiry["product_id"] == product_id

        # Get all inquiries
        inquiries = test_db.get_inquiries()
        assert len(inquiries) > 0

        # Delete the inquiry
        success = test_db.delete_inquiry(inquiry_id)
        assert success is True

        # Verify the deletion
        deleted_inquiry = test_db.get_inquiry(inquiry_id)
        assert deleted_inquiry is None

        # Clean up
        test_db.delete_product(product_id)
        test_db.delete_category(category_id)

    def test_educational_content_operations(self, test_db):
        """Test educational content operations"""
        # Create educational content
        title = "Test Educational Content"
        content = "This is test educational content."
        category = "Test Category"
        content_type = "article"
        content_id = test_db.add_educational_content(
            title=title,
            content=content,
            category=category,
            content_type=content_type
        )
        assert content_id > 0

        # Get the educational content
        edu_content = test_db.get_educational_content(content_id)
        assert edu_content is not None
        assert edu_content["title"] == title
        assert edu_content["content"] == content
        assert edu_content["category"] == category
        assert edu_content["content_type"] == content_type

        # Get all educational content
        all_content = test_db.get_all_educational_content()
        assert len(all_content) > 0

        # Get educational content by category
        category_content = test_db.get_all_educational_content(category=category)
        assert len(category_content) > 0

        # Update the educational content
        new_title = "Updated Test Educational Content"
        success = test_db.update_educational_content(
            content_id=content_id,
            title=new_title
        )
        assert success is True

        # Verify the update
        updated_content = test_db.get_educational_content(content_id)
        assert updated_content["title"] == new_title

        # Delete the educational content
        success = test_db.delete_educational_content(content_id)
        assert success is True

        # Verify the deletion
        deleted_content = test_db.get_educational_content(content_id)
        assert deleted_content is None

    def test_static_content_operations(self, test_db):
        """Test static content operations"""
        # Update about content
        about_content = "This is test about content."
        success = test_db.update_static_content("about", about_content)
        assert success is True

        # Get about content
        retrieved_about = test_db.get_static_content("about")
        assert retrieved_about == about_content

        # Update contact content
        contact_content = "This is test contact content."
        success = test_db.update_static_content("contact", contact_content)
        assert success is True

        # Get contact content
        retrieved_contact = test_db.get_static_content("contact")
        assert retrieved_contact == contact_content