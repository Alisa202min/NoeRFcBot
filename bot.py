import os
import logging
from typing import Dict, Union, Optional, List, Any
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, InputFile, CallbackQuery
from aiogram.utils import executor
from aiogram.utils.exceptions import TelegramAPIError
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import configuration
from database import Database

# Configure logging
logging.basicConfig(
    level=getattr(logging, configuration.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=configuration.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
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
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(PRODUCTS_BTN, callback_data=f"{CATEGORY_PREFIX}product_0"),
        InlineKeyboardButton(SERVICES_BTN, callback_data=f"{CATEGORY_PREFIX}service_0"),
        InlineKeyboardButton(INQUIRY_BTN, callback_data=f"{INQUIRY_PREFIX}start"),
        InlineKeyboardButton(EDUCATION_BTN, callback_data=f"{EDUCATION_PREFIX}0"),
        InlineKeyboardButton(CONTACT_BTN, callback_data="contact"),
        InlineKeyboardButton(ABOUT_BTN, callback_data="about"),
        InlineKeyboardButton(SEARCH_BTN, callback_data="search")
    )
    return keyboard

def get_category_keyboard(category_type: str, parent_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Create keyboard for category navigation."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Get categories
    categories = db.get_categories(category_type, parent_id)
    
    # Add category buttons
    for category in categories:
        keyboard.add(InlineKeyboardButton(
            category['name'], 
            callback_data=f"{CATEGORY_PREFIX}{category_type}_{category['id']}"
        ))
    
    # If we're in a subcategory, add products/services if any
    if parent_id is not None:
        if category_type == 'product':
            products = db.get_products(parent_id)
            for product in products:
                keyboard.add(InlineKeyboardButton(
                    product['name'],
                    callback_data=f"{PRODUCT_PREFIX}{product['id']}"
                ))
        elif category_type == 'service':
            services = db.get_services(parent_id)
            for service in services:
                keyboard.add(InlineKeyboardButton(
                    service['name'],
                    callback_data=f"{SERVICE_PREFIX}{service['id']}"
                ))
    
    # Back button - if we're in a subcategory
    if parent_id is not None:
        # Get parent category to determine its parent
        parent_category = db.get_category(category_type, parent_id)
        grandparent_id = parent_category.get('parent_id') if parent_category else None
        
        if grandparent_id is not None:
            # If there's a grandparent, go back to it
            keyboard.add(InlineKeyboardButton(
                BACK_BTN,
                callback_data=f"{BACK_PREFIX}{category_type}_{grandparent_id}"
            ))
        else:
            # If no grandparent, go back to category root
            keyboard.add(InlineKeyboardButton(
                BACK_BTN,
                callback_data=f"{BACK_PREFIX}{category_type}_0"
            ))
    else:
        # If we're at the root, go back to main menu
        keyboard.add(InlineKeyboardButton(BACK_BTN, callback_data="start"))
    
    return keyboard

def get_product_details_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for product details view."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Add price inquiry button
    keyboard.add(InlineKeyboardButton(
        "استعلام قیمت",
        callback_data=f"{INQUIRY_PREFIX}product_{product_id}"
    ))
    
    # Get product to determine its category
    product = db.get_product(product_id)
    if product:
        # Back button to the product's category
        keyboard.add(InlineKeyboardButton(
            BACK_BTN,
            callback_data=f"{BACK_PREFIX}product_{product['category_id']}"
        ))
    else:
        # If product not found, go back to main products
        keyboard.add(InlineKeyboardButton(
            BACK_BTN,
            callback_data=f"{BACK_PREFIX}product_0"
        ))
    
    return keyboard

def get_service_details_keyboard(service_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for service details view."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Add price inquiry button
    keyboard.add(InlineKeyboardButton(
        "استعلام قیمت",
        callback_data=f"{INQUIRY_PREFIX}service_{service_id}"
    ))
    
    # Get service to determine its category
    service = db.get_service(service_id)
    if service:
        # Back button to the service's category
        keyboard.add(InlineKeyboardButton(
            BACK_BTN,
            callback_data=f"{BACK_PREFIX}service_{service['category_id']}"
        ))
    else:
        # If service not found, go back to main services
        keyboard.add(InlineKeyboardButton(
            BACK_BTN,
            callback_data=f"{BACK_PREFIX}service_0"
        ))
    
    return keyboard

def get_edu_content_keyboard(parent_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Create keyboard for educational content navigation."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Get categories
    categories = db.get_categories('edu', parent_id)
    
    # Add category buttons
    for category in categories:
        keyboard.add(InlineKeyboardButton(
            category['name'], 
            callback_data=f"{EDUCATION_PREFIX}cat_{category['id']}"
        ))
    
    # If we're in a category, add content items
    if parent_id is not None:
        content_items = db.get_edu_content(parent_id)
        for item in content_items:
            keyboard.add(InlineKeyboardButton(
                item['title'],
                callback_data=f"{EDUCATION_PREFIX}item_{item['id']}"
            ))
    
    # Back button logic
    if parent_id is not None:
        # Get parent category to determine its parent
        parent_category = db.get_category('edu', parent_id)
        grandparent_id = parent_category.get('parent_id') if parent_category else None
        
        if grandparent_id is not None:
            # If there's a grandparent, go back to it
            keyboard.add(InlineKeyboardButton(
                BACK_BTN,
                callback_data=f"{EDUCATION_PREFIX}cat_{grandparent_id}"
            ))
        else:
            # If no grandparent, go back to edu root
            keyboard.add(InlineKeyboardButton(
                BACK_BTN,
                callback_data=f"{EDUCATION_PREFIX}0"
            ))
    else:
        # If we're at the root, go back to main menu
        keyboard.add(InlineKeyboardButton(BACK_BTN, callback_data="start"))
    
    return keyboard

def get_edu_item_keyboard(item_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for educational item view."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Get item to determine its category
    item = db.get_edu_item(item_id)
    if item:
        # Back button to the item's category
        keyboard.add(InlineKeyboardButton(
            BACK_BTN,
            callback_data=f"{EDUCATION_PREFIX}cat_{item['category_id']}"
        ))
    else:
        # If item not found, go back to main edu
        keyboard.add(InlineKeyboardButton(
            BACK_BTN,
            callback_data=f"{EDUCATION_PREFIX}0"
        ))
    
    return keyboard

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Create admin panel main keyboard."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("دسته‌بندی محصولات", callback_data=f"{ADMIN_PREFIX}product_cat"),
        InlineKeyboardButton("محصولات", callback_data=f"{ADMIN_PREFIX}products"),
        InlineKeyboardButton("دسته‌بندی خدمات", callback_data=f"{ADMIN_PREFIX}service_cat"),
        InlineKeyboardButton("خدمات", callback_data=f"{ADMIN_PREFIX}services"),
        InlineKeyboardButton("دسته‌بندی آموزشی", callback_data=f"{ADMIN_PREFIX}edu_cat"),
        InlineKeyboardButton("مطالب آموزشی", callback_data=f"{ADMIN_PREFIX}edu_content"),
        InlineKeyboardButton("محتوای ثابت", callback_data=f"{ADMIN_PREFIX}static"),
        InlineKeyboardButton("درخواست‌ها", callback_data=f"{ADMIN_PREFIX}inquiries"),
        InlineKeyboardButton("آپلود CSV", callback_data=f"{ADMIN_PREFIX}csv"),
        InlineKeyboardButton(BACK_BTN, callback_data="start")
    )
    return keyboard

def get_admin_category_keyboard(category_type: str, parent_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Create keyboard for admin category management."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Add new category button
    keyboard.add(InlineKeyboardButton(
        "➕ افزودن دسته‌بندی جدید",
        callback_data=f"{ADMIN_PREFIX}add_cat_{category_type}_{parent_id or 0}"
    ))
    
    # Get categories
    categories = db.get_categories(category_type, parent_id)
    
    # Add category buttons with edit/delete options
    for category in categories:
        # View subcategories button
        keyboard.add(InlineKeyboardButton(
            f"🔍 {category['name']}",
            callback_data=f"{ADMIN_PREFIX}view_cat_{category_type}_{category['id']}"
        ))
        
        # Edit and delete buttons in one row
        keyboard.add(
            InlineKeyboardButton(
                "✏️ ویرایش",
                callback_data=f"{ADMIN_PREFIX}edit_cat_{category_type}_{category['id']}"
            ),
            InlineKeyboardButton(
                "❌ حذف",
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
            keyboard.add(InlineKeyboardButton(
                BACK_BTN,
                callback_data=f"{ADMIN_PREFIX}view_cat_{category_type}_{grandparent_id}"
            ))
        else:
            # If no grandparent, go back to category type root
            keyboard.add(InlineKeyboardButton(
                BACK_BTN,
                callback_data=f"{ADMIN_PREFIX}{category_type}_cat"
            ))
    else:
        # If we're at the root, go back to admin menu
        keyboard.add(InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}main"))
    
    return keyboard

def get_admin_products_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for admin product management."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Add new product button
    keyboard.add(InlineKeyboardButton(
        "➕ افزودن محصول جدید",
        callback_data=f"{ADMIN_PREFIX}add_product_{category_id}"
    ))
    
    # Get products
    products = db.get_products(category_id)
    
    # Add product buttons with edit/delete options
    for product in products:
        # Product name
        keyboard.add(InlineKeyboardButton(
            f"🔍 {product['name']}",
            callback_data=f"{ADMIN_PREFIX}view_product_{product['id']}"
        ))
        
        # Edit and delete buttons in one row
        keyboard.add(
            InlineKeyboardButton(
                "✏️ ویرایش",
                callback_data=f"{ADMIN_PREFIX}edit_product_{product['id']}"
            ),
            InlineKeyboardButton(
                "❌ حذف",
                callback_data=f"{ADMIN_PREFIX}del_product_{product['id']}"
            )
        )
    
    # Back button
    keyboard.add(InlineKeyboardButton(
        BACK_BTN,
        callback_data=f"{ADMIN_PREFIX}view_cat_product_{category_id}"
    ))
    
    return keyboard

def get_admin_services_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for admin service management."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Add new service button
    keyboard.add(InlineKeyboardButton(
        "➕ افزودن خدمت جدید",
        callback_data=f"{ADMIN_PREFIX}add_service_{category_id}"
    ))
    
    # Get services
    services = db.get_services(category_id)
    
    # Add service buttons with edit/delete options
    for service in services:
        # Service name
        keyboard.add(InlineKeyboardButton(
            f"🔍 {service['name']}",
            callback_data=f"{ADMIN_PREFIX}view_service_{service['id']}"
        ))
        
        # Edit and delete buttons in one row
        keyboard.add(
            InlineKeyboardButton(
                "✏️ ویرایش",
                callback_data=f"{ADMIN_PREFIX}edit_service_{service['id']}"
            ),
            InlineKeyboardButton(
                "❌ حذف",
                callback_data=f"{ADMIN_PREFIX}del_service_{service['id']}"
            )
        )
    
    # Back button
    keyboard.add(InlineKeyboardButton(
        BACK_BTN,
        callback_data=f"{ADMIN_PREFIX}view_cat_service_{category_id}"
    ))
    
    return keyboard

def get_admin_static_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for admin static content management."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    keyboard.add(
        InlineKeyboardButton(
            "ویرایش اطلاعات تماس",
            callback_data=f"{ADMIN_PREFIX}edit_static_contact"
        ),
        InlineKeyboardButton(
            "ویرایش درباره ما",
            callback_data=f"{ADMIN_PREFIX}edit_static_about"
        ),
        InlineKeyboardButton(
            BACK_BTN,
            callback_data=f"{ADMIN_PREFIX}main"
        )
    )
    
    return keyboard

def get_admin_inquiries_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for admin inquiries view."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(
            "درخواست‌های جدید",
            callback_data=f"{ADMIN_PREFIX}inquiries_new"
        ),
        InlineKeyboardButton(
            "درخواست‌های در حال بررسی",
            callback_data=f"{ADMIN_PREFIX}inquiries_processing"
        ),
        InlineKeyboardButton(
            "درخواست‌های تکمیل شده",
            callback_data=f"{ADMIN_PREFIX}inquiries_completed"
        ),
        InlineKeyboardButton(
            "درخواست‌های لغو شده",
            callback_data=f"{ADMIN_PREFIX}inquiries_canceled"
        ),
        InlineKeyboardButton(
            "همه درخواست‌ها",
            callback_data=f"{ADMIN_PREFIX}inquiries_all"
        ),
        InlineKeyboardButton(
            BACK_BTN,
            callback_data=f"{ADMIN_PREFIX}main"
        )
    )
    
    return keyboard

def get_admin_csv_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for admin CSV import."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    keyboard.add(
        InlineKeyboardButton(
            "آپلود CSV محصولات",
            callback_data=f"{ADMIN_PREFIX}csv_product"
        ),
        InlineKeyboardButton(
            "آپلود CSV خدمات",
            callback_data=f"{ADMIN_PREFIX}csv_service"
        ),
        InlineKeyboardButton(
            BACK_BTN,
            callback_data=f"{ADMIN_PREFIX}main"
        )
    )
    
    return keyboard

def get_inquiry_item_info(callback_data: str) -> tuple:
    """Extract item type and ID from inquiry callback data."""
    parts = callback_data.split('_')
    if len(parts) >= 2:
        item_type = parts[-2]  # e.g., 'product' or 'service'
        item_id = int(parts[-1])
        return item_type, item_id
    return None, None

def get_search_results_keyboard(results: Dict[str, List[Dict]]) -> InlineKeyboardMarkup:
    """Create keyboard for search results."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Add product results
    for product in results.get('products', []):
        keyboard.add(InlineKeyboardButton(
            f"محصول: {product['name']}",
            callback_data=f"{PRODUCT_PREFIX}{product['id']}"
        ))
    
    # Add service results
    for service in results.get('services', []):
        keyboard.add(InlineKeyboardButton(
            f"خدمت: {service['name']}",
            callback_data=f"{SERVICE_PREFIX}{service['id']}"
        ))
    
    # Add back button
    keyboard.add(InlineKeyboardButton(BACK_BTN, callback_data="start"))
    
    return keyboard

# Command handlers
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """Handle the /start command."""
    # Check if user is admin and add admin button
    keyboard = get_main_menu_keyboard()
    if message.from_user.id == configuration.ADMIN_ID:
        keyboard.add(InlineKeyboardButton(ADMIN_BTN, callback_data=f"{ADMIN_PREFIX}main"))
    
    await message.answer(START_TEXT, reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message_handler(commands=['admin'])
async def cmd_admin(message: types.Message):
    """Handle the /admin command."""
    if message.from_user.id == configuration.ADMIN_ID:
        await message.answer(ADMIN_WELCOME, reply_markup=get_admin_keyboard())
    else:
        await message.answer(ADMIN_ACCESS_DENIED)

@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Cancel any ongoing conversation."""
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
        await message.answer("عملیات لغو شد.", reply_markup=get_main_menu_keyboard())
    else:
        await message.answer("هیچ عملیاتی در حال انجام نیست.", reply_markup=get_main_menu_keyboard())

# Callback query handlers
@dp.callback_query_handler(lambda c: c.data == "start", state='*')
async def process_start_callback(callback_query: CallbackQuery, state: FSMContext):
    """Handle start callback to show main menu."""
    await state.finish()
    
    # Check if user is admin and add admin button
    keyboard = get_main_menu_keyboard()
    if callback_query.from_user.id == configuration.ADMIN_ID:
        keyboard.add(InlineKeyboardButton(ADMIN_BTN, callback_data=f"{ADMIN_PREFIX}main"))
    
    await bot.edit_message_text(
        START_TEXT,
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

@dp.callback_query_handler(lambda c: c.data.startswith(CATEGORY_PREFIX))
async def process_category_callback(callback_query: CallbackQuery):
    """Handle category navigation callbacks."""
    # Parse callback data to get category type and ID
    _, type_id = callback_query.data.split('_', 1)
    category_type, category_id = type_id.split('_')
    category_id = int(category_id)
    
    # Get categories for this type and parent
    keyboard = get_category_keyboard(category_type, category_id if category_id > 0 else None)
    
    # Get category name for the title
    title = PRODUCTS_BTN if category_type == 'product' else SERVICES_BTN
    if category_id > 0:
        category = db.get_category(category_type, category_id)
        if category:
            title = category['name']
    
    await bot.edit_message_text(
        f"دسته‌بندی: {title}",
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith(PRODUCT_PREFIX))
async def process_product_callback(callback_query: CallbackQuery):
    """Handle product detail callbacks."""
    # Get product ID
    product_id = int(callback_query.data.split('_')[1])
    
    # Get product details
    product = db.get_product(product_id)
    
    if product:
        # Prepare message text
        message_text = f"<b>{product['name']}</b>\n\n"
        message_text += f"{product['description']}\n\n"
        
        if product['price']:
            message_text += f"<b>قیمت:</b> {product['price']}\n"
        
        # Get keyboard with inquiry and back buttons
        keyboard = get_product_details_keyboard(product_id)
        
        # If product has image, send photo with caption
        if product['image_path'] and os.path.exists(product['image_path']):
            try:
                with open(product['image_path'], 'rb') as photo:
                    await bot.send_photo(
                        callback_query.from_user.id,
                        photo,
                        caption=message_text,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
                # Delete the previous message
                await bot.delete_message(
                    callback_query.from_user.id,
                    callback_query.message.message_id
                )
            except Exception as e:
                logger.error(f"Error sending product image: {e}")
                # If error, just update the message without image
                await bot.edit_message_text(
                    message_text,
                    callback_query.from_user.id,
                    callback_query.message.message_id,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
        else:
            # No image, just update the message
            await bot.edit_message_text(
                message_text,
                callback_query.from_user.id,
                callback_query.message.message_id,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
    else:
        await bot.edit_message_text(
            "محصول مورد نظر یافت نشد.",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=get_main_menu_keyboard()
        )

@dp.callback_query_handler(lambda c: c.data.startswith(SERVICE_PREFIX))
async def process_service_callback(callback_query: CallbackQuery):
    """Handle service detail callbacks."""
    # Get service ID
    service_id = int(callback_query.data.split('_')[1])
    
    # Get service details
    service = db.get_service(service_id)
    
    if service:
        # Prepare message text
        message_text = f"<b>{service['name']}</b>\n\n"
        message_text += f"{service['description']}\n\n"
        
        # Get keyboard with inquiry and back buttons
        keyboard = get_service_details_keyboard(service_id)
        
        await bot.edit_message_text(
            message_text,
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    else:
        await bot.edit_message_text(
            "خدمت مورد نظر یافت نشد.",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=get_main_menu_keyboard()
        )

@dp.callback_query_handler(lambda c: c.data.startswith(BACK_PREFIX))
async def process_back_callback(callback_query: CallbackQuery):
    """Handle back navigation callbacks."""
    # Parse callback data to get type and parent ID
    if '_' in callback_query.data[len(BACK_PREFIX):]:
        type_id = callback_query.data[len(BACK_PREFIX):]
        category_type, parent_id = type_id.split('_')
        parent_id = int(parent_id)
        
        # Handle back in category navigation
        keyboard = get_category_keyboard(category_type, parent_id if parent_id > 0 else None)
        
        # Get category name for the title
        title = PRODUCTS_BTN if category_type == 'product' else SERVICES_BTN
        if parent_id > 0:
            category = db.get_category(category_type, parent_id)
            if category:
                title = category['name']
        
        await bot.edit_message_text(
            f"دسته‌بندی: {title}",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=keyboard
        )
    else:
        # Back to main menu
        await process_start_callback(callback_query, None)

@dp.callback_query_handler(lambda c: c.data == "contact")
async def process_contact_callback(callback_query: CallbackQuery):
    """Handle contact information callback."""
    # Get contact info from database or use default
    contact_info = db.get_static_content("contact") or CONTACT_DEFAULT
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(BACK_BTN, callback_data="start"))
    
    await bot.edit_message_text(
        f"<b>اطلاعات تماس:</b>\n\n{contact_info}",
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

@dp.callback_query_handler(lambda c: c.data == "about")
async def process_about_callback(callback_query: CallbackQuery):
    """Handle about us callback."""
    # Get about info from database or use default
    about_info = db.get_static_content("about") or ABOUT_DEFAULT
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(BACK_BTN, callback_data="start"))
    
    await bot.edit_message_text(
        f"<b>درباره ما:</b>\n\n{about_info}",
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

@dp.callback_query_handler(lambda c: c.data == "search")
async def process_search_callback(callback_query: CallbackQuery):
    """Handle search callback."""
    await SearchStates.SEARCH.set()
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(BACK_BTN, callback_data="start"))
    
    await bot.edit_message_text(
        SEARCH_PROMPT,
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=keyboard
    )

@dp.message_handler(state=SearchStates.SEARCH)
async def process_search_query(message: types.Message, state: FSMContext):
    """Handle search query input."""
    query = message.text.strip()
    
    if not query:
        await message.answer(SEARCH_PROMPT)
        return
    
    # Search in database
    results = db.search(query)
    
    # Create keyboard with results
    keyboard = get_search_results_keyboard(results)
    
    # Check if we found anything
    if not results['products'] and not results['services']:
        await message.answer(
            f"جستجو برای '{query}': {NOT_FOUND_TEXT}",
            reply_markup=keyboard
        )
    else:
        product_count = len(results['products'])
        service_count = len(results['services'])
        
        result_text = f"نتایج جستجو برای '{query}':\n\n"
        result_text += f"محصولات: {product_count}\n"
        result_text += f"خدمات: {service_count}\n\n"
        result_text += "لطفاً یک مورد را انتخاب کنید:"
        
        await message.answer(result_text, reply_markup=keyboard)
    
    # End the conversation
    await state.finish()

# Inquiry handlers
@dp.callback_query_handler(lambda c: c.data.startswith(INQUIRY_PREFIX))
async def process_inquiry_callback(callback_query: CallbackQuery, state: FSMContext):
    """Handle price inquiry callbacks."""
    if callback_query.data == f"{INQUIRY_PREFIX}start":
        # General inquiry start
        await InquiryStates.INQUIRY_NAME.set()
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("لغو", callback_data="cancel_inquiry"))
        
        await bot.edit_message_text(
            INQUIRY_START,
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=keyboard
        )
    else:
        # Inquiry for specific product/service
        # Extract item type and ID
        item_type, item_id = get_inquiry_item_info(callback_query.data)
        
        if item_type and item_id:
            # Store item info in state
            await state.update_data(item_type=item_type, item_id=item_id)
            
            # Start inquiry flow
            await InquiryStates.INQUIRY_NAME.set()
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("لغو", callback_data="cancel_inquiry"))
            
            await bot.edit_message_text(
                INQUIRY_START,
                callback_query.from_user.id,
                callback_query.message.message_id,
                reply_markup=keyboard
            )
        else:
            await bot.answer_callback_query(
                callback_query.id,
                text="خطا در درخواست استعلام قیمت. لطفاً دوباره تلاش کنید."
            )

@dp.callback_query_handler(lambda c: c.data == "cancel_inquiry", state='*')
async def cancel_inquiry(callback_query: CallbackQuery, state: FSMContext):
    """Cancel the inquiry process."""
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    await bot.edit_message_text(
        "درخواست استعلام قیمت لغو شد.",
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=get_main_menu_keyboard()
    )

@dp.message_handler(state=InquiryStates.INQUIRY_NAME)
async def process_inquiry_name(message: types.Message, state: FSMContext):
    """Process the name input for inquiry."""
    name = message.text.strip()
    
    if not name:
        await message.answer("لطفاً نام معتبر وارد کنید.")
        return
    
    # Save name to state
    await state.update_data(name=name)
    
    # Move to next step
    await InquiryStates.INQUIRY_PHONE.set()
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("لغو", callback_data="cancel_inquiry"))
    
    await message.answer(INQUIRY_PHONE, reply_markup=keyboard)

@dp.message_handler(state=InquiryStates.INQUIRY_PHONE)
async def process_inquiry_phone(message: types.Message, state: FSMContext):
    """Process the phone number input for inquiry."""
    phone = message.text.strip()
    
    if not phone:
        await message.answer("لطفاً شماره تماس معتبر وارد کنید.")
        return
    
    # Save phone to state
    await state.update_data(phone=phone)
    
    # Move to next step
    await InquiryStates.INQUIRY_DESC.set()
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("لغو", callback_data="cancel_inquiry"))
    
    await message.answer(INQUIRY_DESC, reply_markup=keyboard)

@dp.message_handler(state=InquiryStates.INQUIRY_DESC)
async def process_inquiry_desc(message: types.Message, state: FSMContext):
    """Process the description input for inquiry and complete the process."""
    desc = message.text.strip()
    
    # Save description to state
    await state.update_data(description=desc)
    
    # Get all data from state
    data = await state.get_data()
    
    try:
        # Save inquiry to database
        item_type = data.get('item_type', 'general')
        item_id = data.get('item_id', 0)
        
        db.add_inquiry(
            message.from_user.id,
            data['name'],
            data['phone'],
            data['description'],
            item_type,
            item_id
        )
        
        # Clear state
        await state.finish()
        
        # Notify user
        await message.answer(INQUIRY_COMPLETE, reply_markup=get_main_menu_keyboard())
        
        # Notify admin
        if configuration.ADMIN_ID:
            item_info = ""
            if item_type == 'product':
                product = db.get_product(item_id)
                if product:
                    item_info = f"محصول: {product['name']}"
            elif item_type == 'service':
                service = db.get_service(item_id)
                if service:
                    item_info = f"خدمت: {service['name']}"
            
            admin_message = (
                f"استعلام قیمت جدید:\n"
                f"نام: {data['name']}\n"
                f"شماره تماس: {data['phone']}\n"
                f"توضیحات: {data['description']}\n"
                f"{item_info}"
            )
            
            try:
                await bot.send_message(configuration.ADMIN_ID, admin_message)
            except Exception as e:
                logger.error(f"Error sending admin notification: {e}")
                
    except Exception as e:
        logger.error(f"Error saving inquiry: {e}")
        await message.answer(
            "خطا در ثبت استعلام قیمت. لطفاً دوباره تلاش کنید.",
            reply_markup=get_main_menu_keyboard()
        )

# Educational content handlers
@dp.callback_query_handler(lambda c: c.data.startswith(EDUCATION_PREFIX))
async def process_education_callback(callback_query: CallbackQuery):
    """Handle educational content navigation callbacks."""
    callback_data = callback_query.data[len(EDUCATION_PREFIX):]
    
    if callback_data == "0":
        # Root education menu
        keyboard = get_edu_content_keyboard()
        
        await bot.edit_message_text(
            "مطالب آموزشی",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=keyboard
        )
    elif callback_data.startswith("cat_"):
        # Education category
        category_id = int(callback_data[4:])
        keyboard = get_edu_content_keyboard(category_id)
        
        # Get category name
        category = db.get_category("edu", category_id)
        title = "مطالب آموزشی"
        if category:
            title = category['name']
        
        await bot.edit_message_text(
            f"دسته‌بندی: {title}",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=keyboard
        )
    elif callback_data.startswith("item_"):
        # Educational content item
        item_id = int(callback_data[5:])
        item = db.get_edu_item(item_id)
        
        if item:
            # Prepare message text
            message_text = f"<b>{item['title']}</b>\n\n"
            if item['description']:
                message_text += f"{item['description']}\n\n"
            if item['content']:
                message_text += f"{item['content']}"
            
            # Get keyboard for item view
            keyboard = get_edu_item_keyboard(item_id)
            
            # If item has media, send with media
            if item['media_path'] and os.path.exists(item['media_path']):
                try:
                    with open(item['media_path'], 'rb') as media:
                        await bot.send_photo(
                            callback_query.from_user.id,
                            media,
                            caption=message_text,
                            reply_markup=keyboard,
                            parse_mode=ParseMode.HTML
                        )
                    # Delete the previous message
                    await bot.delete_message(
                        callback_query.from_user.id,
                        callback_query.message.message_id
                    )
                except Exception as e:
                    logger.error(f"Error sending educational content media: {e}")
                    # If error, just update the message without media
                    await bot.edit_message_text(
                        message_text,
                        callback_query.from_user.id,
                        callback_query.message.message_id,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
            else:
                # No media, just update the message
                await bot.edit_message_text(
                    message_text,
                    callback_query.from_user.id,
                    callback_query.message.message_id,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
        else:
            await bot.edit_message_text(
                "محتوای آموزشی مورد نظر یافت نشد.",
                callback_query.from_user.id,
                callback_query.message.message_id,
                reply_markup=get_main_menu_keyboard()
            )

# Admin panel handlers
@dp.callback_query_handler(lambda c: c.data.startswith(ADMIN_PREFIX))
async def process_admin_callback(callback_query: CallbackQuery, state: FSMContext):
    """Handle admin panel callbacks."""
    if callback_query.from_user.id != configuration.ADMIN_ID:
        await bot.answer_callback_query(
            callback_query.id,
            text=ADMIN_ACCESS_DENIED
        )
        return
    
    callback_data = callback_query.data[len(ADMIN_PREFIX):]
    
    # Main admin menu
    if callback_data == "main":
        await bot.edit_message_text(
            ADMIN_WELCOME,
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=get_admin_keyboard()
        )
        return
    
    # Category management
    if callback_data in ["product_cat", "service_cat", "edu_cat"]:
        category_type = callback_data.split('_')[0]
        keyboard = get_admin_category_keyboard(category_type)
        
        await bot.edit_message_text(
            f"مدیریت دسته‌بندی‌های {category_type}",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=keyboard
        )
        return
    
    # View category (subcategories)
    if callback_data.startswith("view_cat_"):
        parts = callback_data.split('_')
        category_type = parts[2]
        category_id = int(parts[3])
        
        keyboard = get_admin_category_keyboard(category_type, category_id)
        
        category = db.get_category(category_type, category_id)
        title = f"دسته‌بندی‌های {category_type}"
        if category:
            title = f"زیردسته‌های {category['name']}"
        
        await bot.edit_message_text(
            title,
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=keyboard
        )
        return
    
    # Add category
    if callback_data.startswith("add_cat_"):
        parts = callback_data.split('_')
        category_type = parts[2]
        parent_id = int(parts[3]) if parts[3] != "None" else None
        
        # Store category type and parent ID in state
        await state.update_data(
            admin_action="add_category",
            category_type=category_type,
            parent_id=parent_id
        )
        
        # Set state for category name input
        await AdminStates.ADD_CATEGORY_NAME.set()
        
        # Request category name
        await bot.edit_message_text(
            "لطفاً نام دسته‌بندی جدید را وارد کنید:",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("لغو", callback_data="cancel_admin")
            )
        )
        return
    
    # Edit category
    if callback_data.startswith("edit_cat_"):
        parts = callback_data.split('_')
        category_type = parts[2]
        category_id = int(parts[3])
        
        # Store category info in state
        await state.update_data(
            admin_action="edit_category",
            category_type=category_type,
            category_id=category_id
        )
        
        # Set state for category name input
        await AdminStates.EDIT_ITEM_NAME.set()
        
        # Get current category name
        category = db.get_category(category_type, category_id)
        current_name = category['name'] if category else ""
        
        # Request new category name
        await bot.edit_message_text(
            f"ویرایش نام دسته‌بندی:\nنام فعلی: {current_name}\n\nلطفاً نام جدید را وارد کنید:",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("لغو", callback_data="cancel_admin")
            )
        )
        return
    
    # Delete category
    if callback_data.startswith("del_cat_"):
        parts = callback_data.split('_')
        category_type = parts[2]
        category_id = int(parts[3])
        
        # Get category and parent info
        category = db.get_category(category_type, category_id)
        parent_id = category.get('parent_id') if category else None
        
        # Delete category
        success = db.delete_category(category_type, category_id)
        
        if success:
            await bot.answer_callback_query(
                callback_query.id,
                text="دسته‌بندی با موفقیت حذف شد."
            )
        else:
            await bot.answer_callback_query(
                callback_query.id,
                text="خطا در حذف دسته‌بندی."
            )
        
        # Return to parent category view
        callback_data = f"view_cat_{category_type}_{parent_id if parent_id else 0}"
        await process_admin_callback(callback_query, state)
        return
    
    # Product management
    if callback_data == "products":
        await bot.edit_message_text(
            "لطفاً ابتدا دسته‌بندی محصولات را انتخاب کنید:",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=get_admin_category_keyboard("product")
        )
        return
    
    # View products in category
    if callback_data.startswith("view_products_"):
        category_id = int(callback_data.split('_')[2])
        
        keyboard = get_admin_products_keyboard(category_id)
        
        category = db.get_category("product", category_id)
        title = "محصولات"
        if category:
            title = f"محصولات دسته {category['name']}"
        
        await bot.edit_message_text(
            title,
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=keyboard
        )
        return
    
    # Add product
    if callback_data.startswith("add_product_"):
        category_id = int(callback_data.split('_')[2])
        
        # Store category ID in state
        await state.update_data(
            admin_action="add_product",
            category_id=category_id
        )
        
        # Set state for product name input
        await AdminStates.ADD_PRODUCT_NAME.set()
        
        # Request product name
        await bot.edit_message_text(
            "لطفاً نام محصول جدید را وارد کنید:",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("لغو", callback_data="cancel_admin")
            )
        )
        return
    
    # Edit product
    if callback_data.startswith("edit_product_"):
        product_id = int(callback_data.split('_')[2])
        
        # Store product ID in state
        await state.update_data(
            admin_action="edit_product",
            product_id=product_id
        )
        
        # Set state for product name input
        await AdminStates.EDIT_ITEM_NAME.set()
        
        # Get current product name
        product = db.get_product(product_id)
        current_name = product['name'] if product else ""
        
        # Request new product name
        await bot.edit_message_text(
            f"ویرایش نام محصول:\nنام فعلی: {current_name}\n\nلطفاً نام جدید را وارد کنید:",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("لغو", callback_data="cancel_admin")
            )
        )
        return
    
    # Delete product
    if callback_data.startswith("del_product_"):
        product_id = int(callback_data.split('_')[2])
        
        # Get product and category info
        product = db.get_product(product_id)
        category_id = product.get('category_id') if product else None
        
        # Delete product
        success = db.delete_product(product_id)
        
        if success:
            await bot.answer_callback_query(
                callback_query.id,
                text="محصول با موفقیت حذف شد."
            )
        else:
            await bot.answer_callback_query(
                callback_query.id,
                text="خطا در حذف محصول."
            )
        
        # Return to products view
        callback_data = f"view_products_{category_id}" if category_id else "products"
        await process_admin_callback(callback_query, state)
        return
    
    # Service management
    if callback_data == "services":
        await bot.edit_message_text(
            "لطفاً ابتدا دسته‌بندی خدمات را انتخاب کنید:",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=get_admin_category_keyboard("service")
        )
        return
    
    # View services in category
    if callback_data.startswith("view_services_"):
        category_id = int(callback_data.split('_')[2])
        
        keyboard = get_admin_services_keyboard(category_id)
        
        category = db.get_category("service", category_id)
        title = "خدمات"
        if category:
            title = f"خدمات دسته {category['name']}"
        
        await bot.edit_message_text(
            title,
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=keyboard
        )
        return
    
    # Add service
    if callback_data.startswith("add_service_"):
        category_id = int(callback_data.split('_')[2])
        
        # Store category ID in state
        await state.update_data(
            admin_action="add_service",
            category_id=category_id
        )
        
        # Set state for service name input
        await AdminStates.ADD_SERVICE_NAME.set()
        
        # Request service name
        await bot.edit_message_text(
            "لطفاً نام خدمت جدید را وارد کنید:",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("لغو", callback_data="cancel_admin")
            )
        )
        return
    
    # Edit service
    if callback_data.startswith("edit_service_"):
        service_id = int(callback_data.split('_')[2])
        
        # Store service ID in state
        await state.update_data(
            admin_action="edit_service",
            service_id=service_id
        )
        
        # Set state for service name input
        await AdminStates.EDIT_ITEM_NAME.set()
        
        # Get current service name
        service = db.get_service(service_id)
        current_name = service['name'] if service else ""
        
        # Request new service name
        await bot.edit_message_text(
            f"ویرایش نام خدمت:\nنام فعلی: {current_name}\n\nلطفاً نام جدید را وارد کنید:",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("لغو", callback_data="cancel_admin")
            )
        )
        return
    
    # Delete service
    if callback_data.startswith("del_service_"):
        service_id = int(callback_data.split('_')[2])
        
        # Get service and category info
        service = db.get_service(service_id)
        category_id = service.get('category_id') if service else None
        
        # Delete service
        success = db.delete_service(service_id)
        
        if success:
            await bot.answer_callback_query(
                callback_query.id,
                text="خدمت با موفقیت حذف شد."
            )
        else:
            await bot.answer_callback_query(
                callback_query.id,
                text="خطا در حذف خدمت."
            )
        
        # Return to services view
        callback_data = f"view_services_{category_id}" if category_id else "services"
        await process_admin_callback(callback_query, state)
        return
    
    # Static content management
    if callback_data == "static":
        await bot.edit_message_text(
            "مدیریت محتوای ثابت",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=get_admin_static_keyboard()
        )
        return
    
    # Edit static content
    if callback_data.startswith("edit_static_"):
        content_type = callback_data.split('_')[2]
        
        # Store content type in state
        await state.update_data(
            admin_action="edit_static",
            content_type=content_type
        )
        
        # Set state for content input
        await AdminStates.EDIT_STATIC_CONTENT.set()
        
        # Get current content
        current_content = db.get_static_content(content_type)
        if content_type == "contact":
            title = "اطلاعات تماس"
        elif content_type == "about":
            title = "درباره ما"
        else:
            title = f"محتوای {content_type}"
        
        # Request new content
        await bot.edit_message_text(
            f"ویرایش {title}:\n\n"
            f"محتوای فعلی:\n{current_content}\n\n"
            f"لطفاً محتوای جدید را وارد کنید:",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("لغو", callback_data="cancel_admin")
            )
        )
        return
    
    # Inquiries management
    if callback_data == "inquiries":
        await bot.edit_message_text(
            "مدیریت درخواست‌های استعلام قیمت",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=get_admin_inquiries_keyboard()
        )
        return
    
    # View inquiries by status
    if callback_data.startswith("inquiries_"):
        status = callback_data.split('_')[1]
        status_filter = None if status == "all" else status
        
        # Get inquiries
        inquiries = db.get_inquiries(status_filter)
        
        if not inquiries:
            await bot.edit_message_text(
                f"هیچ درخواستی با وضعیت {status} یافت نشد.",
                callback_query.from_user.id,
                callback_query.message.message_id,
                reply_markup=get_admin_inquiries_keyboard()
            )
            return
        
        # Show first inquiry
        inquiry = inquiries[0]
        
        # Get item info
        item_info = ""
        if inquiry['item_type'] == 'product':
            product = db.get_product(inquiry['item_id'])
            if product:
                item_info = f"محصول: {product['name']}"
        elif inquiry['item_type'] == 'service':
            service = db.get_service(inquiry['item_id'])
            if service:
                item_info = f"خدمت: {service['name']}"
        
        # Create message text
        message_text = (
            f"درخواست #{inquiry['id']}\n"
            f"وضعیت: {inquiry['status']}\n"
            f"تاریخ: {inquiry['created_at']}\n\n"
            f"نام: {inquiry['name']}\n"
            f"شماره تماس: {inquiry['phone']}\n"
            f"توضیحات: {inquiry['description']}\n"
            f"{item_info}\n\n"
        )
        
        # Create keyboard for inquiry navigation
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        # Add status change buttons
        keyboard.add(
            InlineKeyboardButton(
                "در حال بررسی",
                callback_data=f"{ADMIN_PREFIX}inq_status_{inquiry['id']}_processing"
            ),
            InlineKeyboardButton(
                "تکمیل شده",
                callback_data=f"{ADMIN_PREFIX}inq_status_{inquiry['id']}_completed"
            ),
            InlineKeyboardButton(
                "لغو شده",
                callback_data=f"{ADMIN_PREFIX}inq_status_{inquiry['id']}_canceled"
            )
        )
        
        # Add navigation buttons if there are more than 1 inquiry
        if len(inquiries) > 1:
            keyboard.add(
                InlineKeyboardButton(
                    "بعدی",
                    callback_data=f"{ADMIN_PREFIX}inq_next_{inquiry['id']}_{status}"
                )
            )
        
        # Add back button
        keyboard.add(InlineKeyboardButton(BACK_BTN, callback_data=f"{ADMIN_PREFIX}inquiries"))
        
        await bot.edit_message_text(
            message_text,
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=keyboard
        )
        return
    
    # Change inquiry status
    if callback_data.startswith("inq_status_"):
        parts = callback_data.split('_')
        inquiry_id = int(parts[2])
        new_status = parts[3]
        
        # Update status
        success = db.update_inquiry_status(inquiry_id, new_status)
        
        if success:
            await bot.answer_callback_query(
                callback_query.id,
                text=f"وضعیت درخواست به '{new_status}' تغییر یافت."
            )
        else:
            await bot.answer_callback_query(
                callback_query.id,
                text="خطا در تغییر وضعیت درخواست."
            )
        
        # Return to inquiries view
        callback_data = f"inquiries_{new_status}"
        await process_admin_callback(callback_query, state)
        return
    
    # CSV import
    if callback_data == "csv":
        await bot.edit_message_text(
            "آپلود فایل CSV برای وارد کردن داده‌ها",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=get_admin_csv_keyboard()
        )
        return
    
    # Prepare for CSV upload
    if callback_data.startswith("csv_"):
        import_type = callback_data.split('_')[1]
        
        # Store import type in state
        await state.update_data(
            admin_action="import_csv",
            import_type=import_type
        )
        
        # Set state for file upload
        await AdminStates.UPLOAD_CSV.set()
        
        # Request file upload
        if import_type == "product":
            columns = "category_id, name, description, price, image_path"
        else:  # service
            columns = "category_id, name, description"
        
        await bot.edit_message_text(
            f"لطفاً فایل CSV {import_type} را آپلود کنید.\n\n"
            f"ستون‌های مورد نیاز: {columns}\n\n"
            f"توجه: فایل CSV باید با encoding UTF-8 باشد.",
            callback_query.from_user.id,
            callback_query.message.message_id,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("لغو", callback_data="cancel_admin")
            )
        )
        return

