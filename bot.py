
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from aiohttp import web

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

# Import local modules
import sys
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

# Check if BOT_TOKEN is valid (not None or empty)
if not BOT_TOKEN:
    if __name__ == '__main__':
        logger.error("BOT_TOKEN is not set. Please set it in the .env file or environment variables.")
        sys.exit(1)
    # When imported by Flask, we'll create placeholder objects that are properly initialized later
    bot = None
    dp = None
    storage = None
else:
    # Initialize bot and dispatcher globally
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Create a storage for state machine (FSM)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

async def register_handlers():
    """Register all handlers for the bot."""
    # Check if bot is available
    if dp is None:
        logger.error("Dispatcher is None. Cannot register handlers.")
        return
        
    try:
        # Initialize database
        db = Database()

        # Start command
        dp.message.register(start_handler, CommandStart())

        # Admin command
        dp.message.register(admin_handlers.start_admin, Command(commands=["admin"]))

        # Template commands for CSV imports
        dp.message.register(admin_handlers.get_template, Command(commands=["template"]))
        dp.message.register(admin_handlers.get_template, Command(commands=["template_products"]))
        dp.message.register(admin_handlers.get_template, Command(commands=["template_categories"]))
        dp.message.register(admin_handlers.get_template, Command(commands=["template_educational"]))

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
        dp.message.register(admin_handlers.process_edit_category, AdminActions.edit_category)

        # Admin add category handlers
        dp.callback_query.register(admin_handlers.start_add_category, lambda c: c.data.startswith("admin_add_cat_"))
        dp.message.register(admin_handlers.process_add_category, AdminActions.add_category)

        # Admin product edit handlers
        dp.callback_query.register(admin_handlers.start_edit_product, lambda c: c.data.startswith("admin_edit_product_"))
        dp.message.register(admin_handlers.process_edit_product, AdminActions.edit_product)

        # Admin add product handlers
        dp.callback_query.register(admin_handlers.start_add_product, lambda c: c.data.startswith("admin_add_product_"))
        dp.message.register(admin_handlers.process_add_product, AdminActions.add_product)

        # Admin educational content edit handlers
        dp.callback_query.register(admin_handlers.start_edit_edu, lambda c: c.data.startswith("admin_edit_edu_"))
        dp.message.register(admin_handlers.process_edit_edu, AdminActions.edit_edu)

        # Admin add educational content handlers
        dp.callback_query.register(admin_handlers.start_add_edu, lambda c: c.data == "admin_add_edu")
        dp.message.register(admin_handlers.process_add_edu, AdminActions.add_edu)

        # Admin static content edit handlers
        dp.callback_query.register(admin_handlers.start_edit_static, lambda c: c.data.startswith("admin_edit_static_"))
        dp.message.register(admin_handlers.process_edit_static, AdminActions.edit_static)

        # Admin upload CSV handlers
        dp.callback_query.register(admin_handlers.start_import_data, lambda c: c.data.startswith("admin_import_"))
        dp.message.register(admin_handlers.process_import_data, AdminActions.upload_csv, lambda m: m.document is not None)

        # Admin cancel action handler (common for all admin actions)
        dp.message.register(admin_handlers.cancel_admin_action, Command(commands=["cancel"]))
        dp.callback_query.register(admin_handlers.cancel_admin_action, lambda c: c.data.startswith("cancel"))

        # General callback query handler for button presses (must be registered last)
        dp.callback_query.register(handle_callback_query, lambda c: True)

        # Message handler for text messages (must be registered last)
        dp.message.register(handle_message, lambda m: not m.text.startswith('/'))
    except Exception as e:
        logger.error(f"Error registering handlers: {e}")

async def setup_webhook(app, webhook_path):
    """Set up webhook handling for the bot with aiohttp app"""
    if bot is None or dp is None:
        logger.error("Bot or dispatcher is None. Cannot set up webhook.")
        return app
        
    try:
        # Register handlers for the dispatcher
        await register_handlers()

        # Set up webhook handler in the web app
        webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_handler.register(app, path=webhook_path)

        # Configure the bot to use the webhook
        setup_application(app, dp, bot=bot)
    except Exception as e:
        logger.error(f"Error setting up webhook: {e}")

    return app

async def start_polling():
    """Start the bot in polling mode (for testing)."""
    # Check if bot is available
    if bot is None or dp is None:
        logger.error("Bot or dispatcher is None. Cannot start polling.")
        return
        
    try:
        # Register handlers
        await register_handlers()

        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error starting polling: {e}")

if __name__ == '__main__':
    # Check if BOT_TOKEN is set
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set. Please set it in the .env file or environment variables.")
        sys.exit(1)
    
    # Run the bot in polling mode when run directly
    asyncio.run(start_polling())
