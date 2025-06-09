from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from configuration import SERVICES_BTN
from logging_config import get_logger
from extensions import database
from .media import send_service_media
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = get_logger('bot')
router = Router(name="services_router")
db = database

async def show_service_categories(message: Message | CallbackQuery, state: FSMContext, parent_id=None):
    """Show service categories"""
    try:
        await state.update_data(cat_type='service')
        logger.info(f"show_service_categories called with parent_id={parent_id}")
        categories = db.get_service_categories(parent_id=parent_id)

        if not categories:
            if parent_id:
                services = db.get_services(parent_id)
                if services:
                    await show_services_list(message, services, parent_id)
                else:
                    await message.answer("خدمتی در این دسته‌بندی وجود ندارد.")
            else:
                await message.answer("دسته‌بندی خدمات موجود نیست.")
            return

        kb = InlineKeyboardBuilder()
        for category in categories:
            subcategory_count = category.get('subcategory_count', 0)
            service_count = category.get('service_count', 0)
            total_items = subcategory_count + service_count
            display_name = f"{category['name']} ({total_items})" if total_items > 0 else category['name']
            kb.button(text=display_name, callback_data=f"category:{category['id']}")

        if parent_id:
            parent_category = db.get_service_category(parent_id)
            if parent_category and parent_category.get('parent_id'):
                kb.button(text="🔙 بازگشت", callback_data=f"category:{parent_category['parent_id']}")
            else:
                kb.button(text="🔙 بازگشت به دسته‌بندی‌های اصلی", callback_data="services")
        else:
            kb.button(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")
        kb.adjust(1)

        if isinstance(message, CallbackQuery):
            await message.message.answer("دسته‌بندی خدمات را انتخاب کنید:", reply_markup=kb.as_markup())
            await message.answer()
        else:
            await message.answer("دسته‌بندی خدمات را انتخاب کنید:", reply_markup=kb.as_markup())
        await state.set_state(UserStates.browse_categories)
    except Exception as e:
        logger.error(f"Error in show_service_categories: {str(e)}")
        await message.answer("⚠️ خطایی در نمایش دسته‌بندی‌های خدمات رخ داد.")

async def show_services_list(message: Message | CallbackQuery, services, parent_id):
    """Show list of services in a category"""
    kb = InlineKeyboardBuilder()
    for service in services:
        kb.button(text=service['name'], callback_data=f"service:{service['id']}")
    kb.button(text="🔙 بازگشت", callback_data=f"category:{parent_id}")
    kb.adjust(1)
    if isinstance(message, CallbackQuery):
        await message.message.answer("خدمات این دسته‌بندی:", reply_markup=kb.as_markup())
        await message.answer()
    else:
        await message.answer("خدمات این دسته‌بندی:", reply_markup=kb.as_markup())

@router.message(lambda message: message.text == SERVICES_BTN)
@router.message(Command("services"))
async def cmd_services(message: Message, state: FSMContext):
    """Handle /services command or Services button"""
    try:
        logger.info(f"Services requested by user: {message.from_user.id}")
        await state.update_data(cat_type='service')
        await show_service_categories(message, state)
    except Exception as e:
        logger.error(f"Error in cmd_services: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

@router.callback_query(F.data == "services")
async def callback_services(callback: CallbackQuery, state: FSMContext):
    """Handle services button click"""
    logger.debug(f"callback_services called with data: {callback.data}")
    await show_service_categories(callback, state)

@router.callback_query(F.data.startswith("service:"))
async def callback_service(callback: CallbackQuery, state: FSMContext):
    """Handle service selection"""
    await callback.answer()
    service_id = int(callback.data.split(':', 1)[1])
    service = db.get_service(service_id)

    if not service:
        await callback.message.answer("خدمت مورد نظر یافت نشد.")
        return

    await state.update_data(service_id=service_id)
    await state.set_state(UserStates.view_service)

    media_files = db.get_service_media(service_id)
    logger.debug(f"Service details: {service}")

    service_text = f"🛠️ {service['name']}\n\n"
    if 'price' in service and service['price']:
        service_text += f"💰 قیمت: {service['price']} تومان\n\n"

    additional_info = []
    if 'tags' in service and service['tags']:
        additional_info.append(f"🏷️ برچسب‌ها: {service['tags']}")
    if 'featured' in service and service['featured']:
        additional_info.append("⭐ خدمت ویژه")
    if 'available' in service and service['available']:
        additional_info.append("✅ در دسترس")
    if additional_info:
        service_text += "\n\n".join(additional_info) + "\n\n"
    if 'description' in service and service['description']:
        service_text += f"📝 توضیحات:\n{service['description']}\n\n"

    kb = InlineKeyboardBuilder()
    kb.button(text="🛍️ استعلام قیمت", callback_data=f"inquiry:service:{service_id}")
    kb.button(text="🔙 بازگشت", callback_data=f"category:{service['category_id']}")
    kb.adjust(1)
    keyboard = kb.as_markup()

    if media_files:
        try:
            await send_service_media(callback.message.chat.id, media_files, service, keyboard)
        except Exception as e:
            logger.debug(f"Error sending service media: {str(e)}\n{traceback.format_exc()}")
            await callback.message.reply("⚠️ خطایی در ارسال رسانه‌های خدمت رخ داد.")
    await callback.message.answer(service_text, reply_markup=keyboard)