@dp.callback_query_handler(lambda c: c.data == "cancel_admin", state='*')
async def cancel_admin_action(callback_query: CallbackQuery, state: FSMContext):
    """Cancel admin action and return to admin panel."""
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    await bot.edit_message_text(
        "عملیات لغو شد.",
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=get_admin_keyboard()
    )

# Admin state handlers
@dp.message_handler(state=AdminStates.ADD_CATEGORY_NAME)
async def process_add_category_name(message: types.Message, state: FSMContext):
    """Process the name input for new category."""
    name = message.text.strip()
    
    if not name:
        await message.answer("لطفاً نام معتبر وارد کنید.")
        return
    
    # Get data from state
    data = await state.get_data()
    category_type = data.get('category_type')
    parent_id = data.get('parent_id')
    
    try:
        # Add category to database
        db.add_category(category_type, name, parent_id)
        
        # Clear state
        await state.finish()
        
        # Confirm and show updated categories
        keyboard = get_admin_category_keyboard(category_type, parent_id)
        await message.answer(
            f"دسته‌بندی '{name}' با موفقیت اضافه شد.",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error adding category: {e}")
        await message.answer(
            f"خطا در افزودن دسته‌بندی: {str(e)}",
            reply_markup=get_admin_keyboard()
        )
        await state.finish()

@dp.message_handler(state=AdminStates.ADD_PRODUCT_NAME)
async def process_add_product_name(message: types.Message, state: FSMContext):
    """Process the name input for new product."""
    name = message.text.strip()
    
    if not name:
        await message.answer("لطفاً نام معتبر وارد کنید.")
        return
    
    # Save name to state
    await state.update_data(name=name)
    
    # Move to description step
    await AdminStates.ADD_PRODUCT_DESC.set()
    
    await message.answer(
        "لطفاً توضیحات محصول را وارد کنید:",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("لغو", callback_data="cancel_admin")
        )
    )

