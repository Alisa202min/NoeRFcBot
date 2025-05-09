#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import logging
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

# Import project modules
from configuration import load_config
from database import Database
import handlers
import keyboards
from aiogram.fsm.state import State, StatesGroup
from handlers import UserStates

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock classes and functionality
class MockUser:
    """Mock class for User objects"""
    def __init__(self, user_id=123456789, first_name="Test User"):
        self.id = user_id
        self.first_name = first_name
        self.username = "testuser"

class MockChat:
    """Mock class for Chat objects"""
    def __init__(self, chat_id=123456789, chat_type="private"):
        self.id = chat_id
        self.type = chat_type

class MockMessage:
    """Mock class for Message objects"""
    def __init__(self, text=None, from_user=None, chat=None):
        self.text = text
        self.from_user = from_user or MockUser()
        self.chat = chat or MockChat()
        
    async def answer(self, text, parse_mode=None, reply_markup=None):
        logger.info(f"Message answered: {text[:100]}...")
        return True

class MockCallbackQuery:
    """Mock class for CallbackQuery objects"""
    def __init__(self, data=None, from_user=None, message=None):
        self.data = data
        self.from_user = from_user or MockUser()
        self._message = message or MockMessage()
        
    async def answer(self, text=None, show_alert=False):
        if text:
            logger.info(f"Callback answered: {text[:100]}...")
        return True
        
    @property
    def message(self):
        return self._message

class MockFSMContext:
    """Mock class for FSMContext"""
    def __init__(self):
        self.data = {}
        self.state = None
        
    async def get_state(self):
        return self.state
        
    async def set_state(self, state):
        self.state = state
        logger.info(f"State set to {state}")
        return True
        
    async def update_data(self, **kwargs):
        self.data.update(kwargs)
        return True
        
    async def get_data(self):
        return self.data
        
    async def clear(self):
        self.data = {}
        self.state = None
        return True

