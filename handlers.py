"""
ماژول هندلرهای بات تلگرام
این ماژول مدیریت پیام‌ها و دستورات تلگرام را انجام می‌دهد.
"""

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from keyboards import get_main_keyboard, get_back_keyboard, get_categories_keyboard, get_admin_keyboard
from configuration import (
    PRODUCTS_BTN, SERVICES_BTN, INQUIRY_BTN, EDUCATION_BTN, CONTACT_BTN, ABOUT_BTN,
    BACK_BTN, SEARCH_BTN, ADMIN_BTN, PRODUCT_PREFIX, SERVICE_PREFIX, CATEGORY_PREFIX,
    BACK_PREFIX, INQUIRY_PREFIX, EDUCATION_PREFIX, ADMIN_PREFIX
)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define FSM states
class UserStates(StatesGroup):
    """States for the Telegram bot FSM"""
    browse_categories = State()
    view_product = State()
    view_category = State()
    view_educational_content = State()
    inquiry_name = State()
    inquiry_phone = State()
    inquiry_description = State()
    waiting_for_confirmation = State()

# Create routers
main_router = Router()
admin_router = Router()
product_router = Router()
service_router = Router()
inquiry_router = Router()
education_router = Router()

# Database instance
db = Database()

# Command handlers
@main_router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    logger.debug(f"Processing /start command from user {message.from_user.id}")
    await message.answer(
        "به ربات RFCBot خوش آمدید!\n"
        "از منوی زیر یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=get_main_keyboard()
    )

@main_router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    logger.debug(f"Processing /help command from user {message.from_user.id}")
    help_text = (
        "راهنمای استفاده از ربات RFCBot:\n\n"
        "👉 برای مشاهده محصولات: /products یا دکمه «محصولات»\n"
        "👉 برای مشاهده خدمات: /services یا دکمه «خدمات»\n"
        "👉 برای استعلام قیمت: /inquiry یا دکمه «استعلام قیمت»\n"
        "👉 برای محتوای آموزشی: /education یا دکمه «محتوای آموزشی»\n"
        "👉 برای اطلاعات تماس: /contact یا دکمه «تماس با ما»\n"
        "👉 برای اطلاعات درباره ما: /about یا دکمه «درباره ما»"
    )
    await message.answer(help_text, reply_markup=get_main_keyboard())

@main_router.message(Command("products"))
async def cmd_products(message: Message):
    """Handle /products command - Show product categories"""
    logger.debug(f"Processing /products command from user {message.from_user.id}")
    categories = db.get_product_categories()
    if categories:
        await message.answer(
            "لطفاً دسته‌بندی محصولات مورد نظر خود را انتخاب کنید:",
            reply_markup=get_categories_keyboard(categories)
        )
    else:
        logger.warning("No product categories found in database")
        await message.answer(
            "هیچ دسته‌بندی محصولی یافت نشد!",
            reply_markup=get_main_keyboard()
        )

@main_router.message(Command("services"))
async def cmd_services(message: Message):
    """Handle /services command - Show service categories"""
    logger.debug(f"Processing /services command from user {message.from_user.id}")
    categories = db.get_service_categories()
    if categories:
        await message.answer(
            "لطفاً دسته‌بندی خدمات مورد نظر خود را انتخاب کنید:",
            reply_markup=get_categories_keyboard(categories, prefix=SERVICE_PREFIX)
        )
    else:
        logger.warning("No service categories found in database")
        await message.answer(
            "هیچ دسته‌بندی خدماتی یافت نشد!",
            reply_markup=get_main_keyboard()
        )

@main_router.message(Command("about"))
async def cmd_about(message: Message):
    """Handle /about command - Show about information"""
    logger.debug(f"Processing /about command from user {message.from_user.id}")
    about_content = db.get_static_content('about')
    if not about_content:
        logger.warning("No about content found in database")
        about_content = "اطلاعات درباره ما هنوز تنظیم نشده است."
    await message.answer(about_content, reply_markup=get_main_keyboard())

@main_router.message(Command("contact"))
async def cmd_contact(message: Message):
    """Handle /contact command - Show contact information"""
    logger.debug(f"Processing /contact command from user {message.from_user.id}")
    contact_content = db.get_static_content('contact')
    if not contact_content:
        logger.warning("No contact content found in database")
        contact_content = "اطلاعات تماس هنوز تنظیم نشده است."
    await message.answer(contact_content, reply_markup=get_main_keyboard())