@dp.message_handler(state=AdminStates.ADD_PRODUCT_DESC)
async def process_add_product_desc(message: types.Message, state: FSMContext):
    """Process the description input for new product."""
    description = message.text.strip()
    
    # Save description to state
    await state.update_data(description=description)
    
    # Move to price step
    await AdminStates.ADD_PRODUCT_PRICE.set()
    
    await message.answer(
        "لطفاً قیمت محصول را وارد کنید (اختیاری، برای رد کردن 'بدون قیمت' را ارسال کنید):",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("لغو", callback_data="cancel_admin")
        )
    )

@dp.message_handler(state=AdminStates.ADD_PRODUCT_PRICE)
async def process_add_product_price(message: types.Message, state: FSMContext):
    """Process the price input for new product and complete the process."""
    price = message.text.strip()
    
    if price.lower() == "بدون قیمت":
        price = None
    
    # Save price to state
    await state.update_data(price=price)
    
    # Get all data from state
    data = await state.get_data()
    
    try:
        # Add product to database
        db.add_product(
            data['category_id'],
            data['name'],
            data['description'],
            price
        )
        
        # Clear state
        await state.finish()
        
        # Confirm and show updated products
        keyboard = get_admin_products_keyboard(data['category_id'])
        await message.answer(
            f"محصول '{data['name']}' با موفقیت اضافه شد.",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error adding product: {e}")
        await message.answer(
            f"خطا در افزودن محصول: {str(e)}",
            reply_markup=get_admin_keyboard()
        )
        await state.finish()

@dp.message_handler(state=AdminStates.ADD_SERVICE_NAME)
async def process_add_service_name(message: types.Message, state: FSMContext):
    """Process the name input for new service."""
    name = message.text.strip()
    
    if not name:
        await message.answer("لطفاً نام معتبر وارد کنید.")
        return
    
    # Save name to state
    await state.update_data(name=name)
    
    # Move to description step
    await AdminStates.ADD_SERVICE_DESC.set()
    
    await message.answer(
        "لطفاً توضیحات خدمت را وارد کنید:",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("لغو", callback_data="cancel_admin")
        )
    )

