import traceback
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from configuration import SERVICES_BTN
from logging_config import get_logger
from extensions import database
from bot import bot
from utils.media_utils import send_service_media_group_to_user
from keyboards import service_categories_keyboard, service_content_keyboard, service_detail_keyboard
from aiogram.filters import Command

from handlers.handlers_utils import format_price
from callback_formatter import callback_formatter

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
            "🛠️ *دسته‌بندی خدمات*\n\nلطفا یکی از دسته‌بندی‌های زیر را انتخاب کنید:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Service categories sent: {len(categories)} categories")
    except Exception as e:
        logger.error(f"Error in cmd_services: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

@router.callback_query(F.data == callback_formatter.write('services'))
async def callback_services(callback: CallbackQuery):
    """Handle services button click"""
    await callback.answer()
    try:
        categories = db.get_service_categories()
        if not categories:
            await callback.message.answer("در حال حاضر دسته‌بندی خدمات موجود نیست.")
            logger.warning("No service categories found")
            return

        for category in categories:
            category_id = category['id']
            subcategory_count = int(category.get('subcategory_count', 0))
            service_count = int(category.get('service_count', 0))
            category['content_count'] = subcategory_count + service_count

        keyboard = service_categories_keyboard(categories)
        await callback.message.answer("🛠️ دسته‌بندی خدمات را انتخاب کنید:",
                                     reply_markup=keyboard)
        logger.info(f"Service categories sent to user: {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Error in callback_services: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش دسته‌بندی خدمات رخ داد.")

@router.callback_query(lambda c: callback_formatter.read(c.data)[0] == 'service_category' if callback_formatter.read(c.data) else False)
async def callback_service_category(callback: CallbackQuery):
    """Handle service category selection"""
    await callback.answer()
    try:
        result = callback_formatter.read(callback.data)
        if not result or result[0] != 'service_category':
            logger.error(f"Invalid callback data: {callback.data}")
            await callback.message.answer("⚠️ داده نامعتبر است.")
            return

        _, params = result
        category_id = params['category_id']
        logger.info(f"Selected service category ID: {category_id} by user: {callback.from_user.id}")
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
        await callback.message.answer(f"🛠️ خدمات در دسته‌بندی '{category_info['name']}':",
                                     reply_markup=keyboard)
        logger.info(f"Services sent for category ID: {category_id}")
    except Exception as e:
        logger.error(f"Error in callback_service_category: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش خدمات رخ داد.")

@router.callback_query(F.data == callback_formatter.write('services'))
async def callback_service_categories(callback: CallbackQuery):
    """Handle going back to service categories"""
    await callback.answer()
    try:
        categories = db.get_service_categories()
        if not categories:
            await callback.message.answer("در حال حاضر دسته‌بندی خدمات موجود نیست.")
            logger.warning("No service categories found")
            return

        keyboard = service_categories_keyboard(categories)
        await callback.message.answer("🛠️ دسته‌بندی خدمات را انتخاب کنید:",
                                     reply_markup=keyboard)
        logger.info(f"Service categories sent to user: {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Error in callback_service_categories: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش دسته‌بندی‌ها رخ داد.")

@router.callback_query(lambda c: callback_formatter.read(c.data)[0] == 'service_item' if callback_formatter.read(c.data) else False)
async def callback_service(callback: CallbackQuery, state: FSMContext):
    """Handle service selection"""
    logger.debug(f"callback_service called with data: {callback.data}")
    await callback.answer()
    try:
        result = callback_formatter.read(callback.data)
        if not result or result[0] != 'service_item':
            logger.error(f"Invalid callback data: {callback.data}")
            await callback.message.answer("⚠️ داده نامعتبر است.")
            return

        _, params = result
        service_id = params['service_id']
        logger.info(f"Selected service ID: {service_id} by user: {callback.from_user.id}")

        # Get service details
        service = db.get_service(service_id)
        if not service:
            logger.error(f"Service not found for ID: {service_id}")
            await callback.message.answer("⚠️ خدمت مورد نظر یافت نشد.")
            return

        # Save service_id in state for inquiry
        await state.update_data(service_id=service_id)
        await state.set_state("view_service")  # Assuming UserStates.view_service is defined elsewhere

        # Format the service details with additional information
        service_text = f"🛠️ {service['name']}\n\n"
        if 'description' in service and service['description']:
            service_text += f"📝 توضیحات:\n{service['description']}\n\n"
        if 'price' in service and service['price']:
            service_text += f"💰 قیمت: {format_price(service['price'])} تومان\n\n"
        if 'duration' in service and service['duration']:
            service_text += f"⏳ مدت زمان: {service['duration']}\n\n"
        if 'provider' in service and service['provider']:
            service_text += f"🏢 ارائه‌دهنده: {service['provider']}\n\n"

        additional_info = []
        if 'tags' in service and service['tags']:
            additional_info.append(f"🏷️ برچسب‌ها: {service['tags']}")
        if 'featured' in service and service['featured']:
            additional_info.append("⭐ خدمت ویژه")
        if 'available' in service and service['available']:
            additional_info.append("✅ در دسترس")

        if additional_info:
            service_text += "\n\n".join(additional_info) + "\n\n"

        # Create keyboard with inquiry and back buttons
        kb = InlineKeyboardBuilder()
        kb.button(text="🛍️ استعلام قیمت", callback_data=f"inquiry:service:{service_id}")
        kb.button(text="🔙 بازگشت", callback_data=f"service_category:{service['category_id']}")
        kb.adjust(1)
        keyboard = kb.as_markup()

        chat_id = callback.message.chat.id
        media = db.get_service_media(service_id)
        logger.debug(f"Raw media from db.get_service_media for service {service_id}: {media}")

        # Validate inputs
        if not isinstance(bot, Bot):
            logger.error(f"bot باید نمونه Bot باشد، نوع: {type(bot)}")
            await callback.message.answer("⚠️ خطای داخلی سرور. لطفا بعداً تلاش کنید.")
            return
        if not isinstance(chat_id, int):
            logger.error(f"chat_id باید عدد باشد، نوع: {type(chat_id)}")
            await callback.message.answer("⚠️ خطای داخلی سرور. لطفا بعداً تلاش کنید.")
            return
        if not media:
            logger.warning(f"هیچ مدیایی برای خدمت {service_id} پیدا نشد")
            await callback.message.answer(service_text, reply_markup=keyboard, parse_mode="Markdown")
            return
        if not isinstance(media, list):
            logger.error(f"media باید لیست باشد، نوع: {type(media)}")
            await callback.message.answer(service_text, reply_markup=keyboard, parse_mode="Markdown")
            return

        # Convert media to media_items
        media_items = [
            {
                'id': m.get('id'),
                'file_id': m.get('file_id'),
                'file_type': m.get('file_type'),
                'local_path': m.get('local_path')
            } for m in media
        ]
        logger.debug(f"Initial media_items for service {service_id}: {media_items}")

        # Filter out incomplete media items
        media_items = [item for item in media_items if item['id'] and item['file_type'] and (item['file_id'] or item['local_path'])]
        logger.debug(f"Filtered media_items for service {service_id}: {media_items}")

        if not media_items:
            logger.warning(f"media_items خالی یا ناقص است برای خدمت {service_id}")
            await callback.message.answer(service_text, reply_markup=keyboard, parse_mode="Markdown")
            return

        # Send media files with service info and keyboard
        logger.debug(f"Calling send_service_media_group_to_user with bot: {type(bot)}, chat_id: {chat_id}, media_items: {media_items}, caption: {service_text}")
        try:
            await send_service_media_group_to_user(
                bot=bot,
                chat_id=chat_id,
                media_items=media_items,
                caption=service_text,
                reply_markup=keyboard
            )
            logger.info(f"Service {service_id} sent to chat_id: {chat_id}")
        except Exception as e:
            logger.error(f"Error sending service media: {str(e)}\n{traceback.format_exc()}")
            await callback.message.answer("⚠️ خطایی در ارسال رسانه‌های خدمت رخ داد.")
            await callback.message.answer(service_text, reply_markup=keyboard, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in callback_service: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش خدمت رخ داد.")
