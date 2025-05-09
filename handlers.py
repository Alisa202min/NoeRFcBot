#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import csv
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, CommandStart
from aiogram.filters import Filter
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Create a Text filter since it's not included in aiogram 3.x
class Text(Filter):
    def __init__(self, text: str | list[str]):
        self.text = [text] if isinstance(text, str) else text
    
    async def __call__(self, message: types.Message) -> bool:
        return message.text in self.text

from configuration import (
    ADMIN_ID, START_TEXT, PRODUCTS_BTN, SERVICES_BTN, INQUIRY_BTN, EDUCATION_BTN, 
    CONTACT_BTN, ABOUT_BTN, BACK_BTN, ADMIN_BTN, SEARCH_BTN,
    PRODUCT_PREFIX, SERVICE_PREFIX, CATEGORY_PREFIX, BACK_PREFIX, INQUIRY_PREFIX, 
    EDUCATION_PREFIX, ADMIN_PREFIX, NOT_FOUND_TEXT, SEARCH_PROMPT, ERROR_MESSAGE,
    INQUIRY_START, INQUIRY_PHONE, INQUIRY_DESC, INQUIRY_COMPLETE, ADMIN_ACCESS_DENIED,
    ADMIN_WELCOME
)
from database import Database
from keyboards import (
    main_menu_keyboard, admin_keyboard, categories_keyboard, products_keyboard,
    product_detail_keyboard, education_categories_keyboard, education_content_keyboard,
    education_detail_keyboard, cancel_keyboard, confirm_keyboard
)
from utils import (
    format_price, format_product_details, format_inquiry_details, format_educational_content,
    is_valid_phone_number, get_category_path, create_sample_data, import_initial_data,
    generate_csv_template
)

# Initialize database
db = Database()

# Define state classes for FSM
class InquiryForm(StatesGroup):
    name = State()
    phone = State()
    description = State()

class AdminActions(StatesGroup):
    edit_category = State()
    add_category = State()  # Added for add_category operations
    edit_product = State()
    add_product = State()
    edit_edu = State()
    add_edu = State()
    edit_static = State()
    upload_csv = State()

# For compatibility with old code
INQUIRY_NAME, INQUIRY_PHONE, INQUIRY_DESC = range(3)
ADMIN_EDIT_CAT, ADMIN_EDIT_PRODUCT, ADMIN_EDIT_EDU, ADMIN_EDIT_STATIC, ADMIN_UPLOAD_CSV = range(5)

# User state dictionary to store temporary data
user_states = {}

async def start_handler(message: types.Message, state: FSMContext) -> None:
    """Handle the /start command."""
    # Clear any user state if exists
    await state.clear()
    
    # Send welcome message with main menu
    await message.reply(
        START_TEXT,
        reply_markup=main_menu_keyboard()
    )

async def handle_message(message: types.Message, state: FSMContext) -> None:
    """Handle text messages."""
    text = message.text
    user_id = message.from_user.id
    
    # Handle main menu options
    if text == PRODUCTS_BTN:
        # Show product categories
        categories = db.get_categories(parent_id=None, cat_type='product')
        if categories:
            await message.reply(
                "لطفاً یک گروه محصول را انتخاب کنید:",
                reply_markup=categories_keyboard(categories)
            )
        else:
            await message.reply(NOT_FOUND_TEXT)
            
    elif text == SERVICES_BTN:
        # Show service categories
        categories = db.get_categories(parent_id=None, cat_type='service')
        if categories:
            await message.reply(
                "لطفاً یک گروه خدمات را انتخاب کنید:",
                reply_markup=categories_keyboard(categories)
            )
        else:
            await message.reply(NOT_FOUND_TEXT)
            
    elif text == INQUIRY_BTN:
        # Show direct inquiry form
        await message.reply(
            INQUIRY_START,
            reply_markup=cancel_keyboard()
        )
        await state.set_state(InquiryForm.name)
            
    elif text == EDUCATION_BTN:
        # Show educational content categories
        categories = db.get_educational_categories()
        if categories:
            await message.reply(
                "لطفاً یک دسته‌بندی آموزشی را انتخاب کنید:",
                reply_markup=education_categories_keyboard(categories)
            )
        else:
            await message.reply(
                "هنوز مطلب آموزشی ثبت نشده است."
            )
            
    elif text == CONTACT_BTN:
        # Show contact info
        contact_text = db.get_static_content('contact')
        await message.reply(contact_text)
            
    elif text == ABOUT_BTN:
        # Show about info
        about_text = db.get_static_content('about')
        await message.reply(about_text)
            
    elif text == BACK_BTN:
        # Return to main menu
        await start_handler(message, state)
            
    elif text == ADMIN_BTN:
        # Access admin panel
        await admin_handlers.start_admin(message, state)
        
    else:
        # Unknown message
        await message.reply(
            "لطفاً یکی از گزینه‌های منو را انتخاب کنید.",
            reply_markup=main_menu_keyboard()
        )

async def handle_callback_query(callback_query: types.CallbackQuery, bot: "Bot", state: FSMContext) -> None:
    """Handle inline button presses."""
    # Answer the callback query to remove the "loading" state on button
    await callback_query.answer()
    
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    try:
        # Handle category navigation
        if data.startswith(CATEGORY_PREFIX):
            category_id = int(data[len(CATEGORY_PREFIX):])
            category = db.get_category(category_id)
            
            if category:
                # Check for subcategories
                subcategories = db.get_categories(parent_id=category_id)
                
                if subcategories:
                    # Show subcategories
                    await callback_query.message.edit_text(
                        f"زیرگروه‌های {category['name']}:",
                        reply_markup=categories_keyboard(subcategories, category_id)
                    )
                else:
                    # No subcategories, show products
                    products = db.get_products_by_category(category_id)
                    
                    if products:
                        await callback_query.message.edit_text(
                            f"محصولات/خدمات {category['name']}:",
                            reply_markup=products_keyboard(products, category_id)
                        )
                    else:
                        await callback_query.message.edit_text(
                            "هیچ محصول/خدماتی در این گروه یافت نشد.",
                            reply_markup=categories_keyboard([], category_id)
                        )
        
        # Handle product selection
        elif data.startswith(PRODUCT_PREFIX):
            product_id = int(data[len(PRODUCT_PREFIX):])
            product = db.get_product(product_id)
            
            if product:
                # Show product details
                product_text = format_product_details(product)
                
                # Get category for back button
                category_id = product['category_id']
                
                # Check if product has photo
                if product['photo_url']:
                    # Send photo with caption
                    await bot.send_photo(
                        chat_id=user_id,
                        photo=product['photo_url'],
                        caption=product_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=product_detail_keyboard(product_id, category_id)
                    )
                    # Delete the original message
                    await callback_query.message.delete()
                else:
                    # No photo, just update message
                    await callback_query.message.edit_text(
                        product_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=product_detail_keyboard(product_id, category_id)
                    )
        
        # Handle back navigation
        elif data.startswith(BACK_PREFIX):
            back_data = data[len(BACK_PREFIX):]
            
            if back_data == "main":
                # Back to main menu
                await callback_query.message.edit_text(
                    "لطفاً یکی از گزینه‌های منو را انتخاب کنید:",
                    reply_markup=None
                )
            else:
                try:
                    # Back to parent category
                    category_id = int(back_data)
                    category = db.get_category(category_id)
                    
                    if category:
                        # If parent is None, show top-level categories
                        if category['parent_id'] is None:
                            categories = db.get_categories(
                                parent_id=None, 
                                cat_type=category['type']
                            )
                            
                            await callback_query.message.edit_text(
                                f"گروه‌های {category['type'] == 'product' and 'محصولات' or 'خدمات'}:",
                                reply_markup=categories_keyboard(categories)
                            )
                        else:
                            # Show parent category with its subcategories
                            parent_id = category['parent_id']
                            parent = db.get_category(parent_id)
                            subcategories = db.get_categories(parent_id=parent_id)
                            
                            await callback_query.message.edit_text(
                                f"زیرگروه‌های {parent['name']}:",
                                reply_markup=categories_keyboard(subcategories, parent_id)
                            )
                    else:
                        # Category not found
                        await callback_query.message.edit_text(
                            "خطایی رخ داد. لطفاً دوباره تلاش کنید.",
                            reply_markup=None
                        )
                except ValueError:
                    # Invalid category ID
                    await callback_query.message.edit_text(
                        "خطایی رخ داد. لطفاً دوباره تلاش کنید.",
                        reply_markup=None
                    )
        
        # Handle educational content navigation
        elif data.startswith(EDUCATION_PREFIX):
            edu_data = data[len(EDUCATION_PREFIX):]
            
            if edu_data == "categories":
                # Show all educational categories
                categories = db.get_educational_categories()
                
                if categories:
                    await callback_query.message.edit_text(
                        "دسته‌بندی‌های مطالب آموزشی:",
                        reply_markup=education_categories_keyboard(categories)
                    )
                else:
                    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text=BACK_BTN, callback_data=f"{BACK_PREFIX}main")]
                    ])
                    await callback_query.message.edit_text(
                        "هنوز مطلب آموزشی ثبت نشده است.",
                        reply_markup=keyboard
                    )
            elif edu_data.startswith("cat_"):
                # Show content in a specific category
                category = edu_data[4:]
                contents = db.get_all_educational_content(category)
                
                if contents:
                    await callback_query.message.edit_text(
                        f"مطالب آموزشی دسته {category}:",
                        reply_markup=education_content_keyboard(contents, category)
                    )
                else:
                    await callback_query.message.edit_text(
                        f"هیچ مطلبی در دسته {category} یافت نشد.",
                        reply_markup=education_categories_keyboard(db.get_educational_categories())
                    )
            else:
                try:
                    # Show specific content
                    content_id = int(edu_data)
                    content = db.get_educational_content(content_id)
                    
                    if content:
                        content_text = format_educational_content(content)
                        
                        await callback_query.message.edit_text(
                            content_text,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=education_detail_keyboard(content['category']),
                            disable_web_page_preview=False
                        )
                    else:
                        await callback_query.message.edit_text(
                            "مطلب مورد نظر یافت نشد.",
                            reply_markup=education_categories_keyboard(db.get_educational_categories())
                        )
                except ValueError:
                    # Invalid content ID
                    await callback_query.message.edit_text(
                        "خطایی رخ داد. لطفاً دوباره تلاش کنید.",
                        reply_markup=education_categories_keyboard(db.get_educational_categories())
                    )
        
        # Handle admin actions
        elif data.startswith(ADMIN_PREFIX):
            # Check if user is admin
            if user_id != ADMIN_ID:
                await callback_query.message.edit_text(ADMIN_ACCESS_DENIED)
                return
            
            # TODO: Update admin handlers to use aiogram
            # await admin_handlers.handle_admin_action(callback_query, bot, state)
            await callback_query.message.edit_text("Admin panel is currently being updated to use aiogram.")
    
    except Exception as e:
        logging.error(f"Error in handle_callback_query: {e}")
        await callback_query.message.edit_text(
            ERROR_MESSAGE,
            reply_markup=None
        )

