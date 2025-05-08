import os
import logging
import asyncio
from typing import Dict, Union, Optional, List, Any

from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery, 
    InputFile, FSInputFile
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

import configuration
from database import Database

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, configuration.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=configuration.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database()

# Ensure data directory exists
os.makedirs(configuration.DATA_DIR, exist_ok=True)

# Callback data prefixes
PRODUCT_PREFIX = "product_"
SERVICE_PREFIX = "service_"
CATEGORY_PREFIX = "category_"
BACK_PREFIX = "back_"
INQUIRY_PREFIX = "inquiry_"
EDUCATION_PREFIX = "edu_"
ADMIN_PREFIX = "admin_"

# Button texts (Persian)
PRODUCTS_BTN = "محصولات 📦"
SERVICES_BTN = "خدمات 🛠"
INQUIRY_BTN = "استعلام قیمت 💸"
EDUCATION_BTN = "مطالب آموزشی 📚"
CONTACT_BTN = "تماس با ما 📞"
ABOUT_BTN = "درباره ما ℹ️"
BACK_BTN = "بازگشت ↩️"
SEARCH_BTN = "جستجو 🔍"
ADMIN_BTN = "پنل ادمین 🔧"

# Persian text constants
START_TEXT = """به ربات جامع محصولات و خدمات خوش آمدید! این ربات امکانات زیر را در اختیار شما قرار می‌دهد:
محصولات:
• مشاهده محصولات در دسته‌بندی‌های مختلف
• جزئیات کامل هر محصول شامل قیمت و توضیحات
• امکان مشاهده تصاویر محصولات
خدمات:
• دسترسی به لیست خدمات قابل ارائه
• اطلاعات کامل هر خدمت و شرایط ارائه
• امکان استعلام قیمت مستقیم
استعلام قیمت:
• درخواست استعلام قیمت برای محصولات و خدمات
• فرم ساده و سریع برای ثبت درخواست
• پیگیری آسان درخواست‌ها
مطالب آموزشی:
• دسترسی به محتوای آموزشی دسته‌بندی شده
• مقالات و راهنماهای کاربردی
• به‌روزرسانی مستمر محتوا
امکانات دیگر:
• جستجو در محصولات و خدمات
• تماس مستقیم با پشتیبانی
• اطلاعات تماس و درباره ما
لطفاً از منوی زیر بخش مورد نظر خود را انتخاب کنید:"""

NOT_FOUND_TEXT = "موردی یافت نشد."
CONTACT_DEFAULT = "با ما از طریق شماره 1234567890+ یا ایمیل info@example.com در تماس باشید."
ABOUT_DEFAULT = "ما یک شرکت فعال در زمینه تجهیزات الکترونیکی هستیم."
INQUIRY_START = "لطفاً فرم استعلام قیمت را کامل کنید. نام خود را وارد کنید:"
INQUIRY_PHONE = "لطفاً شماره تماس خود را وارد کنید:"
INQUIRY_DESC = "لطفاً توضیحات بیشتر را وارد کنید (اختیاری):"
INQUIRY_COMPLETE = "استعلام قیمت شما با موفقیت ثبت شد. به زودی با شما تماس خواهیم گرفت."
ADMIN_WELCOME = "به پنل مدیریت خوش آمدید. لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
ADMIN_ACCESS_DENIED = "شما دسترسی به پنل مدیریت ندارید."
SEARCH_PROMPT = "لطفاً عبارت جستجو را وارد کنید:"
ERROR_MESSAGE = "خطایی رخ داد. لطفاً دوباره تلاش کنید."

# Define conversation states
class InquiryStates(StatesGroup):
    INQUIRY_NAME = State()
    INQUIRY_PHONE = State()
    INQUIRY_DESC = State()
    ITEM_INFO = State()  # Store item type and ID

class SearchStates(StatesGroup):
    SEARCH = State()

class AdminStates(StatesGroup):
    MAIN = State()
    EDIT_CATEGORY = State()
    EDIT_PRODUCT = State()
    EDIT_SERVICE = State()
    EDIT_EDU = State()
    UPLOAD_CSV = State()
    ADD_CATEGORY_NAME = State()
    ADD_PRODUCT_NAME = State()
    ADD_PRODUCT_DESC = State()
    ADD_PRODUCT_PRICE = State()
    ADD_SERVICE_NAME = State()
    ADD_SERVICE_DESC = State()
    EDIT_STATIC = State()
    EDIT_STATIC_CONTENT = State()
    EDIT_ITEM_NAME = State()
    EDIT_ITEM_DESC = State()
    EDIT_ITEM_PRICE = State()

# Helper functions
def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create the main menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=PRODUCTS_BTN, callback_data=f"{CATEGORY_PREFIX}product_0"),
        InlineKeyboardButton(text=SERVICES_BTN, callback_data=f"{CATEGORY_PREFIX}service_0")
    )
    builder.row(
        InlineKeyboardButton(text=INQUIRY_BTN, callback_data=f"{INQUIRY_PREFIX}start"),
        InlineKeyboardButton(text=EDUCATION_BTN, callback_data=f"{EDUCATION_PREFIX}0")
    )
    builder.row(
        InlineKeyboardButton(text=CONTACT_BTN, callback_data="contact"),
        InlineKeyboardButton(text=ABOUT_BTN, callback_data="about")
    )
    builder.row(
        InlineKeyboardButton(text=SEARCH_BTN, callback_data="search")
    )
    
    return builder.as_markup()

