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


class TestBotCommands:
    """Test bot commands and responses"""

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

    @pytest.mark.asyncio
    async def test_start_command(self, message_factory, mock_bot, mock_state_factory):
        """Test that /start command sends welcome message and keyboard"""
        # Prepare test data
        message = message_factory("/start")
        state = mock_state_factory()
        
        # Patch the database method to avoid actual database calls
        with patch.object(Database, 'get_or_create_telegram_user', return_value=True):
            # Call the start command handler
            start_handler = [h for h in router.message_handlers if "CommandStart" in str(h.filter)][0]
            await start_handler.callback(message, state)
        
        # Check if the bot sent a message with a welcome text and keyboard
        assert message.answer.called
        call_args = message.answer.call_args[1]
        
        # Verify message contains welcome text
        assert "به ربات کاتالوگ" in call_args["text"]
        
        # Verify keyboard is included
        assert isinstance(call_args["reply_markup"], InlineKeyboardMarkup)
        
        # Check if keyboard contains the expected buttons
        keyboard = call_args["reply_markup"].inline_keyboard
        button_texts = [button.text for row in keyboard for button in row]
        assert "محصولات" in button_texts
        assert "خدمات" in button_texts
        assert "مطالب آموزشی" in button_texts
        
        # Check if state was cleared
        assert state.clear.called

    @pytest.mark.asyncio
    async def test_products_command(self, message_factory, mock_bot, mock_state_factory, test_db_cursor):
        """Test that /products command shows product categories"""
        # Prepare test data
        message = message_factory("/products")
        state = mock_state_factory()
        
        # Patch the database method to return our test categories
        with patch.object(Database, 'get_categories') as mock_get_categories:
            # Configure the mock to return our test data
            mock_get_categories.return_value = [
                {"id": 1, "name": "محصولات فرکانس پایین", "parent_id": None},
                {"id": 2, "name": "محصولات فرکانس بالا", "parent_id": None}
            ]
            
            # Call the products command handler
            products_handler = [h for h in router.message_handlers if "/products" in str(h.filter)][0]
            await products_handler.callback(message, state)
        
        # Check if the bot sent a message with categories and keyboard
        assert message.answer.called
        call_args = message.answer.call_args[1]
        
        # Verify message contains category list prompt
        assert "دسته‌بندی‌های محصولات" in call_args["text"]
        
        # Verify keyboard is included
        assert isinstance(call_args["reply_markup"], InlineKeyboardMarkup)
        
        # Check if keyboard contains our test categories
        keyboard = call_args["reply_markup"].inline_keyboard
        button_texts = [button.text for row in keyboard for button in row]
        assert "محصولات فرکانس پایین" in button_texts
        assert "محصولات فرکانس بالا" in button_texts
        
        # Verify state was set to browse_categories
        assert state.set_state.called
        assert state.set_state.call_args[0][0] == UserStates.browse_categories
        
        # Verify category type was stored in state data
        assert state.update_data.called
        assert state.update_data.call_args[0][0]["type"] == "product"

    @pytest.mark.asyncio
    async def test_services_command(self, message_factory, mock_bot, mock_state_factory):
        """Test that /services command shows service categories"""
        # Prepare test data
        message = message_factory("/services")
        state = mock_state_factory()
        
        # Patch the database method to return our test categories
        with patch.object(Database, 'get_categories') as mock_get_categories:
            # Configure the mock to return our test data
            mock_get_categories.return_value = [
                {"id": 3, "name": "خدمات نصب", "parent_id": None},
                {"id": 4, "name": "خدمات تعمیر", "parent_id": None}
            ]
            
            # Call the services command handler
            services_handler = [h for h in router.message_handlers if "/services" in str(h.filter)][0]
            await services_handler.callback(message, state)
        
        # Check if the bot sent a message with categories and keyboard
        assert message.answer.called
        call_args = message.answer.call_args[1]
        
        # Verify message contains category list prompt
        assert "دسته‌بندی‌های خدمات" in call_args["text"]
        
        # Verify keyboard is included
        assert isinstance(call_args["reply_markup"], InlineKeyboardMarkup)
        
        # Check if keyboard contains our test categories
        keyboard = call_args["reply_markup"].inline_keyboard
        button_texts = [button.text for row in keyboard for button in row]
        assert "خدمات نصب" in button_texts
        assert "خدمات تعمیر" in button_texts
        
        # Verify state was set to browse_categories
        assert state.set_state.called
        assert state.set_state.call_args[0][0] == UserStates.browse_categories
        
        # Verify category type was stored in state data
        assert state.update_data.called
        assert state.update_data.call_args[0][0]["type"] == "service"

    @pytest.mark.asyncio
    async def test_category_selection_callback(self, callback_factory, mock_bot, mock_state_factory):
        """Test the callback when a user selects a category"""
        # Prepare test data
        callback = callback_factory("category:1:product")  # Format is category:id:type
        state = mock_state_factory(
            state=UserStates.browse_categories,
            state_data={"type": "product"}
        )
        
        # Patch the database methods
        with patch.object(Database, 'get_category') as mock_get_category, \
             patch.object(Database, 'get_categories') as mock_get_subcategories, \
             patch.object(Database, 'get_products_by_category') as mock_get_products:
            
            # Mock the main category
            mock_get_category.return_value = {
                "id": 1, 
                "name": "محصولات فرکانس پایین", 
                "parent_id": None
            }
            
            # Mock subcategories
            mock_get_subcategories.return_value = [
                {"id": 5, "name": "آنتن‌ها", "parent_id": 1},
                {"id": 6, "name": "ماژول‌ها", "parent_id": 1}
            ]
            
            # Mock that there are no direct products in this category
            mock_get_products.return_value = []
            
            # Find the callback handler for category selection
            category_handlers = [h for h in router.callback_query_handlers if "category:" in str(h.filter)]
            if category_handlers:
                category_handler = category_handlers[0]
                await category_handler.callback(callback, state)
            
            # Verify the callback was answered
            assert callback.answer.called
            
            # Check if the message was edited with subcategories
            assert callback.message.edit_text.called
            call_args = callback.message.edit_text.call_args[1]
            
            # Verify message contains category name
            assert "محصولات فرکانس پایین" in call_args["text"]
            
            # Verify keyboard is included
            assert isinstance(call_args["reply_markup"], InlineKeyboardMarkup)
            
            # Check if keyboard contains subcategories
            keyboard = call_args["reply_markup"].inline_keyboard
            button_texts = [button.text for row in keyboard for button in row]
            assert "آنتن‌ها" in button_texts
            assert "ماژول‌ها" in button_texts
            
            # Check if there's a back button
            assert "بازگشت" in button_texts

    @pytest.mark.asyncio
    async def test_leaf_category_with_products(self, callback_factory, mock_bot, mock_state_factory):
        """Test when a user selects a leaf category with products"""
        # Prepare test data for a leaf category (level 4)
        callback = callback_factory("category:10:product")  # Leaf category ID
        state = mock_state_factory(
            state=UserStates.browse_categories,
            state_data={"type": "product"}
        )
        
        # Patch the database methods
        with patch.object(Database, 'get_category') as mock_get_category, \
             patch.object(Database, 'get_categories') as mock_get_subcategories, \
             patch.object(Database, 'get_products_by_category') as mock_get_products:
            
            # Mock the leaf category
            mock_get_category.return_value = {
                "id": 10, 
                "name": "آنتن‌های یکطرفه موج کوتاه", 
                "parent_id": 7  # This is a level 4 category
            }
            
            # No subcategories for a leaf node
            mock_get_subcategories.return_value = []
            
            # Mock products in this leaf category
            mock_get_products.return_value = [
                {
                    "id": 1, 
                    "name": "آنتن یکطرفه XYZ",
                    "price": 1500000,
                    "description": "آنتن یکطرفه با فرکانس پایین"
                },
                {
                    "id": 2, 
                    "name": "آنتن یکطرفه ABC",
                    "price": 2500000,
                    "description": "آنتن یکطرفه با فرکانس بالا"
                }
            ]
            
            # Find the callback handler for category selection
            category_handlers = [h for h in router.callback_query_handlers if "category:" in str(h.filter)]
            if category_handlers:
                category_handler = category_handlers[0]
                await category_handler.callback(callback, state)
            
            # Verify the callback was answered
            assert callback.answer.called
            
            # Check if the message was edited with products
            assert callback.message.edit_text.called
            call_args = callback.message.edit_text.call_args[1]
            
            # Verify message contains category name
            assert "آنتن‌های یکطرفه موج کوتاه" in call_args["text"]
            
            # Verify keyboard is included
            assert isinstance(call_args["reply_markup"], InlineKeyboardMarkup)
            
            # Check if keyboard contains products
            keyboard = call_args["reply_markup"].inline_keyboard
            button_texts = [button.text for row in keyboard for button in row]
            assert "آنتن یکطرفه XYZ" in button_texts
            assert "آنتن یکطرفه ABC" in button_texts
            
            # Check if there's a back button
            assert "بازگشت" in button_texts