# Inquiry handlers
class handle_inquiry:
    @staticmethod
    async def start_inquiry(callback_query: types.CallbackQuery, state: FSMContext) -> None:
        """Start inquiry process."""
        await callback_query.answer()
        
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        try:
            # Extract product ID from callback data
            product_id = int(data[len(INQUIRY_PREFIX):])
            product = db.get_product(product_id)
            
            if not product:
                await callback_query.message.edit_text("محصول مورد نظر یافت نشد.")
                return
            
            # Store product ID in state
            await state.set_state(InquiryForm.name)
            await state.update_data(inquiry_product_id=product_id)
            
            # Send inquiry form message
            await callback_query.message.edit_text(
                f"استعلام قیمت برای محصول/خدمت: {product['name']}\n\n"
                f"{INQUIRY_START}",
                reply_markup=cancel_keyboard()
            )
            
        except Exception as e:
            logging.error(f"Error in start_inquiry: {e}")
            await callback_query.message.edit_text(ERROR_MESSAGE)
    
    @staticmethod
    async def process_name(message: types.Message, state: FSMContext) -> None:
        """Process name input and ask for phone number."""
        user_id = message.from_user.id
        name = message.text
        
        if not name or len(name) < 2:
            await message.reply(
                "لطفاً یک نام معتبر وارد کنید (حداقل 2 کاراکتر):",
                reply_markup=cancel_keyboard()
            )
            return
        
        # Store name in state
        await state.update_data(inquiry_name=name)
        await state.set_state(InquiryForm.phone)
        
        # Ask for phone number
        await message.reply(
            INQUIRY_PHONE,
            reply_markup=cancel_keyboard()
        )
    
    @staticmethod
    async def process_phone(message: types.Message, state: FSMContext) -> None:
        """Process phone input and ask for description."""
        user_id = message.from_user.id
        phone = message.text
        
        if not is_valid_phone_number(phone):
            await message.reply(
                "لطفاً یک شماره تماس معتبر وارد کنید (حداقل 10 رقم):",
                reply_markup=cancel_keyboard()
            )
            return
        
        # Store phone in state
        await state.update_data(inquiry_phone=phone)
        await state.set_state(InquiryForm.description)
        
        # Ask for description
        await message.reply(
            INQUIRY_DESC,
            reply_markup=cancel_keyboard()
        )
    
    @staticmethod
    async def process_description(message: types.Message, state: FSMContext) -> None:
        """Process description and complete inquiry."""
        user_id = message.from_user.id
        description = message.text
        
        if not state:
            await message.reply(ERROR_MESSAGE)
            return
        
        # Get data from state
        data = await state.get_data()
        name = data.get('inquiry_name', '')
        phone = data.get('inquiry_phone', '')
        product_id = data.get('inquiry_product_id')
        
        # Add inquiry to database
        inquiry_id = db.add_inquiry(
            user_id=user_id,
            name=name,
            phone=phone,
            description=description,
            product_id=product_id
        )
        
        # Get product name if available
        product_name = ""
        if product_id:
            product = db.get_product(product_id)
            if product:
                product_name = f"\nمحصول/خدمت: {product['name']}"
        
        # Send confirmation message
        await message.reply(
            f"{INQUIRY_COMPLETE}\n\n"
            f"نام: {name}\n"
            f"شماره تماس: {phone}{product_name}",
            reply_markup=main_menu_keyboard()
        )
        
        # Notify admin if admin ID is set
        if ADMIN_ID:
            inquiry = db.get_inquiry(inquiry_id)
            if inquiry:
                admin_message = format_inquiry_details(inquiry)
                try:
                    bot = message.bot
                    await bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"📣 استعلام قیمت جدید دریافت شد:\n\n{admin_message}",
                        parse_mode=types.ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logging.error(f"Failed to notify admin: {e}")
        
        # Clear state
        await state.clear()
    
    @staticmethod
    async def cancel_inquiry(callback_query: types.CallbackQuery, state: FSMContext) -> None:
        """Cancel inquiry process."""
        await state.clear()
        
        # Answer the callback query
        await callback_query.answer()
        
        # Edit message text
        try:
            await callback_query.message.edit_text(
                "استعلام قیمت لغو شد.",
                reply_markup=None
            )
        except Exception as e:
            logging.error(f"Error in cancel_inquiry: {e}")
            
    @staticmethod
    async def cancel_inquiry_message(message: types.Message, state: FSMContext) -> None:
        """Cancel inquiry process from a message."""
        await state.clear()
        
        await message.reply(
            "استعلام قیمت لغو شد.",
            reply_markup=main_menu_keyboard()
        )

# States for search
class SearchForm(StatesGroup):
    query = State()

# Search handlers
class handle_search:
    @staticmethod
    async def start_search(message: types.Message, state: FSMContext) -> None:
        """Start search process."""
        # Set state for search
        await state.set_state(SearchForm.query)
        
        await message.reply(
            SEARCH_PROMPT,
            reply_markup=cancel_keyboard()
        )
    
    @staticmethod
    async def process_search(message: types.Message, state: FSMContext) -> None:
        """Process search query."""
        query = message.text
        
        if not query or len(query) < 2:
            await message.reply(
                "لطفاً عبارت جستجو را با حداقل 2 کاراکتر وارد کنید:",
                reply_markup=cancel_keyboard()
            )
            return
        
        # Search products
        results = db.search_products(query)
        
        if results:
            await message.reply(
                f"نتایج جستجو برای «{query}»:",
                reply_markup=products_keyboard(results)
            )
        else:
            await message.reply(
                f"هیچ نتیجه‌ای برای «{query}» یافت نشد.",
                reply_markup=main_menu_keyboard()
            )
        
        # Clear state
        await state.clear()
    
    @staticmethod
    async def cancel_search(message: types.Message, state: FSMContext) -> None:
        """Cancel search process."""
        # Clear state
        await state.clear()
            
        await message.reply(
            "جستجو لغو شد.",
            reply_markup=main_menu_keyboard()
        )