def get_category_keyboard(category_type: str, parent_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Create keyboard for category navigation."""
    builder = InlineKeyboardBuilder()
    
    # Get categories
    categories = db.get_categories(category_type, parent_id)
    
    # Add category buttons
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=category['name'], 
                callback_data=f"{CATEGORY_PREFIX}{category_type}_{category['id']}"
            )
        )
    
    # If we're in a subcategory, add products/services if any
    if parent_id is not None:
        if category_type == 'product':
            products = db.get_products(parent_id)
            for product in products:
                builder.row(
                    InlineKeyboardButton(
                        text=product['name'],
                        callback_data=f"{PRODUCT_PREFIX}{product['id']}"
                    )
                )
        elif category_type == 'service':
            services = db.get_services(parent_id)
            for service in services:
                builder.row(
                    InlineKeyboardButton(
                        text=service['name'],
                        callback_data=f"{SERVICE_PREFIX}{service['id']}"
                    )
                )
    
    # Back button - if we're in a subcategory
    if parent_id is not None:
        # Get parent category to determine its parent
        parent_category = db.get_category(category_type, parent_id)
        grandparent_id = parent_category.get('parent_id') if parent_category else None
        
        if grandparent_id is not None:
            # If there's a grandparent, go back to it
            builder.row(
                InlineKeyboardButton(
                    text=BACK_BTN,
                    callback_data=f"{BACK_PREFIX}{category_type}_{grandparent_id}"
                )
            )
        else:
            # If no grandparent, go back to category root
            builder.row(
                InlineKeyboardButton(
                    text=BACK_BTN,
                    callback_data=f"{BACK_PREFIX}{category_type}_0"
                )
            )
    else:
        # If we're at the root, go back to main menu
        builder.row(
            InlineKeyboardButton(text=BACK_BTN, callback_data="start")
        )
    
    return builder.as_markup()

def get_product_details_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for product details view."""
    builder = InlineKeyboardBuilder()
    
    # Add price inquiry button
    builder.row(
        InlineKeyboardButton(
            text="استعلام قیمت",
            callback_data=f"{INQUIRY_PREFIX}product_{product_id}"
        )
    )
    
    # Get product to determine its category
    product = db.get_product(product_id)
    if product:
        # Back button to the product's category
        builder.row(
            InlineKeyboardButton(
                text=BACK_BTN,
                callback_data=f"{BACK_PREFIX}product_{product['category_id']}"
            )
        )
    else:
        # If product not found, go back to main products
        builder.row(
            InlineKeyboardButton(
                text=BACK_BTN,
                callback_data=f"{BACK_PREFIX}product_0"
            )
        )
    
    return builder.as_markup()

def get_service_details_keyboard(service_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for service details view."""
    builder = InlineKeyboardBuilder()
    
    # Add price inquiry button
    builder.row(
        InlineKeyboardButton(
            text="استعلام قیمت",
            callback_data=f"{INQUIRY_PREFIX}service_{service_id}"
        )
    )
    
    # Get service to determine its category
    service = db.get_service(service_id)
    if service:
        # Back button to the service's category
        builder.row(
            InlineKeyboardButton(
                text=BACK_BTN,
                callback_data=f"{BACK_PREFIX}service_{service['category_id']}"
            )
        )
    else:
        # If service not found, go back to main services
        builder.row(
            InlineKeyboardButton(
                text=BACK_BTN,
                callback_data=f"{BACK_PREFIX}service_0"
            )
        )
    
    return builder.as_markup()

def get_edu_content_keyboard(parent_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Create keyboard for educational content navigation."""
    builder = InlineKeyboardBuilder()
    
    # Get categories
    categories = db.get_categories('edu', parent_id)
    
    # Add category buttons
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=category['name'], 
                callback_data=f"{EDUCATION_PREFIX}cat_{category['id']}"
            )
        )
    
    # If we're in a category, add content items
    if parent_id is not None:
        content_items = db.get_edu_content(parent_id)
        for item in content_items:
            builder.row(
                InlineKeyboardButton(
                    text=item['title'],
                    callback_data=f"{EDUCATION_PREFIX}item_{item['id']}"
                )
            )
    
    # Back button logic
    if parent_id is not None:
        # Get parent category to determine its parent
        parent_category = db.get_category('edu', parent_id)
        grandparent_id = parent_category.get('parent_id') if parent_category else None
        
        if grandparent_id is not None:
            # If there's a grandparent, go back to it
            builder.row(
                InlineKeyboardButton(
                    text=BACK_BTN,
                    callback_data=f"{EDUCATION_PREFIX}cat_{grandparent_id}"
                )
            )
        else:
            # If no grandparent, go back to edu root
            builder.row(
                InlineKeyboardButton(
                    text=BACK_BTN,
                    callback_data=f"{EDUCATION_PREFIX}0"
                )
            )
    else:
        # If we're at the root, go back to main menu
        builder.row(
            InlineKeyboardButton(text=BACK_BTN, callback_data="start")
        )
    
    return builder.as_markup()