@dp.message_handler(state=AdminStates.ADD_SERVICE_DESC)
async def process_add_service_desc(message: types.Message, state: FSMContext):
    """Process the description input for new service and complete the process."""
    description = message.text.strip()
    
    # Save description to state
    await state.update_data(description=description)
    
    # Get all data from state
    data = await state.get_data()
    
    try:
        # Add service to database
        db.add_service(
            data['category_id'],
            data['name'],
            description
        )
        
        # Clear state
        await state.finish()
        
        # Confirm and show updated services
        keyboard = get_admin_services_keyboard(data['category_id'])
        await message.answer(
            f"خدمت '{data['name']}' با موفقیت اضافه شد.",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error adding service: {e}")
        await message.answer(
            f"خطا در افزودن خدمت: {str(e)}",
            reply_markup=get_admin_keyboard()
        )
        await state.finish()

@dp.message_handler(state=AdminStates.EDIT_STATIC_CONTENT)
async def process_edit_static_content(message: types.Message, state: FSMContext):
    """Process the input for static content editing."""
    content = message.text.strip()
    
    # Get data from state
    data = await state.get_data()
    content_type = data.get('content_type')
    
    try:
        # Update static content
        db.update_static_content(content_type, content)
        
        # Clear state
        await state.finish()
        
        # Confirm and show static content menu
        await message.answer(
            f"محتوای {content_type} با موفقیت به‌روزرسانی شد.",
            reply_markup=get_admin_static_keyboard()
        )
    except Exception as e:
        logger.error(f"Error updating static content: {e}")
        await message.answer(
            f"خطا در به‌روزرسانی محتوا: {str(e)}",
            reply_markup=get_admin_keyboard()
        )
        await state.finish()

@dp.message_handler(state=AdminStates.EDIT_ITEM_NAME)
async def process_edit_item_name(message: types.Message, state: FSMContext):
    """Process the name input for editing an item."""
    name = message.text.strip()
    
    if not name:
        await message.answer("لطفاً نام معتبر وارد کنید.")
        return
    
    # Get data from state
    data = await state.get_data()
    admin_action = data.get('admin_action')
    
    try:
        if admin_action == "edit_category":
            # Update category name
            category_type = data.get('category_type')
            category_id = data.get('category_id')
            db.update_category(category_type, category_id, name)
            
            # Get parent info
            category = db.get_category(category_type, category_id)
            parent_id = category.get('parent_id') if category else None
            
            # Clear state
            await state.finish()
            
            # Show updated categories
            keyboard = get_admin_category_keyboard(category_type, parent_id)
            await message.answer(
                f"نام دسته‌بندی به '{name}' تغییر یافت.",
                reply_markup=keyboard
            )
            
        elif admin_action == "edit_product":
            # Save name and move to description step
            await state.update_data(name=name)
            await AdminStates.EDIT_ITEM_DESC.set()
            
            # Get current description
            product_id = data.get('product_id')
            product = db.get_product(product_id)
            current_desc = product['description'] if product else ""
            
            await message.answer(
                f"ویرایش توضیحات محصول:\nتوضیحات فعلی:\n{current_desc}\n\nلطفاً توضیحات جدید را وارد کنید:",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("لغو", callback_data="cancel_admin")
                )
            )
            
        elif admin_action == "edit_service":
            # Save name and move to description step
            await state.update_data(name=name)
            await AdminStates.EDIT_ITEM_DESC.set()
            
            # Get current description
            service_id = data.get('service_id')
            service = db.get_service(service_id)
            current_desc = service['description'] if service else ""
            
            await message.answer(
                f"ویرایش توضیحات خدمت:\nتوضیحات فعلی:\n{current_desc}\n\nلطفاً توضیحات جدید را وارد کنید:",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("لغو", callback_data="cancel_admin")
                )
            )
            
        else:
            await message.answer(
                "خطا: عملیات نامشخص.",
                reply_markup=get_admin_keyboard()
            )
            await state.finish()
            
    except Exception as e:
        logger.error(f"Error in edit item name: {e}")
        await message.answer(
            f"خطا در ویرایش نام: {str(e)}",
            reply_markup=get_admin_keyboard()
        )
        await state.finish()

