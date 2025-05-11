import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import logging
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import handlers
from bot import bot, dp, register_handlers
from database import Database
from configuration import CATEGORY_PREFIX, PRODUCT_PREFIX, SERVICE_PREFIX, BACK_PREFIX

# Configure logging
logging.basicConfig(level=logging.INFO)

# Test category hierarchy and navigation flows
@pytest.mark.asyncio
async def test_category_tree_depth(test_db):
    """Test that the category hierarchy has maximum 4 levels of depth"""
    # Get top-level product categories
    top_categories = test_db.get_categories(parent_id=None, cat_type='product')
    assert len(top_categories) >= 1, "Should have at least one top-level product category"
    
    # Function to check max depth of category tree
    def check_max_depth(category_id, current_depth=1, max_depth=0):
        subcategories = test_db.get_categories(parent_id=category_id)
        if not subcategories:  # Leaf node
            return max(max_depth, current_depth)
        
        # If there are subcategories, recursively check their depth
        for subcat in subcategories:
            depth = check_max_depth(subcat['id'], current_depth + 1, max_depth)
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    # Check depth for each top-level category
    max_depth = 0
    for category in top_categories:
        depth = check_max_depth(category['id'])
        max_depth = max(max_depth, depth)
    
    # The expected maximum depth is 4
    assert max_depth <= 4, f"Category hierarchy should not exceed 4 levels, found {max_depth}"
    assert max_depth >= 4, f"Category hierarchy should have at least 4 levels, found only {max_depth}"

@pytest.mark.asyncio
async def test_leaf_categories_have_products(test_db):
    """Test that leaf categories (level 4) have products"""
    # Get all categories
    all_categories = []
    
    # First get top-level categories
    top_categories = test_db.get_categories(parent_id=None, cat_type='product')
    all_categories.extend(top_categories)
    
    # Then get all subcategories recursively
    def collect_subcategories(parent_id):
        subcategories = test_db.get_categories(parent_id=parent_id)
        if not subcategories:
            return []
        
        result = list(subcategories)
        for subcat in subcategories:
            result.extend(collect_subcategories(subcat['id']))
        
        return result
    
    # Collect all subcategories
    for cat in top_categories:
        all_categories.extend(collect_subcategories(cat['id']))
    
    # Find leaf categories (those that don't have subcategories)
    leaf_categories = []
    for cat in all_categories:
        subcats = test_db.get_categories(parent_id=cat['id'])
        if not subcats:
            leaf_categories.append(cat)
    
    assert len(leaf_categories) > 0, "Should have at least one leaf category"
    
    # Check that leaf categories have products
    for leaf_cat in leaf_categories:
        products = test_db.get_products_by_category(leaf_cat['id'])
        assert len(products) > 0, f"Leaf category {leaf_cat['name']} should have at least one product"

@pytest.mark.asyncio
async def test_show_categories_flow(mock_bot, test_message, test_db):
    """Test the flow of showing categories"""
    # Register handlers
    await register_handlers()
    
    # Patch the show_categories function to verify its behavior
    with patch('handlers.show_categories', side_effect=handlers.show_categories) as mock_show_categories:
        # Call the products command handler
        for handler in dp.message.handlers:
            if isinstance(handler.filter, Command) and "products" in handler.filter.commands:
                await handler.callback(test_message)
                break
        
        # Verify show_categories was called
        mock_show_categories.assert_called_once()
        args, kwargs = mock_show_categories.call_args
        assert args[0] == test_message
        assert args[1] == 'product'
        
        # Verify that the message was sent with keyboard markup
        test_message.answer.assert_called_once()
        args, kwargs = test_message.answer.call_args
        assert 'reply_markup' in kwargs

