from aiogram import Router, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, URLInputFile, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
import os
import traceback
from datetime import datetime
from database import Database
from configuration import (
    PRODUCTS_BTN, SERVICES_BTN, INQUIRY_BTN, EDUCATION_BTN, 
    CONTACT_BTN, ABOUT_BTN, SEARCH_BTN, EDUCATION_PREFIX, 
    PRODUCT_PREFIX, SERVICE_PREFIX, CATEGORY_PREFIX,
    BACK_PREFIX, INQUIRY_PREFIX, ADMIN_PREFIX
)

# Initialize router and database - use name to better identify it in logs
router = Router(name="main_router")
db = Database()

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# Get admin ID from environment variable
ADMIN_ID = os.environ.get('ADMIN_ID')
if ADMIN_ID:
    try:
        ADMIN_ID = int(ADMIN_ID)
    except ValueError:
        logger.error(f"Invalid ADMIN_ID: {ADMIN_ID}")
        ADMIN_ID = None
else:
    logger.warning("ADMIN_ID not set")

# Define FSM states for various flows
class UserStates(StatesGroup):
    browse_categories = State()
    view_product = State()
    view_service = State()
    inquiry_name = State()
    inquiry_phone = State()
    inquiry_description = State()
    waiting_for_confirmation = State()

