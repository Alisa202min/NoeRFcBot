"""
ماژول صفحه کلیدهای تلگرام
این ماژول صفحه کلیدهای درون‌خطی و پاسخ را فراهم می‌کند.
"""

from typing import List, Dict, Optional, Tuple, Union
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from configuration import (
    PRODUCTS_BTN, SERVICES_BTN, INQUIRY_BTN, EDUCATION_BTN, CONTACT_BTN, ABOUT_BTN, 
    BACK_BTN, SEARCH_BTN, ADMIN_BTN, PRODUCT_PREFIX, SERVICE_PREFIX, CATEGORY_PREFIX,
    BACK_PREFIX, INQUIRY_PREFIX, EDUCATION_PREFIX, ADMIN_PREFIX
)

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Create the main menu keyboard
    
    Returns:
        ReplyKeyboardMarkup for the main menu
    """
    keyboard = [
        [KeyboardButton(text=PRODUCTS_BTN), KeyboardButton(text=SERVICES_BTN)],
        [KeyboardButton(text=INQUIRY_BTN), KeyboardButton(text=EDUCATION_BTN)],
        [KeyboardButton(text=CONTACT_BTN), KeyboardButton(text=ABOUT_BTN)]
    ]
    
    # Add admin button if needed
    # keyboard.append([KeyboardButton(text=ADMIN_BTN)])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_back_keyboard() -> ReplyKeyboardMarkup:
    """
    Create a keyboard with just the back button
    
    Returns:
        ReplyKeyboardMarkup with a back button
    """
    keyboard = [[KeyboardButton(text=BACK_BTN)]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_categories_keyboard(categories: List[Dict], parent_id: Optional[int] = None, 
                          prefix: str = CATEGORY_PREFIX) -> InlineKeyboardMarkup:
    """
    Create a keyboard with categories
    
    Args:
        categories: List of category dictionaries
        parent_id: Parent category ID
        prefix: Callback data prefix
        
    Returns:
        InlineKeyboardMarkup with categories
    """
    builder = InlineKeyboardBuilder()
    
    # Filter categories for the current level
    level_categories = [c for c in categories if c['parent_id'] == parent_id]
    
    # Add category buttons
    for category in level_categories:
        builder.add(InlineKeyboardButton(
            text=category['name'],
            callback_data=f"{prefix}{category['id']}"
        ))
    
    # Format as grid with 2 buttons per row
    builder.adjust(2)
    
    # Add back button if we're in a subcategory
    if parent_id is not None:
        # Find parent of current parent to go back to
        parent_category = next((c for c in categories if c['id'] == parent_id), None)
        parent_of_parent_id = parent_category['parent_id'] if parent_category else None
        
        builder.row(InlineKeyboardButton(
            text=BACK_BTN,
            callback_data=f"{BACK_PREFIX}{parent_of_parent_id or 0}"
        ))
    
    return builder.as_markup()

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """
    Create admin panel keyboard
    
    Returns:
        ReplyKeyboardMarkup for admin panel
    """
    keyboard = [
        [KeyboardButton(text="مدیریت محصولات"), KeyboardButton(text="مدیریت خدمات")],
        [KeyboardButton(text="مدیریت دسته‌بندی‌ها"), KeyboardButton(text="مدیریت استعلام‌ها")],
        [KeyboardButton(text="محتوای آموزشی"), KeyboardButton(text="تنظیمات")],
        [KeyboardButton(text="بازگشت به منوی اصلی")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)