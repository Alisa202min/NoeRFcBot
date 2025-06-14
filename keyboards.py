"""
ماژول صفحه کلیدهای تلگرام
این ماژول صفحه کلیدهای درون‌خطی و پاسخ را فراهم می‌کند.
"""

from typing import List, Dict, Optional, Tuple, Union
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from callback_formatter import callback_formatter
from configuration import (
    PRODUCTS_BTN, SERVICES_BTN, INQUIRY_BTN, EDUCATION_BTN, CONTACT_BTN, ABOUT_BTN, 
    BACK_BTN, SEARCH_BTN, ADMIN_BTN, PRODUCT_PREFIX, SERVICE_PREFIX, EDUCATION_PREFIX, ADMIN_PREFIX
)

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Create the main menu keyboard
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=PRODUCTS_BTN), KeyboardButton(text=SERVICES_BTN)],
            [KeyboardButton(text=INQUIRY_BTN), KeyboardButton(text=EDUCATION_BTN)],
            [KeyboardButton(text=CONTACT_BTN), KeyboardButton(text=ABOUT_BTN)],
            [KeyboardButton(text=SEARCH_BTN)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="برای شروع گزینه‌ای را انتخاب کنید..."
    )
    return keyboard

def product_categories_keyboard(categories: List[Dict]) -> InlineKeyboardMarkup:
    """
    Create a keyboard for product categories
    """
    keyboard = []
    for category in categories:
        category_name = category['name']
        category_id = category['id']
        callback_data = callback_formatter.write("product_category", category_id=category_id)
        try:
            content_count = int(category.get('subcategory_count', 0)) + int(category.get('product_count', 0))
        except (ValueError, TypeError):
            content_count = 0
        display_name = f"{category_name} ({content_count})" if content_count > 0 else category_name
        keyboard.append([InlineKeyboardButton(text=display_name, callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data=callback_formatter.write("back_to_main"))])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def service_categories_keyboard(categories: List[Dict]) -> InlineKeyboardMarkup:
    """
    Create a keyboard for service categories
    """
    keyboard = []
    for category in categories:
        category_name = category['name']
        category_id = category['id']
        callback_data = callback_formatter.write("service_category", category_id=category_id)
        try:
            content_count = int(category.get('subcategory_count', 0)) + int(category.get('service_count', 0))
        except (ValueError, TypeError):
            content_count = 0
        display_name = f"{category_name} ({content_count})" if content_count > 0 else category_name
        keyboard.append([InlineKeyboardButton(text=display_name, callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data=callback_formatter.write("back_to_main"))])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def education_categories_keyboard(categories: List[Dict]) -> InlineKeyboardMarkup:
    """
    Create a keyboard for educational content categories
    """
    keyboard = []
    for category in categories:
        category_name = category['name']
        category_id = category['id']
        callback_data = callback_formatter.write("edu_category", category_id=category_id)
        try:
            content_count = int(category.get('content_count', 0))
        except (ValueError, TypeError):
            content_count = 0
        display_name = f"{category_name} ({content_count})" if content_count > 0 else category_name
        keyboard.append([InlineKeyboardButton(text=display_name, callback_data=callback_data)])
    keyboard.append([InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data=callback_formatter.write("back_to_main"))])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def product_content_keyboard(products: List[Dict], category_id: int) -> InlineKeyboardMarkup:
    """
    Create a keyboard for product listing
    """
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(text=product['name'], callback_data=callback_formatter.write("product_item", product_id=product['id']))
    builder.button(text=BACK_BTN, callback_data=callback_formatter.write("product_category", category_id=category_id))
    builder.button(text="🏠 بازگشت به منوی اصلی", callback_data=callback_formatter.write("back_to_main"))
    builder.adjust(1)
    return builder.as_markup()

def service_content_keyboard(services: List[Dict], category_id: int) -> InlineKeyboardMarkup:
    """
    Create a keyboard for service listing
    """
    builder = InlineKeyboardBuilder()
    for service in services:
        builder.button(text=service['name'], callback_data=callback_formatter.write("service_item", service_id=service['id']))
    builder.button(text=BACK_BTN, callback_data=callback_formatter.write("service_category", category_id=category_id))
    builder.button(text="🏠 بازگشت به منوی اصلی", callback_data=callback_formatter.write("back_to_main"))
    builder.adjust(1)
    return builder.as_markup()

def education_content_keyboard(contents: List[Dict], category_id: int) -> InlineKeyboardMarkup:
    """
    Create a keyboard for educational content listing
    """
    builder = InlineKeyboardBuilder()
    for content in contents:
        builder.button(text=content['title'], callback_data=callback_formatter.write("edu_content", content_id=content['id']))
    builder.button(text=BACK_BTN, callback_data=callback_formatter.write("edu_category", category_id=category_id))
    builder.button(text="🏠 بازگشت به منوی اصلی", callback_data=callback_formatter.write("back_to_main"))
    builder.adjust(1)
    return builder.as_markup()

def product_detail_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    """
    Create a keyboard for product detail view
    """
    keyboard = [
        [InlineKeyboardButton(text="استعلام قیمت 📝", callback_data=callback_formatter.write("inquiry", inquiry_type="product", item_id=product_id))],
        [InlineKeyboardButton(text=BACK_BTN, callback_data=callback_formatter.write("product_category", category_id=category_id))],
        [InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data=callback_formatter.write("back_to_main"))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def service_detail_keyboard(service_id: int, category_id: int) -> InlineKeyboardMarkup:
    """
    Create a keyboard for service detail view
    """
    keyboard = [
        [InlineKeyboardButton(text="استعلام قیمت 📝", callback_data=callback_formatter.write("inquiry", inquiry_type="service", item_id=service_id))],
        [InlineKeyboardButton(text=BACK_BTN, callback_data=callback_formatter.write("service_category", category_id=category_id))],
        [InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data=callback_formatter.write("back_to_main"))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def education_detail_keyboard(category_id: int, category_name: Optional[str] = None) -> InlineKeyboardMarkup:
    """
    Create a keyboard for educational content detail
    """
    keyboard = [
        [InlineKeyboardButton(text=BACK_BTN, callback_data=callback_formatter.write("edu_category", category_id=category_id))],
        [InlineKeyboardButton(text="🏠 بازگشت به منوی اصلی", callback_data=callback_formatter.write("back_to_main"))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Other keyboard functions (admin, cancel, etc.) remain unchanged