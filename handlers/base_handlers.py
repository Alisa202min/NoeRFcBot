import traceback
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from logging_config import get_logger

from keyboards import main_menu_keyboard
from extensions import database
from configuration import CONTACT_BTN, ABOUT_BTN

logger = get_logger('bot')
router = Router(name="base_router")
db = database

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command - initial entry point"""
    try:
        logger.info(f"Start command received from user: {message.from_user.id}")
        await state.clear()
        welcome_text = (
            f"🎉 سلام {message.from_user.first_name}!\n\n"
            "به ربات فروشگاه محصولات و خدمات ارتباطی خوش آمدید.\n"
            "از منوی زیر گزینه مورد نظر خود را انتخاب کنید:"
        )
        keyboard = main_menu_keyboard()
        logger.info("Sending welcome message with keyboard buttons")
        await message.answer(welcome_text, reply_markup=keyboard)
        logger.info("Start command response sent successfully")
    except Exception as e:
        logger.error(f"Error in start command handler: {e}\n{traceback.format_exc()}")
        await message.answer("متأسفانه خطایی رخ داد. لطفاً مجدداً تلاش کنید.")

@router.message(Command("help"))
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
    await message.answer(help_text, reply_markup=main_menu_keyboard())

@router.message(lambda message: message.text == CONTACT_BTN)
@router.callback_query(F.data == "contact")
async def cmd_contact(message_or_callback: Message | CallbackQuery):
    """Handle /contact command or Contact button"""
    try:
        logger.info(f"Contact information requested by user: {message_or_callback.from_user.id}")
        contact_text = db.get_static_content('contact')
        if not contact_text:
            response = "⚠️ اطلاعات تماس در حال حاضر در دسترس نیست. لطفا بعدا تلاش کنید."
            logger.warning("Contact information not found in database")
        else:
            response = f"📞 *اطلاعات تماس*\n\n{contact_text}"
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.answer(response, parse_mode="Markdown")
            await message_or_callback.answer()
        else:
            await message_or_callback.answer(response, parse_mode="Markdown")
        logger.info("Contact information sent successfully")
    except Exception as e:
        logger.error(f"Error in cmd_contact: {str(e)}\n{traceback.format_exc()}")
        response = "⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید."
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.answer(response)
            await message_or_callback.answer()
        else:
            await message_or_callback.answer(response)

@router.message(lambda message: message.text == ABOUT_BTN)
@router.callback_query(F.data == "about")
async def cmd_about(message_or_callback: Message | CallbackQuery):
    """Handle /about command or About button"""
    try:
        logger.info(f"About information requested by user: {message_or_callback.from_user.id}")
        about_text = db.get_static_content('about')
        if not about_text:
            response = "⚠️ اطلاعات درباره ما در حال حاضر در دسترس نیست. لطفا بعدا تلاش کنید."
            logger.warning("About information not found in database")
        else:
            response = f"ℹ️ *درباره ما*\n\n{about_text}"
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.answer(response, parse_mode="Markdown")
            await message_or_callback.answer()
        else:
            await message_or_callback.answer(response, parse_mode="Markdown")
        logger.info("About information sent successfully")
    except Exception as e:
        logger.error(f"Error in cmd_about: {str(e)}\n{traceback.format_exc()}")
        response = "⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید."
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.answer(response)
            await message_or_callback.answer()
        else:
            await message_or_callback.answer(response)

@router.callback_query()
async def handle_unknown_callback(callback: CallbackQuery):
    """Handle unknown callback queries"""
    logger.debug(
        f"Unknown callback: update_id={callback.id}, "
        f"user_id={callback.from_user.id}, data={callback.data}"
    )
    await callback.message.answer("این عملیات پشتیبانی نمی‌شود!", reply_markup=main_menu_keyboard())
    await callback.answer()