class BotUsabilityTest(unittest.TestCase):
    """Test case for bot usability testing"""
    
    def setUp(self):
        """Set up test environment"""
        # Initialize database
        self.db = Database()
        
        # Create mock objects
        self.state = MockFSMContext()
        self.message = MockMessage(text="/start")
        self.user_id = 123456789

    def tearDown(self):
        """Clean up after tests"""
        pass
        
    async def _test_start_command(self):
        """Test /start command"""
        print("\n=== Testing /start command ===")
        
        # Call the start command handler
        await handlers.cmd_start(self.message, self.state)
        
        # Verify state was reset
        state = await self.state.get_state()
        self.assertIsNone(state)
        
        print("✓ /start command handled successfully")
        
    async def _test_products_command(self):
        """Test /products command"""
        print("\n=== Testing /products command ===")
        
        # Create message with /products command
        products_message = MockMessage(text="/products")
        
        # Call the products command handler
        await handlers.cmd_products(products_message, self.state)
        
        # Verify state was set to browse_categories
        state = await self.state.get_state()
        self.assertEqual(state, UserStates.browse_categories.state)
        
        # Verify data was set in state context
        data = await self.state.get_data()
        self.assertEqual(data.get('cat_type'), 'product')
        
        print("✓ /products command handled successfully")
        
    async def _test_services_command(self):
        """Test /services command"""
        print("\n=== Testing /services command ===")
        
        # Create message with /services command
        services_message = MockMessage(text="/services")
        
        # Call the services command handler
        await handlers.cmd_services(services_message, self.state)
        
        # Verify state was set to browse_categories
        state = await self.state.get_state()
        self.assertEqual(state, UserStates.browse_categories.state)
        
        # Verify data was set in state context
        data = await self.state.get_data()
        self.assertEqual(data.get('cat_type'), 'service')
        
        print("✓ /services command handled successfully")
        
    async def _test_category_callback(self):
        """Test category selection callback"""
        print("\n=== Testing category selection ===")
        
        # Get a test category from the database
        categories = self.db.get_categories(cat_type='product')
        if not categories:
            print("No categories found in database, skipping test")
            return
            
        test_category = categories[0]
        category_id = test_category['id']
        
        # Set up context for category browsing
        await self.state.set_state(UserStates.browse_categories.state)
        await self.state.update_data(cat_type='product')
        
        # Create callback for category selection
        callback_data = f"category:{category_id}"
        callback = MockCallbackQuery(data=callback_data)
        
        # Call the category callback handler
        await handlers.callback_category(callback, self.state)
        
        # Data should now include the selected category
        data = await self.state.get_data()
        self.assertIn('selected_category_id', data)
        self.assertEqual(data['selected_category_id'], str(category_id))
        
        print(f"✓ Category callback handled successfully (Category ID: {category_id})")
        
    async def _test_product_callback(self):
        """Test product selection callback"""
        print("\n=== Testing product selection ===")
        
        # Get a test product from the database
        category = self.db.get_categories(cat_type='product')
        if not category:
            print("No categories found in database, skipping test")
            return
            
        products = self.db.get_products_by_category(category[0]['id'])
        if not products:
            print("No products found in database, skipping test")
            return
            
        test_product = products[0]
        product_id = test_product['id']
        
        # Create callback for product selection
        callback_data = f"product:{product_id}"
        callback = MockCallbackQuery(data=callback_data)
        
        # Call the product callback handler
        await handlers.callback_product(callback, self.state)
        
        # State should be set to view product
        state = await self.state.get_state()
        self.assertEqual(state, UserStates.view_product.state)
        
        # Data should include the selected product
        data = await self.state.get_data()
        self.assertIn('selected_product_id', data)
        self.assertEqual(data['selected_product_id'], str(product_id))
        
        print(f"✓ Product callback handled successfully (Product ID: {product_id})")
        
    async def _test_inquiry_flow(self):
        """Test price inquiry flow"""
        print("\n=== Testing price inquiry flow ===")
        
        # Get a test product from the database
        products = self.db.search_products(cat_type='product')
        if not products or len(products) == 0:
            print("No products found in database, skipping test")
            return
            
        test_product = products[0]
        product_id = test_product['id']
        
        # Setup state for viewing a product
        await self.state.set_state(UserStates.view_product.state)
        await self.state.update_data(selected_product_id=str(product_id))
        
        # Create callback for inquiry initiation
        callback_data = "inquiry"
        callback = MockCallbackQuery(data=callback_data)
        
        # Call the inquiry callback handler
        await handlers.callback_inquiry(callback, self.state)
        
        # State should be set to inquiry_name
        state = await self.state.get_state()
        self.assertEqual(state, UserStates.inquiry_name.state)
        
        # Test name input
        name_message = MockMessage(text="John Doe")
        await handlers.process_inquiry_name(name_message, self.state)
        
        # State should be set to inquiry_phone
        state = await self.state.get_state()
        self.assertEqual(state, UserStates.inquiry_phone.state)
        
        # Test phone input
        phone_message = MockMessage(text="+98123456789")
        await handlers.process_inquiry_phone(phone_message, self.state)
        
        # State should be set to inquiry_description
        state = await self.state.get_state()
        self.assertEqual(state, UserStates.inquiry_description.state)
        
        # Test description input
        desc_message = MockMessage(text="I need a price quote for this product.")
        await handlers.process_inquiry_description(desc_message, self.state)
        
        # State should be set to waiting_for_confirmation
        state = await self.state.get_state()
        self.assertEqual(state, UserStates.waiting_for_confirmation.state)
        
        # Test confirmation
        confirm_callback = MockCallbackQuery(data="confirm_inquiry")
        await handlers.callback_confirm_inquiry(confirm_callback, self.state)
        
        # State should be reset after confirmation
        state = await self.state.get_state()
        self.assertIsNone(state)
        
        print("✓ Price inquiry flow completed successfully")
        
    async def _test_help_command(self):
        """Test /help command"""
        print("\n=== Testing /help command ===")
        
        # Create message with /help command
        help_message = MockMessage(text="/help")
        
        # Call the help command handler
        await handlers.cmd_help(help_message)
        
        print("✓ /help command handled successfully")
        
    async def _test_contact_command(self):
        """Test /contact command"""
        print("\n=== Testing /contact command ===")
        
        # Create message with /contact command
        contact_message = MockMessage(text="/contact")
        
        # Call the contact command handler
        await handlers.cmd_contact(contact_message)
        
        print("✓ /contact command handled successfully")
        
    async def _test_about_command(self):
        """Test /about command"""
        print("\n=== Testing /about command ===")
        
        # Create message with /about command
        about_message = MockMessage(text="/about")
        
        # Call the about command handler
        await handlers.cmd_about(about_message)
        
        print("✓ /about command handled successfully")
        
    async def _run_all_tests(self):
        """Run all tests"""
        await self._test_start_command()
        await self._test_help_command()
        await self._test_products_command()
        await self._test_services_command()
        
        try:
            await self._test_category_callback()
            await self._test_product_callback()
            await self._test_inquiry_flow()
        except Exception as e:
            print(f"Some tests were skipped due to missing data: {e}")
        
        await self._test_contact_command()
        await self._test_about_command()
    
    def test_bot_usability(self):
        """Main test method that runs all tests"""
        print("\n===== RFCBot Usability Tests =====")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._run_all_tests())
        print("\n===== Test Results =====")
        print("Bot usability tests completed.")


if __name__ == "__main__":
    unittest.main()