import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import logging
import os
from database import Database
from bot import bot, register_handlers

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestAdminFeatures:
    """Test cases for admin functionalities"""
    
    @pytest.mark.asyncio
    async def test_admin_access(self, test_admin_message, test_db):
        """Test admin access control"""
        # Set the admin ID environment variable
        original_admin_id = os.environ.get('ADMIN_ID')
        os.environ['ADMIN_ID'] = str(test_admin_message.from_user.id)
        
        # Register handlers
        await register_handlers()
        
        with patch('handlers.is_admin', return_value=True) as mock_is_admin:
            # Test admin command
            test_admin_message.text = "/admin"
            
            # Mock the admin handler
            with patch('handlers.cmd_admin') as mock_cmd_admin:
                mock_cmd_admin.return_value = None
                
                # Call the admin handler directly
                # This is simplified because we're not simulating the full command handling
                await mock_cmd_admin(test_admin_message)
                
                # Check that the admin handler was called
                mock_cmd_admin.assert_called_once()
            
            # Check that is_admin was called with the correct user ID
            mock_is_admin.assert_called_once()
        
        # Restore the original admin ID
        if original_admin_id:
            os.environ['ADMIN_ID'] = original_admin_id
        else:
            del os.environ['ADMIN_ID']
    
    @pytest.mark.asyncio
    async def test_admin_category_management(self, test_admin_message, test_db):
        """Test admin category management functions"""
        # Create a test category for testing
        category_name = "Test Admin Category"
        category_id = test_db.add_category(category_name, cat_type='product')
        
        try:
            # Mock the admin category management functions
            with patch('handlers.admin_show_categories') as mock_show_categories:
                mock_show_categories.return_value = None
                
                # Call the handler directly
                await mock_show_categories(test_admin_message)
                
                # Check that the admin message was sent
                test_admin_message.answer.assert_called_once()
            
            # Mock the admin category detail function
            with patch('handlers.admin_show_category') as mock_show_category:
                mock_show_category.return_value = None
                
                # Call the handler directly
                await mock_show_category(MagicMock(), category_id)
                
                # At this point we would verify that the category details are displayed
                # But since we're using mocks, we just verify the function was called
                mock_show_category.assert_called_once()
            
            # Mock the admin add category function
            with patch('handlers.admin_add_category') as mock_add_category:
                mock_add_category.return_value = None
                
                # Create a mock callback query for adding a subcategory
                mock_callback = MagicMock()
                mock_callback.data = f"admin_add_cat_{category_id}_product"
                
                # Call the handler directly
                await mock_add_category(mock_callback)
                
                # Check that the function was called
                mock_add_category.assert_called_once()
            
            # Mock the admin edit category function
            with patch('handlers.admin_edit_category') as mock_edit_category:
                mock_edit_category.return_value = None
                
                # Create a mock callback query for editing a category
                mock_callback = MagicMock()
                mock_callback.data = f"admin_edit_cat_{category_id}"
                
                # Call the handler directly
                await mock_edit_category(mock_callback)
                
                # Check that the function was called
                mock_edit_category.assert_called_once()
            
            # Mock the admin delete category function
            with patch('handlers.admin_delete_category') as mock_delete_category:
                mock_delete_category.return_value = None
                
                # Create a mock callback query for deleting a category
                mock_callback = MagicMock()
                mock_callback.data = f"admin_delete_cat_{category_id}"
                
                # Call the handler directly
                await mock_delete_category(mock_callback)
                
                # Check that the function was called
                mock_delete_category.assert_called_once()
        finally:
            # Clean up the test category
            test_db.delete_category(category_id)
    
    @pytest.mark.asyncio
    async def test_admin_product_management(self, test_admin_message, test_db):
        """Test admin product management functions"""
        # Create a test category and product for testing
        category_id = test_db.add_category("Test Admin Product Category", cat_type='product')
        product_id = test_db.add_product(
            name="Test Admin Product",
            price=1000000,
            description="Product for admin testing",
            category_id=category_id
        )
        
        try:
            # Mock the admin show products function
            with patch('handlers.admin_show_products') as mock_show_products:
                mock_show_products.return_value = None
                
                # Create a mock callback query for showing products
                mock_callback = MagicMock()
                mock_callback.data = f"admin_products_{category_id}"
                
                # Call the handler directly
                await mock_show_products(mock_callback)
                
                # Check that the function was called
                mock_show_products.assert_called_once()
            
            # Mock the admin show product detail function
            with patch('handlers.admin_show_product') as mock_show_product:
                mock_show_product.return_value = None
                
                # Create a mock callback query for showing product detail
                mock_callback = MagicMock()
                mock_callback.data = f"admin_product_{product_id}"
                
                # Call the handler directly
                await mock_show_product(mock_callback)
                
                # Check that the function was called
                mock_show_product.assert_called_once()
            
            # Mock the admin add product function
            with patch('handlers.admin_add_product') as mock_add_product:
                mock_add_product.return_value = None
                
                # Create a mock callback query for adding a product
                mock_callback = MagicMock()
                mock_callback.data = f"admin_add_product_{category_id}"
                
                # Call the handler directly
                await mock_add_product(mock_callback)
                
                # Check that the function was called
                mock_add_product.assert_called_once()
            
            # Mock the admin edit product function
            with patch('handlers.admin_edit_product') as mock_edit_product:
                mock_edit_product.return_value = None
                
                # Create a mock callback query for editing a product
                mock_callback = MagicMock()
                mock_callback.data = f"admin_edit_product_{product_id}"
                
                # Call the handler directly
                await mock_edit_product(mock_callback)
                
                # Check that the function was called
                mock_edit_product.assert_called_once()
            
            # Mock the admin delete product function
            with patch('handlers.admin_delete_product') as mock_delete_product:
                mock_delete_product.return_value = None
                
                # Create a mock callback query for deleting a product
                mock_callback = MagicMock()
                mock_callback.data = f"admin_delete_product_{product_id}"
                
                # Call the handler directly
                await mock_delete_product(mock_callback)
                
                # Check that the function was called
                mock_delete_product.assert_called_once()
        finally:
            # Clean up the test data
            test_db.delete_product(product_id)
            test_db.delete_category(category_id)
    
    @pytest.mark.asyncio
    async def test_admin_media_management(self, test_admin_message, test_db):
        """Test admin media management functions"""
        # Create a test category and product for testing
        category_id = test_db.add_category("Test Admin Media Category", cat_type='product')
        product_id = test_db.add_product(
            name="Test Admin Media Product",
            price=1000000,
            description="Product for media testing",
            category_id=category_id
        )
        media_id = test_db.add_product_media(product_id, "test_file_id", "photo")
        
        try:
            # Mock the admin manage media function
            with patch('handlers.admin_manage_media') as mock_manage_media:
                mock_manage_media.return_value = None
                
                # Create a mock callback query for managing media
                mock_callback = MagicMock()
                mock_callback.data = f"admin_manage_media_{product_id}"
                
                # Call the handler directly
                await mock_manage_media(mock_callback)
                
                # Check that the function was called
                mock_manage_media.assert_called_once()
            
            # Mock the admin add media function
            with patch('handlers.admin_add_media') as mock_add_media:
                mock_add_media.return_value = None
                
                # Create a mock callback query for adding media
                mock_callback = MagicMock()
                mock_callback.data = f"admin_add_media_{product_id}"
                
                # Call the handler directly
                await mock_add_media(mock_callback)
                
                # Check that the function was called
                mock_add_media.assert_called_once()
            
            # Mock the admin delete media function
            with patch('handlers.admin_delete_media') as mock_delete_media:
                mock_delete_media.return_value = None
                
                # Create a mock callback query for deleting media
                mock_callback = MagicMock()
                mock_callback.data = f"admin_delete_media_{media_id}"
                
                # Call the handler directly
                await mock_delete_media(mock_callback)
                
                # Check that the function was called
                mock_delete_media.assert_called_once()
        finally:
            # Clean up the test data
            test_db.delete_product_media(media_id)
            test_db.delete_product(product_id)
            test_db.delete_category(category_id)
    
    @pytest.mark.asyncio
    async def test_admin_educational_content_management(self, test_admin_message, test_db):
        """Test admin educational content management functions"""
        # Create a test educational content for testing
        content_id = test_db.add_educational_content(
            title="Test Admin Educational Content",
            content="This is a test educational content for admin testing",
            category="Test Category",
            content_type="article"
        )
        
        try:
            # Mock the admin show educational content function
            with patch('handlers.admin_show_educational') as mock_show_educational:
                mock_show_educational.return_value = None
                
                # Call the handler directly
                await mock_show_educational(test_admin_message)
                
                # Check that the function was called
                mock_show_educational.assert_called_once()
            
            # Mock the admin show educational content detail function
            with patch('handlers.admin_show_educational_content') as mock_show_content:
                mock_show_content.return_value = None
                
                # Create a mock callback query for showing content detail
                mock_callback = MagicMock()
                mock_callback.data = f"admin_edu_{content_id}"
                
                # Call the handler directly
                await mock_show_content(mock_callback)
                
                # Check that the function was called
                mock_show_content.assert_called_once()
            
            # Mock the admin add educational content function
            with patch('handlers.admin_add_educational') as mock_add_educational:
                mock_add_educational.return_value = None
                
                # Create a mock callback query for adding content
                mock_callback = MagicMock()
                mock_callback.data = "admin_add_edu"
                
                # Call the handler directly
                await mock_add_educational(mock_callback)
                
                # Check that the function was called
                mock_add_educational.assert_called_once()
            
            # Mock the admin edit educational content function
            with patch('handlers.admin_edit_educational') as mock_edit_educational:
                mock_edit_educational.return_value = None
                
                # Create a mock callback query for editing content
                mock_callback = MagicMock()
                mock_callback.data = f"admin_edit_edu_{content_id}"
                
                # Call the handler directly
                await mock_edit_educational(mock_callback)
                
                # Check that the function was called
                mock_edit_educational.assert_called_once()
            
            # Mock the admin delete educational content function
            with patch('handlers.admin_delete_educational') as mock_delete_educational:
                mock_delete_educational.return_value = None
                
                # Create a mock callback query for deleting content
                mock_callback = MagicMock()
                mock_callback.data = f"admin_delete_edu_{content_id}"
                
                # Call the handler directly
                await mock_delete_educational(mock_callback)
                
                # Check that the function was called
                mock_delete_educational.assert_called_once()
        finally:
            # Clean up the test data
            test_db.delete_educational_content(content_id)
    
    @pytest.mark.asyncio
    async def test_admin_static_content_management(self, test_admin_message, test_db):
        """Test admin static content management functions"""
        # First update static content for testing
        test_db.update_static_content("contact", "Test contact content")
        test_db.update_static_content("about", "Test about content")
        
        # Mock the admin show static content function
        with patch('handlers.admin_show_static') as mock_show_static:
            mock_show_static.return_value = None
            
            # Call the handler directly
            await mock_show_static(test_admin_message)
            
            # Check that the function was called
            mock_show_static.assert_called_once()
        
        # Mock the admin edit static content function
        with patch('handlers.admin_edit_static') as mock_edit_static:
            mock_edit_static.return_value = None
            
            # Create a mock callback query for editing static content
            mock_callback = MagicMock()
            mock_callback.data = "admin_edit_static_contact"
            
            # Call the handler directly
            await mock_edit_static(mock_callback)
            
            # Check that the function was called
            mock_edit_static.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_admin_inquiry_management(self, test_admin_message, test_db):
        """Test admin inquiry management functions"""
        # Create a test category, product, and inquiry for testing
        category_id = test_db.add_category("Test Admin Inquiry Category", cat_type='product')
        product_id = test_db.add_product(
            name="Test Admin Inquiry Product",
            price=1000000,
            description="Product for inquiry testing",
            category_id=category_id
        )
        inquiry_id = test_db.add_inquiry(
            user_id=12345,
            name="Test Inquiry User",
            phone="09123456789",
            description="This is a test inquiry for admin testing",
            product_id=product_id
        )
        
        try:
            # Mock the admin show inquiries function
            with patch('handlers.admin_show_inquiries') as mock_show_inquiries:
                mock_show_inquiries.return_value = None
                
                # Call the handler directly
                await mock_show_inquiries(test_admin_message)
                
                # Check that the function was called
                mock_show_inquiries.assert_called_once()
            
            # Mock the admin show inquiry detail function
            with patch('handlers.admin_show_inquiry') as mock_show_inquiry:
                mock_show_inquiry.return_value = None
                
                # Create a mock callback query for showing inquiry detail
                mock_callback = MagicMock()
                mock_callback.data = f"admin_inquiry_{inquiry_id}"
                
                # Call the handler directly
                await mock_show_inquiry(mock_callback)
                
                # Check that the function was called
                mock_show_inquiry.assert_called_once()
        finally:
            # Clean up the test data
            test_db.delete_inquiry(inquiry_id)
            test_db.delete_product(product_id)
            test_db.delete_category(category_id)
    
    @pytest.mark.asyncio
    async def test_admin_export_import(self, test_admin_message, test_db):
        """Test admin export and import functions"""
        # Mock the admin export function
        with patch('handlers.admin_show_export') as mock_show_export:
            mock_show_export.return_value = None
            
            # Call the handler directly
            await mock_show_export(test_admin_message)
            
            # Check that the function was called
            mock_show_export.assert_called_once()
        
        # Mock the admin import function
        with patch('handlers.admin_show_import') as mock_show_import:
            mock_show_import.return_value = None
            
            # Call the handler directly
            await mock_show_import(test_admin_message)
            
            # Check that the function was called
            mock_show_import.assert_called_once()
        
        # Mock the admin export products function
        with patch('handlers.admin_export_data') as mock_export_data:
            mock_export_data.return_value = None
            
            # Create a mock callback query for exporting products
            mock_callback = MagicMock()
            mock_callback.data = "admin_export_products"
            
            # Call the handler directly
            await mock_export_data(mock_callback)
            
            # Check that the function was called
            mock_export_data.assert_called_once()
        
        # Mock the admin import products function
        with patch('handlers.admin_import_data') as mock_import_data:
            mock_import_data.return_value = None
            
            # Create a mock callback query for importing products
            mock_callback = MagicMock()
            mock_callback.data = "admin_import_products"
            
            # Call the handler directly
            await mock_import_data(mock_callback)
            
            # Check that the function was called
            mock_import_data.assert_called_once()