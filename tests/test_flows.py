import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram import Bot, Dispatcher
from aiogram.types import Message, User, Chat, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

# Import the bot-related classes and functions
import handlers
from handlers import router, UserStates
from database import Database


class TestCategoryHierarchy:
    """
    Test that the category hierarchy displayed by the bot matches the database's tree structure
    These tests verify that the four-level hierarchy of categories is correctly displayed
    """

    @pytest.fixture
    def message_factory(self):
        """Factory for creating message objects for testing"""
        def _make_message(text, user_id=123456789, username="testuser", first_name="Test", last_name="User"):
            message = AsyncMock(spec=Message)
            message.text = text
            
            # Mock user data
            user = MagicMock(spec=User)
            user.id = user_id
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            message.from_user = user
            
            # Mock chat data
            chat = MagicMock(spec=Chat)
            chat.id = user_id  # Use same ID for simplicity
            message.chat = chat
            
            return message
        return _make_message

    @pytest.fixture
    def callback_factory(self):
        """Factory for creating callback query objects for testing"""
        def _make_callback(data, user_id=123456789, username="testuser", message_text="Test message"):
            callback = AsyncMock(spec=CallbackQuery)
            callback.data = data
            
            # Mock user data
            user = MagicMock(spec=User)
            user.id = user_id
            user.username = username
            callback.from_user = user
            
            # Mock message in the callback
            message = AsyncMock(spec=Message)
            message.text = message_text
            chat = MagicMock(spec=Chat)
            chat.id = user_id
            message.chat = chat
            callback.message = message
            
            return callback
        return _make_callback

    @pytest.fixture
    def mock_state_factory(self):
        """Factory for creating state objects for testing"""
        def _make_state(state=None, state_data=None):
            mock_state = AsyncMock(spec=FSMContext)
            
            # Set current state
            if state:
                mock_state.get_state.return_value = state
            else:
                mock_state.get_state.return_value = None
                
            # Set state data
            if state_data:
                async def mock_get_data():
                    return state_data.copy()
                mock_state.get_data.side_effect = mock_get_data
            else:
                mock_state.get_data.return_value = {}
                
            return mock_state
        return _make_state

    @pytest.fixture
    def test_category_data(self):
        """Create a test dataset for a complete 4-level category hierarchy"""
        # Level 1 (Root) categories
        level1_categories = [
            {"id": 1, "name": "محصولات فرکانس پایین", "parent_id": None, "cat_type": "product"},
            {"id": 2, "name": "محصولات فرکانس بالا", "parent_id": None, "cat_type": "product"}
        ]
        
        # Level 2 categories
        level2_categories = [
            {"id": 3, "name": "آنتن‌ها", "parent_id": 1, "cat_type": "product"},
            {"id": 4, "name": "ماژول‌ها", "parent_id": 1, "cat_type": "product"},
            {"id": 5, "name": "تجهیزات تست", "parent_id": 2, "cat_type": "product"}
        ]
        
        # Level 3 categories
        level3_categories = [
            {"id": 6, "name": "آنتن‌های یکطرفه", "parent_id": 3, "cat_type": "product"},
            {"id": 7, "name": "آنتن‌های دوطرفه", "parent_id": 3, "cat_type": "product"}
        ]
        
        # Level 4 categories (leaf nodes)
        level4_categories = [
            {"id": 8, "name": "آنتن‌های یکطرفه موج کوتاه", "parent_id": 6, "cat_type": "product"}
        ]
        
        # Sample products for leaf category
        level4_products = [
            {
                "id": 1, 
                "name": "آنتن یکطرفه XYZ",
                "price": 1500000,
                "description": "آنتن یکطرفه با فرکانس پایین",
                "category_id": 8,
                "product_type": "product"
            }
        ]
        
        return {
            "level1": level1_categories,
            "level2": level2_categories,
            "level3": level3_categories,
            "level4": level4_categories,
            "products": level4_products
        }

    @pytest.mark.asyncio
    async def test_four_level_product_category_navigation(self, message_factory, callback_factory, 
                                                         mock_bot, mock_state_factory, test_category_data):
        """
        Test that a user can navigate through all 4 levels of product categories
        and verify that the hierarchy matches the database structure
        """
        # Step 1: User sends /products command
        message = message_factory("/products")
        state = mock_state_factory()
        
        # Patch the database method to return our level 1 categories
        with patch.object(Database, 'get_categories') as mock_get_categories:
            mock_get_categories.return_value = test_category_data["level1"]
            
            # Find and call the products command handler
            products_handler = [h for h in router.message_handlers if "/products" in str(h.filter)][0]
            await products_handler.callback(message, state)
            
            # Verify level 1 categories are displayed correctly
            assert message.answer.called
            call_args = message.answer.call_args[1]
            keyboard = call_args["reply_markup"].inline_keyboard
            
            # Check level 1 category names
            level1_buttons = [button.text for row in keyboard for button in row]
            for category in test_category_data["level1"]:
                assert category["name"] in level1_buttons
            
            # Record the button callbacks for level 1
            level1_callbacks = [button.callback_data for row in keyboard for button in row 
                              if not button.callback_data.startswith("back")]
        
        # Step 2: User selects first level 1 category (محصولات فرکانس پایین)
        callback_level1 = callback_factory(level1_callbacks[0])
        state_level1 = mock_state_factory(
            state=UserStates.browse_categories,
            state_data={"type": "product"}
        )
        
        # Patch database methods for level 1 selection
        with patch.object(Database, 'get_category') as mock_get_category, \
             patch.object(Database, 'get_categories') as mock_get_subcategories, \
             patch.object(Database, 'get_products_by_category') as mock_get_products:
            
            mock_get_category.return_value = test_category_data["level1"][0]
            mock_get_subcategories.return_value = [cat for cat in test_category_data["level2"] 
                                                if cat["parent_id"] == test_category_data["level1"][0]["id"]]
            mock_get_products.return_value = []
            
            # Find and call category selection handler
            category_handlers = [h for h in router.callback_query_handlers if "category:" in str(h.filter)]
            if category_handlers:
                category_handler = category_handlers[0]
                await category_handler.callback(callback_level1, state_level1)
            
            # Verify level 2 categories are displayed correctly
            assert callback_level1.message.edit_text.called
            call_args = callback_level1.message.edit_text.call_args[1]
            keyboard = call_args["reply_markup"].inline_keyboard
            
            # Check level 2 category names
            level2_buttons = [button.text for row in keyboard for button in row]
            level2_expected = [cat["name"] for cat in test_category_data["level2"] 
                             if cat["parent_id"] == test_category_data["level1"][0]["id"]]
            for cat_name in level2_expected:
                assert cat_name in level2_buttons
            
            # Record the button callbacks for level 2
            level2_callbacks = [button.callback_data for row in keyboard for button in row 
                              if not button.callback_data.startswith("back")]
        
        # Step 3: User selects first level 2 category (آنتن‌ها)
        callback_level2 = callback_factory(level2_callbacks[0])
        state_level2 = mock_state_factory(
            state=UserStates.browse_categories,
            state_data={"type": "product"}
        )
        
        # Patch database methods for level 2 selection
        with patch.object(Database, 'get_category') as mock_get_category, \
             patch.object(Database, 'get_categories') as mock_get_subcategories, \
             patch.object(Database, 'get_products_by_category') as mock_get_products:
            
            # Find which level 2 category was selected
            selected_level2_id = int(level2_callbacks[0].split(':')[1])
            selected_level2 = next(cat for cat in test_category_data["level2"] if cat["id"] == selected_level2_id)
            
            mock_get_category.return_value = selected_level2
            mock_get_subcategories.return_value = [cat for cat in test_category_data["level3"] 
                                                if cat["parent_id"] == selected_level2_id]
            mock_get_products.return_value = []
            
            # Call category selection handler
            if category_handlers:
                await category_handler.callback(callback_level2, state_level2)
            
            # Verify level 3 categories are displayed correctly
            assert callback_level2.message.edit_text.called
            call_args = callback_level2.message.edit_text.call_args[1]
            keyboard = call_args["reply_markup"].inline_keyboard
            
            # Check level 3 category names
            level3_buttons = [button.text for row in keyboard for button in row]
            level3_expected = [cat["name"] for cat in test_category_data["level3"] 
                             if cat["parent_id"] == selected_level2_id]
            for cat_name in level3_expected:
                assert cat_name in level3_buttons
            
            # Record the button callbacks for level 3
            level3_callbacks = [button.callback_data for row in keyboard for button in row 
                              if not button.callback_data.startswith("back")]
        
        # Step 4: User selects first level 3 category (آنتن‌های یکطرفه)
        callback_level3 = callback_factory(level3_callbacks[0])
        state_level3 = mock_state_factory(
            state=UserStates.browse_categories,
            state_data={"type": "product"}
        )
        
        # Patch database methods for level 3 selection
        with patch.object(Database, 'get_category') as mock_get_category, \
             patch.object(Database, 'get_categories') as mock_get_subcategories, \
             patch.object(Database, 'get_products_by_category') as mock_get_products:
            
            # Find which level 3 category was selected
            selected_level3_id = int(level3_callbacks[0].split(':')[1])
            selected_level3 = next(cat for cat in test_category_data["level3"] if cat["id"] == selected_level3_id)
            
            mock_get_category.return_value = selected_level3
            mock_get_subcategories.return_value = [cat for cat in test_category_data["level4"] 
                                                if cat["parent_id"] == selected_level3_id]
            mock_get_products.return_value = []
            
            # Call category selection handler
            if category_handlers:
                await category_handler.callback(callback_level3, state_level3)
            
            # Verify level 4 categories are displayed correctly
            assert callback_level3.message.edit_text.called
            call_args = callback_level3.message.edit_text.call_args[1]
            keyboard = call_args["reply_markup"].inline_keyboard
            
            # Check level 4 category names
            level4_buttons = [button.text for row in keyboard for button in row]
            level4_expected = [cat["name"] for cat in test_category_data["level4"] 
                             if cat["parent_id"] == selected_level3_id]
            for cat_name in level4_expected:
                assert cat_name in level4_buttons
            
            # Record the button callbacks for level 4
            level4_callbacks = [button.callback_data for row in keyboard for button in row 
                              if not button.callback_data.startswith("back")]
        
        # Step 5: User selects the level 4 category (آنتن‌های یکطرفه موج کوتاه)
        callback_level4 = callback_factory(level4_callbacks[0])
        state_level4 = mock_state_factory(
            state=UserStates.browse_categories,
            state_data={"type": "product"}
        )
        
        # Patch database methods for level 4 selection
        with patch.object(Database, 'get_category') as mock_get_category, \
             patch.object(Database, 'get_categories') as mock_get_subcategories, \
             patch.object(Database, 'get_products_by_category') as mock_get_products:
            
            # Find which level 4 category was selected
            selected_level4_id = int(level4_callbacks[0].split(':')[1])
            selected_level4 = next(cat for cat in test_category_data["level4"] if cat["id"] == selected_level4_id)
            
            mock_get_category.return_value = selected_level4
            mock_get_subcategories.return_value = []  # No subcategories for level 4 (leaf)
            mock_get_products.return_value = [p for p in test_category_data["products"] 
                                           if p["category_id"] == selected_level4_id]
            
            # Call category selection handler
            if category_handlers:
                await category_handler.callback(callback_level4, state_level4)
            
            # Verify products are displayed for the leaf category
            assert callback_level4.message.edit_text.called
            call_args = callback_level4.message.edit_text.call_args[1]
            keyboard = call_args["reply_markup"].inline_keyboard
            
            # Check product names
            product_buttons = [button.text for row in keyboard for button in row 
                             if not button.text == "بازگشت"]
            product_expected = [p["name"] for p in test_category_data["products"] 
                              if p["category_id"] == selected_level4_id]
            for product_name in product_expected:
                assert product_name in product_buttons

    @pytest.mark.asyncio
    async def test_back_navigation_in_category_hierarchy(self, message_factory, callback_factory, 
                                                       mock_bot, mock_state_factory, test_category_data):
        """
        Test that a user can navigate back up the category hierarchy
        """
        # Start at a level 3 category and test navigating back to level 2
        # First setup the state data as if user has navigated to level 3
        state_data = {
            "type": "product",
            "category_stack": [
                {"id": 1, "name": "محصولات فرکانس پایین"},  # Level 1
                {"id": 3, "name": "آنتن‌ها"}  # Level 2
            ]
        }
        
        callback = callback_factory("back:product")
        state = mock_state_factory(
            state=UserStates.browse_categories,
            state_data=state_data
        )
        
        # Patch database methods for back navigation
        with patch.object(Database, 'get_category') as mock_get_category, \
             patch.object(Database, 'get_categories') as mock_get_subcategories, \
             patch.object(Database, 'get_products_by_category') as mock_get_products:
            
            # We're going back to level 2, so set up the data for level 2
            mock_get_category.return_value = test_category_data["level2"][0]  # آنتن‌ها
            mock_get_subcategories.return_value = test_category_data["level3"]  # Level 3 categories
            mock_get_products.return_value = []
            
            # Find and call back button handler
            back_handlers = [h for h in router.callback_query_handlers if "back:" in str(h.filter)]
            if back_handlers:
                back_handler = back_handlers[0]
                await back_handler.callback(callback, state)
            
            # Verify message shows level 2 content
            assert callback.message.edit_text.called
            call_args = callback.message.edit_text.call_args[1]
            
            # Check if the category name for level 2 is in the message
            assert test_category_data["level2"][0]["name"] in call_args["text"]
            
            # Check if level 3 categories are shown in the keyboard
            keyboard = call_args["reply_markup"].inline_keyboard
            level3_buttons = [button.text for row in keyboard for button in row 
                            if not button.text == "بازگشت"]
            for category in test_category_data["level3"]:
                assert category["name"] in level3_buttons
            
            # Verify state data was updated to pop the stack
            assert state.update_data.called
            # The new state should not include the level 2 category in the stack
            new_stack = state.update_data.call_args[0][0]["category_stack"]
            assert len(new_stack) == 1
            assert new_stack[0]["id"] == 1  # Only level 1 should remain

    @pytest.mark.asyncio
    async def test_services_category_hierarchy(self, message_factory, callback_factory, 
                                              mock_bot, mock_state_factory):
        """
        Test that the service category hierarchy is displayed correctly
        """
        # Create a test dataset for service categories
        service_categories = {
            "level1": [
                {"id": 9, "name": "خدمات نصب", "parent_id": None, "cat_type": "service"},
                {"id": 10, "name": "خدمات تعمیر", "parent_id": None, "cat_type": "service"}
            ],
            "level2": [
                {"id": 11, "name": "نصب آنتن", "parent_id": 9, "cat_type": "service"},
                {"id": 12, "name": "نصب ماژول", "parent_id": 9, "cat_type": "service"}
            ],
            "level3": [
                {"id": 13, "name": "نصب آنتن‌های خارجی", "parent_id": 11, "cat_type": "service"}
            ],
            "level4": [
                {"id": 14, "name": "نصب آنتن‌های خارجی فرکانس پایین", "parent_id": 13, "cat_type": "service"}
            ],
            "services": [
                {
                    "id": 2, 
                    "name": "نصب آنتن خارجی",
                    "price": 500000,
                    "description": "خدمات نصب آنتن خارجی به همراه تنظیمات",
                    "category_id": 14,
                    "product_type": "service"
                }
            ]
        }
        
        # Step 1: User sends /services command
        message = message_factory("/services")
        state = mock_state_factory()
        
        # Patch the database method to return our level 1 service categories
        with patch.object(Database, 'get_categories') as mock_get_categories:
            mock_get_categories.return_value = service_categories["level1"]
            
            # Find and call the services command handler
            services_handler = [h for h in router.message_handlers if "/services" in str(h.filter)][0]
            await services_handler.callback(message, state)
            
            # Verify level 1 service categories are displayed correctly
            assert message.answer.called
            call_args = message.answer.call_args[1]
            keyboard = call_args["reply_markup"].inline_keyboard
            
            # Check level 1 service category names
            level1_buttons = [button.text for row in keyboard for button in row]
            for category in service_categories["level1"]:
                assert category["name"] in level1_buttons
            
            # Verify state was updated with the service type
            assert state.update_data.called
            assert state.update_data.call_args[0][0]["type"] == "service"
            
            # This verifies that services are handled the same way as products
            # but with the different type, ensuring consistency across the bot