# Admin states
class AdminForm(StatesGroup):
    edit_category = State()
    edit_product = State()
    edit_edu = State()
    edit_static = State()
    upload_csv = State()

# Admin handlers
class admin_handlers:
    @staticmethod
    async def start_admin(message: types.Message, state: FSMContext) -> None:
        """Start admin panel."""
        user_id = message.from_user.id
        
        # Check if user is admin
        if user_id != ADMIN_ID:
            await message.reply(ADMIN_ACCESS_DENIED)
            return
        
        # Show admin menu
        await message.reply(
            ADMIN_WELCOME,
            reply_markup=admin_keyboard()
        )
    
    @staticmethod
    async def handle_admin_action(callback_query: types.CallbackQuery, state: FSMContext) -> None:
        """Handle admin actions from inline buttons."""
        data = callback_query.data
        admin_data = data[len(ADMIN_PREFIX):]
        
        # Back to main admin menu
        if admin_data == "back_main":
            await callback_query.message.edit_text(
                ADMIN_WELCOME,
                reply_markup=None
            )
        
        # Manage products - show categories
        elif admin_data == "manage_products":
            categories = db.get_categories(parent_id=None, cat_type='product')
            
            if categories:
                await query.edit_message_text(
                    "مدیریت دسته‌بندی‌های محصولات:",
                    reply_markup=admin_keyboards.admin_categories_keyboard(categories, None, 'product')
                )
            else:
                await query.edit_message_text(
                    "هیچ دسته‌بندی محصولی یافت نشد. دسته‌بندی جدید ایجاد کنید.",
                    reply_markup=admin_keyboards.admin_categories_keyboard([], None, 'product')
                )
        
        # Manage services - show categories
        elif admin_data == "manage_services":
            categories = db.get_categories(parent_id=None, cat_type='service')
            
            if categories:
                await query.edit_message_text(
                    "مدیریت دسته‌بندی‌های خدمات:",
                    reply_markup=admin_keyboards.admin_categories_keyboard(categories, None, 'service')
                )
            else:
                await query.edit_message_text(
                    "هیچ دسته‌بندی خدماتی یافت نشد. دسته‌بندی جدید ایجاد کنید.",
                    reply_markup=admin_keyboards.admin_categories_keyboard([], None, 'service')
                )
        
        # Manage category
        elif admin_data.startswith("cat_"):
            category_id = int(admin_data[4:])
            category = db.get_category(category_id)
            
            if category:
                parent_id = category['parent_id']
                
                await query.edit_message_text(
                    f"مدیریت دسته‌بندی: {category['name']}\n"
                    f"نوع: {category['type'] == 'product' and 'محصول' or 'خدمات'}\n"
                    f"مسیر: {get_category_path(db, category_id)}",
                    reply_markup=admin_keyboards.admin_category_detail_keyboard(category_id, parent_id)
                )
            else:
                await query.edit_message_text(
                    "دسته‌بندی مورد نظر یافت نشد.",
                    reply_markup=None
                )
        
        # Category subcategories
        elif admin_data.startswith("subcats_"):
            category_id = int(admin_data[8:])
            category = db.get_category(category_id)
            
            if category:
                subcategories = db.get_categories(parent_id=category_id)
                
                await query.edit_message_text(
                    f"زیرگروه‌های {category['name']}:",
                    reply_markup=admin_keyboards.admin_categories_keyboard(
                        subcategories, category_id, category['type']
                    )
                )
            else:
                await query.edit_message_text(
                    "دسته‌بندی مورد نظر یافت نشد.",
                    reply_markup=None
                )
        
        # Category products
        elif admin_data.startswith("products_"):
            category_id = int(admin_data[9:])
            category = db.get_category(category_id)
            
            if category:
                products = db.get_products_by_category(category_id)
                
                await query.edit_message_text(
                    f"محصولات/خدمات {category['name']}:",
                    reply_markup=admin_keyboards.admin_products_keyboard(products, category_id)
                )
            else:
                await query.edit_message_text(
                    "دسته‌بندی مورد نظر یافت نشد.",
                    reply_markup=None
                )
        
        # Product detail
        elif admin_data.startswith("product_"):
            product_id = int(admin_data[8:])
            product = db.get_product(product_id)
            
            if product:
                category_id = product['category_id']
                
                product_text = (
                    f"محصول/خدمت: {product['name']}\n"
                    f"قیمت: {format_price(product['price'])}\n"
                    f"توضیحات: {product['description'] or 'بدون توضیحات'}\n"
                    f"تصویر: {product['photo_url'] or 'بدون تصویر'}\n"
                    f"دسته‌بندی: {get_category_path(db, category_id)}"
                )
                
                await query.edit_message_text(
                    product_text,
                    reply_markup=admin_keyboards.admin_product_detail_keyboard(product_id, category_id)
                )
            else:
                await query.edit_message_text(
                    "محصول/خدمت مورد نظر یافت نشد.",
                    reply_markup=None
                )
        
        # Edit category - start conversation
        elif admin_data.startswith("edit_cat_"):
            return await admin_handlers.start_edit_category(update, context)
        
        # Add category - start conversation
        elif admin_data.startswith("add_cat_"):
            return await admin_handlers.start_add_category(update, context)
        
        # Edit product - start conversation
        elif admin_data.startswith("edit_product_"):
            return await admin_handlers.start_edit_product(update, context)
        
        # Add product - start conversation
        elif admin_data.startswith("add_product_"):
            return await admin_handlers.start_add_product(update, context)
        
        # Delete category - confirm
        elif admin_data.startswith("delete_cat_"):
            category_id = int(admin_data[11:])
            category = db.get_category(category_id)
            
            if category:
                await query.edit_message_text(
                    f"آیا از حذف دسته‌بندی «{category['name']}» و تمام زیرگروه‌ها و محصولات آن اطمینان دارید؟",
                    reply_markup=confirm_keyboard("delete_cat", category_id)
                )
            else:
                await query.edit_message_text(
                    "دسته‌بندی مورد نظر یافت نشد.",
                    reply_markup=None
                )
        
        # Delete product - confirm
        elif admin_data.startswith("delete_product_"):
            product_id = int(admin_data[15:])
            product = db.get_product(product_id)
            
            if product:
                await query.edit_message_text(
                    f"آیا از حذف محصول/خدمت «{product['name']}» اطمینان دارید؟",
                    reply_markup=confirm_keyboard("delete_product", product_id)
                )
            else:
                await query.edit_message_text(
                    "محصول/خدمت مورد نظر یافت نشد.",
                    reply_markup=None
                )
        
        # Confirm delete category
        elif admin_data.startswith("confirm_delete_cat_"):
            category_id = int(admin_data[19:])
            category = db.get_category(category_id)
            
            if category:
                parent_id = category['parent_id']
                success = db.delete_category(category_id)
                
                if success:
                    if parent_id is None:
                        # If top-level category, show all categories
                        categories = db.get_categories(parent_id=None, cat_type=category['type'])
                        
                        await query.edit_message_text(
                            f"دسته‌بندی «{category['name']}» با موفقیت حذف شد.",
                            reply_markup=admin_keyboards.admin_categories_keyboard(
                                categories, None, category['type']
                            )
                        )
                    else:
                        # Show parent's subcategories
                        parent = db.get_category(parent_id)
                        subcategories = db.get_categories(parent_id=parent_id)
                        
                        await query.edit_message_text(
                            f"دسته‌بندی «{category['name']}» با موفقیت حذف شد.",
                            reply_markup=admin_keyboards.admin_categories_keyboard(
                                subcategories, parent_id, parent['type']
                            )
                        )
                else:
                    await query.edit_message_text(
                        "خطا در حذف دسته‌بندی. لطفاً دوباره تلاش کنید.",
                        reply_markup=None
                    )
            else:
                await query.edit_message_text(
                    "دسته‌بندی مورد نظر یافت نشد.",
                    reply_markup=None
                )
        
        # Confirm delete product
        elif admin_data.startswith("confirm_delete_product_"):
            product_id = int(admin_data[23:])
            product = db.get_product(product_id)
            
            if product:
                category_id = product['category_id']
                success = db.delete_product(product_id)
                
                if success:
                    # Show category products
                    products = db.get_products_by_category(category_id)
                    
                    await query.edit_message_text(
                        f"محصول/خدمت «{product['name']}» با موفقیت حذف شد.",
                        reply_markup=admin_keyboards.admin_products_keyboard(products, category_id)
                    )
                else:
                    await query.edit_message_text(
                        "خطا در حذف محصول/خدمت. لطفاً دوباره تلاش کنید.",
                        reply_markup=None
                    )
            else:
                await query.edit_message_text(
                    "محصول/خدمت مورد نظر یافت نشد.",
                    reply_markup=None
                )
        
        # Cancel delete
        elif admin_data.startswith("cancel_delete_"):
            if "cat_" in admin_data:
                category_id = int(admin_data.split("_")[-1])
                category = db.get_category(category_id)
                
                if category:
                    await query.edit_message_text(
                        f"حذف دسته‌بندی «{category['name']}» لغو شد.",
                        reply_markup=admin_keyboards.admin_category_detail_keyboard(
                            category_id, category['parent_id']
                        )
                    )
                else:
                    await query.edit_message_text(
                        "دسته‌بندی مورد نظر یافت نشد.",
                        reply_markup=None
                    )
            elif "product_" in admin_data:
                product_id = int(admin_data.split("_")[-1])
                product = db.get_product(product_id)
                
                if product:
                    await query.edit_message_text(
                        f"حذف محصول/خدمت «{product['name']}» لغو شد.",
                        reply_markup=admin_keyboards.admin_product_detail_keyboard(
                            product_id, product['category_id']
                        )
                    )
                else:
                    await query.edit_message_text(
                        "محصول/خدمت مورد نظر یافت نشد.",
                        reply_markup=None
                    )
        
        # Manage educational content
        elif admin_data == "educational":
            contents = db.get_all_educational_content()
            
            await query.edit_message_text(
                "مدیریت مطالب آموزشی:",
                reply_markup=admin_keyboards.admin_educational_keyboard(contents)
            )
        
        # Educational content detail
        elif admin_data.startswith("edu_"):
            content_id = int(admin_data[4:])
            content = db.get_educational_content(content_id)
            
            if content:
                content_text = (
                    f"عنوان: {content['title']}\n"
                    f"دسته‌بندی: {content['category']}\n"
                    f"نوع: {content['type']}\n\n"
                    f"محتوا:\n{content['content']}"
                )
                
                await query.edit_message_text(
                    content_text,
                    reply_markup=admin_keyboards.admin_edu_detail_keyboard(content_id)
                )
            else:
                await query.edit_message_text(
                    "مطلب مورد نظر یافت نشد.",
                    reply_markup=None
                )
        
        # Edit educational content - start conversation
        elif admin_data.startswith("edit_edu_"):
            return await admin_handlers.start_edit_edu(update, context)
        
        # Add educational content - start conversation
        elif admin_data == "add_edu":
            return await admin_handlers.start_add_edu(update, context)
        
        # Delete educational content - confirm
        elif admin_data.startswith("delete_edu_"):
            content_id = int(admin_data[11:])
            content = db.get_educational_content(content_id)
            
            if content:
                await query.edit_message_text(
                    f"آیا از حذف مطلب «{content['title']}» اطمینان دارید؟",
                    reply_markup=confirm_keyboard("delete_edu", content_id)
                )
            else:
                await query.edit_message_text(
                    "مطلب مورد نظر یافت نشد.",
                    reply_markup=None
                )
        
        # Confirm delete educational content
        elif admin_data.startswith("confirm_delete_edu_"):
            content_id = int(admin_data[19:])
            content = db.get_educational_content(content_id)
            
            if content:
                success = db.delete_educational_content(content_id)
                
                if success:
                    # Show all educational content
                    contents = db.get_all_educational_content()
                    
                    await query.edit_message_text(
                        f"مطلب «{content['title']}» با موفقیت حذف شد.",
                        reply_markup=admin_keyboards.admin_educational_keyboard(contents)
                    )
                else:
                    await query.edit_message_text(
                        "خطا در حذف مطلب. لطفاً دوباره تلاش کنید.",
                        reply_markup=None
                    )
            else:
                await query.edit_message_text(
                    "مطلب مورد نظر یافت نشد.",
                    reply_markup=None
                )
        
        # Cancel delete educational content
        elif admin_data.startswith("cancel_delete_edu_"):
            content_id = int(admin_data[19:])
            content = db.get_educational_content(content_id)
            
            if content:
                await query.edit_message_text(
                    f"حذف مطلب «{content['title']}» لغو شد.",
                    reply_markup=admin_keyboards.admin_edu_detail_keyboard(content_id)
                )
            else:
                await query.edit_message_text(
                    "مطلب مورد نظر یافت نشد.",
                    reply_markup=None
                )
        
        # Manage inquiries
        elif admin_data == "inquiries":
            inquiries = db.get_inquiries()
            
            if inquiries:
                await query.edit_message_text(
                    "استعلام‌های دریافت شده:",
                    reply_markup=admin_keyboards.admin_inquiries_keyboard(inquiries)
                )
            else:
                await query.edit_message_text(
                    "هیچ استعلامی یافت نشد.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_main")
                    ]])
                )
        
        # Inquiry detail
        elif admin_data.startswith("inquiry_"):
            inquiry_id = int(admin_data[8:])
            inquiry = db.get_inquiry(inquiry_id)
            
            if inquiry:
                inquiry_text = format_inquiry_details(inquiry)
                
                await query.edit_message_text(
                    inquiry_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}inquiries")
                    ]])
                )
            else:
                await query.edit_message_text(
                    "استعلام مورد نظر یافت نشد.",
                    reply_markup=None
                )
        
        # Filter inquiries - not implemented yet
        elif admin_data == "filter_inquiries":
            await query.edit_message_text(
                "این قابلیت هنوز پیاده‌سازی نشده است.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}inquiries")
                ]])
            )
        
        # Export inquiries to CSV
        elif admin_data == "export_inquiries":
            # Create CSV file in temp directory
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
                temp_path = temp_file.name
            
            success = db.export_to_csv('inquiries', temp_path)
            
            if success:
                # Send CSV file
                with open(temp_path, 'rb') as file:
                    await context.bot.send_document(
                        chat_id=update.effective_user.id,
                        document=file,
                        filename='inquiries.csv',
                        caption="خروجی CSV استعلام‌ها"
                    )
                
                # Delete temp file
                os.unlink(temp_path)
                
                await query.edit_message_text(
                    "خروجی CSV استعلام‌ها با موفقیت ارسال شد.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}inquiries")
                    ]])
                )
            else:
                await query.edit_message_text(
                    "خطا در ایجاد خروجی CSV. لطفاً دوباره تلاش کنید.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}inquiries")
                    ]])
                )
        
        # Manage static content
        elif admin_data == "static_content":
            await query.edit_message_text(
                "مدیریت صفحات ثابت:",
                reply_markup=admin_keyboards.admin_static_keyboard()
            )
        
        # Edit static content - start conversation
        elif admin_data.startswith("edit_static_"):
            return await admin_handlers.start_edit_static(update, context)
        
        # Export menu
        elif admin_data == "export":
            await query.edit_message_text(
                "انتخاب داده برای خروجی CSV:",
                reply_markup=admin_keyboards.admin_export_keyboard()
            )
        
        # Export to CSV
        elif admin_data.startswith("export_"):
            entity_type = admin_data[7:]
            
            # Create CSV file in temp directory
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
                temp_path = temp_file.name
            
            success = db.export_to_csv(entity_type, temp_path)
            
            if success:
                # Send CSV file
                with open(temp_path, 'rb') as file:
                    await context.bot.send_document(
                        chat_id=update.effective_user.id,
                        document=file,
                        filename=f'{entity_type}.csv',
                        caption=f"خروجی CSV {entity_type}"
                    )
                
                # Delete temp file
                os.unlink(temp_path)
                
                await query.edit_message_text(
                    f"خروجی CSV {entity_type} با موفقیت ارسال شد.",
                    reply_markup=admin_keyboards.admin_export_keyboard()
                )
            else:
                await query.edit_message_text(
                    "خطا در ایجاد خروجی CSV. لطفاً دوباره تلاش کنید.",
                    reply_markup=admin_keyboards.admin_export_keyboard()
                )
        
        # Import menu
        elif admin_data == "import":
            await query.edit_message_text(
                "انتخاب داده برای ورود از CSV:",
                reply_markup=admin_keyboards.admin_import_keyboard()
            )
        
        # Import from CSV - start conversation
        elif admin_data.startswith("import_"):
            return await admin_handlers.start_import_data(update, context)
        
        # Generate CSV template
        elif admin_data.startswith("template_"):
            entity_type = admin_data[9:]
            
            # Create CSV file in temp directory
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
                temp_path = temp_file.name
            
            success = generate_csv_template(temp_path, entity_type)
            
            if success:
                # Send CSV file
                with open(temp_path, 'rb') as file:
                    await context.bot.send_document(
                        chat_id=update.effective_user.id,
                        document=file,
                        filename=f'{entity_type}_template.csv',
                        caption=f"قالب CSV {entity_type}"
                    )
                
                # Delete temp file
                os.unlink(temp_path)
                
                await query.edit_message_text(
                    f"قالب CSV {entity_type} با موفقیت ارسال شد.",
                    reply_markup=admin_keyboards.admin_import_keyboard()
                )
            else:
                await query.edit_message_text(
                    "خطا در ایجاد قالب CSV. لطفاً دوباره تلاش کنید.",
                    reply_markup=admin_keyboards.admin_import_keyboard()
                )
        
        return None  # No conversation started
    
    @staticmethod
    async def start_edit_category(callback_query: types.CallbackQuery, state: FSMContext) -> None:
        """Start editing a category."""
        await callback_query.answer()
        
        user_id = callback_query.from_user.id
        data = callback_query.data
        category_id = int(data[len(ADMIN_PREFIX + "edit_cat_"):])
        
        category = db.get_category(category_id)
        if not category:
            await callback_query.message.edit_text("دسته‌بندی مورد نظر یافت نشد.")
            return
        
        # Store category ID and current data in state
        await state.set_state(AdminActions.edit_category)
        await state.update_data(
            edit_category_id=category_id,
            edit_category_name=category['name'],
            edit_category_type=category['type'],
            edit_category_parent_id=category['parent_id']
        )
        
        # Send edit form
        await callback_query.message.edit_text(
            f"ویرایش دسته‌بندی «{category['name']}»\n\n"
            f"لطفاً نام جدید را وارد کنید:",
            reply_markup=cancel_keyboard()
        )
    
    @staticmethod
    async def process_edit_category(message: types.Message, state: FSMContext) -> None:
        """Process category edit."""
        user_id = message.from_user.id
        name = message.text
        
        # Get data from state
        data = await state.get_data()
        category_id = data.get('edit_category_id')
        parent_id = data.get('edit_category_parent_id')
        cat_type = data.get('edit_category_type')
        
        if not category_id:
            await message.reply(ERROR_MESSAGE)
            await state.clear()
            return
        
        # Update category
        success = db.update_category(
            category_id=category_id,
            name=name,
            parent_id=parent_id,
            cat_type=cat_type
        )
        
        if success:
            category = db.get_category(category_id)
            
            await message.reply(
                f"دسته‌بندی با موفقیت به «{name}» تغییر نام یافت.",
                reply_markup=admin_keyboard()
            )
            
            # Send updated category detail
            if category:
                await message.reply(
                    f"اطلاعات دسته‌بندی:\n"
                    f"نام: {category['name']}\n"
                    f"نوع: {category['type'] == 'product' and 'محصول' or 'خدمات'}\n"
                    f"مسیر: {get_category_path(db, category_id)}",
                    # Note: we need to implement the admin_keyboards class or update the imports
                    reply_markup=None  # We'll update this later
                )
        else:
            await message.reply(
                "خطا در ویرایش دسته‌بندی. لطفاً دوباره تلاش کنید.",
                reply_markup=admin_keyboard()
            )
        
        # Clear state
        await state.clear()
    
    @staticmethod
    async def start_add_category(callback_query: types.CallbackQuery, state: FSMContext) -> None:
        """Start adding a new category."""
        await callback_query.answer()
        
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        # Extract parent ID and type
        parts = data[len(ADMIN_PREFIX + "add_cat_"):].split("_")
        parent_id = int(parts[0]) if parts[0] != "0" else None
        cat_type = parts[1]
        
        # Store data in state
        await state.set_state(AdminActions.edit_category)  # We can reuse the edit state for adding
        await state.update_data(
            add_category_parent_id=parent_id,
            add_category_type=cat_type
        )
        
        # Send add form
        parent_info = ""
        if parent_id is not None:
            parent = db.get_category(parent_id)
            if parent:
                parent_info = f"\nدسته‌بندی والد: {parent['name']}"
        
        await callback_query.message.edit_text(
            f"افزودن دسته‌بندی جدید{parent_info}\n\n"
            f"لطفاً نام دسته‌بندی را وارد کنید:",
            reply_markup=cancel_keyboard()
        )
    
    @staticmethod
    async def process_add_category(message: types.Message, state: FSMContext) -> None:
        """Process new category addition."""
        user_id = message.from_user.id
        name = message.text
        
        # Get data from state
        data = await state.get_data()
        parent_id = data.get('add_category_parent_id')
        cat_type = data.get('add_category_type')
        
        if not cat_type:
            await message.reply(ERROR_MESSAGE)
            await state.clear()
            return
        
        # Add category
        category_id = db.add_category(
            name=name,
            parent_id=parent_id,
            cat_type=cat_type
        )
        
        if category_id:
            await message.reply(
                f"دسته‌بندی «{name}» با موفقیت ایجاد شد.",
                reply_markup=admin_keyboard()
            )
            
            # If parent exists, show updated subcategories
            if parent_id is not None:
                parent = db.get_category(parent_id)
                if parent:
                    subcategories = db.get_categories(parent_id=parent_id)
                    
                    await message.reply(
                        f"زیرگروه‌های {parent['name']}:",
                        # Note: we need to implement the admin_keyboards class or update the imports
                        reply_markup=None  # We'll update this later
                    )
            else:
                # Show all top-level categories
                categories = db.get_categories(parent_id=None, cat_type=cat_type)
                
                await message.reply(
                    f"دسته‌بندی‌های {cat_type == 'product' and 'محصولات' or 'خدمات'}:",
                    # Note: we need to implement the admin_keyboards class or update the imports
                    reply_markup=None  # We'll update this later
                )
        else:
            await message.reply(
                "خطا در ایجاد دسته‌بندی. لطفاً دوباره تلاش کنید.",
                reply_markup=admin_keyboard()
            )
        
        # Clear state
        await state.clear()
    
    @staticmethod
    async def start_edit_product(callback_query: types.CallbackQuery, state: FSMContext) -> None:
        """Start editing a product."""
        await callback_query.answer()
        
        user_id = callback_query.from_user.id
        data = callback_query.data
        product_id = int(data[len(ADMIN_PREFIX + "edit_product_"):])
        
        product = db.get_product(product_id)
        if not product:
            await callback_query.message.edit_text("محصول/خدمت مورد نظر یافت نشد.")
            return
        
        # Store product ID and current data in state
        await state.set_state(AdminActions.edit_product)
        await state.update_data(
            edit_product_id=product_id,
            edit_product_name=product['name'],
            edit_product_price=product['price'],
            edit_product_description=product['description'],
            edit_product_photo_url=product['photo_url'],
            edit_product_category_id=product['category_id'],
            edit_product_step=0  # 0: name, 1: price, 2: description, 3: photo_url
        )
        
        # Send edit form - start with name
        await callback_query.message.edit_text(
            f"ویرایش محصول/خدمت «{product['name']}»\n\n"
            f"مرحله 1/4: لطفاً نام جدید را وارد کنید (یا 'skip' برای رد کردن):",
            reply_markup=cancel_keyboard()
        )
    
    @staticmethod
    async def process_edit_product(message: types.Message, state: FSMContext) -> None:
        """Process product edit, step by step."""
        user_id = message.from_user.id
        text = message.text
        
        # Get data from state
        data = await state.get_data()
        product_id = data.get('edit_product_id')
        step = data.get('edit_product_step', 0)
        
        if not product_id:
            await message.reply(ERROR_MESSAGE)
            await state.clear()
            return
        
        # Process current step
        if step == 0:  # Name
            edit_product_name = data.get('edit_product_name')
            if text.lower() != 'skip':
                edit_product_name = text
            
            # Move to price
            await state.update_data(
                edit_product_name=edit_product_name,
                edit_product_step=1
            )
            
            await message.reply(
                f"مرحله 2/4: لطفاً قیمت جدید را به عدد وارد کنید (یا 'skip' برای رد کردن):",
                reply_markup=cancel_keyboard()
            )
            
        elif step == 1:  # Price
            edit_product_price = data.get('edit_product_price')
            if text.lower() != 'skip':
                try:
                    price = int(text.replace(',', ''))
                    edit_product_price = price
                except ValueError:
                    await message.reply(
                        "لطفاً یک عدد معتبر وارد کنید (یا 'skip' برای رد کردن):",
                        reply_markup=cancel_keyboard()
                    )
                    return
            
            # Move to description
            await state.update_data(
                edit_product_price=edit_product_price,
                edit_product_step=2
            )
            
            await message.reply(
                f"مرحله 3/4: لطفاً توضیحات جدید را وارد کنید (یا 'skip' برای رد کردن):",
                reply_markup=cancel_keyboard()
            )
            
        elif step == 2:  # Description
            edit_product_description = data.get('edit_product_description')
            if text.lower() != 'skip':
                edit_product_description = text
            
            # Move to photo URL
            await state.update_data(
                edit_product_description=edit_product_description,
                edit_product_step=3
            )
            
            await message.reply(
                f"مرحله 4/4: لطفاً آدرس عکس جدید را وارد کنید (یا 'skip' برای رد کردن یا 'none' برای حذف):",
                reply_markup=cancel_keyboard()
            )
            
        elif step == 3:  # Photo URL
            edit_product_photo_url = data.get('edit_product_photo_url')
            if text.lower() == 'none':
                edit_product_photo_url = None
            elif text.lower() != 'skip':
                edit_product_photo_url = text
            
            # Get all values from state
            edit_product_name = data.get('edit_product_name')
            edit_product_price = data.get('edit_product_price')
            edit_product_description = data.get('edit_product_description')
            edit_product_category_id = data.get('edit_product_category_id')
            
            # Update product
            success = db.update_product(
                product_id=product_id,
                name=edit_product_name,
                price=edit_product_price,
                description=edit_product_description,
                photo_url=edit_product_photo_url,
                category_id=edit_product_category_id
            )
            
            if success:
                product = db.get_product(product_id)
                
                await message.reply(
                    f"محصول/خدمت «{edit_product_name}» با موفقیت به‌روزرسانی شد.",
                    reply_markup=admin_keyboard()
                )
                
                # Send updated product detail
                if product:
                    product_text = (
                        f"محصول/خدمت: {product['name']}\n"
                        f"قیمت: {format_price(product['price'])}\n"
                        f"توضیحات: {product['description'] or 'بدون توضیحات'}\n"
                        f"تصویر: {product['photo_url'] or 'بدون تصویر'}\n"
                        f"دسته‌بندی: {get_category_path(db, edit_product_category_id)}"
                    )
                    
                    await message.reply(
                        product_text,
                        reply_markup=admin_keyboards.admin_product_detail_keyboard(product_id, edit_product_category_id)
                    )
            else:
                await message.reply(
                    "خطا در به‌روزرسانی محصول/خدمت. لطفاً دوباره تلاش کنید.",
                    reply_markup=admin_keyboard()
                )
            
            # Clear state
            await state.clear()
    
    @staticmethod
    async def start_add_product(callback_query: types.CallbackQuery, state: FSMContext) -> None:
        """Start adding a new product."""
        await callback_query.answer()
        
        user_id = callback_query.from_user.id
        data = callback_query.data
        category_id = int(data[len(ADMIN_PREFIX + "add_product_"):])
        
        category = db.get_category(category_id)
        if not category:
            await callback_query.message.edit_text("دسته‌بندی مورد نظر یافت نشد.")
            return
        
        # Store data in state
        await state.set_state(AdminActions.add_product)
        await state.update_data(
            add_product_category_id=category_id,
            add_product_step=0  # 0: name, 1: price, 2: description, 3: photo_url
        )
        
        # Send add form - start with name
        await callback_query.message.edit_text(
            f"افزودن محصول/خدمت جدید به دسته‌بندی «{category['name']}»\n\n"
            f"مرحله 1/4: لطفاً نام را وارد کنید:",
            reply_markup=cancel_keyboard()
        )
    
    @staticmethod
    async def process_add_product(message: types.Message, state: FSMContext) -> None:
        """Process new product addition, step by step."""
        user_id = message.from_user.id
        text = message.text
        
        # Get data from state
        data = await state.get_data()
        add_product_step = data.get('add_product_step', 0)
        category_id = data.get('add_product_category_id')
        
        if not category_id:
            await message.reply(ERROR_MESSAGE)
            await state.clear()
            return
        
        # Process current step
        if add_product_step == 0:  # Name
            # Store name and move to price
            await state.update_data(
                add_product_name=text,
                add_product_step=1
            )
            
            await message.reply(
                f"مرحله 2/4: لطفاً قیمت را به عدد وارد کنید:",
                reply_markup=cancel_keyboard()
            )
            
        elif add_product_step == 1:  # Price
            try:
                price = int(text.replace(',', ''))
                
                # Store price and move to description
                await state.update_data(
                    add_product_price=price,
                    add_product_step=2
                )
                
                await message.reply(
                    f"مرحله 3/4: لطفاً توضیحات را وارد کنید (یا 'none' برای خالی گذاشتن):",
                    reply_markup=cancel_keyboard()
                )
            except ValueError:
                await message.reply(
                    "لطفاً یک عدد معتبر وارد کنید:",
                    reply_markup=cancel_keyboard()
                )
            
        elif add_product_step == 2:  # Description
            description = None if text.lower() == 'none' else text
            
            # Store description and move to photo URL
            await state.update_data(
                add_product_description=description,
                add_product_step=3
            )
            
            await message.reply(
                f"مرحله 4/4: لطفاً آدرس عکس را وارد کنید (یا 'none' برای بدون عکس):",
                reply_markup=cancel_keyboard()
            )
            
        elif add_product_step == 3:  # Photo URL
            photo_url = None if text.lower() == 'none' else text
            
            # Get all data from state
            data = await state.get_data()
            name = data.get('add_product_name', '')
            price = data.get('add_product_price', 0)
            description = data.get('add_product_description')
            
            # Add product
            product_id = db.add_product(
                name=name,
                price=price,
                description=description,
                photo_url=photo_url,
                category_id=category_id
            )
            
            if product_id:
                await message.reply(
                    f"محصول/خدمت «{name}» با موفقیت ایجاد شد.",
                    reply_markup=admin_keyboard()
                )
                
                # Show category products
                category = db.get_category(category_id)
                if category:
                    products = db.get_products_by_category(category_id)
                    
                    await message.reply(
                        f"محصولات/خدمات {category['name']}:",
                        reply_markup=admin_keyboards.admin_products_keyboard(products, category_id)
                    )
            else:
                await message.reply(
                    "خطا در ایجاد محصول/خدمت. لطفاً دوباره تلاش کنید.",
                    reply_markup=admin_keyboard()
                )
            
            # Clear state
            await state.clear()
    
    @staticmethod
    async def start_edit_edu(callback_query: types.CallbackQuery, state: FSMContext) -> None:
        """Start editing educational content."""
        await callback_query.answer()
        
        user_id = callback_query.from_user.id
        data = callback_query.data
        content_id = int(data[len(ADMIN_PREFIX + "edit_edu_"):])
        
        content = db.get_educational_content(content_id)
        if not content:
            await callback_query.message.edit_text("مطلب مورد نظر یافت نشد.")
            return
        
        # Store content ID and current data in state
        await state.set_state(AdminActions.edit_edu)
        await state.update_data(
            edit_edu_id=content_id,
            edit_edu_title=content['title'],
            edit_edu_content=content['content'],
            edit_edu_category=content['category'],
            edit_edu_type=content['type'],
            edit_edu_step=0  # 0: title, 1: content, 2: category, 3: type
        )
        
        # Send edit form - start with title
        await callback_query.message.edit_text(
            f"ویرایش مطلب «{content['title']}»\n\n"
            f"مرحله 1/4: لطفاً عنوان جدید را وارد کنید (یا 'skip' برای رد کردن):",
            reply_markup=cancel_keyboard()
        )
    
    @staticmethod
    async def process_edit_edu(message: types.Message, state: FSMContext) -> None:
        """Process educational content edit, step by step."""
        user_id = message.from_user.id
        text = message.text
        
        # Get data from state
        data = await state.get_data()
        content_id = data.get('edit_edu_id')
        step = data.get('edit_edu_step', 0)
        
        if not content_id:
            await message.reply(ERROR_MESSAGE)
            await state.clear()
            return
        
        # Process current step
        if step == 0:  # Title
            # Update title if not skipped
            if text.lower() != 'skip':
                await state.update_data(edit_edu_title=text)
            
            # Move to content step
            await state.update_data(edit_edu_step=1)
            
            await message.reply(
                f"مرحله 2/4: لطفاً محتوای جدید را وارد کنید (یا 'skip' برای رد کردن):",
                reply_markup=cancel_keyboard()
            )
            
        elif step == 1:  # Content
            # Update content if not skipped
            if text.lower() != 'skip':
                await state.update_data(edit_edu_content=text)
            
            # Move to category step
            await state.update_data(edit_edu_step=2)
            
            await message.reply(
                f"مرحله 3/4: لطفاً دسته‌بندی جدید را وارد کنید (یا 'skip' برای رد کردن):",
                reply_markup=cancel_keyboard()
            )
            
        elif step == 2:  # Category
            # Update category if not skipped
            if text.lower() != 'skip':
                await state.update_data(edit_edu_category=text)
            
            # Move to type step
            await state.update_data(edit_edu_step=3)
            
            await message.reply(
                f"مرحله 4/4: لطفاً نوع محتوا را وارد کنید (text یا link) (یا 'skip' برای رد کردن):",
                reply_markup=cancel_keyboard()
            )
            
        elif step == 3:  # Type
            # Update content type if not skipped
            if text.lower() != 'skip':
                content_type = text.lower()
                if content_type not in ['text', 'link']:
                    await message.reply(
                        "لطفاً یکی از انواع معتبر (text یا link) را وارد کنید:",
                        reply_markup=cancel_keyboard()
                    )
                    return
                await state.update_data(edit_edu_type=content_type)
            
            # Get final data from state
            data = await state.get_data()
            title = data.get('edit_edu_title')
            content = data.get('edit_edu_content')
            category = data.get('edit_edu_category')
            content_type = data.get('edit_edu_type')
            
            # Update database record
            success = db.update_educational_content(
                content_id=content_id,
                title=title,
                content=content,
                category=category,
                content_type=content_type
            )
            
            if success:
                edu_content = db.get_educational_content(content_id)
                
                await message.reply(
                    f"مطلب «{title}» با موفقیت به‌روزرسانی شد.",
                    reply_markup=admin_keyboard()
                )
                
                # Send updated content detail
                if edu_content:
                    content_text = (
                        f"عنوان: {edu_content['title']}\n"
                        f"دسته‌بندی: {edu_content['category']}\n"
                        f"نوع: {edu_content['type']}\n\n"
                        f"محتوا:\n{edu_content['content']}"
                    )
                    
                    await message.reply(
                        content_text,
                        reply_markup=admin_keyboards.admin_edu_detail_keyboard(content_id)
                    )
            else:
                await message.reply(
                    "خطا در به‌روزرسانی مطلب. لطفاً دوباره تلاش کنید.",
                    reply_markup=admin_keyboard()
                )
            
            # Clear state
            await state.clear()
    
    @staticmethod
    async def start_add_edu(callback_query: types.CallbackQuery, state: FSMContext) -> None:
        """Start adding new educational content."""
        await callback_query.answer()
        
        # Set state and initialize step
        await state.set_state(AdminActions.add_edu)
        await state.update_data(add_edu_step=0)  # 0: title, 1: content, 2: category, 3: type
        
        # Send add form - start with title
        await callback_query.message.edit_text(
            f"افزودن مطلب آموزشی جدید\n\n"
            f"مرحله 1/4: لطفاً عنوان را وارد کنید:",
            reply_markup=cancel_keyboard()
        )
    
    @staticmethod
    async def process_add_edu(message: types.Message, state: FSMContext) -> None:
        """Process new educational content addition, step by step."""
        user_id = message.from_user.id
        text = message.text
        
        # Get data from state
        data = await state.get_data()
        step = data.get('add_edu_step', 0)
        
        # Process current step
        if step == 0:  # Title
            # Store title and move to content step
            await state.update_data(add_edu_title=text, add_edu_step=1)
            
            await message.reply(
                f"مرحله 2/4: لطفاً محتوا را وارد کنید:",
                reply_markup=cancel_keyboard()
            )
            
        elif step == 1:  # Content
            # Store content and move to category step
            await state.update_data(add_edu_content=text, add_edu_step=2)
            
            # Show existing categories as suggestions
            categories = db.get_educational_categories()
            category_list = "\n".join([f"- {cat}" for cat in categories]) if categories else "هنوز دسته‌بندی ثبت نشده است."
            
            await message.reply(
                f"مرحله 3/4: لطفاً دسته‌بندی را وارد کنید:\n\n"
                f"دسته‌بندی‌های موجود:\n{category_list}",
                reply_markup=cancel_keyboard()
            )
            
        elif step == 2:  # Category
            # Store category and move to type step
            await state.update_data(add_edu_category=text, add_edu_step=3)
            
            await message.reply(
                f"مرحله 4/4: لطفاً نوع محتوا را وارد کنید (text یا link):",
                reply_markup=cancel_keyboard()
            )
            
        elif step == 3:  # Type
            content_type = text.lower()
            if content_type not in ['text', 'link']:
                await message.reply(
                    "لطفاً یکی از انواع معتبر (text یا link) را وارد کنید:",
                    reply_markup=cancel_keyboard()
                )
                return
            
            # Get all data from state
            data = await state.get_data()
            title = data.get('add_edu_title')
            content = data.get('add_edu_content')
            category = data.get('add_edu_category')
            
            # Add the educational content
            content_id = db.add_educational_content(
                title=title,
                content=content,
                category=category,
                content_type=content_type
            )
            
            if content_id:
                await message.reply(
                    f"مطلب «{title}» با موفقیت ایجاد شد.",
                    reply_markup=admin_keyboard()
                )
                
                # Show all educational content
                contents = db.get_all_educational_content()
                
                await message.reply(
                    "مدیریت مطالب آموزشی:",
                    reply_markup=admin_keyboards.admin_educational_keyboard(contents)
                )
            else:
                await message.reply(
                    "خطا در ایجاد مطلب. لطفاً دوباره تلاش کنید.",
                    reply_markup=admin_keyboard()
                )
            
            # Clear state
            await state.clear()
    
    @staticmethod
    async def start_edit_static(callback_query: types.CallbackQuery, state: FSMContext) -> None:
        """Start editing static content."""
        await callback_query.answer()
        
        data = callback_query.data
        content_type = data[len(ADMIN_PREFIX + "edit_static_"):]
        
        if content_type not in ['contact', 'about']:
            await callback_query.message.edit_text("نوع محتوا نامعتبر است.")
            return
        
        content = db.get_static_content(content_type)
        
        # Set state and store type and current content
        await state.set_state(AdminActions.edit_static)
        await state.update_data(edit_static_type=content_type, edit_static_content=content)
        
        # Send edit form
        title = "تماس با ما" if content_type == 'contact' else "درباره ما"
        await callback_query.message.edit_text(
            f"ویرایش {title}\n\n"
            f"محتوای فعلی:\n{content}\n\n"
            f"لطفاً محتوای جدید را وارد کنید:",
            reply_markup=cancel_keyboard()
        )
    
    @staticmethod
    async def process_edit_static(message: types.Message, state: FSMContext) -> None:
        """Process static content edit."""
        text = message.text
        
        # Get data from state
        data = await state.get_data()
        content_type = data.get('edit_static_type')
        
        if not content_type:
            await message.reply(ERROR_MESSAGE)
            await state.clear()
            return
        
        # Update static content
        success = db.update_static_content(content_type, text)
        
        if success:
            title = "تماس با ما" if content_type == 'contact' else "درباره ما"
            await message.reply(
                f"محتوای {title} با موفقیت به‌روزرسانی شد.",
                reply_markup=admin_keyboard()
            )
            
            # Show updated content
            await message.reply(
                f"محتوای جدید {title}:\n\n{text}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}static_content")
                ]])
            )
        else:
            await message.reply(
                "خطا در به‌روزرسانی محتوا. لطفاً دوباره تلاش کنید.",
                reply_markup=admin_keyboard()
            )
        
        # Clear state
        await state.clear()
    
    @staticmethod
    async def start_import_data(callback_query: types.CallbackQuery, state: FSMContext) -> None:
        """Start importing data from CSV."""
        await callback_query.answer()
        
        data = callback_query.data
        entity_type = data[len(ADMIN_PREFIX + "import_"):]
        
        if entity_type not in ['products', 'categories', 'educational']:
            await callback_query.message.edit_text("نوع داده نامعتبر است.")
            await state.clear()
            return
        
        # Set state and store entity type
        await state.set_state(AdminActions.upload_csv)
        await state.update_data(import_entity_type=entity_type)
        
        # Send instruction
        await callback_query.message.edit_text(
            f"ورود داده‌های {entity_type} از فایل CSV\n\n"
            f"لطفاً فایل CSV را آپلود کنید.\n"
            f"توجه: فایل باید شامل ستون‌های مناسب باشد.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("دریافت قالب", callback_data=f"{ADMIN_PREFIX}template_{entity_type}"),
                InlineKeyboardButton("انصراف", callback_data="cancel")
            ]])
        )
    
    @staticmethod
    async def process_import_data(message: types.Message, state: FSMContext, bot: Bot) -> None:
        """Process CSV import."""
        file = message.document
        
        # Get entity type from state
        data = await state.get_data()
        entity_type = data.get('import_entity_type')
        
        if not entity_type:
            await message.reply(ERROR_MESSAGE)
            await state.clear()
            return
        
        # Download file
        file_info = await bot.get_file(file.file_id)
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            temp_path = temp_file.name
        
        await bot.download_file(file_info.file_path, temp_path)
        
        # Import data
        success_count, error_count = db.import_from_csv(entity_type, temp_path)
        
        # Delete temp file
        os.unlink(temp_path)
        
        # Send result
        await message.reply(
            f"نتیجه ورود داده‌ها:\n"
            f"تعداد موارد موفق: {success_count}\n"
            f"تعداد خطاها: {error_count}",
            reply_markup=admin_keyboard()
        )
        
        # Clear state
        await state.clear()
    
    @staticmethod
    async def cancel_admin_action(message_or_callback, state: FSMContext = None) -> None:
        """Cancel admin action.
        
        Can be called from either a message handler or a callback query handler.
        """
        # Check if it's a callback query or a message
        if isinstance(message_or_callback, types.CallbackQuery):
            await message_or_callback.answer()
            await message_or_callback.message.edit_text(
                "عملیات لغو شد.",
                reply_markup=None
            )
        else:  # It's a Message
            await message_or_callback.reply(
                "عملیات لغو شد.",
                reply_markup=admin_keyboard()
            )
        
        # Clear state if provided
        if state:
            await state.clear()