def get_edu_item_keyboard(item_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for educational item view."""
    builder = InlineKeyboardBuilder()
    
    # Get item to determine its category
    item = db.get_edu_item(item_id)
    if item:
        # Back button to the item's category
        builder.row(
            InlineKeyboardButton(
                text=BACK_BTN,
                callback_data=f"{EDUCATION_PREFIX}cat_{item['category_id']}"
            )
        )
    else:
        # If item not found, go back to main edu
        builder.row(
            InlineKeyboardButton(
                text=BACK_BTN,
                callback_data=f"{EDUCATION_PREFIX}0"
            )
        )
    
    return builder.as_markup()

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Create admin panel main keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="دسته‌بندی محصولات", callback_data=f"{ADMIN_PREFIX}product_cat"),
        InlineKeyboardButton(text="محصولات", callback_data=f"{ADMIN_PREFIX}products")
    )
    builder.row(
        InlineKeyboardButton(text="دسته‌بندی خدمات", callback_data=f"{ADMIN_PREFIX}service_cat"),
        InlineKeyboardButton(text="خدمات", callback_data=f"{ADMIN_PREFIX}services")
    )
    builder.row(
        InlineKeyboardButton(text="دسته‌بندی آموزشی", callback_data=f"{ADMIN_PREFIX}edu_cat"),
        InlineKeyboardButton(text="مطالب آموزشی", callback_data=f"{ADMIN_PREFIX}edu_content")
    )
    builder.row(
        InlineKeyboardButton(text="محتوای ثابت", callback_data=f"{ADMIN_PREFIX}static"),
        InlineKeyboardButton(text="درخواست‌ها", callback_data=f"{ADMIN_PREFIX}inquiries")
    )
    builder.row(
        InlineKeyboardButton(text="آپلود CSV", callback_data=f"{ADMIN_PREFIX}csv")
    )
    builder.row(
        InlineKeyboardButton(text=BACK_BTN, callback_data="start")
    )
    
    return builder.as_markup()

def get_admin_category_keyboard(category_type: str, parent_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Create keyboard for admin category management."""
    builder = InlineKeyboardBuilder()
    
    # Add new category button
    builder.row(
        InlineKeyboardButton(
            text="➕ افزودن دسته‌بندی جدید",
            callback_data=f"{ADMIN_PREFIX}add_cat_{category_type}_{parent_id or 0}"
        )
    )
    
    # Get categories
    categories = db.get_categories(category_type, parent_id)
    
    # Add category buttons with edit/delete options
    for category in categories:
        # View subcategories button
        builder.row(
            InlineKeyboardButton(
                text=f"🔍 {category['name']}",
                callback_data=f"{ADMIN_PREFIX}view_cat_{category_type}_{category['id']}"
            )
        )
        
        # Edit and delete buttons in one row
        builder.row(
            InlineKeyboardButton(
                text="✏️ ویرایش",
                callback_data=f"{ADMIN_PREFIX}edit_cat_{category_type}_{category['id']}"
            ),
            InlineKeyboardButton(
                text="❌ حذف",
                callback_data=f"{ADMIN_PREFIX}del_cat_{category_type}_{category['id']}"
            )
        )
    
    # Back button logic
    if parent_id is not None:
        # Get parent category to determine its parent
        parent_category = db.get_category(category_type, parent_id)
        grandparent_id = parent_category.get('parent_id') if parent_category else None
        
        if grandparent_id is not None:
            # If there's a grandparent, go back to it
            builder.row(
                InlineKeyboardButton(
                    text=BACK_BTN,
                    callback_data=f"{ADMIN_PREFIX}view_cat_{category_type}_{grandparent_id}"
                )
            )
        else:
            # If no grandparent, go back to category type root
            builder.row(
                InlineKeyboardButton(
                    text=BACK_BTN,
                    callback_data=f"{ADMIN_PREFIX}{category_type}_cat"
                )
            )
    else:
        # If we're at the root, go back to admin menu
        builder.row(
            InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}main")
        )
    
    return builder.as_markup()