@main_router.message(Command("education"))
async def cmd_education(message: Message):
    """Handle /education command - Show educational content categories"""
    logger.debug(f"Processing /education command from user {message.from_user.id}")
    categories = db.get_educational_categories()
    if not categories:
        logger.warning("No educational categories found in database")
        await message.answer(
            "هیچ دسته‌بندی محتوای آموزشی یافت نشد!",
            reply_markup=get_main_keyboard()
        )
        return
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.add(InlineKeyboardButton(
            text=category['name'],
            callback_data=f"{EDUCATION_PREFIX}{category['id']}"
        ))
    builder.adjust(2)  # 2 buttons per row
    await message.answer(
        "لطفاً دسته‌بندی محتوای آموزشی مورد نظر خود را انتخاب کنید:",
        reply_markup=builder.as_markup()
    )

@main_router.message(Command("inquiry"))
async def cmd_inquiry(message: Message, state: FSMContext):
    """Handle /inquiry command - Start inquiry process"""
    logger.debug(f"Processing /inquiry command from user {message.from_user.id}")
    await message.answer(
        "لطفاً نام خود را وارد کنید:",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(UserStates.inquiry_name)

# Text message handlers
@main_router.message(F.text == PRODUCTS_BTN)
async def text_products(message: Message):
    """Handle 'Products' button press"""
    logger.debug(f"Processing 'Products' button from user {message.from_user.id}")
    await cmd_products(message)

@main_router.message(F.text == SERVICES_BTN)
async def text_services(message: Message):
    """Handle 'Services' button press"""
    logger.debug(f"Processing 'Services' button from user {message.from_user.id}")
    await cmd_services(message)

@main_router.message(F.text == EDUCATION_BTN)
async def text_education(message: Message):
    """Handle 'Educational Content' button press"""
    logger.debug(f"Processing 'Education' button from user {message.from_user.id}")
    await cmd_education(message)

@main_router.message(F.text == ABOUT_BTN)
async def text_about(message: Message):
    """Handle 'About' button press"""
    logger.debug(f"Processing 'About' button from user {message.from_user.id}")
    await cmd_about(message)

@main_router.message(F.text == CONTACT_BTN)
async def text_contact(message: Message):
    """Handle 'Contact' button press"""
    logger.debug(f"Processing 'Contact' button from user {message.from_user.id}")
    await cmd_contact(message)

@main_router.message(F.text == INQUIRY_BTN)
async def text_inquiry(message: Message, state: FSMContext):
    """Handle 'Inquiry' button press"""
    logger.debug(f"Processing 'Inquiry' button from user {message.from_user.id}")
    await cmd_inquiry(message, state)

@main_router.message(F.text == BACK_BTN)
async def text_back(message: Message, state: FSMContext):
    """Handle 'Back' button press"""
    logger.debug(f"Processing 'Back' button from user {message.from_user.id}")
    await state.clear()  # Reset FSM state
    await cmd_start(message)

# Inquiry FSM handlers
@main_router.message(UserStates.inquiry_name)
async def process_inquiry_name(message: Message, state: FSMContext):
    """Handle inquiry name input"""
    logger.debug(f"Processing inquiry name from user {message.from_user.id}: {message.text}")
    await state.update_data(name=message.text)
    await message.answer(
        "لطفاً شماره تماس خود را وارد کنید:",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(UserStates.inquiry_phone)

@main_router.message(UserStates.inquiry_phone)
async def process_inquiry_phone(message: Message, state: FSMContext):
    """Handle inquiry phone input"""
    logger.debug(f"Processing inquiry phone from user {message.from_user.id}: {message.text}")
    await state.update_data(phone=message.text)
    await message.answer(
        "لطفاً توضیحات استعلام خود را وارد کنید:",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(UserStates.inquiry_description)

@main_router.message(UserStates.inquiry_description)
async def process_inquiry_description(message: Message, state: FSMContext):
    """Handle inquiry description input"""
    logger.debug(f"Processing inquiry description from user {message.from_user.id}: {message.text}")
    data = await state.get_data()
    name = data.get('name')
    phone = data.get('phone')
    description = message.text
    try:
        inquiry_id = db.add_inquiry(
            user_id=message.from_user.id,
            name=name,
            phone=phone,
            description=description
        )
        await message.answer(
            f"استعلام شما با موفقیت ثبت شد! شماره استعلام: {inquiry_id}",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Error saving inquiry: {str(e)}")
        await message.answer(
            "خطایی در ثبت استعلام رخ داد. لطفاً دوباره تلاش کنید.",
            reply_markup=get_main_keyboard()
        )
    finally:
        await state.clear()

# Callback query handlers
@product_router.callback_query(F.data.startswith(PRODUCT_PREFIX))
async def handle_product_callback(callback: CallbackQuery):
    """Handle product selection callback"""
    logger.debug(f"Processing product callback: {callback.data}")
    try:
        product_id = int(callback.data[len(PRODUCT_PREFIX):])
        product = db.get_product(product_id)
        if product:
            media = db.get_product_media(product_id)
            media_text = f"\nرسانه‌ها: {len(media)} فایل" if media else ""
            await callback.message.answer(
                f"محصول: {product['name']}\n"
                f"قیمت: {product['price']}\n"
                f"توضیحات: {product['description']}\n"
                f"برند: {product['brand']}\n"
                f"مدل: {product['model']}\n"
                f"موجودی: {'موجود' if product['in_stock'] else 'ناموجود'}\n"
                f"برچسب‌ها: {product['tags']}{media_text}",
                reply_markup=get_back_keyboard()
            )
            # Send media if available
            for m in media:
                try:
                    if m['file_type'] == 'photo':
                        await callback.message.answer_photo(m['file_id'])
                    elif m['file_type'] == 'video':
                        await callback.message.answer_video(m['file_id'])
                except Exception as e:
                    logger.error(f"Error sending media {m['file_id']}: {str(e)}")
        else:
            logger.warning(f"Product not found: ID={product_id}")
            await callback.message.answer("محصول یافت نشد!", reply_markup=get_back_keyboard())
    except ValueError:
        logger.error(f"Invalid product ID in callback: {callback.data}")
        await callback.message.answer("خطای ناشناخته در انتخاب محصول!", reply_markup=get_back_keyboard())
    await callback.answer()

@service_router.callback_query(F.data.startswith(SERVICE_PREFIX))
async def handle_service_callback(callback: CallbackQuery):
    """Handle service selection callback"""
    logger.debug(f"Processing service callback: {callback.data}")
    try:
        service_id = int(callback.data[len(SERVICE_PREFIX):])
        service = db.get_service(service_id)
        if service:
            media = db.get_service_media(service_id)
            media_text = f"\nرسانه‌ها: {len(media)} فایل" if media else ""
            await callback.message.answer(
                f"خدمت: {service['name']}\n"
                f"قیمت: {service['price']}\n"
                f"توضیحات: {service['description']}\n"
                f"برچسب‌ها: {service['tags']}{media_text}",
                reply_markup=get_back_keyboard()
            )
            # Send media if available
            for m in media:
                try:
                    if m['file_type'] == 'photo':
                        await callback.message.answer_photo(m['file_id'])
                    elif m['file_type'] == 'video':
                        await callback.message.answer_video(m['file_id'])
                except Exception as e:
                    logger.error(f"Error sending media {m['file_id']}: {str(e)}")
        else:
            logger.warning(f"Service not found: ID={service_id}")
            await callback.message.answer("خدمت یافت نشد!", reply_markup=get_back_keyboard())
    except ValueError:
        logger.error(f"Invalid service ID in callback: {callback.data}")
        await callback.message.answer("خطای ناشناخته در انتخاب خدمت!", reply_markup=get_back_keyboard())
    await callback.answer()

@product_router.callback_query(F.data.startswith(CATEGORY_PREFIX))
async def handle_product_category_callback(callback: CallbackQuery):
    """Handle product category selection callback"""
    logger.debug(f"Processing product category callback: {callback.data}")
    try:
        category_id = int(callback.data[len(CATEGORY_PREFIX):])
        categories = db.get_product_categories_by_parent(category_id)
        products = db.get_products(category_id)
        builder = InlineKeyboardBuilder()
        # Add subcategories
        for category in categories:
            builder.add(InlineKeyboardButton(
                text=category['name'],
                callback_data=f"{CATEGORY_PREFIX}{category['id']}"
            ))
        # Add products
        for product in products:
            builder.add(InlineKeyboardButton(
                text=product['name'],
                callback_data=f"{PRODUCT_PREFIX}{product['id']}"
            ))
        builder.adjust(2)  # 2 buttons per row
        # Add back button
        parent_id = db.get_product_category(category_id)['parent_id'] if db.get_product_category(category_id) else None
        builder.row(InlineKeyboardButton(
            text=BACK_BTN,
            callback_data=f"{BACK_PREFIX}{parent_id or 0}"
        ))
        if categories or products:
            await callback.message.answer(
                "لطفاً یک دسته‌بندی یا محصول انتخاب کنید:",
                reply_markup=builder.as_markup()
            )
        else:
            logger.warning(f"No content in product category: ID={category_id}")
            await callback.message.answer(
                "محتوایی در این دسته‌بندی یافت نشد!",
                reply_markup=get_back_keyboard()
            )
    except ValueError:
        logger.error(f"Invalid category ID in callback: {callback.data}")
        await callback.message.answer("خطای ناشناخته در انتخاب دسته‌بندی!", reply_markup=get_back_keyboard())
    await callback.answer()

@service_router.callback_query(F.data.startswith(CATEGORY_PREFIX))
async def handle_service_category_callback(callback: CallbackQuery):
    """Handle service category selection callback"""
    logger.debug(f"Processing service category callback: {callback.data}")
    try:
        category_id = int(callback.data[len(CATEGORY_PREFIX):])
        categories = db.get_service_categories_by_parent(category_id)
        services = db.get_services(category_id)
        builder = InlineKeyboardBuilder()
        # Add subcategories
        for category in categories:
            builder.add(InlineKeyboardButton(
                text=category['name'],
                callback_data=f"{CATEGORY_PREFIX}{category['id']}"
            ))
        # Add services
        for service in services:
            builder.add(InlineKeyboardButton(
                text=service['name'],
                callback_data=f"{SERVICE_PREFIX}{service['id']}"
            ))
        builder.adjust(2)  # 2 buttons per row
        # Add back button
        parent_id = db.get_service_category(category_id)['parent_id'] if db.get_service_category(category_id) else None
        builder.row(InlineKeyboardButton(
            text=BACK_BTN,
            callback_data=f"{BACK_PREFIX}{parent_id or 0}"
        ))
        if categories or services:
            await callback.message.answer(
                "لطفاً یک دسته‌بندی یا خدمت انتخاب کنید:",
                reply_markup=builder.as_markup()
            )
        else:
            logger.warning(f"No content in service category: ID={category_id}")
            await callback.message.answer(
                "محتوایی در این دسته‌بندی یافت نشد!",
                reply_markup=get_back_keyboard()
            )
    except ValueError:
        logger.error(f"Invalid category ID in callback: {callback.data}")
        await callback.message.answer("خطای ناشناخته در انتخاب دسته‌بندی!", reply_markup=get_back_keyboard())
    await callback.answer()

@education_router.callback_query(F.data.startswith(EDUCATION_PREFIX))
async def handle_education_category_callback(callback: CallbackQuery):
    """Handle educational category selection callback"""
    logger.debug(f"Processing education category callback: {callback.data}")
    try:
        if callback.data.startswith(f"{EDUCATION_PREFIX}content_"):
            content_id = int(callback.data[len(f"{EDUCATION_PREFIX}content_"):])
            content = db.get_educational_content(content_id)
            if content:
                media_text = f"\nرسانه‌ها: {len(content['media'])} فایل" if content['media'] else ""
                await callback.message.answer(
                    f"عنوان: {content['title']}\n"
                    f"دسته‌بندی: {content['category_name'] or content['category']}\n"
                    f"محتوا: {content['content']}{media_text}",
                    reply_markup=get_back_keyboard()
                )
                # Send media if available
                for m in content['media']:
                    try:
                        if m['file_type'] == 'photo':
                            await callback.message.answer_photo(m['file_id'])
                        elif m['file_type'] == 'video':
                            await callback.message.answer_video(m['file_id'])
                    except Exception as e:
                        logger.error(f"Error sending media {m['file_id']}: {str(e)}")
            else:
                logger.warning(f"Educational content not found: ID={content_id}")
                await callback.message.answer(
                    "محتوای آموزشی یافت نشد!",
                    reply_markup=get_back_keyboard()
                )
        else:
            category_id = int(callback.data[len(EDUCATION_PREFIX):])
            contents = db.get_all_educational_content(category_id=category_id)
            if not contents:
                logger.warning(f"No educational content in category: ID={category_id}")
                await callback.message.answer(
                    "هیچ محتوای آموزشی در این دسته‌بندی یافت نشد!",
                    reply_markup=get_back_keyboard()
                )
                await callback.answer()
                return
            builder = InlineKeyboardBuilder()
            for content in contents:
                builder.add(InlineKeyboardButton(
                    text=content['title'],
                    callback_data=f"{EDUCATION_PREFIX}content_{content['id']}"
                ))
            builder.adjust(2)  # 2 buttons per row
            builder.row(InlineKeyboardButton(
                text=BACK_BTN,
                callback_data=f"{BACK_PREFIX}0"
            ))
            await callback.message.answer(
                "محتوای آموزشی موجود:",
                reply_markup=builder.as_markup()
            )
    except ValueError:
        logger.error(f"Invalid education ID in callback: {callback.data}")
        await callback.message.answer("خطای ناشناخته در انتخاب محتوای آموزشی!", reply_markup=get_back_keyboard())
    await callback.answer()

@main_router.callback_query(F.data.startswith(BACK_PREFIX))
async def handle_back_callback(callback: CallbackQuery):
    """Handle back button callback"""
    logger.debug(f"Processing back callback: {callback.data}")
    try:
        parent_id = int(callback.data[len(BACK_PREFIX):])
        if parent_id == 0:
            await cmd_start(callback.message)
        else:
            # Try product categories first
            categories = db.get_product_categories_by_parent(parent_id)
            if not categories:
                # Try service categories if no product categories found
                categories = db.get_service_categories_by_parent(parent_id)
            if categories:
                await callback.message.answer(
                    "لطفاً یک دسته‌بندی انتخاب کنید:",
                    reply_markup=get_categories_keyboard(categories, parent_id=parent_id)
                )
            else:
                logger.warning(f"No parent categories found for ID={parent_id}")
                await cmd_start(callback.message)
    except ValueError:
        logger.error(f"Invalid parent ID in back callback: {callback.data}")
        await cmd_start(callback.message)
    await callback.answer()

# Handle all message types
@main_router.message()
async def handle_unprocessed(message: Message):
    """Handle unprocessed messages of any type"""
    logger.info(
        f"Unprocessed message: update_id={message.message_id}, "
        f"user_id={message.from_user.id}, text={message.text}, "
        f"type={message.content_type}, full_update={message.to_python()}"
    )
    await message.answer("این نوع پیام پشتیبانی نمی‌شود!", reply_markup=get_main_keyboard())

# Handle all callback queries
@main_router.callback_query()
async def handle_unknown_callback(callback: CallbackQuery):
    """Handle unknown callback queries"""
    logger.warning(
        f"Unknown callback: update_id={callback.id}, "
        f"user_id={callback.from_user.id}, data={callback.data}, "
        f"full_update={callback.to_python()}"
    )
    await callback.message.answer("این عملیات پشتیبانی نمی‌شود!", reply_markup=get_main_keyboard())
    await callback.answer()

# Handle edited messages
@main_router.edited_message()
async def handle_edited_message(message: Message):
    """Handle edited messages"""
    logger.info(
        f"Edited message received: update_id={message.message_id}, "
        f"user_id={message.from_user.id}, text={message.text}, "
        f"type={message.content_type}"
    )
    await message.answer("ویرایش پیام پشتیبانی نمی‌شود!", reply_markup=get_main_keyboard())

# Handle channel posts and edited channel posts
@main_router.channel_post()
async def handle_channel_post(message: Message):
    """Handle channel posts"""
    logger.info(
        f"Channel post received: update_id={message.message_id}, "
        f"chat_id={message.chat.id}, text={message.text}"
    )
    # No response since channel posts don't expect replies

@main_router.edited_channel_post()
async def handle_edited_channel_post(message: Message):
    """Handle edited channel posts"""
    logger.info(
        f"Edited channel post received: update_id={message.message_id}, "
        f"chat_id={message.chat.id}, text={message.text}"
    )
    # No response since channel posts don't expect replies



# Function to register all handlers

def register_all_handlers(dp: Dispatcher):
    logger.info("Registering all routers with dispatcher")
    dp.include_router(main_router)
    logger.debug("Registered main_router")
    dp.include_router(admin_router)
    logger.debug("Registered admin_router")
    dp.include_router(product_router)
    logger.debug("Registered product_router")
    dp.include_router(service_router)
    logger.debug("Registered service_router")
    dp.include_router(inquiry_router)
    logger.debug("Registered inquiry_router")
    dp.include_router(education_router)
    logger.debug("Registered education_router")