@pytest.mark.asyncio
async def test_category_navigation_flow(mock_bot, test_callback_query, test_db):
    """Test the flow of navigating through categories"""
    # Register handlers
    await register_handlers()
    
    # Mock category handler for testing
    async def mock_category_handler(callback_query, category_id):
        # Assume this is called when a category button is clicked
        category = test_db.get_category(category_id)
        subcategories = test_db.get_categories(parent_id=category_id)
        
        if subcategories:
            # Show subcategories
            subcategory_text = "\n".join([f"- {subcat['name']}" for subcat in subcategories])
            await callback_query.message.edit_text(
                f"زیردسته‌های {category['name']}:\n{subcategory_text}",
                reply_markup=MagicMock()  # Simplified for test
            )
        else:
            # Show products
            products = test_db.get_products_by_category(category_id)
            product_text = "\n".join([f"- {product['name']}" for product in products])
            await callback_query.message.edit_text(
                f"محصولات موجود در {category['name']}:\n{product_text}",
                reply_markup=MagicMock()  # Simplified for test
            )
        
        return subcategories, products
    
    # Patch the show_category function
    with patch('handlers.show_category', side_effect=mock_category_handler) as mock_show_category:
        # Set the callback data
        test_callback_query.data = f"{CATEGORY_PREFIX}1"  # Category with ID 1
        
        # Find and call the category callback handler
        category_handler = None
        for handler in dp.callback_query.handlers:
            if hasattr(handler.filter, "text") and handler.filter.text.startswith(f"{CATEGORY_PREFIX}"):
                category_handler = handler
                await handler.callback(test_callback_query)
                break
        
        assert category_handler is not None, "Category handler not found"
        
        # Verify mock_show_category was called
        mock_show_category.assert_called_once()
        args, kwargs = mock_show_category.call_args
        assert args[0] == test_callback_query
        assert args[1] == 1  # Category ID
        
        # Navigate to a subcategory (level 2)
        test_callback_query.data = f"{CATEGORY_PREFIX}4"  # Subcategory ID
        await category_handler.callback(test_callback_query)
        
        # Verify second call
        assert mock_show_category.call_count == 2
        args, kwargs = mock_show_category.call_args
        assert args[1] == 4  # Subcategory ID

@pytest.mark.asyncio
async def test_back_button_navigation(mock_bot, test_callback_query, test_db):
    """Test the flow of navigating back through categories"""
    # Register handlers
    await register_handlers()
    
    # Mock back handler for testing
    async def mock_back_handler(callback_query, back_to_id):
        if back_to_id == "main":
            # Back to main menu
            await callback_query.message.edit_text("منوی اصلی", reply_markup=MagicMock())
            return None
        else:
            # Back to a category
            back_to_id = int(back_to_id)
            category = test_db.get_category(back_to_id)
            if category:
                parent_id = category.get('parent_id')
                if parent_id:
                    # If category has a parent, show that parent's subcategories
                    await callback_query.message.edit_text(
                        f"بازگشت به {category['name']}",
                        reply_markup=MagicMock()
                    )
                else:
                    # If category is a top-level category, show top-level categories
                    await callback_query.message.edit_text(
                        f"بازگشت به {category['name']}",
                        reply_markup=MagicMock()
                    )
            return category
    
    # Patch the handle_back function
    with patch('handlers.handle_back', side_effect=mock_back_handler) as mock_handle_back:
        # Set the callback data
        test_callback_query.data = f"{BACK_PREFIX}1"  # Back to category 1
        
        # Find and call the back callback handler
        back_handler = None
        for handler in dp.callback_query.handlers:
            if hasattr(handler.filter, "text") and handler.filter.text.startswith(f"{BACK_PREFIX}"):
                back_handler = handler
                await handler.callback(test_callback_query)
                break
        
        assert back_handler is not None, "Back handler not found"
        
        # Verify mock_handle_back was called
        mock_handle_back.assert_called_once()
        args, kwargs = mock_handle_back.call_args
        assert args[0] == test_callback_query
        assert args[1] == "1"  # Back to category ID
        
        # Back to main menu
        test_callback_query.data = f"{BACK_PREFIX}main"
        await back_handler.callback(test_callback_query)
        
        # Verify second call
        assert mock_handle_back.call_count == 2
        args, kwargs = mock_handle_back.call_args
        assert args[1] == "main"  # Back to main menu

@pytest.mark.asyncio
async def test_product_detail_flow(mock_bot, test_callback_query, test_db):
    """Test the flow of viewing product details"""
    # Register handlers
    await register_handlers()
    
    # Mock product handler for testing
    async def mock_product_handler(callback_query, product_id):
        product = test_db.get_product(product_id)
        product_media = test_db.get_product_media(product_id)
        
        if product:
            if product_media:
                # Show product with media
                await callback_query.message.delete()
                await callback_query.message.answer_photo(
                    photo=MagicMock(),
                    caption=f"{product['name']}\n\n{product['description']}\n\nقیمت: {product['price']:,} تومان",
                    reply_markup=MagicMock()
                )
            else:
                # Show product without media
                await callback_query.message.edit_text(
                    f"{product['name']}\n\n{product['description']}\n\nقیمت: {product['price']:,} تومان",
                    reply_markup=MagicMock()
                )
        return product
    
    # Patch the show_product function
    with patch('handlers.show_product', side_effect=mock_product_handler) as mock_show_product:
        # Set the callback data
        test_callback_query.data = f"{PRODUCT_PREFIX}1"  # Product with ID 1
        
        # Find and call the product callback handler
        product_handler = None
        for handler in dp.callback_query.handlers:
            if hasattr(handler.filter, "text") and handler.filter.text.startswith(f"{PRODUCT_PREFIX}"):
                product_handler = handler
                await handler.callback(test_callback_query)
                break
        
        assert product_handler is not None, "Product handler not found"
        
        # Verify mock_show_product was called
        mock_show_product.assert_called_once()
        args, kwargs = mock_show_product.call_args
        assert args[0] == test_callback_query
        assert args[1] == 1  # Product ID