def get_admin_products_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for admin product management."""
    builder = InlineKeyboardBuilder()
    
    # Add new product button
    builder.row(
        InlineKeyboardButton(
            text="➕ افزودن محصول جدید",
            callback_data=f"{ADMIN_PREFIX}add_product_{category_id}"
        )
    )
    
    # Get products
    products = db.get_products(category_id)
    
    # Add product buttons with edit/delete options
    for product in products:
        # Product name
        builder.row(
            InlineKeyboardButton(
                text=f"🔍 {product['name']}",
                callback_data=f"{ADMIN_PREFIX}view_product_{product['id']}"
            )
        )
        
        # Edit and delete buttons in one row
        builder.row(
            InlineKeyboardButton(
                text="✏️ ویرایش",
                callback_data=f"{ADMIN_PREFIX}edit_product_{product['id']}"
            ),
            InlineKeyboardButton(
                text="❌ حذف",
                callback_data=f"{ADMIN_PREFIX}del_product_{product['id']}"
            )
        )
    
    # Back button
    builder.row(
        InlineKeyboardButton(
            text=BACK_BTN,
            callback_data=f"{ADMIN_PREFIX}view_cat_product_{category_id}"
        )
    )
    
    return builder.as_markup()

def get_admin_services_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for admin service management."""
    builder = InlineKeyboardBuilder()
    
    # Add new service button
    builder.row(
        InlineKeyboardButton(
            text="➕ افزودن خدمت جدید",
            callback_data=f"{ADMIN_PREFIX}add_service_{category_id}"
        )
    )
    
    # Get services
    services = db.get_services(category_id)
    
    # Add service buttons with edit/delete options
    for service in services:
        # Service name
        builder.row(
            InlineKeyboardButton(
                text=f"🔍 {service['name']}",
                callback_data=f"{ADMIN_PREFIX}view_service_{service['id']}"
            )
        )
        
        # Edit and delete buttons in one row
        builder.row(
            InlineKeyboardButton(
                text="✏️ ویرایش",
                callback_data=f"{ADMIN_PREFIX}edit_service_{service['id']}"
            ),
            InlineKeyboardButton(
                text="❌ حذف",
                callback_data=f"{ADMIN_PREFIX}del_service_{service['id']}"
            )
        )
    
    # Back button
    builder.row(
        InlineKeyboardButton(
            text=BACK_BTN,
            callback_data=f"{ADMIN_PREFIX}view_cat_service_{category_id}"
        )
    )
    
    return builder.as_markup()

def get_admin_static_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for admin static content management."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📞 تماس با ما", 
            callback_data=f"{ADMIN_PREFIX}edit_static_contact"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="ℹ️ درباره ما", 
            callback_data=f"{ADMIN_PREFIX}edit_static_about"
        )
    )
    builder.row(
        InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}main")
    )
    
    return builder.as_markup()

def get_admin_inquiries_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for admin inquiries view."""
    builder = InlineKeyboardBuilder()
    
    # Get inquiries
    inquiries = db.get_inquiries()
    
    # Add inquiry buttons
    for inquiry in inquiries:
        item_type = inquiry['item_type']
        item_id = inquiry['item_id']
        item_name = ""
        
        # Get item name
        if item_type == 'product':
            product = db.get_product(item_id)
            if product:
                item_name = product['name']
        elif item_type == 'service':
            service = db.get_service(item_id)
            if service:
                item_name = service['name']
                
        # Format status emoji
        status_emoji = "🆕"
        if inquiry['status'] == 'processing':
            status_emoji = "⏳"
        elif inquiry['status'] == 'completed':
            status_emoji = "✅"
        elif inquiry['status'] == 'canceled':
            status_emoji = "❌"
        
        # Add button with inquiry info
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} {inquiry['name']} - {item_name}",
                callback_data=f"{ADMIN_PREFIX}inquiry_{inquiry['id']}"
            )
        )
    
    # Back button
    builder.row(
        InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}main")
    )
    
    return builder.as_markup()

def get_admin_csv_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for admin CSV import."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📥 آپلود فایل محصولات", 
            callback_data=f"{ADMIN_PREFIX}upload_product_csv"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📥 آپلود فایل خدمات", 
            callback_data=f"{ADMIN_PREFIX}upload_service_csv"
        )
    )
    builder.row(
        InlineKeyboardButton(text=BACK_BTN, callback_data=f"{ADMIN_PREFIX}main")
    )
    
    return builder.as_markup()

def get_inquiry_item_info(callback_data: str) -> tuple:
    """Extract item type and ID from inquiry callback data."""
    parts = callback_data.replace(f"{INQUIRY_PREFIX}", "").split("_")
    if len(parts) >= 2:
        return parts[0], int(parts[1])
    return None, None

def get_search_results_keyboard(results: Dict[str, List[Dict]]) -> InlineKeyboardMarkup:
    """Create keyboard for search results."""
    builder = InlineKeyboardBuilder()
    
    # Add product results
    if results.get('products'):
        builder.row(
            InlineKeyboardButton(text="📦 محصولات:", callback_data="ignore")
        )
        for product in results['products']:
            builder.row(
                InlineKeyboardButton(
                    text=product['name'],
                    callback_data=f"{PRODUCT_PREFIX}{product['id']}"
                )
            )
    
    # Add service results
    if results.get('services'):
        builder.row(
            InlineKeyboardButton(text="🛠 خدمات:", callback_data="ignore")
        )
        for service in results['services']:
            builder.row(
                InlineKeyboardButton(
                    text=service['name'],
                    callback_data=f"{SERVICE_PREFIX}{service['id']}"
                )
            )
    
    # Back button
    builder.row(
        InlineKeyboardButton(text=BACK_BTN, callback_data="start")
    )
    
    return builder.as_markup()

# Command handlers
@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Handle the /start command."""
    # Check if user is admin and add admin button if so
    if message.from_user.id == configuration.ADMIN_ID:
        builder = InlineKeyboardBuilder()
        main_menu = get_main_menu_keyboard()
        
        # Add all buttons from main menu
        for row in main_menu.inline_keyboard:
            builder.row(*row)
        
        # Add admin button
        builder.row(
            InlineKeyboardButton(text=ADMIN_BTN, callback_data=f"{ADMIN_PREFIX}main")
        )
        
        keyboard = builder.as_markup()
    else:
        keyboard = get_main_menu_keyboard()
    
    await message.answer(START_TEXT, reply_markup=keyboard)

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Handle the /admin command."""
    if message.from_user.id == configuration.ADMIN_ID:
        await message.answer(ADMIN_WELCOME, reply_markup=get_admin_keyboard())
    else:
        await message.answer(ADMIN_ACCESS_DENIED)

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Cancel any ongoing conversation."""
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer("عملیات لغو شد.", reply_markup=get_main_menu_keyboard())
    else:
        await message.answer("هیچ عملیاتی در حال انجام نیست.", reply_markup=get_main_menu_keyboard())

