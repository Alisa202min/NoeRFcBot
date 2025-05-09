
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, Filters
from telegram import Update
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
    handle_button_press,
    handle_inquiry,
    handle_search,
    admin_handlers,
    INQUIRY_NAME, INQUIRY_PHONE, INQUIRY_DESC,
    ADMIN_EDIT_CAT, ADMIN_EDIT_PRODUCT, ADMIN_EDIT_EDU, ADMIN_EDIT_STATIC,
    ADMIN_UPLOAD_CSV
)

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

def main():
    """Start the bot."""
    # Initialize database
    db = Database()
    
    # Create the Updater and pass it your bot's token
    updater = Updater(BOT_TOKEN)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Register handlers
    
    # Start command
    dispatcher.add_handler(CommandHandler("start", start_handler))
    
    # Admin command
    dispatcher.add_handler(CommandHandler("admin", admin_handlers.start_admin))
    
    # Inquiry conversation handler
    inquiry_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_inquiry.start_inquiry, pattern=r'^inquiry_')],
        states={
            INQUIRY_NAME: [MessageHandler(Filters.text & ~Filters.command, handle_inquiry.process_name)],
            INQUIRY_PHONE: [MessageHandler(Filters.text & ~Filters.command, handle_inquiry.process_phone)],
            INQUIRY_DESC: [MessageHandler(Filters.text & ~Filters.command, handle_inquiry.process_description)],
        },
        fallbacks=[
            CommandHandler("cancel", handle_inquiry.cancel_inquiry),
            CallbackQueryHandler(handle_inquiry.cancel_inquiry, pattern=r'^cancel$')
        ],
        per_message=True
    )
    dispatcher.add_handler(inquiry_conv_handler)
    
    # Search conversation handler
    search_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'جستجو 🔍'), handle_search.start_search)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search.process_search)],
        },
        fallbacks=[CommandHandler("cancel", handle_search.cancel_search)],
        per_message=True
    )
    application.add_handler(search_conv_handler)
    
    # Admin category edit conversation handler
    admin_cat_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.start_edit_category, pattern=r'^admin_edit_cat_')],
        states={
            ADMIN_EDIT_CAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.process_edit_category)],
        },
        fallbacks=[
            CommandHandler("cancel", admin_handlers.cancel_admin_action),
            CallbackQueryHandler(admin_handlers.cancel_admin_action, pattern=r'^cancel')
        ],
        per_message=True
    )
    application.add_handler(admin_cat_conv_handler)
    
    # Admin add category conversation handler
    admin_add_cat_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.start_add_category, pattern=r'^admin_add_cat_')],
        states={
            ADMIN_EDIT_CAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.process_add_category)],
        },
        fallbacks=[
            CommandHandler("cancel", admin_handlers.cancel_admin_action),
            CallbackQueryHandler(admin_handlers.cancel_admin_action, pattern=r'^cancel')
        ],
        per_message=True
    )
    application.add_handler(admin_add_cat_conv_handler)
    
    # Admin product edit conversation handler
    admin_product_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.start_edit_product, pattern=r'^admin_edit_product_')],
        states={
            ADMIN_EDIT_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.process_edit_product)],
        },
        fallbacks=[
            CommandHandler("cancel", admin_handlers.cancel_admin_action),
            CallbackQueryHandler(admin_handlers.cancel_admin_action, pattern=r'^cancel')
        ],
        per_message=True
    )
    application.add_handler(admin_product_conv_handler)
    
    # Admin add product conversation handler
    admin_add_product_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.start_add_product, pattern=r'^admin_add_product_')],
        states={
            ADMIN_EDIT_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.process_add_product)],
        },
        fallbacks=[
            CommandHandler("cancel", admin_handlers.cancel_admin_action),
            CallbackQueryHandler(admin_handlers.cancel_admin_action, pattern=r'^cancel')
        ],
        per_message=True
    )
    application.add_handler(admin_add_product_conv_handler)
    
    # Admin educational content edit conversation handler
    admin_edu_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.start_edit_edu, pattern=r'^admin_edit_edu_')],
        states={
            ADMIN_EDIT_EDU: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.process_edit_edu)],
        },
        fallbacks=[
            CommandHandler("cancel", admin_handlers.cancel_admin_action),
            CallbackQueryHandler(admin_handlers.cancel_admin_action, pattern=r'^cancel')
        ],
        per_message=True
    )
    application.add_handler(admin_edu_conv_handler)
    
    # Admin add educational content conversation handler
    admin_add_edu_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.start_add_edu, pattern=r'^admin_add_edu$')],
        states={
            ADMIN_EDIT_EDU: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.process_add_edu)],
        },
        fallbacks=[
            CommandHandler("cancel", admin_handlers.cancel_admin_action),
            CallbackQueryHandler(admin_handlers.cancel_admin_action, pattern=r'^cancel')
        ],
        per_message=True
    )
    application.add_handler(admin_add_edu_conv_handler)
    
    # Admin static content edit conversation handler
    admin_static_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.start_edit_static, pattern=r'^admin_edit_static_')],
        states={
            ADMIN_EDIT_STATIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.process_edit_static)],
        },
        fallbacks=[
            CommandHandler("cancel", admin_handlers.cancel_admin_action),
            CallbackQueryHandler(admin_handlers.cancel_admin_action, pattern=r'^cancel')
        ],
        per_message=True
    )
    application.add_handler(admin_static_conv_handler)
    
    # Admin upload CSV conversation handler
    admin_upload_csv_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.start_import_data, pattern=r'^admin_import_')],
        states={
            ADMIN_UPLOAD_CSV: [MessageHandler(filters.Document.ALL, admin_handlers.process_import_data)],
        },
        fallbacks=[
            CommandHandler("cancel", admin_handlers.cancel_admin_action),
            CallbackQueryHandler(admin_handlers.cancel_admin_action, pattern=r'^cancel')
        ],
        per_message=True
    )
    application.add_handler(admin_upload_csv_conv_handler)
    
    # General callback query handler for button presses
    application.add_handler(CallbackQueryHandler(handle_button_press))
    
    # Message handler for text messages (must be registered last)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
