"""
ماژول هندلرهای بات تلگرام
این ماژول، مدیریت پیام‌ها و دستورات تلگرام را انجام می‌دهد.
"""

import os
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.models.database import Database
from src.bot.keyboards import get_main_keyboard, get_back_keyboard, get_categories_keyboard, get_admin_keyboard
from src.config.configuration import (
    PRODUCTS_BTN, SERVICES_BTN, INQUIRY_BTN, EDUCATION_BTN, CONTACT_BTN, ABOUT_BTN, 
    BACK_BTN, SEARCH_BTN, ADMIN_BTN, PRODUCT_PREFIX, SERVICE_PREFIX, CATEGORY_PREFIX,
    BACK_PREFIX, INQUIRY_PREFIX, EDUCATION_PREFIX, ADMIN_PREFIX
)

# Create routers
main_router = Router()
admin_router = Router()
product_router = Router()
service_router = Router()
inquiry_router = Router()
education_router = Router()

# Database instance
db = Database()

# Logging
logger = logging.getLogger(__name__)

# Command handlers
@main_router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    await message.answer(
        "به ربات RFCBot خوش آمدید!\n"
        "از منوی زیر یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=get_main_keyboard()
    )

@main_router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = (
        "راهنمای استفاده از ربات RFCBot:\n\n"
        "👉 برای مشاهده محصولات: /products یا دکمه «محصولات»\n"
        "👉 برای مشاهده خدمات: /services یا دکمه «خدمات»\n"
        "👉 برای استعلام قیمت: دکمه «استعلام قیمت»\n"
        "👉 برای محتوای آموزشی: /education یا دکمه «محتوای آموزشی»\n"
        "👉 برای اطلاعات تماس: /contact یا دکمه «تماس با ما»\n"
        "👉 برای اطلاعات درباره ما: /about یا دکمه «درباره ما»"
    )
    await message.answer(help_text, reply_markup=get_main_keyboard())

@main_router.message(Command("products"))
async def cmd_products(message: Message):
    """Handle /products command - Show product categories"""
    categories = db.get_categories(cat_type='product')
    await message.answer(
        "لطفاً دسته‌بندی محصولات مورد نظر خود را انتخاب کنید:",
        reply_markup=get_categories_keyboard(categories)
    )

@main_router.message(Command("services"))
async def cmd_services(message: Message):
    """Handle /services command - Show service categories"""
    categories = db.get_categories(cat_type='service')
    await message.answer(
        "لطفاً دسته‌بندی خدمات مورد نظر خود را انتخاب کنید:",
        reply_markup=get_categories_keyboard(categories, prefix=SERVICE_PREFIX)
    )

@main_router.message(Command("about"))
async def cmd_about(message: Message):
    """Handle /about command - Show about information"""
    about_content = db.get_static_content('about')
    if not about_content:
        about_content = "اطلاعات درباره ما هنوز تنظیم نشده است."
    
    await message.answer(about_content, reply_markup=get_main_keyboard())

@main_router.message(Command("contact"))
async def cmd_contact(message: Message):
    """Handle /contact command - Show contact information"""
    contact_content = db.get_static_content('contact')
    if not contact_content:
        contact_content = "اطلاعات تماس هنوز تنظیم نشده است."
    
    await message.answer(contact_content, reply_markup=get_main_keyboard())

@main_router.message(Command("education"))
async def cmd_education(message: Message):
    """Handle /education command - Show educational content categories"""
    categories = db.get_educational_categories()
    
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.add(InlineKeyboardButton(
            text=category,
            callback_data=f"{EDUCATION_PREFIX}{category}"
        ))
    
    builder.adjust(2)  # 2 buttons per row
    
    await message.answer(
        "لطفاً دسته‌بندی محتوای آموزشی مورد نظر خود را انتخاب کنید:",
        reply_markup=builder.as_markup()
    )

# Text message handlers
@main_router.message(lambda message: message.text == PRODUCTS_BTN)
async def text_products(message: Message):
    """Handle 'Products' button press"""
    await cmd_products(message)

@main_router.message(lambda message: message.text == SERVICES_BTN)
async def text_services(message: Message):
    """Handle 'Services' button press"""
    await cmd_services(message)

@main_router.message(lambda message: message.text == EDUCATION_BTN)
async def text_education(message: Message):
    """Handle 'Educational Content' button press"""
    await cmd_education(message)

@main_router.message(lambda message: message.text == ABOUT_BTN)
async def text_about(message: Message):
    """Handle 'About' button press"""
    await cmd_about(message)

@main_router.message(lambda message: message.text == CONTACT_BTN)
async def text_contact(message: Message):
    """Handle 'Contact' button press"""
    await cmd_contact(message)

@main_router.message(lambda message: message.text == BACK_BTN)
async def text_back(message: Message):
    """Handle 'Back' button press"""
    await cmd_start(message)

# Function to register all handlers
def register_all_handlers(dp: Dispatcher):
    """Register all handlers with the dispatcher"""
    dp.include_router(main_router)
    dp.include_router(admin_router)
    dp.include_router(product_router)
    dp.include_router(service_router)
    dp.include_router(inquiry_router)
    dp.include_router(education_router)