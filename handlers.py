from aiogram import Router, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, URLInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
import os
import traceback
from datetime import datetime
from database import Database
from configuration import (
    PRODUCTS_BTN, SERVICES_BTN, INQUIRY_BTN, EDUCATION_BTN, 
    CONTACT_BTN, ABOUT_BTN, SEARCH_BTN
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
    contact_text = db.get_static_content('contact')
    await message.answer(contact_text)

# About command handler
@router.message(Command("about"))
@router.message(lambda message: message.text == ABOUT_BTN)
async def cmd_about(message: Message):
    """Handle /about command or About button"""
    about_text = db.get_static_content('about')
    await message.answer(about_text)

# Education button handler
@router.message(lambda message: message.text == EDUCATION_BTN)
async def cmd_education(message: Message):
    """Handle Education button"""
    categories = db.get_educational_categories()
    if not categories:
        await message.answer("محتوای آموزشی در حال حاضر در دسترس نیست. لطفا بعدا تلاش کنید.")
        return
    
    from keyboards import education_categories_keyboard
    keyboard = education_categories_keyboard(categories)
    await message.answer("لطفا یک دسته‌بندی آموزشی را انتخاب کنید:", reply_markup=keyboard)

# Inquiry button handler
@router.message(lambda message: message.text == INQUIRY_BTN)
async def cmd_inquiry(message: Message, state: FSMContext):
    """Handle Inquiry button"""
    await message.answer("لطفا نام خود را وارد کنید:")
    await state.set_state(UserStates.inquiry_name)

# Search button handler
@router.message(lambda message: message.text == SEARCH_BTN)
async def cmd_search(message: Message):
    """Handle Search button"""
    await message.answer("این قابلیت در حال حاضر در دسترس نیست. لطفا بعدا تلاش کنید.")

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
    kb = InlineKeyboardBuilder()
    for category in categories:
        kb.button(text=category, callback_data=f"edu_cat:{category}")
    
    kb.button(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")
    kb.adjust(1)
    
    await callback.message.answer("🎓 دسته‌بندی محتوای آموزشی را انتخاب کنید:", 
                               reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("edu_cat:"))
async def callback_educational_category(callback: CallbackQuery):
    """Handle educational category selection"""
    await callback.answer()
    
    # Extract category name
    category = callback.data.split(':', 1)[1]
    
    # Get educational content for this category
    content_list = db.get_all_educational_content(category)
    
    if not content_list:
        await callback.message.answer(f"محتوای آموزشی برای دسته {category} موجود نیست.")
        return
    
    # Create keyboard with content items
    kb = InlineKeyboardBuilder()
    for content in content_list:
        kb.button(text=content['title'], callback_data=f"edu_content:{content['id']}")
    
    kb.button(text="🔙 بازگشت به دسته‌بندی‌ها", callback_data="educational")
    kb.adjust(1)
    
    await callback.message.answer(f"📚 محتوای آموزشی دسته {category}:", 
                               reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("edu_content:"))
async def callback_educational_content(callback: CallbackQuery):
    """Handle educational content selection"""
    await callback.answer()
    
    # Extract content ID
    content_id = int(callback.data.split(':', 1)[1])
    
    # Get content details
    content = db.get_educational_content(content_id)
    
    if not content:
        await callback.message.answer("محتوای آموزشی مورد نظر یافت نشد.")
        return
    
    # Format the content based on its type
    content_text = f"📖 {content['title']}\n\n{content['content']}"
    
    # Add back button
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 بازگشت به لیست محتوا", callback_data=f"edu_cat:{content['category']}")
    
    await callback.message.answer(content_text, reply_markup=kb.as_markup())

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
async def send_product_media(chat_id, media_files):
    """Send product media files to user"""
    from bot import bot  # Import bot here to avoid circular imports
    
    for media in media_files:
        try:
            file_id = media.get('file_id', '')
            file_type = media.get('file_type', 'photo')
            
            if not file_id:
                logger.warning(f"Empty file_id for media: {media}")
                continue
                
            # Check if file_id is a telegram file_id or a local path
            if os.path.exists(file_id) or (isinstance(file_id, str) and file_id.startswith('http')):
                # It's a local file path or URL, convert to InputFile
                file = URLInputFile(file_id) if isinstance(file_id, str) and file_id.startswith('http') else file_id
                
                if file_type == 'photo':
                    await bot.send_photo(chat_id=chat_id, photo=file)
                elif file_type == 'video':
                    await bot.send_video(chat_id=chat_id, video=file)
            else:
                # It's a Telegram file_id, use directly
                if file_type == 'photo':
                    await bot.send_photo(chat_id=chat_id, photo=file_id)
                elif file_type == 'video':
                    await bot.send_video(chat_id=chat_id, video=file_id)
        except Exception as e:
            logger.error(f"Error sending product media: {e}")

async def send_service_media(chat_id, media_files):
    """Send service media files to user"""
    from bot import bot  # Import bot here to avoid circular imports
    
    for media in media_files:
        try:
            file_id = media.get('file_id', '')
            file_type = media.get('file_type', 'photo')
            
            if not file_id:
                logger.warning(f"Empty file_id for media: {media}")
                continue
                
            # Check if file_id is a telegram file_id or a local path
            if os.path.exists(file_id) or (isinstance(file_id, str) and file_id.startswith('http')):
                # It's a local file path or URL, convert to InputFile
                file = URLInputFile(file_id) if isinstance(file_id, str) and file_id.startswith('http') else file_id
                
                if file_type == 'photo':
                    await bot.send_photo(chat_id=chat_id, photo=file)
                elif file_type == 'video':
                    await bot.send_video(chat_id=chat_id, video=file)
            else:
                # It's a Telegram file_id, use directly
                if file_type == 'photo':
                    await bot.send_photo(chat_id=chat_id, photo=file_id)
                elif file_type == 'video':
                    await bot.send_video(chat_id=chat_id, video=file_id)
        except Exception as e:
            logger.error(f"Error sending service media: {e}")

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