# Callback handlers
@dp.callback_query(lambda c: c.data == "start")
async def process_start_callback(callback_query: CallbackQuery, state: FSMContext):
    """Handle start callback to show main menu."""
    await state.clear()
    
    # Check if user is admin and add admin button if so
    if callback_query.from_user.id == configuration.ADMIN_ID:
        builder = InlineKeyboardBuilder()
        main_menu = get_main_menu_keyboard()
        
        # Add all buttons from main menu
        for row in main_menu.inline_keyboard:
            builder.row(*row)
        
        # Add admin button
        builder.row(
            InlineKeyboardButton(text=ADMIN_BTN, callback_data=f"{ADMIN_PREFIX}main")
        )
        
        keyboard = builder.as_markup()
    else:
        keyboard = get_main_menu_keyboard()
    
    await callback_query.message.edit_text(START_TEXT, reply_markup=keyboard)
    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith(CATEGORY_PREFIX))
async def process_category_callback(callback_query: CallbackQuery):
    """Handle category navigation callbacks."""
    # Extract category type and ID from callback data
    # Format: "category_TYPE_ID"
    data = callback_query.data.replace(CATEGORY_PREFIX, "")
    parts = data.split("_")
    category_type = parts[0]  # 'product' or 'service'
    category_id = int(parts[1]) if parts[1] != "0" else None
    
    # Get category name and path for header text
    header_text = ""
    if category_id is not None:
        category = db.get_category(category_type, category_id)
        if category:
            path = db.get_category_path(category_type, category_id)
            path_names = [cat['name'] for cat in path]
            header_text = " > ".join(path_names) + "\n\n"
    
    # Add appropriate title
    if category_type == 'product':
        if not header_text:
            header_text = "دسته‌بندی محصولات:\n\n"
    elif category_type == 'service':
        if not header_text:
            header_text = "دسته‌بندی خدمات:\n\n"
    
    # Get and display the category content
    keyboard = get_category_keyboard(category_type, category_id)
    
    await callback_query.message.edit_text(header_text, reply_markup=keyboard)
    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith(PRODUCT_PREFIX))
async def process_product_callback(callback_query: CallbackQuery):
    """Handle product detail callbacks."""
    # Extract product ID from callback data
    # Format: "product_ID"
    product_id = int(callback_query.data.replace(PRODUCT_PREFIX, ""))
    
    # Get product details
    product = db.get_product(product_id)
    if not product:
        await callback_query.message.edit_text(NOT_FOUND_TEXT, reply_markup=get_main_menu_keyboard())
        await callback_query.answer()
        return
    
    # Create product details message
    product_text = f"<b>{product['name']}</b>\n\n"
    product_text += f"{product['description']}\n\n"
    
    if product['price']:
        product_text += f"<b>قیمت:</b> {product['price']}\n"
    
    # Get category path for breadcrumb
    category_path = db.get_category_path('product', product['category_id'])
    if category_path:
        path_names = [cat['name'] for cat in category_path]
        product_text += f"\n<i>دسته‌بندی: {' > '.join(path_names)}</i>"
    
    # Send product image if available
    keyboard = get_product_details_keyboard(product_id)
    
    if product['image_path'] and os.path.exists(product['image_path']):
        # Send photo with caption and keyboard
        photo = FSInputFile(product['image_path'])
        await callback_query.message.delete()
        await callback_query.message.answer_photo(
            photo=photo,
            caption=product_text,
            reply_markup=keyboard
        )
    else:
        # Just send text with keyboard
        await callback_query.message.edit_text(
            product_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith(SERVICE_PREFIX))