@pytest.mark.asyncio
async def test_inquiry_flow(mock_bot, test_callback_query, test_db):
    """Test the flow of starting a price inquiry for a product"""
    # Register handlers
    await register_handlers()
    
    # Mock inquiry handler for testing
    async def mock_inquiry_handler(callback_query, entity_id):
        # Start the inquiry process
        await callback_query.message.edit_text(
            "لطفا نام خود را وارد کنید:",
            reply_markup=None  # Remove the inline keyboard
        )
        # Here we're just testing the start of the inquiry
        return entity_id
    
    # Patch the start_inquiry function
    with patch('handlers.start_inquiry', side_effect=mock_inquiry_handler) as mock_start_inquiry:
        # Set the callback data
        test_callback_query.data = f"inquiry_1"  # Inquiry for product/service with ID 1
        
        # Find and call the inquiry callback handler
        for handler in dp.callback_query.handlers:
            if hasattr(handler.filter, "text") and handler.filter.text.startswith("inquiry_"):
                await handler.callback(test_callback_query)
                break
        
        # Verify mock_start_inquiry was called
        mock_start_inquiry.assert_called_once()
        args, kwargs = mock_start_inquiry.call_args
        assert args[0] == test_callback_query
        assert args[1] == 1  # Entity ID

@pytest.mark.asyncio
async def test_complete_inquiry_flow_simulation(mock_bot, test_message, test_callback_query, test_db):
    """Test the complete flow of an inquiry from product to submission"""
    # Register handlers
    await register_handlers()
    
    # Create a mock FSMContext
    mock_state = MagicMock()
    mock_state.get_state = AsyncMock(return_value=None)
    mock_state.set_state = AsyncMock()
    mock_state.update_data = AsyncMock()
    mock_state.get_data = AsyncMock(return_value={"product_id": 1, "name": "Test User"})
    mock_state.clear = AsyncMock()
    
    # Step 1: User clicks on inquiry button for a product
    test_callback_query.data = "inquiry_1"
    
    # Find and patch the inquiry callback handler
    for handler in dp.message.handlers:
        if hasattr(handler, "states"):
            # This is likely a state handler for inquiries
            # We'll simulate the flow here
            
            # Step 1: Start inquiry
            with patch('handlers.start_inquiry') as mock_start_inquiry:
                mock_start_inquiry.return_value = None
                # Simulate clicking the inquiry button
                for cq_handler in dp.callback_query.handlers:
                    if hasattr(cq_handler.filter, "text") and cq_handler.filter.text.startswith("inquiry_"):
                        await cq_handler.callback(test_callback_query)
                        break
                
                # Verify inquiry was started
                mock_start_inquiry.assert_called_once()
            
            # Step 2: User enters their name
            mock_state.get_state.return_value = "waiting_for_name"
            test_message.text = "Test User"
            await handler.callback(test_message, state=mock_state)
            
            # Step 3: User enters their phone
            mock_state.get_state.return_value = "waiting_for_phone"
            test_message.text = "09123456789"
            await handler.callback(test_message, state=mock_state)
            
            # Step 4: User enters their inquiry
            mock_state.get_state.return_value = "waiting_for_description"
            test_message.text = "I would like to inquire about 5 units of this product."
            with patch.object(Database, 'add_inquiry', return_value=1) as mock_add_inquiry:
                await handler.callback(test_message, state=mock_state)
                
                # Verify inquiry was added to database
                mock_add_inquiry.assert_called_once()
                args, kwargs = mock_add_inquiry.call_args
                assert kwargs["name"] == "Test User"
                assert kwargs["phone"] == "09123456789"
                assert "5 units" in kwargs["description"]
                assert kwargs["product_id"] == 1
            
            break
    
    # Verify message confirmations
    assert test_message.answer.call_count >= 3  # At least three confirmation messages

if __name__ == "__main__":
    pytest.main()