import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import logging
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import handlers
from bot import bot, dp, set_commands, register_handlers
from database import Database

# Configure logging
logging.basicConfig(level=logging.INFO)

# Test command handlers
@pytest.mark.asyncio
async def test_start_command(mock_bot, test_message, test_db):
    """Test the /start command handler"""
    # Register the handlers
    await register_handlers()
    
    # Find the start handler and call it directly
    for handler in dp.message.handlers:
        if isinstance(handler.filter, Command) and "start" in handler.filter.commands:
            await handler.callback(test_message)
            break
    
    # Check that the welcome message was sent
    test_message.answer.assert_called_once()
    
    # Verify the welcome message contains expected content
    args, kwargs = test_message.answer.call_args
    assert "به ربات فروشگاه" in args[0]
    assert "keyboard" in kwargs or "reply_markup" in kwargs

@pytest.mark.asyncio
async def test_help_command(mock_bot, test_message, test_db):
    """Test the /help command handler"""
    # Change the command in the test message
    test_message.text = "/help"
    
    # Register the handlers
    await register_handlers()
    
    # Find the help handler and call it directly
    for handler in dp.message.handlers:
        if isinstance(handler.filter, Command) and "help" in handler.filter.commands:
            await handler.callback(test_message)
            break
    
    # Check that the help message was sent
    test_message.answer.assert_called_once()
    
    # Verify the help message contains expected commands
    args, kwargs = test_message.answer.call_args
    assert "/start" in args[0]
    assert "/products" in args[0]
    assert "/services" in args[0]
    assert "/contact" in args[0]
    assert "/about" in args[0]

@pytest.mark.asyncio
async def test_products_command(mock_bot, test_message, test_db):
    """Test the /products command handler"""
    # Change the command in the test message
    test_message.text = "/products"
    
    # Register the handlers
    await register_handlers()
    
    # Find the products handler and call it directly
    for handler in dp.message.handlers:
        if isinstance(handler.filter, Command) and "products" in handler.filter.commands:
            with patch('handlers.show_categories') as mock_show_categories:
                await handler.callback(test_message)
                # Check that show_categories was called with correct parameters
                mock_show_categories.assert_called_once()
                args, kwargs = mock_show_categories.call_args
                assert args[0] == test_message
                assert args[1] == 'product'

@pytest.mark.asyncio
async def test_services_command(mock_bot, test_message, test_db):
    """Test the /services command handler"""
    # Change the command in the test message
    test_message.text = "/services"
    
    # Register the handlers
    await register_handlers()
    
    # Find the services handler and call it directly
    for handler in dp.message.handlers:
        if isinstance(handler.filter, Command) and "services" in handler.filter.commands:
            with patch('handlers.show_categories') as mock_show_categories:
                await handler.callback(test_message)
                # Check that show_categories was called with correct parameters
                mock_show_categories.assert_called_once()
                args, kwargs = mock_show_categories.call_args
                assert args[0] == test_message
                assert args[1] == 'service'

@pytest.mark.asyncio
async def test_contact_command(mock_bot, test_message, test_db):
    """Test the /contact command handler"""
    # Change the command in the test message
    test_message.text = "/contact"
    
    # Register the handlers
    await register_handlers()
    
    # Mock the database.get_static_content method
    with patch.object(Database, 'get_static_content', return_value="اطلاعات تماس با ما") as mock_get_content:
        # Find the contact handler and call it directly
        for handler in dp.message.handlers:
            if isinstance(handler.filter, Command) and "contact" in handler.filter.commands:
                await handler.callback(test_message)
                break
        
        # Check that the database method was called
        mock_get_content.assert_called_once_with('contact')
        
        # Check that the contact message was sent
        test_message.answer.assert_called_once()
        
        # Verify the contact message contains expected content
        args, kwargs = test_message.answer.call_args
        assert "اطلاعات تماس با ما" in args[0]

@pytest.mark.asyncio
async def test_about_command(mock_bot, test_message, test_db):
    """Test the /about command handler"""
    # Change the command in the test message
    test_message.text = "/about"
    
    # Register the handlers
    await register_handlers()
    
    # Mock the database.get_static_content method
    with patch.object(Database, 'get_static_content', return_value="درباره فروشگاه ما") as mock_get_content:
        # Find the about handler and call it directly
        for handler in dp.message.handlers:
            if isinstance(handler.filter, Command) and "about" in handler.filter.commands:
                await handler.callback(test_message)
                break
        
        # Check that the database method was called
        mock_get_content.assert_called_once_with('about')
        
        # Check that the about message was sent
        test_message.answer.assert_called_once()
        
        # Verify the about message contains expected content
        args, kwargs = test_message.answer.call_args
        assert "درباره فروشگاه ما" in args[0]