async def process_service_callback(callback_query: CallbackQuery):
    """Handle service detail callbacks."""
    # Extract service ID from callback data
    # Format: "service_ID"
    service_id = int(callback_query.data.replace(SERVICE_PREFIX, ""))
    
    # Get service details
    service = db.get_service(service_id)
    if not service:
        await callback_query.message.edit_text(NOT_FOUND_TEXT, reply_markup=get_main_menu_keyboard())
        await callback_query.answer()
        return
    
    # Create service details message
    service_text = f"<b>{service['name']}</b>\n\n"
    service_text += f"{service['description']}\n\n"
    
    # Get category path for breadcrumb
    category_path = db.get_category_path('service', service['category_id'])
    if category_path:
        path_names = [cat['name'] for cat in category_path]
        service_text += f"\n<i>دسته‌بندی: {' > '.join(path_names)}</i>"
    
    # Send service details
    keyboard = get_service_details_keyboard(service_id)
    
    await callback_query.message.edit_text(
        service_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith(BACK_PREFIX))
async def process_back_callback(callback_query: CallbackQuery):
    """Handle back navigation callbacks."""
    # Format: "back_TYPE_ID"
    data = callback_query.data.replace(BACK_PREFIX, "")
    
    if data == "main" or data == "start":
        # Go back to main menu
        await process_start_callback(callback_query, state=FSMContext(storage=storage, key=callback_query.from_user.id))
    elif "_" in data:
        parts = data.split("_")
        category_type = parts[0]  # 'product', 'service', etc.
        category_id = parts[1]
        
        # Determine what to show based on type
        if category_type in ['product', 'service']:
            # Recreate the callback data for the category handler
            new_callback_data = f"{CATEGORY_PREFIX}{category_type}_{category_id}"
            callback_query.data = new_callback_data
            await process_category_callback(callback_query)
        elif category_type == 'edu':
            if data.startswith('edu_cat_'):
                # Extract category ID and recreate callback data
                cat_id = data.replace('edu_cat_', '')
                callback_query.data = f"{EDUCATION_PREFIX}cat_{cat_id}"
                await process_education_callback(callback_query)
            else:
                # Go back to education main
                callback_query.data = f"{EDUCATION_PREFIX}0"
                await process_education_callback(callback_query)
    else:
        # Default to main menu if we can't parse
        await process_start_callback(callback_query, state=FSMContext(storage=storage, key=callback_query.from_user.id))

@dp.callback_query(lambda c: c.data == "contact")
async def process_contact_callback(callback_query: CallbackQuery):
    """Handle contact information callback."""
    contact_text = db.get_static_content('contact')
    if not contact_text:
        contact_text = CONTACT_DEFAULT
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=BACK_BTN, callback_data="start")
    )
    
    await callback_query.message.edit_text(
        f"<b>اطلاعات تماس:</b>\n\n{contact_text}",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "about")
async def process_about_callback(callback_query: CallbackQuery):
    """Handle about us callback."""
    about_text = db.get_static_content('about')
    if not about_text:
        about_text = ABOUT_DEFAULT
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=BACK_BTN, callback_data="start")
    )
    
    await callback_query.message.edit_text(
        f"<b>درباره ما:</b>\n\n{about_text}",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "search")
async def process_search_callback(callback_query: CallbackQuery, state: FSMContext):
    """Handle search callback."""
    await state.set_state(SearchStates.SEARCH)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=BACK_BTN, callback_data="start")
    )
    
    await callback_query.message.edit_text(
        SEARCH_PROMPT,
        reply_markup=builder.as_markup()
    )
    
    await callback_query.answer()

@dp.message(SearchStates.SEARCH)
async def process_search_query(message: Message, state: FSMContext):
    """Handle search query input."""
    query = message.text.strip()
    
    if not query:
        await message.answer(
            "لطفاً یک عبارت معتبر برای جستجو وارد کنید.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        return
    
    # Search in database
    results = db.search(query)
    
    if not results.get('products') and not results.get('services'):
        await message.answer(
            f"<b>نتایج جستجو برای '{query}':</b>\n\n{NOT_FOUND_TEXT}",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Count results
        product_count = len(results.get('products', []))
        service_count = len(results.get('services', []))
        total = product_count + service_count
        
        # Create result message
        result_text = f"<b>نتایج جستجو برای '{query}':</b>\n\n"
        result_text += f"تعداد {total} مورد یافت شد."
        
        # Send results with keyboard
        await message.answer(
            result_text,
            reply_markup=get_search_results_keyboard(results),
            parse_mode="HTML"
        )
    
    await state.clear()

@dp.callback_query(lambda c: c.data.startswith(INQUIRY_PREFIX))
async def process_inquiry_callback(callback_query: CallbackQuery, state: FSMContext):
    """Handle price inquiry callbacks."""
    # Check if this is the start of inquiry process
    if callback_query.data == f"{INQUIRY_PREFIX}start":
        # General inquiry without a specific item
        await state.set_state(InquiryStates.INQUIRY_NAME)
        await state.update_data(item_type=None, item_id=None)
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="لغو", callback_data="cancel_inquiry")
        )
        
        await callback_query.message.edit_text(
            INQUIRY_START,
            reply_markup=builder.as_markup()
        )
    else:
        # Specific item inquiry
        item_type, item_id = get_inquiry_item_info(callback_query.data)
        
        if not item_type or not item_id:
            await callback_query.answer("خطا در پردازش درخواست.")
            return
        
        # Store item info in state
        await state.set_state(InquiryStates.INQUIRY_NAME)
        await state.update_data(item_type=item_type, item_id=item_id)
        
        # Get item details for confirmation
        item_name = ""
        if item_type == 'product':
            product = db.get_product(item_id)
            if product:
                item_name = product['name']
        elif item_type == 'service':
            service = db.get_service(item_id)
            if service:
                item_name = service['name']
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="لغو", callback_data="cancel_inquiry")
        )
        
        await callback_query.message.edit_text(
            f"درخواست استعلام قیمت برای: <b>{item_name}</b>\n\n{INQUIRY_START}",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "cancel_inquiry")
