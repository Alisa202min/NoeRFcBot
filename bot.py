
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

# Import local modules
from configuration import BOT_TOKEN, ADMIN_ID, DATA_DIR
from database import Database
from handlers import (
    start_handler, 
    handle_message, 
    handle_callback_query,
    handle_inquiry,
    handle_search,
    admin_handlers,
    InquiryForm,
    SearchForm,
    AdminActions
)

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize bot and dispatcher globally
bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
# Create a storage for state machine (FSM)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def main():
    """Start the bot."""
    # Initialize database
    db = Database()
    
    # Register handlers
    
    # Start command
    dp.message.register(start_handler, CommandStart())
    
    # Admin command
    dp.message.register(admin_handlers.start_admin, Command(commands=["admin"]))
    
    # Inquiry conversation handlers with state management
    dp.callback_query.register(handle_inquiry.start_inquiry, lambda c: c.data.startswith("inquiry_"))
    
    # Name state handler - add state filter
    dp.message.register(handle_inquiry.process_name, InquiryForm.name)
    
    # Phone state handler
    dp.message.register(handle_inquiry.process_phone, InquiryForm.phone)
    
    # Description state handler
    dp.message.register(handle_inquiry.process_description, InquiryForm.description)
    
    # Cancel handlers
    dp.message.register(handle_inquiry.cancel_inquiry_message, Command(commands=["cancel"]))
    dp.callback_query.register(handle_inquiry.cancel_inquiry, lambda c: c.data == "cancel")
    
    # Search conversation handlers
    dp.message.register(handle_search.start_search, lambda m: m.text == "جستجو 🔍")
    
    # Process search query with state filter
    dp.message.register(handle_search.process_search, SearchForm.query)
    
    # Cancel search
    dp.message.register(handle_search.cancel_search, Command(commands=["cancel"]), SearchForm.query)
    
    # Admin category edit handlers
    dp.callback_query.register(admin_handlers.start_edit_category, lambda c: c.data.startswith("admin_edit_cat_"))
    dp.message.register(admin_handlers.process_edit_category, lambda m: not m.text.startswith('/'))
    
    # Admin add category handlers
    dp.callback_query.register(admin_handlers.start_add_category, lambda c: c.data.startswith("admin_add_cat_"))
    dp.message.register(admin_handlers.process_add_category, lambda m: not m.text.startswith('/'))
    
    # Admin product edit handlers
    dp.callback_query.register(admin_handlers.start_edit_product, lambda c: c.data.startswith("admin_edit_product_"))
    dp.message.register(admin_handlers.process_edit_product, AdminActions.edit_product)
    
    # Admin add product handlers
    dp.callback_query.register(admin_handlers.start_add_product, lambda c: c.data.startswith("admin_add_product_"))
    dp.message.register(admin_handlers.process_add_product, AdminActions.add_product)
    
    # Admin educational content edit handlers
    dp.callback_query.register(admin_handlers.start_edit_edu, lambda c: c.data.startswith("admin_edit_edu_"))
    dp.message.register(admin_handlers.process_edit_edu, lambda m: not m.text.startswith('/'))
    
    # Admin add educational content handlers
    dp.callback_query.register(admin_handlers.start_add_edu, lambda c: c.data == "admin_add_edu")
    dp.message.register(admin_handlers.process_add_edu, lambda m: not m.text.startswith('/'))
    
    # Admin static content edit handlers
    dp.callback_query.register(admin_handlers.start_edit_static, lambda c: c.data.startswith("admin_edit_static_"))
    dp.message.register(admin_handlers.process_edit_static, lambda m: not m.text.startswith('/'))
    
    # Admin upload CSV handlers
    dp.callback_query.register(admin_handlers.start_import_data, lambda c: c.data.startswith("admin_import_"))
    dp.message.register(admin_handlers.process_import_data, lambda m: m.document is not None)
    
    # Admin cancel action handler (common for all admin actions)
    dp.message.register(admin_handlers.cancel_admin_action, Command(commands=["cancel"]))
    dp.callback_query.register(admin_handlers.cancel_admin_action, lambda c: c.data.startswith("cancel"))
    
    # General callback query handler for button presses (must be registered last)
    dp.callback_query.register(handle_callback_query, lambda c: True)
    
    # Message handler for text messages (must be registered last)
    dp.message.register(handle_message, lambda m: not m.text.startswith('/'))
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    # Run the async main function
    asyncio.run(main())
