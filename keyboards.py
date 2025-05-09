from typing import List, Dict, Optional, Tuple, Union
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from configuration import (
    PRODUCTS_BTN, SERVICES_BTN, INQUIRY_BTN, EDUCATION_BTN, CONTACT_BTN, ABOUT_BTN, 
    BACK_BTN, SEARCH_BTN, ADMIN_BTN, PRODUCT_PREFIX, SERVICE_PREFIX, CATEGORY_PREFIX,
    BACK_PREFIX, INQUIRY_PREFIX, EDUCATION_PREFIX, ADMIN_PREFIX
)

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Create the main menu keyboard
    
    Returns:
        ReplyKeyboardMarkup for the main menu
    """
    keyboard = [
        [KeyboardButton(text=PRODUCTS_BTN), KeyboardButton(text=SERVICES_BTN)],
        [KeyboardButton(text=INQUIRY_BTN), KeyboardButton(text=EDUCATION_BTN)],
        [KeyboardButton(text=CONTACT_BTN), KeyboardButton(text=ABOUT_BTN)],
        [KeyboardButton(text=SEARCH_BTN)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def admin_keyboard() -> ReplyKeyboardMarkup:
    """
    Create the admin menu keyboard
    
    Returns:
        ReplyKeyboardMarkup for the admin panel
    """
    keyboard = [
        [KeyboardButton(text="مدیریت محصولات 🛍"), KeyboardButton(text="مدیریت خدمات 🛠")],
        [KeyboardButton(text="مدیریت مطالب آموزشی 📚"), KeyboardButton(text="مشاهده استعلام‌ها 📝")],
        [KeyboardButton(text="مدیریت صفحات ثابت 📄"), KeyboardButton(text="خروجی CSV 📊")],
        [KeyboardButton(text="افزودن از CSV 📥"), KeyboardButton(text=BACK_BTN)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def categories_keyboard(categories: List[Dict], parent_id: Optional[int] = None, 
                       add_back: bool = True, include_products: bool = False) -> InlineKeyboardMarkup:
    """
    Create a keyboard for category navigation
    
    Args:
        categories: List of category dictionaries
        parent_id: ID of the parent category (for back button)
        add_back: Whether to add a back button
        include_products: Whether to include product buttons
        
    Returns:
        InlineKeyboardMarkup for category navigation
    """
    keyboard = []
    
    # Add category buttons
    for category in categories:
        prefix = PRODUCT_PREFIX if category['type'] == 'product' else SERVICE_PREFIX
        callback_data = f"{CATEGORY_PREFIX}{category['id']}"
        keyboard.append([InlineKeyboardButton(text=category['name'], callback_data=callback_data)])
    
    # Add back button if needed
    if add_back:
        if parent_id is None:
            # Back to main menu
            keyboard.append([InlineKeyboardButton(text=BACK_BTN, callback_data=f"{BACK_PREFIX}main")])
        else:
            # Back to parent category
            keyboard.append([InlineKeyboardButton(text=BACK_BTN, callback_data=f"{BACK_PREFIX}{parent_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def products_keyboard(products: List[Dict], category_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """
    Create a keyboard for product listing
    
    Args:
        products: List of product dictionaries
        category_id: ID of the parent category (for back button)
        
    Returns:
        InlineKeyboardMarkup for product listing
    """
    keyboard = []
    
    # Add product buttons
    for product in products:
        callback_data = f"{PRODUCT_PREFIX}{product['id']}"
        keyboard.append([InlineKeyboardButton(text=product['name'], callback_data=callback_data)])
    
    # Add back button
    if category_id is not None:
        keyboard.append([InlineKeyboardButton(text=BACK_BTN, callback_data=f"{BACK_PREFIX}{category_id}")])
    else:
        keyboard.append([InlineKeyboardButton(text=BACK_BTN, callback_data=f"{BACK_PREFIX}main")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def product_detail_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    """
    Create a keyboard for product detail view
    
    Args:
        product_id: ID of the current product
        category_id: ID of the parent category
        
    Returns:
        InlineKeyboardMarkup for product detail
    """
    keyboard = [
        [InlineKeyboardButton(text="استعلام قیمت 📝", callback_data=f"{INQUIRY_PREFIX}{product_id}")],
        [InlineKeyboardButton(text=BACK_BTN, callback_data=f"{BACK_PREFIX}{category_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def education_categories_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    """
    Create a keyboard for educational content categories
    
    Args:
        categories: List of category names
        
    Returns:
        InlineKeyboardMarkup for educational categories
    """
    keyboard = []
    
    # Add category buttons
    for category in categories:
        callback_data = f"{EDUCATION_PREFIX}cat_{category}"
        keyboard.append([InlineKeyboardButton(text=category, callback_data=callback_data)])
    
    # Add back button
    keyboard.append([InlineKeyboardButton(text=BACK_BTN, callback_data=f"{BACK_PREFIX}main")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def education_content_keyboard(contents: List[Dict], category: str) -> InlineKeyboardMarkup:
    """
    Create a keyboard for educational content listing
    
    Args:
        contents: List of content dictionaries
        category: Category name (for back button)
        
    Returns:
        InlineKeyboardMarkup for educational content
    """
    keyboard = []
    
    # Add content buttons
    for content in contents:
        callback_data = f"{EDUCATION_PREFIX}{content['id']}"
        keyboard.append([InlineKeyboardButton(text=content['title'], callback_data=callback_data)])
    
    # Add back button
    keyboard.append([InlineKeyboardButton(text=BACK_BTN, callback_data=f"{EDUCATION_PREFIX}categories")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def education_detail_keyboard(category: str) -> InlineKeyboardMarkup:
    """
    Create a keyboard for educational content detail
    
    Args:
        category: Category name
        
    Returns:
        InlineKeyboardMarkup for content detail
    """
    keyboard = [
        [InlineKeyboardButton(text=BACK_BTN, callback_data=f"{EDUCATION_PREFIX}cat_{category}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_categories_keyboard(categories: List[Dict], parent_id: Optional[int] = None, 
                            entity_type: str = 'product') -> InlineKeyboardMarkup:
    """
    Create a keyboard for admin category management
    
    Args:
        categories: List of category dictionaries
        parent_id: ID of the parent category
        entity_type: Type of entity (product/service)
        
    Returns:
        InlineKeyboardMarkup for admin category management
    """
    keyboard = []
    
    # Add category buttons
    for category in categories:
        callback_data = f"{ADMIN_PREFIX}cat_{category['id']}"
        keyboard.append([InlineKeyboardButton(text=category['name'], callback_data=callback_data)])
    
    # Add action buttons
    keyboard.append([
        InlineKeyboardButton(text="➕ افزودن", callback_data=f"{ADMIN_PREFIX}add_cat_{parent_id or 0}_{entity_type}"),
    ])
    
    # Add back button
    if parent_id is None:
        # Back to admin menu
        keyboard.append([InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_main")])
    else:
        # Back to parent category
        keyboard.append([InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_cat_{parent_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_category_detail_keyboard(category_id: int, parent_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """
    Create a keyboard for admin category detail
    
    Args:
        category_id: ID of the current category
        parent_id: ID of the parent category
        
    Returns:
        InlineKeyboardMarkup for admin category detail
    """
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"{ADMIN_PREFIX}edit_cat_{category_id}"),
            InlineKeyboardButton(text="❌ حذف", callback_data=f"{ADMIN_PREFIX}delete_cat_{category_id}")
        ],
        [
            InlineKeyboardButton(text="📝 محصولات", callback_data=f"{ADMIN_PREFIX}products_{category_id}"),
            InlineKeyboardButton(text="📁 زیرگروه‌ها", callback_data=f"{ADMIN_PREFIX}subcats_{category_id}")
        ]
    ]
    
    # Add back button
    if parent_id is None:
        keyboard.append([InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}categories")])
    else:
        keyboard.append([InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}cat_{parent_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_products_keyboard(products: List[Dict], category_id: int) -> InlineKeyboardMarkup:
    """
    Create a keyboard for admin product management
    
    Args:
        products: List of product dictionaries
        category_id: ID of the parent category
        
    Returns:
        InlineKeyboardMarkup for admin product management
    """
    keyboard = []
    
    # Add product buttons
    for product in products:
        callback_data = f"{ADMIN_PREFIX}product_{product['id']}"
        keyboard.append([InlineKeyboardButton(text=product['name'], callback_data=callback_data)])
    
    # Add action buttons
    keyboard.append([
        InlineKeyboardButton(text="➕ افزودن", callback_data=f"{ADMIN_PREFIX}add_product_{category_id}"),
    ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}cat_{category_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_product_detail_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    """
    Create a keyboard for admin product detail
    
    Args:
        product_id: ID of the current product
        category_id: ID of the parent category
        
    Returns:
        InlineKeyboardMarkup for admin product detail
    """
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"{ADMIN_PREFIX}edit_product_{product_id}"),
            InlineKeyboardButton(text="❌ حذف", callback_data=f"{ADMIN_PREFIX}delete_product_{product_id}")
        ],
        [InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}products_{category_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_educational_keyboard(contents: List[Dict]) -> InlineKeyboardMarkup:
    """
    Create a keyboard for admin educational content management
    
    Args:
        contents: List of content dictionaries
        
    Returns:
        InlineKeyboardMarkup for admin educational content
    """
    keyboard = []
    
    # Add content buttons
    for content in contents:
        callback_data = f"{ADMIN_PREFIX}edu_{content['id']}"
        keyboard.append([InlineKeyboardButton(text=content['title'], callback_data=callback_data)])
    
    # Add action buttons
    keyboard.append([
        InlineKeyboardButton(text="➕ افزودن", callback_data=f"{ADMIN_PREFIX}add_edu"),
    ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_edu_detail_keyboard(content_id: int) -> InlineKeyboardMarkup:
    """
    Create a keyboard for admin educational content detail
    
    Args:
        content_id: ID of the current content
        
    Returns:
        InlineKeyboardMarkup for admin content detail
    """
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"{ADMIN_PREFIX}edit_edu_{content_id}"),
            InlineKeyboardButton(text="❌ حذف", callback_data=f"{ADMIN_PREFIX}delete_edu_{content_id}")
        ],
        [InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}educational")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_inquiries_keyboard(inquiries: List[Dict]) -> InlineKeyboardMarkup:
    """
    Create a keyboard for admin inquiries management
    
    Args:
        inquiries: List of inquiry dictionaries
        
    Returns:
        InlineKeyboardMarkup for admin inquiries
    """
    keyboard = []
    
    # Add inquiry buttons (limited to 10)
    for i, inquiry in enumerate(inquiries[:10]):
        name = inquiry['name']
        date = inquiry['date'].split('T')[0]  # Just the date part
        product_name = inquiry.get('product_name', 'بدون محصول')
        
        callback_data = f"{ADMIN_PREFIX}inquiry_{inquiry['id']}"
        button_text = f"{name} - {date} - {product_name}"
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    
    # Add filter options
    keyboard.append([
        InlineKeyboardButton(text="🔍 فیلتر", callback_data=f"{ADMIN_PREFIX}filter_inquiries"),
        InlineKeyboardButton(text="📊 خروجی CSV", callback_data=f"{ADMIN_PREFIX}export_inquiries")
    ])
    
    # Add back button
    keyboard.append([InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_static_keyboard() -> InlineKeyboardMarkup:
    """
    Create a keyboard for admin static content management
    
    Returns:
        InlineKeyboardMarkup for admin static content
    """
    keyboard = [
        [
            InlineKeyboardButton(text="ویرایش تماس با ما", callback_data=f"{ADMIN_PREFIX}edit_static_contact"),
            InlineKeyboardButton(text="ویرایش درباره ما", callback_data=f"{ADMIN_PREFIX}edit_static_about")
        ],
        [InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_export_keyboard() -> InlineKeyboardMarkup:
    """
    Create a keyboard for admin export options
    
    Returns:
        InlineKeyboardMarkup for admin export
    """
    keyboard = [
        [
            InlineKeyboardButton(text="محصولات", callback_data=f"{ADMIN_PREFIX}export_products"),
            InlineKeyboardButton(text="دسته‌بندی‌ها", callback_data=f"{ADMIN_PREFIX}export_categories")
        ],
        [
            InlineKeyboardButton(text="استعلام‌ها", callback_data=f"{ADMIN_PREFIX}export_inquiries"),
            InlineKeyboardButton(text="مطالب آموزشی", callback_data=f"{ADMIN_PREFIX}export_educational")
        ],
        [InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_import_keyboard() -> InlineKeyboardMarkup:
    """
    Create a keyboard for admin import options
    
    Returns:
        InlineKeyboardMarkup for admin import
    """
    keyboard = [
        [
            InlineKeyboardButton(text="محصولات", callback_data=f"{ADMIN_PREFIX}import_products"),
            InlineKeyboardButton(text="دسته‌بندی‌ها", callback_data=f"{ADMIN_PREFIX}import_categories")
        ],
        [
            InlineKeyboardButton(text="مطالب آموزشی", callback_data=f"{ADMIN_PREFIX}import_educational")
        ],
        [InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def cancel_keyboard() -> InlineKeyboardMarkup:
    """
    Create a simple cancel keyboard
    
    Returns:
        InlineKeyboardMarkup with cancel button
    """
    keyboard = [[InlineKeyboardButton(text="انصراف ❌", callback_data="cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def confirm_keyboard(action: str, entity_id: int) -> InlineKeyboardMarkup:
    """
    Create a confirmation keyboard
    
    Args:
        action: Action to confirm (delete, etc.)
        entity_id: ID of the entity
        
    Returns:
        InlineKeyboardMarkup with confirm/cancel buttons
    """
    keyboard = [
        [
            InlineKeyboardButton(text="بله ✅", callback_data=f"confirm_{action}_{entity_id}"),
            InlineKeyboardButton(text="خیر ❌", callback_data=f"cancel_{action}_{entity_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