# Admin keyboard utilities (defined here to avoid circular imports)
class admin_keyboards:
    @staticmethod
    def admin_categories_keyboard(categories: List[Dict], parent_id: Optional[int] = None, 
                                 entity_type: str = 'product') -> InlineKeyboardMarkup:
        """Create keyboard for admin category management."""
        keyboard = []
        
        # Add category buttons
        for category in categories:
            callback_data = f"{ADMIN_PREFIX}cat_{category['id']}"
            keyboard.append([InlineKeyboardButton(category['name'], callback_data=callback_data)])
        
        # Add action buttons
        keyboard.append([
            InlineKeyboardButton("➕ افزودن", callback_data=f"{ADMIN_PREFIX}add_cat_{parent_id or 0}_{entity_type}"),
        ])
        
        # Add back button
        if parent_id is None:
            # Back to admin menu
            keyboard.append([InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_main")])
        else:
            # Back to parent category
            keyboard.append([InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}cat_{parent_id}")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_category_detail_keyboard(category_id: int, parent_id: Optional[int] = None) -> InlineKeyboardMarkup:
        """Create keyboard for admin category detail."""
        keyboard = [
            [
                InlineKeyboardButton("✏️ ویرایش", callback_data=f"{ADMIN_PREFIX}edit_cat_{category_id}"),
                InlineKeyboardButton("❌ حذف", callback_data=f"{ADMIN_PREFIX}delete_cat_{category_id}")
            ],
            [
                InlineKeyboardButton("📝 محصولات", callback_data=f"{ADMIN_PREFIX}products_{category_id}"),
                InlineKeyboardButton("📁 زیرگروه‌ها", callback_data=f"{ADMIN_PREFIX}subcats_{category_id}")
            ]
        ]
        
        # Add back button
        if parent_id is None:
            keyboard.append([InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_main")])
        else:
            keyboard.append([InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}cat_{parent_id}")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_products_keyboard(products: List[Dict], category_id: int) -> InlineKeyboardMarkup:
        """Create keyboard for admin product management."""
        keyboard = []
        
        # Add product buttons
        for product in products:
            callback_data = f"{ADMIN_PREFIX}product_{product['id']}"
            keyboard.append([InlineKeyboardButton(product['name'], callback_data=callback_data)])
        
        # Add action buttons
        keyboard.append([
            InlineKeyboardButton("➕ افزودن", callback_data=f"{ADMIN_PREFIX}add_product_{category_id}"),
        ])
        
        # Add back button
        keyboard.append([InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}cat_{category_id}")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_product_detail_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:
        """Create keyboard for admin product detail."""
        keyboard = [
            [
                InlineKeyboardButton("✏️ ویرایش", callback_data=f"{ADMIN_PREFIX}edit_product_{product_id}"),
                InlineKeyboardButton("❌ حذف", callback_data=f"{ADMIN_PREFIX}delete_product_{product_id}")
            ],
            [InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}products_{category_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_educational_keyboard(contents: List[Dict]) -> InlineKeyboardMarkup:
        """Create keyboard for admin educational content management."""
        keyboard = []
        
        # Add content buttons
        for content in contents:
            callback_data = f"{ADMIN_PREFIX}edu_{content['id']}"
            keyboard.append([InlineKeyboardButton(content['title'], callback_data=callback_data)])
        
        # Add action buttons
        keyboard.append([
            InlineKeyboardButton("➕ افزودن", callback_data=f"{ADMIN_PREFIX}add_edu"),
        ])
        
        # Add back button
        keyboard.append([InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_main")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_edu_detail_keyboard(content_id: int) -> InlineKeyboardMarkup:
        """Create keyboard for admin educational content detail."""
        keyboard = [
            [
                InlineKeyboardButton("✏️ ویرایش", callback_data=f"{ADMIN_PREFIX}edit_edu_{content_id}"),
                InlineKeyboardButton("❌ حذف", callback_data=f"{ADMIN_PREFIX}delete_edu_{content_id}")
            ],
            [InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}educational")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_inquiries_keyboard(inquiries: List[Dict]) -> InlineKeyboardMarkup:
        """Create keyboard for admin inquiries management."""
        keyboard = []
        
        # Add inquiry buttons (limited to 10)
        for i, inquiry in enumerate(inquiries[:10]):
            name = inquiry['name']
            date = inquiry['date'].split('T')[0]  # Just the date part
            product_name = inquiry.get('product_name', 'بدون محصول')
            
            callback_data = f"{ADMIN_PREFIX}inquiry_{inquiry['id']}"
            button_text = f"{name} - {date} - {product_name}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add filter options
        keyboard.append([
            InlineKeyboardButton("🔍 فیلتر", callback_data=f"{ADMIN_PREFIX}filter_inquiries"),
            InlineKeyboardButton("📊 خروجی CSV", callback_data=f"{ADMIN_PREFIX}export_inquiries")
        ])
        
        # Add back button
        keyboard.append([InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_main")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_static_keyboard() -> InlineKeyboardMarkup:
        """Create keyboard for admin static content management."""
        keyboard = [
            [
                InlineKeyboardButton("ویرایش تماس با ما", callback_data=f"{ADMIN_PREFIX}edit_static_contact"),
                InlineKeyboardButton("ویرایش درباره ما", callback_data=f"{ADMIN_PREFIX}edit_static_about")
            ],
            [InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_export_keyboard() -> InlineKeyboardMarkup:
        """Create keyboard for admin export options."""
        keyboard = [
            [
                InlineKeyboardButton("محصولات", callback_data=f"{ADMIN_PREFIX}export_products"),
                InlineKeyboardButton("دسته‌بندی‌ها", callback_data=f"{ADMIN_PREFIX}export_categories")
            ],
            [
                InlineKeyboardButton("استعلام‌ها", callback_data=f"{ADMIN_PREFIX}export_inquiries"),
                InlineKeyboardButton("مطالب آموزشی", callback_data=f"{ADMIN_PREFIX}export_educational")
            ],
            [InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_import_keyboard() -> InlineKeyboardMarkup:
        """Create keyboard for admin import options."""
        keyboard = [
            [
                InlineKeyboardButton("محصولات", callback_data=f"{ADMIN_PREFIX}import_products"),
                InlineKeyboardButton("دسته‌بندی‌ها", callback_data=f"{ADMIN_PREFIX}import_categories")
            ],
            [
                InlineKeyboardButton("مطالب آموزشی", callback_data=f"{ADMIN_PREFIX}import_educational")
            ],
            [InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)
