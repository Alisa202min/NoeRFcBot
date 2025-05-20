from aiogram import Router, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, URLInputFile, FSInputFile, InputMediaPhoto, InputMediaVideo
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
    try:
        logging.info(f"Products requested by user: {message.from_user.id}")
        
        # تنظیم حالت برای محصولات
        await state.update_data(cat_type='product')
        
        # نمایش دسته‌بندی‌های محصولات با استفاده از تابع مخصوص محصولات
        await show_product_categories(message, state)
        
    except Exception as e:
        logging.error(f"Error in cmd_products: {str(e)}")
        logging.error(traceback.format_exc())
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

# Services command handler
@router.message(Command("services"))
@router.message(lambda message: message.text == SERVICES_BTN)
async def cmd_services(message: Message, state: FSMContext):
    """Handle /services command or Services button"""
    try:
        logging.info(f"Services requested by user: {message.from_user.id}")
        
        # تنظیم حالت برای خدمات
        await state.update_data(cat_type='service')
        
        # نمایش دسته‌بندی‌های خدمات با استفاده از تابع مخصوص خدمات
        await show_service_categories(message, state)
        
    except Exception as e:
        logging.error(f"Error in cmd_services: {str(e)}")
        logging.error(traceback.format_exc())
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

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
    
    logging.info(f"Educational content requested by user: {callback.from_user.id}")
    
    # Get educational categories
    categories = db.get_educational_categories()
    
    if not categories:
        await callback.message.answer("در حال حاضر محتوای آموزشی موجود نیست.")
        return
    
    # برای هر دسته‌بندی، محتوای قدیمی (legacy) مرتبط با آن را نیز بررسی کنیم
    updated_categories = []
    for category in categories:
        category_name = category['name']
        category_id = category['id']
        # دریافت محتوای آموزشی قدیمی با استفاده از نام دسته‌بندی
        legacy_content = db.get_all_educational_content(category=category_name)
        
        # اضافه کردن تعداد محتوای قدیمی به شمارش کلی محتوا
        legacy_count = len(legacy_content) if legacy_content else 0
        
        # ساخت یک نسخه جدید از دسته‌بندی با مقادیر به‌روز شده
        new_category = dict(category)  # کپی از دیکشنری اصلی
        
        # به‌روزرسانی شمارش محتوا
        content_count = 0
        if 'content_count' in category:
            try:
                content_count = int(category['content_count'])
            except (ValueError, TypeError):
                content_count = 0
        
        # اضافه کردن تعداد محتوای قدیمی
        total_count = content_count + legacy_count
        new_category['content_count'] = total_count
        
        # گزارش‌دهی برای اشکال‌زدایی
        logging.info(f"Category '{category_name}' (ID: {category_id}): content_count={content_count}, legacy_count={legacy_count}, total={total_count}")
        
        updated_categories.append(new_category)
    
    # جایگزینی لیست دسته‌بندی‌ها با نسخه به‌روز شده
    categories = updated_categories
            
    # ثبت تعداد کل دسته‌بندی‌ها
    logging.info(f"Educational categories sent: {len(categories)} categories")
    
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
            telegraph_url = None
            
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
                    logging.info(f"Created Telegraph page: {telegraph_url}")
                    
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
            
            # Prepare media items for the group
            from bot import bot
            from aiogram.types import InputMediaPhoto, FSInputFile
            
            media_group = []
            found_valid_media = False
            
            # Process media files
            for idx, media in enumerate(media_files):
                file_id = media.get('file_id')
                local_path = media.get('local_path')
                file_type = media.get('file_type', 'photo')
                
                # Skip if no file_id
                if not file_id:
                    continue
                
                # For first media item, include caption
                item_caption = caption_text if idx == 0 else ""
                
                # Check if file exists in static/media/educational folder
                if file_id.startswith('educational_content_image_'):
                    # Extract content ID from file_id (format: educational_content_image_[content_id]_...)
                    try:
                        # Try to get content ID from the file_id format
                        parts = file_id.split('_')
                        content_id_str = parts[3] if len(parts) > 3 else None
                        
                        logging.info(f"Looking for media files for content ID: {content_id_str}")
                        
                        # Look for all files in static/media/educational directory
                        import glob
                        import os.path
                        
                        # First try with local_path if available
                        found_file = False
                        if local_path:
                            # Try with static prefix
                            if not local_path.startswith('static/'):
                                full_path = f"./static/{local_path}"
                            else:
                                full_path = f"./{local_path}"
                                
                            if os.path.exists(full_path) and os.path.isfile(full_path):
                                logging.info(f"Found media file using local_path: {full_path}")
                                media_path = full_path
                                found_file = True
                        
                        # If no file found yet, try with different glob patterns
                        if not found_file:
                            # Try all jpg files in the educational directory
                            possible_files = glob.glob(f"./static/media/educational/*.jpg")
                            if possible_files:
                                # Use first media file found as fallback
                                media_path = possible_files[0]
                                logging.info(f"Using first available media file from: {media_path}")
                                found_file = True
                        
                        if found_file:
                            media_group.append(
                                InputMediaPhoto(
                                    media=FSInputFile(media_path),
                                    caption=item_caption,
                                    parse_mode="Markdown"
                                )
                            )
                            found_valid_media = True
                        else:
                            logging.error(f"Could not find any media file for content ID: {content_id_str}")
                    except Exception as e:
                        logging.error(f"Error processing media file: {str(e)}")
                else:
                    try:
                        # Try to use as direct Telegram file_id
                        media_group.append(
                            InputMediaPhoto(
                                media=file_id,
                                caption=item_caption,
                                parse_mode="Markdown"
                            )
                        )
                        found_valid_media = True
                    except Exception as e:
                        logging.error(f"Error adding media: {str(e)}")
            
            if found_valid_media and media_group:
                logging.info(f"Sending media group with {len(media_group)} items")
                try:
                    # Send media group
                    await bot.send_media_group(
                        chat_id=callback.message.chat.id,
                        media=media_group
                    )
                    
                    # Send keyboard in separate message if needed
                    if keyboard:
                        await bot.send_message(
                            chat_id=callback.message.chat.id,
                            text="🔍 گزینه‌های مرتبط با محتوای آموزشی:",
                            reply_markup=keyboard
                        )
                except Exception as e:
                    logging.error(f"Error sending media group: {str(e)}")
                    # Fallback to text-only message
                    content_text = f"📖 *{title}*\n\n{content_text}"
                    if telegraph_url:
                        content_text += f"\n\n[متن کامل]({telegraph_url})"
                    
                    await callback.message.answer(content_text, parse_mode="Markdown", reply_markup=keyboard)
            else:
                # No valid media found, fallback to text message
                content_text = f"📖 *{title}*\n\n{content['content']}"
                if telegraph_url:
                    content_text += f"\n\n[متن کامل]({telegraph_url})"
                
                await callback.message.answer(content_text, parse_mode="Markdown", reply_markup=keyboard)
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
async def show_product_categories(message, state, parent_id=None):
    """Show product categories only - separate function for products"""
    try:
        # ذخیره نوع دسته‌بندی در حالت
        await state.update_data(cat_type='product')
        
        # ثبت گزارش در لاگ
        logging.info(f"show_product_categories called with parent_id={parent_id}")
        
        # فقط از جدول محصولات استفاده می‌کنیم
        categories = db.get_product_categories(parent_id=parent_id)
        logging.info(f"Product categories: {categories}")
        
        # اگر هیچ دسته‌بندی یافت نشد، بررسی کنیم آیا این یک دسته‌بندی نهایی است که محصول دارد
        if not categories:
            # If no categories but we're in a subcategory, show products
            if parent_id is not None:
                # نمایش محصولات
                products = db.get_products(parent_id)
                logging.info(f"Retrieved {len(products)} products for category ID {parent_id}")
                if products:
                    await show_products_list(message, products, parent_id)
                else:
                    await message.answer("محصولی در این دسته‌بندی وجود ندارد.")
            else:
                # No top-level categories
                await message.answer("دسته‌بندی محصولات موجود نیست.")
            return
        
        # نمایش دسته‌بندی‌ها
        kb = InlineKeyboardBuilder()
        
        # ساخت دکمه‌ها با نمایش تعداد زیرمجموعه‌ها و محصولات
        for category in categories:
            # بررسی وجود اطلاعات تعداد زیرمجموعه‌ها و محصولات
            subcategory_count = category.get('subcategory_count', 0)
            product_count = category.get('product_count', 0)
            
            # محاسبه مجموع تعداد آیتم‌ها
            total_items = subcategory_count + product_count
            
            # ساخت نام نمایشی برای دکمه
            display_name = category['name']
            if total_items > 0:
                display_name = f"{category['name']} ({total_items})"
                
            # اضافه کردن دکمه به کیبورد
            kb.button(text=display_name, callback_data=f"category:{category['id']}")
            
        # اضافه کردن دکمه بازگشت
        if parent_id is not None:
            parent_category = db.get_category(parent_id)
            if parent_category and parent_category.get('parent_id') is not None:
                kb.button(text="🔙 بازگشت", callback_data=f"category:{parent_category['parent_id']}")
            else:
                kb.button(text="🔙 بازگشت به دسته‌بندی‌های اصلی", callback_data="products")
        else:
            kb.button(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")
        
        # تنظیم نمایش دکمه‌ها در یک ستون
        kb.adjust(1)
        
        # ارسال پیام
        await message.answer("دسته‌بندی محصولات را انتخاب کنید:", reply_markup=kb.as_markup())
        
        # تنظیم حالت کاربر
        await state.set_state(UserStates.browse_categories)
        
    except Exception as e:
        logging.error(f"Error in show_product_categories: {str(e)}")
        logging.error(traceback.format_exc())
        await message.answer("⚠️ متأسفانه در نمایش دسته‌بندی‌های محصولات خطایی رخ داد. لطفا مجددا تلاش کنید یا با پشتیبانی تماس بگیرید.")


async def show_service_categories(message, state, parent_id=None):
    """Show service categories only - separate function for services"""
    try:
        # ذخیره نوع دسته‌بندی در حالت
        await state.update_data(cat_type='service')
        
        # ثبت گزارش در لاگ
        logging.info(f"show_service_categories called with parent_id={parent_id}")
        
        # فقط از جدول خدمات استفاده می‌کنیم
        categories = db.get_service_categories(parent_id=parent_id)
        logging.info(f"Service categories: {categories}")
        
        # اگر هیچ دسته‌بندی یافت نشد، بررسی کنیم آیا این یک دسته‌بندی نهایی است که خدمت دارد
        if not categories:
            # If no categories but we're in a subcategory, show services
            if parent_id is not None:
                # نمایش خدمات
                services = db.get_services(parent_id)
                logging.info(f"Retrieved {len(services)} services for category ID {parent_id}")
                if services:
                    await show_services_list(message, services, parent_id)
                else:
                    await message.answer("خدمتی در این دسته‌بندی وجود ندارد.")
            else:
                # No top-level categories
                await message.answer("دسته‌بندی خدمات موجود نیست.")
            return
        
        # نمایش دسته‌بندی‌ها
        kb = InlineKeyboardBuilder()
        
        # ساخت دکمه‌ها با نمایش تعداد زیرمجموعه‌ها و خدمات
        for category in categories:
            # بررسی وجود اطلاعات تعداد زیرمجموعه‌ها و خدمات
            subcategory_count = category.get('subcategory_count', 0)
            service_count = category.get('service_count', 0)
            
            # محاسبه مجموع تعداد آیتم‌ها
            total_items = subcategory_count + service_count
            
            # ساخت نام نمایشی برای دکمه
            display_name = category['name']
            if total_items > 0:
                display_name = f"{category['name']} ({total_items})"
                
            # اضافه کردن دکمه به کیبورد
            kb.button(text=display_name, callback_data=f"category:{category['id']}")
            
        # اضافه کردن دکمه بازگشت
        if parent_id is not None:
            parent_category = db.get_category(parent_id)
            if parent_category and parent_category.get('parent_id') is not None:
                kb.button(text="🔙 بازگشت", callback_data=f"category:{parent_category['parent_id']}")
            else:
                kb.button(text="🔙 بازگشت به دسته‌بندی‌های اصلی", callback_data="services")
        else:
            kb.button(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")
        
        # تنظیم نمایش دکمه‌ها در یک ستون
        kb.adjust(1)
        
        # ارسال پیام
        await message.answer("دسته‌بندی خدمات را انتخاب کنید:", reply_markup=kb.as_markup())
        
        # تنظیم حالت کاربر
        await state.set_state(UserStates.browse_categories)
        
    except Exception as e:
        logging.error(f"Error in show_service_categories: {str(e)}")
        logging.error(traceback.format_exc())
        await message.answer("⚠️ متأسفانه در نمایش دسته‌بندی‌های خدمات خطایی رخ داد. لطفا مجددا تلاش کنید یا با پشتیبانی تماس بگیرید.")

@router.callback_query(F.data.startswith("category:"))
async def callback_category(callback: CallbackQuery, state: FSMContext):
    """Handle category selection"""
    await callback.answer()
    
    try:
        # ثبت گزارش درباره درخواست
        logging.info(f"Category callback received: {callback.data}")
        
        # استخراج شناسه دسته‌بندی
        category_id = int(callback.data.split(':', 1)[1])
        
        # دریافت اطلاعات حالت
        state_data = await state.get_data()
        
        # نوع دسته‌بندی (محصول یا خدمت) را قطعی از حالت دریافت می‌کنیم
        cat_type = state_data.get('cat_type', 'product')
        
        logging.info(f"Processing category ID {category_id} as {cat_type} type")
        
        # براساس نوع دسته‌بندی، تابع مناسب را فراخوانی می‌کنیم
        if cat_type == 'product':
            # فقط دسته‌بندی‌های محصول را بررسی می‌کنیم
            is_valid = db.check_product_category_exists(category_id)
            if not is_valid:
                logging.warning(f"Category {category_id} is not found in product_categories")
                await callback.message.answer("⚠️ این دسته‌بندی محصول وجود ندارد. لطفا دسته‌بندی دیگری انتخاب کنید.")
                return
                
            # نمایش زیردسته‌بندی‌های محصول یا محصولات
            await show_product_categories(callback.message, state, category_id)
                
        elif cat_type == 'service':
            # فقط دسته‌بندی‌های خدمت را بررسی می‌کنیم
            is_valid = db.check_service_category_exists(category_id)
            if not is_valid:
                logging.warning(f"Category {category_id} is not found in service_categories")
                await callback.message.answer("⚠️ این دسته‌بندی خدمت وجود ندارد. لطفا دسته‌بندی دیگری انتخاب کنید.")
                return
                
            # نمایش زیردسته‌بندی‌های خدمت یا خدمات
            await show_service_categories(callback.message, state, category_id)
            
        else:
            logging.error(f"Unknown category type: {cat_type}")
            await callback.message.answer("⚠️ نوع دسته‌بندی نامشخص است. لطفا دوباره تلاش کنید.")
    
    except Exception as e:
        logging.error(f"Error in callback_category: {str(e)}")
        logging.error(traceback.format_exc())
        await callback.message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید یا با پشتیبانی تماس بگیرید.")

@router.callback_query(F.data == "products")
async def callback_products(callback: CallbackQuery, state: FSMContext):
    """Handle products button click"""
    await callback.answer()
    await state.update_data(cat_type='product')
    await show_product_categories(callback.message, state)
    
@router.callback_query(F.data == "services")
async def callback_services(callback: CallbackQuery, state: FSMContext):
    """Handle services button click"""
    await callback.answer()
    await state.update_data(cat_type='service')
    await show_service_categories(callback.message, state)

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
    
    # Log product information for debugging
    logging.debug(f"Product details: {product}")
    
    # Format the product details with additional information
    product_text = f"🛒 {product['name']}\n\n"
    
    # Add price information if available
    if 'price' in product and product['price']:
        product_text += f"💰 قیمت: {product['price']} تومان\n\n"
    
    # Add additional information if available
    additional_info = []
    
    # Add brand if available
    if 'brand' in product and product['brand']:
        additional_info.append(f"🏢 برند: {product['brand']}")
    
    # Add model if available
    if 'model' in product and product['model']:
        additional_info.append(f"📱 مدل: {product['model']}")
    
    # Add model_number if available
    if 'model_number' in product and product['model_number']:
        additional_info.append(f"📋 شماره مدل: {product['model_number']}")
    
    # Add manufacturer if available
    if 'manufacturer' in product and product['manufacturer']:
        additional_info.append(f"🏭 سازنده: {product['manufacturer']}")
    
    # Add tags if available
    if 'tags' in product and product['tags']:
        additional_info.append(f"🏷️ برچسب‌ها: {product['tags']}")
    
    # Add in_stock status if available and true
    if 'in_stock' in product and product['in_stock']:
        additional_info.append("✅ موجود در انبار")
    
    # Add featured status if available and true
    if 'featured' in product and product['featured']:
        additional_info.append("⭐ محصول ویژه")
    
    # Add additional info to product text if available
    if additional_info:
        product_text += "\n".join(additional_info) + "\n\n"
    
    # Add description
    if 'description' in product and product['description']:
        product_text += f"📝 توضیحات:\n{product['description']}\n\n"
    
    # Add keyboard for inquiry and back
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍️ استعلام قیمت", callback_data=f"inquiry:product:{product_id}")
    
    # Get category for back button
    kb.button(text="🔙 بازگشت", callback_data=f"category:{product['category_id']}")
    kb.adjust(1)
    
    # Create keyboard with inquiry button
    keyboard = kb.as_markup()
    
    # Send media files with product info and keyboard
    if media_files:
        await send_product_media(callback.message.chat.id, media_files, product, keyboard)
    else:
        # If no media, send only text description with keyboard
        await callback.message.answer(product_text, reply_markup=keyboard)

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
    
    # Log service information for debugging
    logging.debug(f"Service details: {service}")
    
    # Format the service details with additional information
    service_text = f"🛠️ {service['name']}\n\n"
    
    # Add price information if available
    if 'price' in service and service['price']:
        service_text += f"💰 قیمت: {service['price']} تومان\n\n"
    
    # Add additional information if available
    additional_info = []
    
    # Add tags if available
    if 'tags' in service and service['tags']:
        additional_info.append(f"🏷️ برچسب‌ها: {service['tags']}")
    
    # Add featured status if available and true
    if 'featured' in service and service['featured']:
        additional_info.append("⭐ خدمت ویژه")
    
    # Add available status if available and true
    if 'available' in service and service['available']:
        additional_info.append("✅ در دسترس")
    
    # Add additional info to service text if available
    if additional_info:
        service_text += "\n".join(additional_info) + "\n\n"
    
    # Add description
    if 'description' in service and service['description']:
        service_text += f"📝 توضیحات:\n{service['description']}\n\n"
    
    # Add keyboard for inquiry and back
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍️ استعلام قیمت", callback_data=f"inquiry:service:{service_id}")
    
    # Get category for back button
    kb.button(text="🔙 بازگشت", callback_data=f"category:{service['category_id']}")
    kb.adjust(1)
    
    # Create keyboard with inquiry button
    keyboard = kb.as_markup()
    
    # Send media files with service info and keyboard
    if media_files:
        await send_service_media(callback.message.chat.id, media_files, service, keyboard)
    else:
        # If no media, send only text description with keyboard
        await callback.message.answer(service_text, reply_markup=keyboard)

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
            
            # Handle auto-generated educational content IDs specially
            elif file_id.startswith('educational_content_image_'):
                # Extract the content ID and search for the associated image
                try:
                    # Extract content ID from file_id
                    content_id = file_id.split('_')[3]  # educational_content_image_56_timestamp
                    
                    # Special case for known problem files
                    if file_id == "educational_content_image_56_1747350587":
                        # This is our problem file, directly use the known correct path
                        file_found = True
                        file_path = "./static/media/educational/image_7.jpg"
                        logging.info(f"Using hardcoded path for problem file: {file_path}")
                    else:
                        # Try common paths for educational content images
                        test_paths = [
                            f"./static/media/educational/image_{content_id}.jpg",
                            f"./media/educational/image_{content_id}.jpg",
                            f"./static/media/educational/content_{content_id}.jpg",
                            f"./media/educational/content_{content_id}.jpg",
                            "./static/media/educational/image_7.jpg",  # Specific path from logs
                            "./media/educational/image_7.jpg"         # Alternative path
                        ]
                    
                    # Try each possible path
                    for test_path in test_paths:
                        logging.info(f"Checking path: {test_path} (exists: {os.path.exists(test_path)})")
                        if os.path.exists(test_path):
                            file_found = True
                            file_path = test_path
                            logging.info(f"Found auto-generated educational content image at: {file_path}")
                            break
                    
                    if not file_found:
                        logging.error(f"Could not find image for educational content ID {content_id} after trying multiple paths")
                    
                    # If found, add to media group
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
                except Exception as e:
                    logging.error(f"Error processing auto-generated educational content ID: {str(e)}")
                    
            # If file wasn't found and it looks like a Telegram file_id (no slashes)
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


async def send_product_media(chat_id, media_files, product_info=None, reply_markup=None):
    """
    Send product media files to user as a media group with caption
    
    Args:
        chat_id: Telegram chat ID to send media to
        media_files: List of media file information
        product_info: Optional dictionary with product information (name, price, description)
        reply_markup: Optional reply markup (keyboard) to include with the message
    """
    from bot import bot  # Import bot here to avoid circular imports
    from utils import create_telegraph_page  # Import telegraph function
    
    # Log what we received for debugging
    logging.debug(f"Product info received: {product_info}")
    
    # Check if we have any media files
    if not media_files:
        logging.warning(f"No media files provided to send_product_media for chat_id {chat_id}")
        
        # If we have product info but no media, send text message with keyboard
        if product_info:
            title = product_info.get('name', '')
            price = product_info.get('price', '')
            description = product_info.get('description', '')
            
            # Get additional product metadata
            brand = product_info.get('brand')
            model = product_info.get('model')
            model_number = product_info.get('model_number')
            manufacturer = product_info.get('manufacturer')
            tags = product_info.get('tags')
            in_stock = product_info.get('in_stock')
            featured = product_info.get('featured')
            
            message_text = f"🛒 *{title}*\n\n"
            if price:
                message_text += f"💰 قیمت: {price} تومان\n\n"
                
            # Add additional information if available
            additional_info = []
            if brand:
                additional_info.append(f"🏢 برند: {brand}")
            if model:
                additional_info.append(f"📱 مدل: {model}")
            if model_number:
                additional_info.append(f"📋 شماره مدل: {model_number}")
            if manufacturer:
                additional_info.append(f"🏭 سازنده: {manufacturer}")
            if tags:
                additional_info.append(f"🏷️ برچسب‌ها: {tags}")
            if in_stock:
                additional_info.append("✅ موجود در انبار")
            if featured:
                additional_info.append("⭐ محصول ویژه")
                
            # Add additional info to message_text if available
            if additional_info:
                message_text += "\n".join(additional_info) + "\n\n"
                
            message_text += f"📝 توضیحات:\n{description}\n\n"
            
            # Send message with keyboard
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logging.error(f"Failed to send product message: {e}")
        
        return
        
    logging.info(f"Attempting to send {len(media_files)} media files to chat_id {chat_id}")
    
    # Prepare the caption for the first media
    caption = ""
    title = ""
    description = ""
    telegraph_url = None
    
    if product_info:
        title = product_info.get('name', '')
        price = product_info.get('price', '')
        description = product_info.get('description', '')
        
        # Get additional product metadata
        brand = product_info.get('brand')
        model = product_info.get('model')
        model_number = product_info.get('model_number')
        manufacturer = product_info.get('manufacturer')
        tags = product_info.get('tags')
        in_stock = product_info.get('in_stock')
        featured = product_info.get('featured')
        
        # Build caption
        caption = f"🛒 {title}\n\n"
        if price:
            caption += f"💰 قیمت: {price} تومان\n\n"
        
        # Add additional information if available
        additional_info = []
        if brand:
            additional_info.append(f"🏢 برند: {brand}")
        if model:
            additional_info.append(f"📱 مدل: {model}")
        if model_number:
            additional_info.append(f"📋 شماره مدل: {model_number}")
        if manufacturer:
            additional_info.append(f"🏭 سازنده: {manufacturer}")
        if tags:
            additional_info.append(f"🏷️ برچسب‌ها: {tags}")
        if in_stock:
            additional_info.append("✅ موجود در انبار")
        if featured:
            additional_info.append("⭐ محصول ویژه")
            
        # Add additional info to caption if available
        if additional_info:
            caption += "\n".join(additional_info) + "\n\n"
        
        # Check if description is too long (limit around 1000 characters for captions)
        if description and len(description) > 800:
            # Create Telegraph page for long descriptions
            try:
                telegraph_url = await create_telegraph_page(
                    title=title,
                    content=description,
                    author="RFCatalogbot"
                )
                
                # Add shortened description + link
                caption += f"📝 توضیحات:\n{description[:300]}...\n\n"
                if telegraph_url:
                    caption += f"📄 [مشاهده توضیحات کامل]({telegraph_url})"
            except Exception as e:
                logging.error(f"Error creating Telegraph page: {e}")
                # If Telegraph creation fails, use regular caption
                caption += f"📝 توضیحات:\n{description}\n\n"
        else:
            # Description fits in caption
            caption += f"📝 توضیحات:\n{description}\n\n"
    
    # Create a media group for sending multiple files
    media_group = []
    found_valid_media = False
    
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
    
    # Add product main image first if it exists and we're processing a product
    main_photo_added = False
    if product_info and 'photo_url' in product_info and product_info['photo_url']:
        photo_url = product_info.get('photo_url')
        logging.info(f"Adding product main photo: {photo_url}")
        
        # Check if the main photo exists as a file
        photo_path = f"static/{photo_url}"
        if os.path.isfile(photo_path):
            logging.info(f"Main product photo file found at: {photo_path}")
            try:
                # Add the main photo as the first item with caption
                media_object = InputMediaPhoto(
                    media=FSInputFile(photo_path),
                    caption=caption,
                    parse_mode="Markdown"
                )
                media_group.append(media_object)
                found_valid_media = True
                main_photo_added = True
            except Exception as e:
                logging.error(f"Error adding main product photo: {e}")

    # Process the rest of media files
    for i, media in enumerate(media_files):
        try:
            file_id = media.get('file_id', '')
            file_type = media.get('file_type', 'photo')
            file_name = media.get('file_name', 'unknown')
            local_path = media.get('local_path', '')
            
            # Log the full media info for debugging
            logging.info(f"Processing media: file_id={file_id}, file_type={file_type}, file_name={file_name}")
            
            if not file_id:
                logging.warning(f"Empty file_id for media: {media}")
                continue
            
            # Only add caption to the first item in media group, and only if main photo wasn't added
            item_caption = caption if i == 0 and not main_photo_added else None
            
            # Try a few sample files from attached_assets (this is temporary for testing)
            if file_id == 'show.jpg' and not os.path.isfile(file_id):
                test_file = './attached_assets/show.jpg'
                if os.path.isfile(test_file):
                    file_id = test_file
                    logging.info(f"Found test file at {test_file}")
            
            media_found = False
            media_object = None
            
            # Check if it's an URL
            if isinstance(file_id, str) and file_id.startswith('http'):
                logging.info(f"File is a URL: {file_id}")
                if file_type == 'photo':
                    media_object = InputMediaPhoto(
                        media=file_id,
                        caption=item_caption,
                        parse_mode="Markdown"
                    )
                elif file_type == 'video':
                    media_object = InputMediaVideo(
                        media=file_id,
                        caption=item_caption,
                        parse_mode="Markdown"
                    )
                media_found = True
                
            # Check if it's a local file with full path
            elif file_id and os.path.isfile(file_id):
                logging.info(f"File is a local path that exists: {file_id}")
                if file_type == 'photo':
                    media_object = InputMediaPhoto(
                        media=FSInputFile(file_id),
                        caption=item_caption,
                        parse_mode="Markdown"
                    )
                elif file_type == 'video':
                    media_object = InputMediaVideo(
                        media=FSInputFile(file_id),
                        caption=item_caption,
                        parse_mode="Markdown"
                    )
                media_found = True
                
            # Try with local_path if available
            elif local_path:
                full_path = None
                # Check if it's a relative path or starts with static
                if not local_path.startswith('static/'):
                    full_path = f"./static/{local_path}"
                else:
                    full_path = f"./{local_path}"
                    
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    logging.info(f"Found media file using local_path: {full_path}")
                    if file_type == 'photo':
                        media_object = InputMediaPhoto(
                            media=FSInputFile(full_path),
                            caption=item_caption,
                            parse_mode="Markdown"
                        )
                    elif file_type == 'video':
                        media_object = InputMediaVideo(
                            media=FSInputFile(full_path),
                            caption=item_caption,
                            parse_mode="Markdown"
                        )
                    media_found = True
            
            # Try with filename in various directories
            if not media_found and '/' not in file_id:
                for path in media_paths:
                    full_path = f"{path}{file_id}"
                    if os.path.isfile(full_path):
                        logging.info(f"Found file at {full_path}")
                        if file_type == 'photo':
                            media_object = InputMediaPhoto(
                                media=FSInputFile(full_path),
                                caption=item_caption,
                                parse_mode="Markdown"
                            )
                        elif file_type == 'video':
                            media_object = InputMediaVideo(
                                media=FSInputFile(full_path),
                                caption=item_caption,
                                parse_mode="Markdown"
                            )
                        media_found = True
                        break
            
            # If not found yet, try using file_id as Telegram file_id
            if not media_found:
                logging.info(f"Assuming file_id is a Telegram file_id: {file_id}")
                if file_type == 'photo':
                    media_object = InputMediaPhoto(
                        media=file_id,
                        caption=item_caption,
                        parse_mode="Markdown"
                    )
                elif file_type == 'video':
                    media_object = InputMediaVideo(
                        media=file_id,
                        caption=item_caption,
                        parse_mode="Markdown"
                    )
                media_found = True
            
            # Add to media group if found
            if media_found and media_object:
                media_group.append(media_object)
                found_valid_media = True
                
        except Exception as e:
            logging.error(f"Error processing media file: {str(e)}")
            continue
    
    # Send the media group if we have valid media
    if found_valid_media and media_group:
        logging.info(f"Sending media group with {len(media_group)} items")
        try:
            # First send media group
            await bot.send_media_group(
                chat_id=chat_id,
                media=media_group
            )
            
            # Then send inquiry button and back in a separate message
            if reply_markup:
                await bot.send_message(
                    chat_id=chat_id,
                    text="🔽 گزینه‌های محصول:",
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            logging.error(f"Error sending media group: {str(e)}")
            # Fallback to text-only message with description and telegraph link
            fallback_text = f"🛒 *{title}*\n\n"
            if product_info and product_info.get('price'):
                fallback_text += f"💰 قیمت: {product_info.get('price')} تومان\n\n"
                
            fallback_text += f"📝 توضیحات:\n{description[:500]}...\n\n"
            
            if telegraph_url:
                fallback_text += f"📄 [مشاهده توضیحات کامل]({telegraph_url})"
                
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=fallback_text,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            except Exception as err:
                logging.error(f"Failed to send fallback message: {err}")
    elif product_info:
        # No valid media found, send text-only message
        fallback_text = f"🛒 *{title}*\n\n"
        if product_info.get('price'):
            fallback_text += f"💰 قیمت: {product_info.get('price')} تومان\n\n"
            
        fallback_text += f"📝 توضیحات:\n{description}\n\n"
        
        if telegraph_url:
            fallback_text += f"📄 [مشاهده توضیحات کامل]({telegraph_url})"
            
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=fallback_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        except Exception as e:
            logging.error(f"Failed to send fallback message: {e}")

async def send_service_media(chat_id, media_files, service_info=None, reply_markup=None):
    """
    Send service media files to user as a media group with caption
    
    Args:
        chat_id: Telegram chat ID to send media to
        media_files: List of media file information
        service_info: Optional dictionary with service information (name, price, description)
        reply_markup: Optional reply markup (keyboard) to include with the message
    """
    logging.info(f"send_service_media called with {len(media_files) if media_files else 0} files")
    
    from bot import bot  # Import bot here to avoid circular imports
    from utils import create_telegraph_page  # Import telegraph function
    
    # Check if we have any media files
    if not media_files:
        logging.warning(f"No media files provided to send_service_media for chat_id {chat_id}")
        
        # If we have service info but no media, send text message with keyboard
        if service_info:
            title = service_info.get('name', '')
            price = service_info.get('price', '')
            description = service_info.get('description', '')
            tags = service_info.get('tags', '')
            featured = service_info.get('featured')
            
            # Add service emoji if not already present
            if not title.startswith('🛠️'):
                title = f"🛠️ {title}"
                
            message_text = f"{title}\n\n"
            if price:
                message_text += f"💰 قیمت: {price} تومان\n\n"
                
            # Add additional information if available
            additional_info = []
            if tags:
                additional_info.append(f"🏷️ برچسب‌ها: {tags}")
            if featured:
                additional_info.append("⭐ خدمت ویژه")
                
            # Add additional info to message_text if available
            if additional_info:
                message_text += "\n".join(additional_info) + "\n\n"
                
            message_text += f"📝 توضیحات:\n{description}\n\n"
            
            # Send message with keyboard
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logging.error(f"Failed to send service message: {e}")
        
        return
    
    # Check if service_info exists
    if service_info:
        # Customize service information for display
        title = service_info.get('name', '')
        price = service_info.get('price', '')
        description = service_info.get('description', '')
        tags = service_info.get('tags', '')
        featured = service_info.get('featured')
        
        # Add service emoji if not already present
        if not title.startswith('🛠️'):
            title = f"🛠️ {title}"
            
        # Create caption
        caption = f"{title}\n\n"
        if price:
            caption += f"💰 قیمت: {price} تومان\n\n"
            
        # Add additional information if available
        additional_info = []
        
        # Log values for debugging
        logging.info(f"Service tags: '{tags}' (type: {type(tags)})")
        logging.info(f"Service featured: '{featured}' (type: {type(featured)})")
        
        if tags:
            additional_info.append(f"🏷️ برچسب‌ها: {tags}")
        if featured:
            additional_info.append("⭐ خدمت ویژه")
            
        # Add additional info to caption if available
        if additional_info:
            logging.info(f"Additional info to add: {additional_info}")
            caption += "\n".join(additional_info) + "\n\n"
        else:
            logging.warning("No additional info was added to caption")
        
        # Check if description is too long
        telegraph_url = None
        if description and len(description) > 800:
            # Create Telegraph page for long descriptions
            try:
                telegraph_url = await create_telegraph_page(
                    title=title,
                    content=description,
                    author="RFCatalogbot"
                )
                
                # Add shortened description + link
                caption += f"📝 توضیحات:\n{description[:300]}...\n\n"
                if telegraph_url:
                    caption += f"📄 [مشاهده توضیحات کامل]({telegraph_url})"
            except Exception as e:
                logging.error(f"Error creating Telegraph page: {e}")
                # If Telegraph creation fails, use regular caption
                caption += f"📝 توضیحات:\n{description}\n\n"
        else:
            # Description fits in caption
            caption += f"📝 توضیحات:\n{description}\n\n"
        
        # Process and send service media files
        # First create an empty media group
        found_valid_media = False
        media_group = []
        
        # Add service main image first if it exists
        main_photo_added = False
        if service_info and 'photo_url' in service_info and service_info['photo_url']:
            photo_url = service_info.get('photo_url')
            logging.info(f"Adding service main photo: {photo_url}")
            
            # Check if the photo exists as a file - add all possible paths to try
            possible_paths = [
                f"static/{photo_url}",
                photo_url,
                f"static/uploads/services/{photo_url}",
                f"static/uploads/{photo_url}",
                # Try without 'main' in the path
                photo_url.replace('main/', ''),
                f"static/{photo_url.replace('main/', '')}",
                
                # Try with explicit main path
                f"./static/{photo_url}",
                f"./{photo_url}"
            ]
            
            # Log all path attempts for debugging
            logging.info(f"Trying to find main photo in these paths: {possible_paths}")
            
            photo_path = None
            for path in possible_paths:
                logging.info(f"Checking path: {path}")
                if os.path.isfile(path):
                    photo_path = path
                    logging.info(f"Found main photo at path: {path}")
                    break
                    
            if photo_path:
                logging.info(f"Main service photo file found at: {photo_path}")
                try:
                    # Add the main photo as the first item with caption
                    media_object = InputMediaPhoto(
                        media=FSInputFile(photo_path),
                        caption=caption,
                        parse_mode="Markdown"
                    )
                    media_group.append(media_object)
                    found_valid_media = True
                    main_photo_added = True
                except Exception as e:
                    logging.error(f"Error adding main service photo: {e}")
            else:
                logging.warning(f"Main photo not found in any of the checked paths for photo_url: {photo_url}")
        
        # Filter the media files to remove invalid default media
        valid_media_files = []
        for media_file in media_files:
            file_id = media_file.get('file_id', '')
            # Skip default media files that are causing errors
            if file_id and file_id.startswith('default_media_'):
                logging.warning(f"Skipping likely invalid default media file: {file_id}")
                continue
            valid_media_files.append(media_file)
        
        # If no valid media files and no main photo, send text-only message
        if not valid_media_files and not main_photo_added:
            logging.warning(f"All {len(media_files)} media files were filtered out as invalid and no main photo was found")
            # Send text-only message with full service information
            service_text = f"🛠️ *{title}*\n\n"
            if price:
                service_text += f"💰 قیمت: {price} تومان\n\n"
            
            # Add additional information if available
            if additional_info:
                service_text += "\n".join(additional_info) + "\n\n"
                
            service_text += f"📝 توضیحات:\n{description}\n\n"
            
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=service_text,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
                logging.info(f"Sent text-only message for service with tags: {tags}, featured: {featured}")
                return
            except Exception as e:
                logging.error(f"Failed to send service text-only message: {e}")
                return
                
        # Caption will only be used for the first media if main photo wasn't added
        item_caption = None if main_photo_added else caption
        
        # Define possible paths to check for media files
        media_paths = [
            './', 
            'static/media/services/', 
            'static/uploads/services/',
            'media/services/'
        ]
        
        # Process each media file
        for i, media_file in enumerate(valid_media_files):
            try:
                file_id = media_file.get('file_id', '')
                file_type = media_file.get('file_type', 'photo')  # Default to photo if not specified
                local_path = media_file.get('local_path', '')
                
                # Only the first item should have the caption if main photo wasn't already added
                item_caption = caption if i == 0 and not main_photo_added else ""
                
                media_object = None
                media_found = False
                
                logging.info(f"Processing service media file {i+1}/{len(valid_media_files)}: {file_id}, type: {file_type}")
                
                # Try all possible paths for this service media file
                possible_paths = [
                    local_path,
                    file_id,
                    f"static/{file_id}",
                    f"./{file_id}",
                    f"./static/{file_id}",
                    # For services with paths that include 'uploads/services/'
                    f"static/uploads/services/{os.path.basename(file_id)}",
                    f"static/uploads/services/21/{os.path.basename(file_id)}"
                ]
                
                # Log all path attempts for debugging
                logging.info(f"Trying to find service media file in these paths: {possible_paths}")
                
                # Try all possible paths
                for path in possible_paths:
                    if path and os.path.isfile(path):
                        logging.info(f"Found service media file at path: {path}")
                        if file_type == 'photo':
                            media_object = InputMediaPhoto(
                                media=FSInputFile(path),
                                caption=item_caption,
                                parse_mode="Markdown"
                            )
                        elif file_type == 'video':
                            media_object = InputMediaVideo(
                                media=FSInputFile(path),
                                caption=item_caption,
                                parse_mode="Markdown"
                            )
                        media_found = True
                        break
                
                # If still not found, try with various directory combinations
                if not media_found:
                    # Try with all media paths
                    for path in media_paths:
                        # Try with various combinations
                        path_combinations = [
                            f"{path}{file_id}",
                            f"{path}{os.path.basename(file_id)}",
                            f"{path}21/{os.path.basename(file_id)}",
                            f"{path}main/{os.path.basename(file_id)}"
                        ]
                        
                        for full_path in path_combinations:
                            logging.info(f"Checking service media path: {full_path}")
                            if os.path.isfile(full_path):
                                logging.info(f"Found service media file at: {full_path}")
                                if file_type == 'photo':
                                    media_object = InputMediaPhoto(
                                        media=FSInputFile(full_path),
                                        caption=item_caption,
                                        parse_mode="Markdown"
                                    )
                                elif file_type == 'video':
                                    media_object = InputMediaVideo(
                                        media=FSInputFile(full_path),
                                        caption=item_caption,
                                        parse_mode="Markdown"
                                    )
                                media_found = True
                                break
                        
                        if media_found:
                            break
                
                # If not found yet, try using file_id as Telegram file_id only if it looks valid
                if not media_found and not file_id.startswith('default_media_'):
                    logging.info(f"Assuming file_id is a Telegram file_id: {file_id}")
                    if file_type == 'photo':
                        media_object = InputMediaPhoto(
                            media=file_id,
                            caption=item_caption,
                            parse_mode="Markdown"
                        )
                    elif file_type == 'video':
                        media_object = InputMediaVideo(
                            media=file_id,
                            caption=item_caption,
                            parse_mode="Markdown"
                        )
                    media_found = True
                
                # Add to media group if found
                if media_found and media_object:
                    media_group.append(media_object)
                    found_valid_media = True
                    
            except Exception as e:
                logging.error(f"Error processing service media file: {str(e)}")
                continue
        
        # Send the media group if we have valid media
        if found_valid_media and media_group:
            logging.info(f"Sending service media group with {len(media_group)} items")
            try:
                # First send media group
                await bot.send_media_group(
                    chat_id=chat_id,
                    media=media_group
                )
                
                # Then send inquiry button and back in a separate message
                if reply_markup:
                    await bot.send_message(
                        chat_id=chat_id,
                        text="🔽 گزینه‌های خدمت:",
                        reply_markup=reply_markup
                    )
                    
            except Exception as e:
                logging.error(f"Error sending service media group: {str(e)}")
                # Fallback to text-only message with description
                fallback_text = f"🛠️ *{title}*\n\n"
                if price:
                    fallback_text += f"💰 قیمت: {price} تومان\n\n"
                
                # Add additional information if available
                if additional_info:
                    fallback_text += "\n".join(additional_info) + "\n\n"
                    
                fallback_text += f"📝 توضیحات:\n{description[:500]}...\n\n"
                
                if telegraph_url:
                    fallback_text += f"📄 [مشاهده توضیحات کامل]({telegraph_url})"
                    
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=fallback_text,
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
                except Exception as err:
                    logging.error(f"Failed to send service fallback message: {err}")
        else:
            # No valid media found, send text-only message
            fallback_text = f"🛠️ *{title}*\n\n"
            if price:
                fallback_text += f"💰 قیمت: {price} تومان\n\n"
            
            # Add additional information if available
            if additional_info:
                fallback_text += "\n".join(additional_info) + "\n\n"
                
            fallback_text += f"📝 توضیحات:\n{description}\n\n"
            
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=fallback_text,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logging.error(f"Failed to send service text-only message: {e}")
    else:
        # If no service_info, send a generic message
        if media_files:
            await bot.send_message(
                chat_id=chat_id,
                text="⚠️ اطلاعات خدمت موجود نیست.",
                reply_markup=reply_markup
            )

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