async def cancel_inquiry(callback_query: CallbackQuery, state: FSMContext):
    """Cancel the inquiry process."""
    await state.clear()
    await process_start_callback(callback_query, state)

@dp.message(InquiryStates.INQUIRY_NAME)
async def process_inquiry_name(message: Message, state: FSMContext):
    """Process the name input for inquiry."""
    name = message.text.strip()
    
    if not name:
        await message.answer("لطفاً نام معتبری وارد کنید:")
        return
    
    # Store name and move to next state
    await state.update_data(name=name)
    await state.set_state(InquiryStates.INQUIRY_PHONE)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="لغو", callback_data="cancel_inquiry")
    )
    
    await message.answer(
        INQUIRY_PHONE,
        reply_markup=builder.as_markup()
    )

@dp.message(InquiryStates.INQUIRY_PHONE)
async def process_inquiry_phone(message: Message, state: FSMContext):
    """Process the phone number input for inquiry."""
    phone = message.text.strip()
    
    if not phone:
        await message.answer("لطفاً شماره تماس معتبری وارد کنید:")
        return
    
    # Store phone and move to next state
    await state.update_data(phone=phone)
    await state.set_state(InquiryStates.INQUIRY_DESC)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="لغو", callback_data="cancel_inquiry")
    )
    
    await message.answer(
        INQUIRY_DESC,
        reply_markup=builder.as_markup()
    )