@dp.message_handler(state=AdminStates.EDIT_ITEM_DESC)
async def process_edit_item_desc(message: types.Message, state: FSMContext):
    """Process the description input for editing an item."""
    description = message.text.strip()
    
    # Get data from state
    data = await state.get_data()
    admin_action = data.get('admin_action')
    name = data.get('name')
    
    try:
        if admin_action == "edit_product":
            # Save description and move to price step
            await state.update_data(description=description)
            await AdminStates.EDIT_ITEM_PRICE.set()
            
            # Get current price
            product_id = data.get('product_id')
            product = db.get_product(product_id)
            current_price = product['price'] if product and product['price'] else "بدون قیمت"
            
            await message.answer(
                f"ویرایش قیمت محصول:\nقیمت فعلی: {current_price}\n\nلطفاً قیمت جدید را وارد کنید (برای حذف قیمت 'بدون قیمت' را ارسال کنید):",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("لغو", callback_data="cancel_admin")
                )
            )
            
        elif admin_action == "edit_service":
            # Update service
            service_id = data.get('service_id')
            db.update_service(service_id, name, description)
            
            # Get service info
            service = db.get_service(service_id)
            category_id = service.get('category_id') if service else None
            
            # Clear state
            await state.finish()
            
            # Show updated services
            keyboard = get_admin_services_keyboard(category_id)
            await message.answer(
                f"خدمت با موفقیت به‌روزرسانی شد.",
                reply_markup=keyboard
            )
            
        else:
            await message.answer(
                "خطا: عملیات نامشخص.",
                reply_markup=get_admin_keyboard()
            )
            await state.finish()
            
    except Exception as e:
        logger.error(f"Error in edit item description: {e}")
        await message.answer(
            f"خطا در ویرایش توضیحات: {str(e)}",
            reply_markup=get_admin_keyboard()
        )
        await state.finish()