# Start command handler - add a debug message to see if it's being called
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command - initial entry point"""
    try:
        logging.info(f"Start command received from user: {message.from_user.id}")
        await state.clear()
        
        # Welcome message
        welcome_text = (
            f"🎉 سلام {message.from_user.first_name}!\n\n"
            "به ربات فروشگاه محصولات و خدمات ارتباطی خوش آمدید.\n"
            "از منوی زیر گزینه مورد نظر خود را انتخاب کنید:"
        )
        
        # Import the keyboard function from keyboards.py
        from keyboards import main_menu_keyboard
        
        # Get the main menu keyboard
        keyboard = main_menu_keyboard()
        
        # Log that we're about to send the message with buttons
        logging.info("Sending welcome message with keyboard buttons")
        
        # Send the message with the solid buttons
        await message.answer(welcome_text, reply_markup=keyboard)
        logging.info("Start command response sent successfully")
    except Exception as e:
        logging.error(f"Error in start command handler: {e}")
        logging.error(traceback.format_exc())
        await message.answer("متأسفانه خطایی رخ داد. لطفاً مجدداً تلاش کنید.")

# Help command handler
@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = (
        "🆘 راهنمای ربات:\n\n"
        "/start - شروع مجدد ربات\n"
        "/products - مشاهده محصولات\n"
        "/services - مشاهده خدمات\n"
        "/contact - تماس با ما\n"
        "/about - درباره ما"
    )
    await message.answer(help_text)

# This import is now at the top of the file

# Products command handler
@router.message(Command("products"))
@router.message(lambda message: message.text == PRODUCTS_BTN)
async def cmd_products(message: Message, state: FSMContext):
    """Handle /products command or Products button"""
    await show_categories(message, 'product', state)

# Services command handler
@router.message(Command("services"))
@router.message(lambda message: message.text == SERVICES_BTN)
async def cmd_services(message: Message, state: FSMContext):
    """Handle /services command or Services button"""
    await show_categories(message, 'service', state)

# Contact command handler
@router.message(Command("contact"))
@router.message(lambda message: message.text == CONTACT_BTN)
async def cmd_contact(message: Message):
    """Handle /contact command or Contact button"""
    try:
        logging.info(f"Contact information requested by user: {message.from_user.id}")
        contact_text = db.get_static_content('contact')
        if not contact_text:
            await message.answer("⚠️ اطلاعات تماس در حال حاضر در دسترس نیست. لطفا بعدا تلاش کنید.")
            logging.warning("Contact information not found in database")
            return
            
        # Format the message nicely
        formatted_text = f"📞 *اطلاعات تماس*\n\n{contact_text}"
        await message.answer(formatted_text, parse_mode="Markdown")
        logging.info("Contact information sent successfully")
    except Exception as e:
        error_msg = f"خطا در دریافت اطلاعات تماس: {str(e)}"
        logging.error(f"Error in cmd_contact: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

# About command handler
@router.message(Command("about"))
@router.message(lambda message: message.text == ABOUT_BTN)
async def cmd_about(message: Message):
    """Handle /about command or About button"""
    try:
        logging.info(f"About information requested by user: {message.from_user.id}")
        about_text = db.get_static_content('about')
        if not about_text:
            await message.answer("⚠️ اطلاعات درباره ما در حال حاضر در دسترس نیست. لطفا بعدا تلاش کنید.")
            logging.warning("About information not found in database")
            return
            
        # Format the message nicely
        formatted_text = f"ℹ️ *درباره ما*\n\n{about_text}"
        await message.answer(formatted_text, parse_mode="Markdown")
        logging.info("About information sent successfully")
    except Exception as e:
        error_msg = f"خطا در دریافت اطلاعات درباره ما: {str(e)}"
        logging.error(f"Error in cmd_about: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

# Education button handler
@router.message(lambda message: message.text == EDUCATION_BTN)
async def cmd_education(message: Message):
    """Handle Education button"""
    try:
        logging.info(f"Educational content requested by user: {message.from_user.id}")
        categories = db.get_educational_categories()
        if not categories:
            await message.answer("⚠️ محتوای آموزشی در حال حاضر در دسترس نیست. لطفا بعدا تلاش کنید.")
            logging.warning("No educational categories found in database")
            return
        
        # Format the message nicely
        from keyboards import education_categories_keyboard
        keyboard = education_categories_keyboard(categories)
        await message.answer(
            "📚 *محتوای آموزشی*\n\nلطفا یکی از دسته‌بندی‌های زیر را انتخاب کنید:", 
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logging.info(f"Educational categories sent: {len(categories)} categories")
    except Exception as e:
        error_msg = f"خطا در دریافت محتوای آموزشی: {str(e)}"
        logging.error(f"Error in cmd_education: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

# Inquiry button handler
@router.message(lambda message: message.text == INQUIRY_BTN)
async def cmd_inquiry(message: Message, state: FSMContext):
    """Handle Inquiry button"""
    try:
        logging.info(f"Inquiry process started by user: {message.from_user.id}")
        
        # Format the message nicely
        inquiry_text = (
            "📝 *استعلام قیمت*\n\n"
            "برای ارسال استعلام قیمت، لطفا اطلاعات زیر را به ترتیب وارد کنید:\n"
            "1️⃣ نام و نام خانوادگی\n"
            "2️⃣ شماره تماس\n"
            "3️⃣ شرح محصول یا خدمات درخواستی\n\n"
            "لطفا نام و نام خانوادگی خود را وارد کنید:"
        )
        
        await message.answer(inquiry_text, parse_mode="Markdown")
        await state.set_state(UserStates.inquiry_name)
        logging.info(f"User {message.from_user.id} entered inquiry name state")
    except Exception as e:
        error_msg = f"خطا در شروع فرآیند استعلام: {str(e)}"
        logging.error(f"Error in cmd_inquiry: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

# Search button handler
@router.message(lambda message: message.text == SEARCH_BTN)
async def cmd_search(message: Message):
    """Handle Search button"""
    try:
        logging.info(f"Search requested by user: {message.from_user.id}")
        await message.answer(
            "🔍 *جستجو*\n\n"
            "این قابلیت در حال حاضر در دسترس نیست. لطفا بعدا تلاش کنید.",
            parse_mode="Markdown"
        )
        logging.info("Search feature not available message sent")
    except Exception as e:
        logging.error(f"Error in cmd_search: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

# Button callbacks
@router.callback_query(F.data == "products")
async def callback_products(callback: CallbackQuery, state: FSMContext):
    """Handle products button click"""
    await callback.answer()
    await show_categories(callback.message, 'product', state)

@router.callback_query(F.data == "services")
async def callback_services(callback: CallbackQuery, state: FSMContext):
    """Handle services button click"""
    await callback.answer()
    await show_categories(callback.message, 'service', state)

@router.callback_query(F.data == "contact")
async def callback_contact(callback: CallbackQuery):
    """Handle contact button click"""
    await callback.answer()
    contact_text = db.get_static_content('contact')
    await callback.message.answer(contact_text)

@router.callback_query(F.data == "about")
async def callback_about(callback: CallbackQuery):
    """Handle about button click"""
    await callback.answer()
    about_text = db.get_static_content('about')
    await callback.message.answer(about_text)

@router.callback_query(F.data == "educational")
async def callback_educational(callback: CallbackQuery):
    """Handle educational content button click"""
    await callback.answer()
    
    # Get educational categories
    categories = db.get_educational_categories()
    
    if not categories:
        await callback.message.answer("در حال حاضر محتوای آموزشی موجود نیست.")
        return
    
    # Create keyboard with educational categories
    from keyboards import education_categories_keyboard
    keyboard = education_categories_keyboard(categories)
    
    await callback.message.answer("🎓 دسته‌بندی محتوای آموزشی را انتخاب کنید:", 
                               reply_markup=keyboard)

@router.callback_query(F.data.startswith(f"{EDUCATION_PREFIX}cat_"))
async def callback_educational_category(callback: CallbackQuery):
    """Handle educational category selection"""
    await callback.answer()
    
    try:
        # استخراج شناسه دسته‌بندی
        category_id = int(callback.data.replace(f"{EDUCATION_PREFIX}cat_", ""))
        logging.info(f"Selected educational category ID: {category_id}")
        
        # دریافت اطلاعات دسته‌بندی
        category_info = None
        categories = db.get_educational_categories()
        logging.info(f"All educational categories: {categories}")
        
        for cat in categories:
            if cat['id'] == category_id:
                category_info = cat
                break
                
        if not category_info:
            logging.error(f"Category info not found for ID: {category_id}")
            await callback.message.answer("⚠️ دسته‌بندی مورد نظر یافت نشد.")
            return
            
        category_name = category_info['name']
        logging.info(f"Category name: {category_name}")
        
        # دریافت محتوای آموزشی برای این دسته‌بندی
        content_list = db.get_all_educational_content(category_id=category_id)
        logging.info(f"Content list for category {category_id}: {content_list}")
        
        if not content_list:
            logging.warning(f"No educational content found for category ID: {category_id}")
            
            # دریافت محتوای آموزشی با استفاده از نام دسته بندی (رفتار قدیمی)
            legacy_content = db.get_all_educational_content(category=category_name)
            logging.info(f"Legacy content search by category name: {legacy_content}")
            
            if legacy_content:
                content_list = legacy_content
                logging.info(f"Using legacy content for display: {content_list}")
            else:
                await callback.message.answer(f"⚠️ محتوای آموزشی برای دسته‌بندی '{category_name}' موجود نیست.")
                return
        
        # ساخت کیبورد با آیتم‌های محتوا
        from keyboards import education_content_keyboard
        keyboard = education_content_keyboard(content_list, category_id)
        
        await callback.message.answer(f"📚 محتوای آموزشی در دسته‌بندی '{category_name}':", 
                               reply_markup=keyboard)
    except Exception as e:
        logging.error(f"خطا در نمایش محتوای آموزشی دسته‌بندی: {str(e)}")
        logging.error(traceback.format_exc())
        await callback.message.answer("⚠️ خطایی در نمایش محتوای آموزشی رخ داد. لطفا مجددا تلاش کنید.")

@router.callback_query(F.data == f"{EDUCATION_PREFIX}categories")
async def callback_educational_categories(callback: CallbackQuery):
    """Handle going back to educational categories"""
    await callback.answer()
    
    # Get educational categories
    categories = db.get_educational_categories()
    
    if not categories:
        await callback.message.answer("در حال حاضر محتوای آموزشی موجود نیست.")
        return
    
    # Create keyboard with educational categories
    from keyboards import education_categories_keyboard
    keyboard = education_categories_keyboard(categories)
    
    await callback.message.answer("🎓 دسته‌بندی محتوای آموزشی را انتخاب کنید:", 
                           reply_markup=keyboard)

@router.callback_query(
    lambda c: c.data and c.data.startswith(f"{EDUCATION_PREFIX}") and "cat_" not in c.data and "categories" not in c.data
)
async def callback_educational_content(callback: CallbackQuery):
    """Handle educational content selection - direct navigation to content"""
    await callback.answer()
    
    try:
        # Extract content ID (removing the prefix)
        content_id = int(callback.data.replace(f"{EDUCATION_PREFIX}", ""))
        
        # Get content details
        content = db.get_educational_content(content_id)
        
        if not content:
            await callback.message.answer("⚠️ محتوای آموزشی مورد نظر یافت نشد.")
            return
        
        # Get category_id for back button
        category_id = content.get('category_id')
        if not category_id:
            # اگر category_id موجود نیست، به صفحه اصلی دسته‌بندی‌ها برگردیم
            from keyboards import education_detail_keyboard
            keyboard = education_detail_keyboard(0)  # صفر به عنوان پیش‌فرض
        else:
            from keyboards import education_detail_keyboard
            keyboard = education_detail_keyboard(category_id)
        
        # Get the associated media files
        media_files = db.get_educational_content_media(content_id)
        
        if media_files:
            logging.info(f"Found {len(media_files)} media files for educational content {content_id}")
            
            # Format the content title and text
            title = content['title']
            content_text = content.get('content', '')
            
            # Check if text is too long for a media caption (Telegram limit ~1024 chars)
            MAX_CAPTION_LENGTH = 850  # Leave some room for the title and "متن کامل" link
            
            caption_text = f"📖 *{title}*\n\n"
            
            if len(content_text) > MAX_CAPTION_LENGTH:
                # Create a shortened version with link to full text
                short_text = content_text[:MAX_CAPTION_LENGTH] + "...\n\n"
                short_text += "[(متن کامل)](https://telegra.ph/temp-link)"  # Placeholder, will be updated
                caption_text += short_text
                
                # Create Telegra.ph article with full content
                from utils import create_telegraph_page
                try:
                    telegraph_url = await create_telegraph_page(
                        title=title,
                        content=content_text,
                        author="RFCatalogbot"
                    )
                    
                    # Update the caption with the actual link
                    if telegraph_url:
                        caption_text = caption_text.replace("https://telegra.ph/temp-link", telegraph_url)
                except Exception as e:
                    logging.error(f"Error creating Telegraph page: {e}")
                    # Fallback to regular text without link
                    caption_text = f"📖 *{title}*\n\n{content_text[:MAX_CAPTION_LENGTH]}..."
            else:
                # Text fits in caption, use it directly
                caption_text += content_text
            
            # Send as media group with caption on first item
            await send_educational_media_group(
                chat_id=callback.message.chat.id, 
                media_files=media_files, 
                caption=caption_text, 
                keyboard=keyboard
            )
        else:
            # No media files, send as regular text message
            content_text = f"📖 *{content['title']}*\n\n{content['content']}"
            await callback.message.answer(content_text, parse_mode="Markdown", reply_markup=keyboard)
            
    except Exception as e:
        logging.error(f"خطا در نمایش محتوای آموزشی: {str(e)}")
        logging.error(traceback.format_exc())
        await callback.message.answer("⚠️ خطایی در نمایش محتوا رخ داد. لطفا مجددا تلاش کنید.")

@router.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: CallbackQuery, state: FSMContext):
    """Handle back to main menu button"""
    await callback.answer()
    await state.clear()
    
    # Create main menu keyboard
    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 محصولات", callback_data="products")
    kb.button(text="🛠️ خدمات", callback_data="services")
    kb.button(text="📚 محتوای آموزشی", callback_data="educational")
    kb.button(text="📞 تماس با ما", callback_data="contact")
    kb.button(text="ℹ️ درباره ما", callback_data="about")
    kb.adjust(2, 2, 1)
    
    await callback.message.answer("به منوی اصلی بازگشتید:", reply_markup=kb.as_markup())

# Helper functions for category navigation
async def show_categories(message, cat_type, state, parent_id=None):
    """Show categories for products or services"""
    await state.update_data(cat_type=cat_type)
    
    # Get categories
    categories = db.get_categories(parent_id, cat_type)
    
    if not categories:
        # If no categories but we're in a subcategory, show items
        if parent_id is not None:
            if cat_type == 'product':
                products = db.get_products_by_category(parent_id)
                if products:
                    await show_products_list(message, products, parent_id)
                else:
                    await message.answer("محصولی در این دسته‌بندی وجود ندارد.")
            else:  # service
                services = db.get_products_by_category(parent_id, 'service')
                if services:
                    await show_services_list(message, services, parent_id)
                else:
                    await message.answer("خدمتی در این دسته‌بندی وجود ندارد.")
        else:
            # No top-level categories
            await message.answer(f"دسته‌بندی {'محصولات' if cat_type == 'product' else 'خدمات'} موجود نیست.")
        return
    
    # Build keyboard with categories
    kb = InlineKeyboardBuilder()
    for category in categories:
        kb.button(text=category['name'], callback_data=f"category:{category['id']}")
    
    # Add back button if in subcategory
    if parent_id is not None:
        parent_category = db.get_category(parent_id)
        if parent_category and parent_category.get('parent_id') is not None:
            kb.button(text="🔙 بازگشت", callback_data=f"category:{parent_category['parent_id']}")
        else:
            kb.button(text="🔙 بازگشت به دسته‌بندی‌های اصلی", 
                     callback_data=f"{'products' if cat_type == 'product' else 'services'}")
    else:
        kb.button(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")
    
    kb.adjust(1)
    
    await message.answer(f"دسته‌بندی {'محصولات' if cat_type == 'product' else 'خدمات'} را انتخاب کنید:", 
                       reply_markup=kb.as_markup())
    
    # Set state
    await state.set_state(UserStates.browse_categories)

@router.callback_query(F.data.startswith("category:"))
async def callback_category(callback: CallbackQuery, state: FSMContext):
    """Handle category selection"""
    await callback.answer()
    
    # Extract category ID
    category_id = int(callback.data.split(':', 1)[1])
    
    # Get the category type from state
    state_data = await state.get_data()
    cat_type = state_data.get('cat_type', 'product')
    
    # Show subcategories or products/services for this category
    await show_categories(callback.message, cat_type, state, category_id)

async def show_products_list(message, products, category_id):
    """Show list of products in a category"""
    # Build keyboard with products
    kb = InlineKeyboardBuilder()
    for product in products:
        kb.button(text=product['name'], callback_data=f"product:{product['id']}")
    
    # Add back button
    kb.button(text="🔙 بازگشت", callback_data=f"category:{category_id}")
    kb.adjust(1)
    
    await message.answer("محصولات موجود در این دسته‌بندی:", reply_markup=kb.as_markup())

async def show_services_list(message, services, category_id):
    """Show list of services in a category"""
    # Build keyboard with services
    kb = InlineKeyboardBuilder()
    for service in services:
        kb.button(text=service['name'], callback_data=f"service:{service['id']}")
    
    # Add back button
    kb.button(text="🔙 بازگشت", callback_data=f"category:{category_id}")
    kb.adjust(1)
    
    await message.answer("خدمات موجود در این دسته‌بندی:", reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("product:"))
async def callback_product(callback: CallbackQuery, state: FSMContext):
    """Handle product selection"""
    await callback.answer()
    
    # Extract product ID
    product_id = int(callback.data.split(':', 1)[1])
    
    # Get product details
    product = db.get_product(product_id)
    
    if not product:
        await callback.message.answer("محصول مورد نظر یافت نشد.")
        return
    
    # Save product_id in state for inquiry
    await state.update_data(product_id=product_id)
    await state.set_state(UserStates.view_product)
    
    # Get product media
    media_files = db.get_product_media(product_id)
    
    # Format the product details
    product_text = (
        f"🛒 {product['name']}\n\n"
        f"💰 قیمت: {product['price']} تومان\n\n"
        f"📝 توضیحات:\n{product['description']}\n\n"
    )
    
    # Add keyboard for inquiry and back
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍️ استعلام قیمت", callback_data=f"inquiry:product:{product_id}")
    
    # Get category for back button
    kb.button(text="🔙 بازگشت", callback_data=f"category:{product['category_id']}")
    kb.adjust(1)
    
    # First send text description
    await callback.message.answer(product_text, reply_markup=kb.as_markup())
    
    # Then send media files if available
    if media_files:
        await send_product_media(callback.message.chat.id, media_files)

@router.callback_query(F.data.startswith("service:"))
async def callback_service(callback: CallbackQuery, state: FSMContext):
    """Handle service selection"""
    await callback.answer()
    
    # Extract service ID
    service_id = int(callback.data.split(':', 1)[1])
    
    # Get service details
    service = db.get_service(service_id)
    
    if not service:
        await callback.message.answer("خدمت مورد نظر یافت نشد.")
        return
    
    # Save service_id in state for inquiry
    await state.update_data(service_id=service_id)
    await state.set_state(UserStates.view_service)
    
    # Get service media
    media_files = db.get_service_media(service_id)
    
    # Format the service details
    service_text = (
        f"🛠️ {service['name']}\n\n"
        f"💰 قیمت: {service['price']} تومان\n\n"
        f"📝 توضیحات:\n{service['description']}\n\n"
    )
    
    # Add keyboard for inquiry and back
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍️ استعلام قیمت", callback_data=f"inquiry:service:{service_id}")
    
    # Get category for back button
    kb.button(text="🔙 بازگشت", callback_data=f"category:{service['category_id']}")
    kb.adjust(1)
    
    # First send text description
    await callback.message.answer(service_text, reply_markup=kb.as_markup())
    
    # Then send media files if available
    if media_files:
        await send_service_media(callback.message.chat.id, media_files)

# Media handling functions
async def send_educational_media(chat_id, media_files):
    """Send educational content media files to user"""
    from bot import bot  # Import bot here to avoid circular imports
    
    # Check if we have any media files
    if not media_files:
        logging.warning(f"No media files provided to send_educational_media for chat_id {chat_id}")
        return
        
    logging.info(f"Attempting to send {len(media_files)} educational media files to chat_id {chat_id}")
    
    # Define possible paths to check
    media_paths = [
        './', 
        './static/', 
        './static/images/', 
        './static/photos/',
        './static/uploads/',
        './static/media/',
        './static/media/educational/',
        './static/products/',
        './attached_assets/',
        './data/',
    ]
    
    for media in media_files:
        try:
            file_id = media.get('file_id', '')
            local_path = media.get('local_path', '')
            file_type = media.get('file_type', 'photo')
            
            # Log the full media info for debugging
            logging.info(f"Processing educational media: file_id={file_id}, local_path={local_path}, file_type={file_type}")
            
            # Check if we have any valid path to use
            if not file_id and not local_path:
                logging.warning(f"Both file_id and local_path empty for educational media: {media}")
                continue
            
            # Prioritize checking local_path if available
            if local_path and os.path.isfile(local_path):
                logging.info(f"Using educational media local_path that exists: {local_path}")
                
                if file_type == 'photo':
                    photo_file = FSInputFile(local_path)
                    await bot.send_photo(chat_id=chat_id, photo=photo_file)
                    logging.info(f"Sent educational photo from local_path: {local_path}")
                    continue  # Skip the rest of the loop for this media item
                elif file_type == 'video':
                    video_file = FSInputFile(local_path)
                    await bot.send_video(chat_id=chat_id, video=video_file)
                    logging.info(f"Sent educational video from local_path: {local_path}")
                    continue  # Skip the rest of the loop for this media item
            
            # Handle different file location scenarios for file_id
            if isinstance(file_id, str) and file_id.startswith('http'):
                # It's a URL, use URLInputFile
                logging.info(f"Educational media file is a URL: {file_id}")
                file = URLInputFile(file_id)
                
                if file_type == 'photo':
                    await bot.send_photo(chat_id=chat_id, photo=file)
                    logging.info(f"Sent educational photo from URL: {file_id}")
                elif file_type == 'video':
                    await bot.send_video(chat_id=chat_id, video=file)
                    logging.info(f"Sent educational video from URL: {file_id}")
                    
            elif file_id and os.path.isfile(file_id):
                # It's a local file that exists at the given path
                logging.info(f"Educational media file is a local path that exists: {file_id}")
                
                if file_type == 'photo':
                    photo_file = FSInputFile(file_id)
                    await bot.send_photo(chat_id=chat_id, photo=photo_file)
                    logging.info(f"Sent educational photo from local file: {file_id}")
                elif file_type == 'video':
                    video_file = FSInputFile(file_id)
                    await bot.send_video(chat_id=chat_id, video=video_file)
                    logging.info(f"Sent educational video from local file: {file_id}")
            else:
                # Try to find the file in various directories
                file_found = False
                
                # If a path pattern starts with 'media/' or 'static/' (non-Telegram file_id format)
                if file_id and ('/' in file_id):
                    # Handle common path patterns by checking root and with './static/' prefix
                    possible_paths = [
                        file_id,                # As is
                        f"./{file_id}",         # With ./ prefix
                        f"./static/{file_id}",  # With ./static/ prefix
                    ]
                    
                    for path in possible_paths:
                        if os.path.isfile(path):
                            logging.info(f"Found educational media at alternative path: {path}")
                            file_found = True
                            
                            if file_type == 'photo':
                                photo_file = FSInputFile(path)
                                await bot.send_photo(chat_id=chat_id, photo=photo_file)
                                logging.info(f"Sent educational photo from alt path: {path}")
                            elif file_type == 'video':
                                video_file = FSInputFile(path)
                                await bot.send_video(chat_id=chat_id, video=video_file)
                                logging.info(f"Sent educational video from alt path: {path}")
                                
                            break
                
                # If file not found yet and path doesn't contain '/', try all media directories
                if not file_found and '/' not in file_id:
                    for path in media_paths:
                        full_path = f"{path}{file_id}"
                        if os.path.isfile(full_path):
                            logging.info(f"Found educational media file at {full_path}")
                            file_found = True
                            
                            if file_type == 'photo':
                                photo_file = FSInputFile(full_path)
                                await bot.send_photo(chat_id=chat_id, photo=photo_file)
                                logging.info(f"Sent educational photo from path: {full_path}")
                            elif file_type == 'video':
                                video_file = FSInputFile(full_path)
                                await bot.send_video(chat_id=chat_id, video=video_file)
                                logging.info(f"Sent educational video from path: {full_path}")
                                
                            break
                
                # If file wasn't found in any of our directories, try as a Telegram file_id (last resort)
                if not file_found:
                    # Only if it doesn't look like a local path pattern (no slashes)
                    if '/' not in file_id:
                        logging.info(f"Trying as Telegram file_id: {file_id}")
                        
                        try:
                            if file_type == 'photo':
                                await bot.send_photo(chat_id=chat_id, photo=file_id)
                                logging.info(f"Sent educational photo using file_id: {file_id}")
                            elif file_type == 'video':
                                await bot.send_video(chat_id=chat_id, video=file_id)
                                logging.info(f"Sent educational video using file_id: {file_id}")
                        except Exception as e:
                            logging.error(f"Failed to send educational media using file_id, error: {str(e)}")
                            await bot.send_message(
                                chat_id=chat_id, 
                                text=f"⚠️ تصویر یا ویدیوی محتوای آموزشی موجود نیست"
                            )
                    else:
                        # It looks like a path but we couldn't find the file
                        logging.error(f"Educational media file not found at path: {file_id}")
                        await bot.send_message(
                            chat_id=chat_id, 
                            text=f"⚠️ تصویر یا ویدیوی محتوای آموزشی موجود نیست"
                        )
                    
        except Exception as e:
            logging.error(f"Error sending educational media: {str(e)}")
            logging.error(f"Full error details: {traceback.format_exc()}")
            # Try sending a notification about the failed media
            try:
                await bot.send_message(chat_id=chat_id, text=f"⚠️ خطا در نمایش فایل رسانه‌ای آموزشی")
            except:
                pass


async def send_educational_media_group(chat_id, media_files, caption="", keyboard=None):
    """
    Send educational content as a media group with caption
    
    Args:
        chat_id: Telegram chat ID to send to
        media_files: List of media file dictionaries
        caption: Caption text for the first media (supports Markdown)
        keyboard: Optional inline keyboard to attach to the last message
    """
    from bot import bot  # Import bot here to avoid circular imports
    import os
    import traceback
    from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
    from aiogram.methods.send_media_group import SendMediaGroup
    
    # Check if we have any media files
    if not media_files:
        # No media files, send just the text with keyboard
        if caption:
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        return
    
    # Define possible paths to check
    media_paths = [
        './', 
        './static/', 
        './static/images/', 
        './static/photos/',
        './static/uploads/',
        './static/media/',
        './static/media/educational/',
        './static/products/',
        './static/services/',
    ]
    
    # Process media files to create a media group
    media_list = []
    valid_media_count = 0
    
    # For each media file
    for i, media in enumerate(media_files):
        file_id = media.get('file_id')
        local_path = media.get('local_path')
        file_type = media.get('file_type', 'photo')  # Default to photo if not specified
        
        logging.info(f"Processing media for group: file_id={file_id}, local_path={local_path}, file_type={file_type}")
        
        # Skip if no file_id or local_path
        if not file_id and not local_path:
            logging.warning(f"Media has no file_id or local_path")
            continue
        
        # If we have a local_path but no file_id, use local_path as file_id
        if not file_id and local_path:
            file_id = local_path
            logging.info(f"Using local_path as file_id: {file_id}")
        
        try:
            file_found = False
            file_path = None
            
            # First check if the path exists as is
            if os.path.exists(file_id):
                file_found = True
                file_path = file_id
                logging.info(f"Found media at direct path: {file_path}")
            
            # If file not found and the file_id looks like a path (has slashes)
            if not file_found and ('/' in file_id):
                # Handle common path patterns by checking root and with './static/' prefix
                possible_paths = [
                    file_id,                # As is
                    f"./{file_id}",         # With ./ prefix
                    f"./static/{file_id}",  # With ./static/ prefix
                ]
                
                # Check all paths in our list
                for media_path in media_paths:
                    # If the path already has a common prefix like 'media/' or 'static/', we take just the filename part
                    if file_id.startswith(('media/', 'static/')):
                        # Extract just the filename part
                        parts = file_id.split('/')
                        filename = parts[-1]  # Get the last part (filename)
                        
                        # Create a path with our media_path + filename
                        test_path = os.path.join(media_path, filename)
                    else:
                        # Use the full file_id with the media_path
                        test_path = os.path.join(media_path, file_id)
                    
                    # Add this to our possible paths
                    possible_paths.append(test_path)
                
                # Try all possible paths
                for path in possible_paths:
                    if os.path.exists(path):
                        file_found = True
                        file_path = path
                        logging.info(f"Found media at alternative path: {file_path}")
                        break
            
            # If file was found locally
            if file_found and file_path:
                # For the first media, include the caption
                media_caption = caption if i == 0 else ""
                
                # Add to media group based on file type
                if file_type == 'photo':
                    media_list.append(
                        InputMediaPhoto(
                            media=FSInputFile(file_path),
                            caption=media_caption,
                            parse_mode="Markdown"
                        )
                    )
                    valid_media_count += 1
                elif file_type == 'video':
                    media_list.append(
                        InputMediaVideo(
                            media=FSInputFile(file_path),
                            caption=media_caption,
                            parse_mode="Markdown"
                        )
                    )
                    valid_media_count += 1
            
            # If file wasn't found, try as a Telegram file_id (no slashes)
            elif '/' not in file_id:
                logging.info(f"Trying as Telegram file_id: {file_id}")
                
                # For the first media, include the caption
                media_caption = caption if i == 0 else ""
                
                # Add to media group based on file type
                if file_type == 'photo':
                    media_list.append(
                        InputMediaPhoto(
                            media=file_id,
                            caption=media_caption,
                            parse_mode="Markdown"
                        )
                    )
                    valid_media_count += 1
                elif file_type == 'video':
                    media_list.append(
                        InputMediaVideo(
                            media=file_id,
                            caption=media_caption,
                            parse_mode="Markdown"
                        )
                    )
                    valid_media_count += 1
            
            else:
                # File couldn't be found as path or file_id
                logging.error(f"Media file not found: {file_id}")
        
        except Exception as e:
            logging.error(f"Error processing media for group: {str(e)}")
            logging.error(traceback.format_exc())
    
    # Now send the media group if we have any valid media
    try:
        if valid_media_count > 0:
            # Send the media group using SendMediaGroup method
            await bot.send_media_group(chat_id=chat_id, media=media_list)
            logging.info(f"Sent media group with {valid_media_count} files")
            
            # Send a separate message with keyboard if needed
            if keyboard:
                await bot.send_message(
                    chat_id=chat_id,
                    text="🔍 گزینه‌های زیر را انتخاب کنید:",
                    reply_markup=keyboard
                )
        elif caption:
            # If we couldn't send any media but have a caption, send as text message
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    except Exception as e:
        logging.error(f"Error sending media group: {str(e)}")
        logging.error(traceback.format_exc())
        
        # Fallback to sending individual messages
        if caption:
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        
        # Try to send notification about error
        try:
            await bot.send_message(
                chat_id=chat_id, 
                text=f"⚠️ خطا در نمایش مجموعه فایل‌های رسانه‌ای"
            )
        except:
            pass


async def send_product_media(chat_id, media_files):
    """Send product media files to user"""
    from bot import bot  # Import bot here to avoid circular imports
    
    # Check if we have any media files
    if not media_files:
        logging.warning(f"No media files provided to send_product_media for chat_id {chat_id}")
        return
        
    logging.info(f"Attempting to send {len(media_files)} media files to chat_id {chat_id}")
    
    # Define possible paths to check
    media_paths = [
        './', 
        './static/', 
        './static/images/', 
        './static/photos/',
        './static/uploads/',
        './static/media/',
        './static/products/',
        './attached_assets/',
        './data/',
    ]
    
    for media in media_files:
        try:
            file_id = media.get('file_id', '')
            file_type = media.get('file_type', 'photo')
            file_name = media.get('file_name', 'unknown')
            
            # Log the full media info for debugging
            logging.info(f"Processing media: file_id={file_id}, file_type={file_type}, file_name={file_name}")
            
            if not file_id:
                logging.warning(f"Empty file_id for media: {media}")
                continue
            
            # Try a few sample files from attached_assets (this is temporary for testing)
            if file_id == 'show.jpg' and not os.path.isfile(file_id):
                test_file = './attached_assets/show.jpg'
                if os.path.isfile(test_file):
                    file_id = test_file
                    logging.info(f"Found test file at {test_file}")
                    
            # Handle different file location scenarios
            if isinstance(file_id, str) and file_id.startswith('http'):
                # It's a URL, use URLInputFile
                logging.info(f"File is a URL: {file_id}")
                file = URLInputFile(file_id)
                
                if file_type == 'photo':
                    await bot.send_photo(chat_id=chat_id, photo=file, caption=file_name)
                    logging.info(f"Sent photo from URL: {file_id}")
                elif file_type == 'video':
                    await bot.send_video(chat_id=chat_id, video=file, caption=file_name)
                    logging.info(f"Sent video from URL: {file_id}")
                    
            elif file_id and os.path.isfile(file_id):
                # It's a local file that exists at the given path
                logging.info(f"File is a local path that exists: {file_id}")
                
                if file_type == 'photo':
                    photo_file = FSInputFile(file_id)
                    await bot.send_photo(chat_id=chat_id, photo=photo_file, caption=file_name)
                    logging.info(f"Sent photo from local file: {file_id}")
                elif file_type == 'video':
                    video_file = FSInputFile(file_id)
                    await bot.send_video(chat_id=chat_id, video=video_file, caption=file_name)
                    logging.info(f"Sent video from local file: {file_id}")
            else:
                # Try to find the file in various directories
                file_found = False
                
                # If only the filename is stored (common case), try in multiple folders
                if '/' not in file_id:
                    for path in media_paths:
                        full_path = f"{path}{file_id}"
                        if os.path.isfile(full_path):
                            logging.info(f"Found file at {full_path}")
                            file_found = True
                            
                            if file_type == 'photo':
                                photo_file = FSInputFile(full_path)
                                await bot.send_photo(chat_id=chat_id, photo=photo_file, caption=file_name)
                                logging.info(f"Sent photo from path: {full_path}")
                            elif file_type == 'video':
                                video_file = FSInputFile(full_path)
                                await bot.send_video(chat_id=chat_id, video=video_file, caption=file_name)
                                logging.info(f"Sent video from path: {full_path}")
                                
                            break
                
                # If file wasn't found in any of our directories, assume it's a Telegram file_id
                if not file_found:
                    logging.info(f"Assuming file_id is a Telegram file_id: {file_id}")
                    
                    try:
                        if file_type == 'photo':
                            await bot.send_photo(chat_id=chat_id, photo=file_id, caption=file_name)
                            logging.info(f"Sent photo using file_id: {file_id}")
                        elif file_type == 'video':
                            await bot.send_video(chat_id=chat_id, video=file_id, caption=file_name)
                            logging.info(f"Sent video using file_id: {file_id}")
                    except Exception as e:
                        logging.error(f"Failed to send using file_id, sending error message: {str(e)}")
                        await bot.send_message(
                            chat_id=chat_id, 
                            text=f"⚠️ تصویر یا ویدیوی مورد نظر موجود نیست: {file_name}"
                        )
                    
        except Exception as e:
            logging.error(f"Error sending product media: {str(e)}")
            logging.error(f"Full error details: {traceback.format_exc()}")
            # Try sending a notification about the failed media
            try:
                await bot.send_message(chat_id=chat_id, text=f"⚠️ خطا در نمایش فایل رسانه‌ای: {file_name}")
            except:
                pass

async def send_service_media(chat_id, media_files):
    """Send service media files to user"""
    # This function is now just a wrapper around send_product_media for consistency
    # since both products and services use the same underlying mechanism
    
    logging.info(f"send_service_media called, redirecting to send_product_media with {len(media_files) if media_files else 0} files")
    await send_product_media(chat_id, media_files)

# Inquiry process handlers
@router.callback_query(F.data.startswith("inquiry:"))
async def callback_inquiry(callback: CallbackQuery, state: FSMContext):
    """Handle inquiry initiation"""
    await callback.answer()
    
    try:
        # Extract item type and ID
        _, item_type, item_id = callback.data.split(':', 2)
        item_id = int(item_id)
        
        # Save inquiry details in state
        if item_type == 'product':
            await state.update_data(product_id=item_id, service_id=None)
            product = db.get_product(item_id)
            if product and 'name' in product:
                await callback.message.answer(f"شما در حال استعلام قیمت برای محصول «{product['name']}» هستید.")
            else:
                await callback.message.answer("شما در حال استعلام قیمت برای یک محصول هستید.")
                logger.error(f"Product not found or missing name: {item_id}")
        else:  # service
            await state.update_data(service_id=item_id, product_id=None)
            service = db.get_service(item_id)
            if service and 'name' in service:
                await callback.message.answer(f"شما در حال استعلام قیمت برای خدمت «{service['name']}» هستید.")
            else:
                await callback.message.answer("شما در حال استعلام قیمت برای یک خدمت هستید.")
                logger.error(f"Service not found or missing name: {item_id}")
    except Exception as e:
        logger.error(f"Error in inquiry callback: {e}")
        await callback.message.answer("خطایی در شروع فرآیند استعلام قیمت رخ داد. لطفا دوباره تلاش کنید.")
    
    # Ask for name
    await callback.message.answer("لطفاً نام خود را وارد کنید:")
    await state.set_state(UserStates.inquiry_name)

@router.message(UserStates.inquiry_name)
async def process_inquiry_name(message: Message, state: FSMContext):
    """Process name input for inquiry"""
    # Save name
    await state.update_data(name=message.text)
    
    # Ask for phone
    await message.answer("لطفاً شماره تماس خود را وارد کنید:")
    await state.set_state(UserStates.inquiry_phone)

@router.message(UserStates.inquiry_phone)
async def process_inquiry_phone(message: Message, state: FSMContext):
    """Process phone input for inquiry"""
    # Simple phone validation
    phone = message.text.strip()
    if not phone.isdigit() or len(phone) < 10:
        await message.answer("لطفاً یک شماره تماس معتبر وارد کنید:")
        return
    
    # Save phone
    await state.update_data(phone=phone)
    
    # Ask for description
    await message.answer("لطفاً توضیحات درخواست خود را وارد کنید:")
    await state.set_state(UserStates.inquiry_description)

@router.message(UserStates.inquiry_description)
async def process_inquiry_description(message: Message, state: FSMContext):
    """Process description input for inquiry"""
    # Save description
    await state.update_data(description=message.text)
    
    try:
        # Get all inquiry data
        inquiry_data = await state.get_data()
        
        # Format confirmation message
        confirmation = (
            "📋 لطفاً اطلاعات درخواست خود را تأیید کنید:\n\n"
            f"👤 نام: {inquiry_data.get('name', 'نامشخص')}\n"
            f"📞 شماره تماس: {inquiry_data.get('phone', 'نامشخص')}\n"
            f"📝 توضیحات: {inquiry_data.get('description', 'بدون توضیحات')}\n\n"
        )
        
        # Add product/service info
        product_id = inquiry_data.get('product_id')
        service_id = inquiry_data.get('service_id')
        
        if product_id:
            product = db.get_product(product_id)
            if product and 'name' in product:
                confirmation += f"🛒 محصول: {product['name']}\n"
            else:
                confirmation += "🛒 محصول: نامشخص\n"
                logger.error(f"Product not found or missing name in confirmation: {product_id}")
        elif service_id:
            service = db.get_service(service_id)
            if service and 'name' in service:
                confirmation += f"🛠️ خدمت: {service['name']}\n"
            else:
                confirmation += "🛠️ خدمت: نامشخص\n"
                logger.error(f"Service not found or missing name in confirmation: {service_id}")
    except Exception as e:
        logger.error(f"Error formatting inquiry confirmation: {e}")
        confirmation = "📋 لطفاً اطلاعات درخواست خود را تأیید کنید (بدون جزئیات به دلیل خطای فنی)"
    
    # Add confirmation keyboard
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ تأیید", callback_data="confirm_inquiry")
    kb.button(text="❌ انصراف", callback_data="cancel_inquiry")
    kb.adjust(2)
    
    await message.answer(confirmation, reply_markup=kb.as_markup())
    await state.set_state(UserStates.waiting_for_confirmation)

@router.callback_query(F.data == "confirm_inquiry", UserStates.waiting_for_confirmation)
async def callback_confirm_inquiry(callback: CallbackQuery, state: FSMContext):
    """Handle inquiry confirmation"""
    await callback.answer()
    
    # Get all inquiry data
    inquiry_data = await state.get_data()
    
    try:
        # Add inquiry to database
        user_id = callback.from_user.id
        name = inquiry_data.get('name', 'نامشخص')
        phone = inquiry_data.get('phone', 'نامشخص')
        description = inquiry_data.get('description', 'بدون توضیحات')
        product_id = inquiry_data.get('product_id')
        service_id = inquiry_data.get('service_id')
        
        # Safely add the inquiry
        try:
            # تبدیل user_id به int برای اطمینان از سازگاری
            user_id_int = int(user_id)
            # تبدیل product_id و service_id به int در صورت لزوم
            product_id_int = int(product_id) if product_id else None
            service_id_int = int(service_id) if service_id else None
            
            # ثبت درخواست
            db.add_inquiry(user_id_int, name, phone, description, product_id_int, service_id_int)
            
            # ارسال پیام موفقیت
            await callback.message.answer(
                "✅ درخواست شما با موفقیت ثبت شد.\n"
                "کارشناسان ما در اسرع وقت با شما تماس خواهند گرفت."
            )
            logger.info(f"Inquiry successfully added for user: {user_id_int}")
        except ValueError as e:
            # خطای تبدیل نوع داده
            logger.error(f"Value conversion error in inquiry: {e}")
            await callback.message.answer(
                "❌ خطا در ثبت درخواست. لطفاً مجدداً تلاش کنید.\n"
                "دلیل: مقادیر نامعتبر"
            )
        except Exception as e:
            # سایر خطاها
            logger.error(f"Database error adding inquiry: {e}")
            logger.error(traceback.format_exc())
            await callback.message.answer(
                "❌ خطا در ثبت درخواست. لطفاً مجدداً تلاش کنید."
            )
        
        # Notify admin if ADMIN_ID is set
        if ADMIN_ID:
            # Format admin notification
            notification = (
                "🔔 استعلام قیمت جدید:\n\n"
                f"👤 نام: {name}\n"
                f"📞 شماره تماس: {phone}\n"
                f"📝 توضیحات: {description}\n\n"
            )
            
            # Add product/service info
            try:
                if product_id:
                    product = db.get_product(product_id)
                    if product and 'name' in product:
                        notification += f"🛒 محصول: {product['name']}\n"
                    else:
                        notification += f"🛒 محصول: (ID: {product_id})\n"
                elif service_id:
                    service = db.get_service(service_id)
                    if service and 'name' in service:
                        notification += f"🛠️ خدمت: {service['name']}\n"
                    else:
                        notification += f"🛠️ خدمت: (ID: {service_id})\n"
            except Exception as e:
                logger.error(f"Error getting product/service details for admin notification: {e}")
                notification += "مشکل در نمایش اطلاعات محصول/خدمت\n"
            
            notification += f"\n📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            try:
                # به جای واردکردن bot که ممکن است باعث خطای دور (circular import) شود
                # از آرگومان callback استفاده می‌کنیم
                await callback.bot.send_message(chat_id=ADMIN_ID, text=notification)
            except Exception as e:
                logger.error(f"Failed to notify admin: {e}")
        
        # Clear state and return to main menu
        await state.clear()
        
        # Show main menu
        kb = InlineKeyboardBuilder()
        kb.button(text="🛒 محصولات", callback_data="products")
        kb.button(text="🛠️ خدمات", callback_data="services")
        kb.button(text="📚 محتوای آموزشی", callback_data="educational")
        kb.button(text="📞 تماس با ما", callback_data="contact")
        kb.button(text="ℹ️ درباره ما", callback_data="about")
        kb.adjust(2, 2, 1)
        
        await callback.message.answer("می‌توانید به استفاده از ربات ادامه دهید:", 
                                    reply_markup=kb.as_markup())
    except Exception as e:
        logger.error(f"Error processing inquiry: {e}")
        logger.error(traceback.format_exc())
        await callback.message.answer(
            "❌ خطا در ثبت درخواست. لطفاً مجدداً تلاش کنید."
        )

@router.callback_query(F.data == "cancel_inquiry")
async def callback_cancel_inquiry(callback: CallbackQuery, state: FSMContext):
    """Handle inquiry cancellation"""
    await callback.answer()
    await state.clear()
    
    await callback.message.answer("درخواست استعلام قیمت لغو شد.")
    
    # Show main menu
    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 محصولات", callback_data="products")
    kb.button(text="🛠️ خدمات", callback_data="services")
    kb.button(text="📚 محتوای آموزشی", callback_data="educational")
    kb.button(text="📞 تماس با ما", callback_data="contact")
    kb.button(text="ℹ️ درباره ما", callback_data="about")
    kb.adjust(2, 2, 1)
    
    await callback.message.answer("می‌توانید به استفاده از ربات ادامه دهید:", 
                               reply_markup=kb.as_markup())