@dp.message(InquiryStates.INQUIRY_DESC)
async def process_inquiry_desc(message: Message, state: FSMContext):
    """Process the description input for inquiry and complete the process."""
    description = message.text.strip()
    
    # Get all inquiry data
    data = await state.get_data()
    name = data.get('name', '')
    phone = data.get('phone', '')
    item_type = data.get('item_type')
    item_id = data.get('item_id')
    
    # Add inquiry to database
    try:
        db.add_inquiry(
            user_id=message.from_user.id,
            name=name,
            phone=phone,
            description=description,
            item_type=item_type or 'general',
            item_id=item_id or 0
        )
        
        # Send confirmation
        await message.answer(
            INQUIRY_COMPLETE,
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Error adding inquiry: {e}")
        await message.answer(
            ERROR_MESSAGE,
            reply_markup=get_main_menu_keyboard()
        )
    
    # Clear state
    await state.clear()

@dp.callback_query(lambda c: c.data.startswith(EDUCATION_PREFIX))
async def process_education_callback(callback_query: CallbackQuery):
    """Handle educational content navigation callbacks."""
    data = callback_query.data
    
    # Handle different cases
    if data == f"{EDUCATION_PREFIX}0":
        # Show main education categories
        header_text = "محتوای آموزشی:\n\n"
        keyboard = get_edu_content_keyboard()
        
        await callback_query.message.edit_text(header_text, reply_markup=keyboard)
    elif data.startswith(f"{EDUCATION_PREFIX}cat_"):
        # Show subcategories and content in a category
        category_id = int(data.replace(f"{EDUCATION_PREFIX}cat_", ""))
        
        # Get category path for header text
        category = db.get_category('edu', category_id)
        if category:
            path = db.get_category_path('edu', category_id)
            path_names = [cat['name'] for cat in path]
            header_text = " > ".join(path_names) + "\n\n"
        else:
            header_text = "محتوای آموزشی:\n\n"
        
        keyboard = get_edu_content_keyboard(category_id)
        
        await callback_query.message.edit_text(header_text, reply_markup=keyboard)
    elif data.startswith(f"{EDUCATION_PREFIX}item_"):
        # Show specific content item
        item_id = int(data.replace(f"{EDUCATION_PREFIX}item_", ""))
        
        # Get item details
        item = db.get_edu_item(item_id)
        if not item:
            await callback_query.message.edit_text(NOT_FOUND_TEXT, reply_markup=get_main_menu_keyboard())
            await callback_query.answer()
            return
        
        # Create content message
        content_text = f"<b>{item['title']}</b>\n\n"
        if item['description']:
            content_text += f"{item['description']}\n\n"
        content_text += f"{item['content']}\n\n"
        
        # Get category path for breadcrumb
        category_path = db.get_category_path('edu', item['category_id'])
        if category_path:
            path_names = [cat['name'] for cat in category_path]
            content_text += f"\n<i>دسته‌بندی: {' > '.join(path_names)}</i>"
        
        keyboard = get_edu_item_keyboard(item_id)
        
        if item['media_path'] and os.path.exists(item['media_path']):
            # Send photo with caption and keyboard
            photo = FSInputFile(item['media_path'])
            await callback_query.message.delete()
            await callback_query.message.answer_photo(
                photo=photo,
                caption=content_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            # Just send text with keyboard
            await callback_query.message.edit_text(
                content_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    
    await callback_query.answer()

# Admin panel handlers
@dp.callback_query(lambda c: c.data.startswith(ADMIN_PREFIX))
async def process_admin_callback(callback_query: CallbackQuery, state: FSMContext):
    """Handle admin panel callbacks."""
    # Check if user is admin
    if callback_query.from_user.id != configuration.ADMIN_ID:
        await callback_query.message.edit_text(ADMIN_ACCESS_DENIED, reply_markup=get_main_menu_keyboard())
        await callback_query.answer()
        return
    
    data = callback_query.data
    
    # Main admin panel
    if data == f"{ADMIN_PREFIX}main":
        await state.set_state(AdminStates.MAIN)
        await callback_query.message.edit_text(ADMIN_WELCOME, reply_markup=get_admin_keyboard())
    
    # Category management
    elif data.endswith("_cat"):
        category_type = data.replace(f"{ADMIN_PREFIX}", "").replace("_cat", "")
        await state.set_state(AdminStates.EDIT_CATEGORY)
        await state.update_data(category_type=category_type)
        
        type_name = ""
        if category_type == 'product':
            type_name = "محصولات"
        elif category_type == 'service':
            type_name = "خدمات"
        elif category_type == 'edu':
            type_name = "آموزشی"
            
        await callback_query.message.edit_text(
            f"مدیریت دسته‌بندی‌های {type_name}",
            reply_markup=get_admin_category_keyboard(category_type)
        )
    
    # View category contents
    elif data.startswith(f"{ADMIN_PREFIX}view_cat_"):
        parts = data.replace(f"{ADMIN_PREFIX}view_cat_", "").split("_")
        category_type = parts[0]
        category_id = int(parts[1])
        
        await state.set_state(AdminStates.EDIT_CATEGORY)
        await state.update_data(category_type=category_type, parent_id=category_id)
        
        # Get category info for header
        category = db.get_category(category_type, category_id)
        category_name = category['name'] if category else ""
        
        # Different behavior based on category type
        if category_type == 'product':
            # For product categories, show subcategories and products
            await callback_query.message.edit_text(
                f"دسته‌بندی: {category_name}",
                reply_markup=get_admin_category_keyboard(category_type, category_id)
            )
        elif category_type == 'service':
            # For service categories, show subcategories and services
            await callback_query.message.edit_text(
                f"دسته‌بندی: {category_name}",
                reply_markup=get_admin_category_keyboard(category_type, category_id)
            )
        elif category_type == 'edu':
            # For educational categories, show subcategories
            await callback_query.message.edit_text(
                f"دسته‌بندی: {category_name}",
                reply_markup=get_admin_category_keyboard(category_type, category_id)
            )
    
    # Product management
    elif data == f"{ADMIN_PREFIX}products":
        # Show product categories
        await callback_query.message.edit_text(
            "انتخاب دسته‌بندی محصولات:",
            reply_markup=get_admin_category_keyboard('product')
        )
    
    # Service management
    elif data == f"{ADMIN_PREFIX}services":
        # Show service categories
        await callback_query.message.edit_text(
            "انتخاب دسته‌بندی خدمات:",
            reply_markup=get_admin_category_keyboard('service')
        )
    
    # Static content management
    elif data == f"{ADMIN_PREFIX}static":
        await state.set_state(AdminStates.EDIT_STATIC)
        await callback_query.message.edit_text(
            "مدیریت محتوای ثابت:",
            reply_markup=get_admin_static_keyboard()
        )
    
    # Inquiries management
    elif data == f"{ADMIN_PREFIX}inquiries":
        await callback_query.message.edit_text(
            "لیست درخواست‌های استعلام قیمت:",
            reply_markup=get_admin_inquiries_keyboard()
        )
    
    # CSV import
    elif data == f"{ADMIN_PREFIX}csv":
        await state.set_state(AdminStates.UPLOAD_CSV)
        await callback_query.message.edit_text(
            "آپلود فایل CSV برای محصولات یا خدمات:",
            reply_markup=get_admin_csv_keyboard()
        )
    
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "cancel_admin")
async def cancel_admin_action(callback_query: CallbackQuery, state: FSMContext):
    """Cancel admin action and return to admin panel."""
    await state.set_state(AdminStates.MAIN)
    await callback_query.message.edit_text(ADMIN_WELCOME, reply_markup=get_admin_keyboard())
    await callback_query.answer()

# Main execution
async def main():
    # Start the bot
    print("Starting bot...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    # Run the bot
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped!")