@dp.message_handler(state=AdminStates.EDIT_ITEM_PRICE)
async def process_edit_item_price(message: types.Message, state: FSMContext):
    """Process the price input for editing a product."""
    price = message.text.strip()
    
    if price.lower() == "بدون قیمت":
        price = None
    
    # Get data from state
    data = await state.get_data()
    product_id = data.get('product_id')
    name = data.get('name')
    description = data.get('description')
    
    try:
        # Update product
        db.update_product(product_id, name, description, price)
        
        # Get product info
        product = db.get_product(product_id)
        category_id = product.get('category_id') if product else None
        
        # Clear state
        await state.finish()
        
        # Show updated products
        keyboard = get_admin_products_keyboard(category_id)
        await message.answer(
            f"محصول با موفقیت به‌روزرسانی شد.",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in edit product price: {e}")
        await message.answer(
            f"خطا در ویرایش قیمت: {str(e)}",
            reply_markup=get_admin_keyboard()
        )
        await state.finish()

@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=AdminStates.UPLOAD_CSV)
async def process_csv_upload(message: types.Message, state: FSMContext):
    """Process uploaded CSV file."""
    # Get data from state
    data = await state.get_data()
    import_type = data.get('import_type')
    
    if not message.document:
        await message.answer("لطفاً یک فایل CSV آپلود کنید.")
        return
    
    # Check file extension
    if not message.document.file_name.lower().endswith('.csv'):
        await message.answer("لطفاً یک فایل با پسوند .csv آپلود کنید.")
        return
    
    try:
        # Download file
        file_id = message.document.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        
        # Create local file path
        local_file_path = os.path.join(configuration.DATA_DIR, message.document.file_name)
        
        # Download file
        await bot.download_file(file_path, local_file_path)
        
        # Import CSV
        success_count, error_count, error_messages = db.import_csv(local_file_path, import_type)
        
        # Clear state
        await state.finish()
        
        # Report results
        result_text = f"آپلود CSV {import_type} انجام شد:\n\n"
        result_text += f"موارد موفق: {success_count}\n"
        result_text += f"خطاها: {error_count}\n\n"
        
        if error_count > 0:
            result_text += "گزارش خطاها:\n"
            for i, error in enumerate(error_messages[:10], 1):
                result_text += f"{i}. {error}\n"
            
            if len(error_messages) > 10:
                result_text += f"و {len(error_messages) - 10} خطای دیگر...\n"
        
        await message.answer(
            result_text,
            reply_markup=get_admin_csv_keyboard()
        )
        
        # Clean up file
        os.remove(local_file_path)
        
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        await message.answer(
            f"خطا در پردازش فایل CSV: {str(e)}",
            reply_markup=get_admin_keyboard()
        )
        await state.finish()

# Error handler
@dp.errors_handler()
async def error_handler(update, exception):
    """Handle errors in the dispatcher."""
    logger.error(f"Update {update} caused error {exception}")
    
    try:
        # Check if we can identify the chat to send error message
        if hasattr(update, 'message') and update.message:
            await update.message.answer(ERROR_MESSAGE)
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.answer(ERROR_MESSAGE)
    except Exception as e:
        logger.error(f"Error in error handler: {e}")
    
    return True

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs(configuration.DATA_DIR, exist_ok=True)
    
    logger.info("Starting bot...")
    executor.start_polling(dp, skip_updates=True)