# Test callback query handlers
@pytest.mark.asyncio
async def test_category_callback(mock_bot, test_callback_query, test_db):
    """Test the category callback handler"""
    # Set the callback data to a category
    test_callback_query.data = "category_1"
    
    # Register the handlers
    await register_handlers()
    
    # Find the category callback handler and call it directly
    for handler in dp.callback_query.handlers:
        if hasattr(handler.filter, "text") and handler.filter.text.startswith("category_"):
            with patch('handlers.show_category') as mock_show_category:
                await handler.callback(test_callback_query)
                # Check that show_category was called with correct parameters
                mock_show_category.assert_called_once()
                args, kwargs = mock_show_category.call_args
                assert args[0] == test_callback_query
                assert args[1] == 1  # Category ID

@pytest.mark.asyncio
async def test_product_callback(mock_bot, test_callback_query, test_db):
    """Test the product callback handler"""
    # Set the callback data to a product
    test_callback_query.data = "product_1"
    
    # Register the handlers
    await register_handlers()
    
    # Find the product callback handler and call it directly
    for handler in dp.callback_query.handlers:
        if hasattr(handler.filter, "text") and handler.filter.text.startswith("product_"):
            with patch('handlers.show_product') as mock_show_product:
                await handler.callback(test_callback_query)
                # Check that show_product was called with correct parameters
                mock_show_product.assert_called_once()
                args, kwargs = mock_show_product.call_args
                assert args[0] == test_callback_query
                assert args[1] == 1  # Product ID

@pytest.mark.asyncio
async def test_service_callback(mock_bot, test_callback_query, test_db):
    """Test the service callback handler"""
    # Set the callback data to a service
    test_callback_query.data = "service_1"
    
    # Register the handlers
    await register_handlers()
    
    # Find the service callback handler and call it directly
    for handler in dp.callback_query.handlers:
        if hasattr(handler.filter, "text") and handler.filter.text.startswith("service_"):
            with patch('handlers.show_service') as mock_show_service:
                await handler.callback(test_callback_query)
                # Check that show_service was called with correct parameters
                mock_show_service.assert_called_once()
                args, kwargs = mock_show_service.call_args
                assert args[0] == test_callback_query
                assert args[1] == 1  # Service ID

@pytest.mark.asyncio
async def test_back_callback(mock_bot, test_callback_query, test_db):
    """Test the back callback handler"""
    # Set the callback data to a back action
    test_callback_query.data = "back_1"
    
    # Register the handlers
    await register_handlers()
    
    # Find the back callback handler and call it directly
    for handler in dp.callback_query.handlers:
        if hasattr(handler.filter, "text") and handler.filter.text.startswith("back_"):
            with patch('handlers.handle_back') as mock_handle_back:
                await handler.callback(test_callback_query)
                # Check that handle_back was called with correct parameters
                mock_handle_back.assert_called_once()
                args, kwargs = mock_handle_back.call_args
                assert args[0] == test_callback_query
                assert args[1] == 1  # Back to category/location ID

@pytest.mark.asyncio
async def test_inquiry_callback(mock_bot, test_callback_query, test_db):
    """Test the inquiry callback handler"""
    # Set the callback data to an inquiry action
    test_callback_query.data = "inquiry_1"
    
    # Register the handlers
    await register_handlers()
    
    # Find the inquiry callback handler and call it directly
    for handler in dp.callback_query.handlers:
        if hasattr(handler.filter, "text") and handler.filter.text.startswith("inquiry_"):
            with patch('handlers.start_inquiry') as mock_start_inquiry:
                await handler.callback(test_callback_query)
                # Check that start_inquiry was called with correct parameters
                mock_start_inquiry.assert_called_once()
                args, kwargs = mock_start_inquiry.call_args
                assert args[0] == test_callback_query
                assert args[1] == 1  # Product/Service ID

# Test complex flows
@pytest.mark.asyncio
async def test_flow_product_browsing(mock_bot, test_message, test_callback_query, test_db):
    """Test the full flow of browsing products"""
    # Register handlers
    await register_handlers()
    
    # 1. Start with products command
    test_message.text = "/products"
    await asyncio.gather(*[
        handler.callback(test_message) 
        for handler in dp.message.handlers 
        if isinstance(handler.filter, Command) and "products" in handler.filter.commands
    ])
    
    # 2. Simulate selecting a category
    test_callback_query.data = "category_1"
    await asyncio.gather(*[
        handler.callback(test_callback_query)
        for handler in dp.callback_query.handlers
        if hasattr(handler.filter, "text") and handler.filter.text.startswith("category_")
    ])
    
    # 3. Simulate selecting a product
    test_callback_query.data = "product_1"
    await asyncio.gather(*[
        handler.callback(test_callback_query)
        for handler in dp.callback_query.handlers
        if hasattr(handler.filter, "text") and handler.filter.text.startswith("product_")
    ])
    
    # 4. Simulate going back to categories
    test_callback_query.data = "back_1"
    await asyncio.gather(*[
        handler.callback(test_callback_query)
        for handler in dp.callback_query.handlers
        if hasattr(handler.filter, "text") and handler.filter.text.startswith("back_")
    ])
    
    # Each step should make a call to test_message.answer or test_callback_query.message.edit_text
    assert test_message.answer.call_count > 0
    assert test_callback_query.message.edit_text.call_count > 0

if __name__ == "__main__":
    pytest.main()