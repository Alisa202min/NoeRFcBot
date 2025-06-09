"""
ماژول هندلرهای بات تلگرام
این ماژول مدیریت پیام‌ها و دستورات تلگرام را انجام می‌دهد.
"""

from aiogram import Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from logging_config import get_logger
from extensions import database
from bot import bot
from configuration import (
    PRODUCTS_BTN, SERVICES_BTN, INQUIRY_BTN, EDUCATION_BTN,
    CONTACT_BTN, ABOUT_BTN, SEARCH_BTN
)
from handlers.base_handlers import router as base_router
import UserStates
from handlers.product_handlers import router as products_router
from handlers.service_handlers import router as services_router
from handlers.education_handlers import router as educational_router
from handlers.inquiry_handlers import router as inquiry_router

db = database
logger = get_logger('bot')

router = Router(name="main_router")

router.include_router(base_router)
router.include_router(products_router)
router.include_router(services_router)
router.include_router(educational_router)
router.include_router(inquiry_router)

@router.message(lambda message: message.text == CONTACT_BTN)
async def cmd_contact(message: Message):
    """Handle /contact command or Contact button"""
    try:
        logger.info(f"Contact information requested by user: {message.from_user.id}")
        contact_text = db.get_static_content('contact')
        if not contact_text:
            await message.answer("⚠️ اطلاعات تماس در حال حاضر در دسترس نیست. لطفا بعدا تلاش کنید.")
            logger.warning("Contact information not found in database")
            return

        formatted_text = f"📞 *اطلاعات تماس*\n\n{contact_text}"
        await message.answer(formatted_text, parse_mode="Markdown")
        logger.info("Contact information sent successfully")
    except Exception as e:
        logger.error(f"Error in cmd_contact: {str(e)}", exc_info=True)
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

@router.message(lambda message: message.text == ABOUT_BTN)
async def cmd_about(message: Message):
    """Handle /about command or About button"""
    try:
        logger.info(f"About information requested by user: {message.from_user.id}")
        about_text = db.get_static_content('about')
        if not about_text:
            await message.answer("⚠️ اطلاعات درباره ما در حال حاضر در دسترس نیست. لطفا بعدا تلاش کنید.")
            logger.warning("About information not found in database")
            return

        formatted_text = f"ℹ️ *درباره ما*\n\n{about_text}"
        await message.answer(formatted_text, parse_mode="Markdown")
        logger.info("About information sent successfully")
    except Exception as e:
        logger.error(f"Error in cmd_about: {str(e)}", exc_info=True)
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

@router.message(lambda message: message.text == SEARCH_BTN)
async def cmd_search(message: Message, state: FSMContext):
    """Handle Search button"""
    try:
        logger.info(f"Search requested by user: {message.from_user.id}")
        search_text = (
            "🔍 *جستجو در محتوا*\n\n"
            "برای جستجو در تمام محصولات، خدمات و محتوای آموزشی، "
            "کلمه کلیدی خود را تایپ کنید:\n\n"
            "• حداقل ۳ حرف وارد کنید\n"
            "• می‌توانید به فارسی یا انگلیسی جستجو کنید\n"
            "• جستجو در نام، توضیحات، برندها و دسته‌بندی‌ها انجام می‌شود"
        )
        await message.answer(search_text, parse_mode="Markdown")
        await state.set_state(UserStates.waiting_for_search)
        logger.info(f"User {message.from_user.id} entered search state")
    except Exception as e:
        logger.error(f"Error in cmd_search: {str(e)}", exc_info=True)
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

@router.message(UserStates.waiting_for_search)
async def handle_search_input(message: Message, state: FSMContext):
    """Handle search input from user"""
    try:
        search_query = message.text.strip()
        logger.info(f"Search query received from user {message.from_user.id}: {search_query}")

        if len(search_query) < 3:
            await message.answer("⚠️ لطفا حداقل ۳ حرف وارد کنید.")
            return

        search_results = db.unified_search(search_query)
        total_results = (
            len(search_results['products']) +
            len(search_results['services']) +
            len(search_results['educational'])
        )

        if total_results == 0:
            await message.answer(
                f"🔍 نتایج جستجو برای: *{search_query}*\n\n"
                "❌ هیچ نتیجه‌ای یافت نشد.\n\n"
                "💡 پیشنهاد: کلمات کلیدی دیگری امتحان کنید یا از واژه‌های کلی‌تر استفاده کنید.",
                parse_mode="Markdown"
            )
            await state.clear()
            return

        response_text = f"🔍 نتایج جستجو برای: *{search_query}*\n\n"
        response_text += f"📊 تعداد کل نتایج: {total_results}\n\n"

        from handlers_utils import format_price

        if search_results['products']:
            response_text += f"🛍️ *محصولات ({len(search_results['products'])})*\n"
            for product in search_results['products'][:5]:
                price_text = format_price(product['price']) if product['price'] else "قیمت نامشخص"
                stock_text = "✅ موجود" if product.get('in_stock') else "❌ ناموجود"
                featured_text = "⭐" if product.get('featured') else ""
                response_text += (
                    f"• {featured_text}{product['name']}\n"
                    f"  💰 {price_text} | {stock_text}\n"
                    f"  📁 {product.get('category_name', 'بدون دسته‌بندی')}\n\n"
                )

        if search_results['services']:
            response_text += f"🔧 *خدمات ({len(search_results['services'])})*\n"
            for service in search_results['services'][:5]:
                price_text = format_price(service['price']) if service['price'] else "قیمت نامشخص"
                featured_text = "⭐" if service.get('featured') else ""
                response_text += (
                    f"• {featured_text}{service['name']}\n"
                    f"  💰 {price_text}\n"
                    f"  📁 {service.get('category_name', 'بدون دسته‌بندی')}\n\n"
                )

        if search_results['educational']:
            response_text += f"📚 *محتوای آموزشی ({len(search_results['educational'])})*\n"
            for edu in search_results['educational'][:5]:
                response_text += (
                    f"• {edu['title']}\n"
                    f"  📁 {edu.get('category_name', 'بدون دسته‌بندی')}\n\n"
                )

        response_text += "💡 برای مشاهده جزئیات بیشتر، از منوی اصلی به بخش مربوطه مراجعه کنید."
        await message.answer(response_text, parse_mode="Markdown")
        await state.clear()
        logger.info(f"Search results sent to user {message.from_user.id}: {total_results} total results")
    except Exception as e:
        logger.error(f"Error in handle_search_input: {str(e)}", exc_info=True)
        await message.answer("⚠️ متأسفانه در جستجو خطایی رخ داد.")
        await state.clear()

@router.callback_query(lambda c: c.data == "back_to_main")
async def callback_back_to_main(callback: CallbackQuery, state: FSMContext):
    """Handle back to main menu button"""
    try:
        await state.clear()
        from keyboards import main_menu_keyboard
        keyboard = main_menu_keyboard()
        await callback.message.answer("به منوی اصلی بازگشتید:", reply_markup=keyboard)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_back_to_main: {str(e)}", exc_info=True)
        await callback.message.answer("⚠️ خطایی رخ داد. لطفا دوباره تلاش کنید.")
        await callback.answer()

@router.callback_query()
async def handle_unknown_callback(callback: CallbackQuery):
    """Handle unknown callback queries"""
    logger.debug(f"Unknown callback: update_id={callback.id}, user_id={callback.from_user.id}, data={callback.data}")
    from keyboards import main_menu_keyboard
    await callback.message.answer("این عملیات پشتیبانی نمی‌شود!", reply_markup=main_menu_keyboard())
    await callback.answer()