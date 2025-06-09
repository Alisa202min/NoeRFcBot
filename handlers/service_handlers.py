from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from configuration import SERVICES_BTN, SERVICE_PREFIX
from logging_config import get_logger
from extensions import database
from bot import bot

from keyboards import service_categories_keyboard, service_content_keyboard, service_detail_keyboard
from aiogram.filters import Command
import traceback
from handlers.handlers_utils import format_price
logger = get_logger('bot')
router = Router(name="services_router")
db = database

@router.message(lambda message: message.text == SERVICES_BTN)
@router.message(Command("services"))
async def cmd_services(message: Message, state: FSMContext):
    """Handle /services command or Services button"""
    try:
        logger.info(f"Services requested by user: {message.from_user.id}")
        categories = db.get_service_categories()
        if not categories:
            await message.answer("⚠️ دسته‌بندی خدمات در حال حاضر در دسترس نیست. لطفا بعدا تلاش کنید.")
            logger.warning("No service categories found in database")
            return

        keyboard = service_categories_keyboard(categories)
        await message.answer(
            "🔧 *دسته‌بندی خدمات*\n\nلطفا یکی از دسته‌بندی‌های زیر را انتخاب کنید:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Service categories sent: {len(categories)} categories")
    except Exception as e:
        logger.error(f"Error in cmd_services: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

@router.callback_query(F.data == "services")
async def callback_services(callback: CallbackQuery):
    """Handle services button click"""
    await callback.answer()
    try:
        categories = db.get_service_categories()
        if not categories:
            await callback.message.answer("در حال حاضر دسته‌بندی خدمات موجود نیست.")
            return

        for category in categories:
            category_id = category['id']
            subcategory_count = int(category.get('subcategory_count', 0))
            service_count = int(category.get('service_count', 0))
            category['content_count'] = subcategory_count + service_count

        keyboard = service_categories_keyboard(categories)
        await callback.message.answer("🔧 دسته‌بندی خدمات را انتخاب کنید:",
                                   reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in callback_services: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش دسته‌بندی خدمات رخ داد.")

@router.callback_query(F.data.startswith(f"{SERVICE_PREFIX}cat_"))
async def callback_service_category(callback: CallbackQuery):
    """Handle service category selection"""
    await callback.answer()
    try:
        category_id = int(callback.data.replace(f"{SERVICE_PREFIX}cat_", ""))
        logger.info(f"Selected service category ID: {category_id}")
        category_info = db.get_service_category(category_id)
        if not category_info:
            logger.error(f"Service category not found for ID: {category_id}")
            await callback.message.answer("⚠️ دسته‌بندی مورد نظر یافت نشد.")
            return

        services = db.get_services(category_id=category_id)
        if not services:
            logger.warning(f"No services found for category ID: {category_id}")
            await callback.message.answer(f"⚠️ خدماتی برای دسته‌بندی '{category_info['name']}' موجود نیست.")
            return

        keyboard = service_content_keyboard(services, category_id)
        await callback.message.answer(f"🔧 خدمات در دسته‌بندی '{category_info['name']}':",
                                   reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in callback_service_category: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش خدمات رخ داد.")

@router.callback_query(F.data == f"{SERVICE_PREFIX}categories")
async def callback_service_categories(callback: CallbackQuery):
    """Handle going back to service categories"""
    await callback.answer()
    try:
        categories = db.get_service_categories()
        if not categories:
            await callback.message.answer("در حال حاضر دسته‌بندی خدمات موجود نیست.")
            return

        keyboard = service_categories_keyboard(categories)
        await callback.message.answer("🔧 دسته‌بندی خدمات را انتخاب کنید:",
                                   reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in callback_service_categories: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش دسته‌بندی‌ها رخ داد.")

@router.callback_query(F.data.startswith(f"{SERVICE_PREFIX}:"))
async def callback_service(callback: CallbackQuery, state: FSMContext):
    """Handle service selection"""
    await callback.answer()
    try:
        service_id = int(callback.data.replace(f"{SERVICE_PREFIX}:", ""))
        logger.info(f"Selected service ID: {service_id}")
        service = db.get_service(service_id)
        if not service:
            logger.error(f"Service not found for ID: {service_id}")
            await callback.message.answer("⚠️ خدمت مورد نظر یافت نشد.")
            return

        category_id = service.get('category_id', 0)
        keyboard = service_detail_keyboard(service_id, category_id)
        service_text = (
            f"🔧 *{service['name']}*\n\n"
            f"💰 قیمت: {format_price(service['price'])}\n\n"
            f"📝 توضیحات:\n{service['description'] or 'بدون توضیحات'}\n"
        )
        if service.get('tags'):
            service_text += f"🏷️ برچسب‌ها: {service['tags']}\n"
        if service.get('available'):
            service_text += "✅ در دسترس\n"
        else:
            service_text += "❌ غیرفعال\n"
        if service.get('featured'):
            service_text += "⭐️ خدمت ویژه\n"

        media_items = db.get_service_media(service_id)
        await send_service_media_group_to_user(
            bot=bot,
            chat_id=callback.message.chat.id,
            media_items=media_items,
            caption=service_text,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in callback_service: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش خدمت رخ داد.")

