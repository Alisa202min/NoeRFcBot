from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from configuration import INQUIRY_BTN, ADMIN_ID
from logging_config import get_logger
from extensions import database
from bot import bot
from datetime import datetime
from callback_formatter import callback_formatter
import UserStates
import traceback

logger = get_logger('bot')
router = Router(name="inquiry_router")
db = database

@router.callback_query()
async def debug_all_callbacks(callback: CallbackQuery):
    """Debug handler to log all callbacks"""
    logger.debug(f"Debug: Received callback data: {callback.data}")
    await callback.answer()
    # Do not process further to allow other handlers to handle the callback

@router.message(lambda message: message.text == INQUIRY_BTN)
async def cmd_inquiry(message: Message, state: FSMContext):
    """Handle Inquiry button"""
    try:
        logger.info(f"Inquiry process started by user: {message.from_user.id}")
        inquiry_text = (
            "📝 *استعلام قیمت*\n\n"
            "برای ارسال استعلام قیمت، لطفا اطلاعات زیر را به ترتیب وارد کنید:\n"
            "1️⃣ نام و نام خانوادگی\n"
            "2️⃣ شماره تماس\n"
            "3️⃣ شرح محصول یا خدمات درخواستی\n\n"
            "لطفا نام و نام خانوادگی خود را وارد کنید:"
        )
        await message.answer(inquiry_text, parse_mode="Markdown")
        await state.set_state(UserStates.UserStates.inquiry_name)
        logger.info(f"User {message.from_user.id} entered inquiry name state")
    except Exception as e:
        logger.error(f"Error in cmd_inquiry: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد.")

@router.callback_query(lambda c: callback_formatter.read(c.data)[0] == 'inquiry' if callback_formatter.read(c.data) else False)
async def callback_inquiry(callback: CallbackQuery, state: FSMContext):
    """Handle inquiry initiation"""
    await callback.answer()
    logger.debug(f"Inquiry callback received: {callback.data}")
    try:
        callback_result = callback_formatter.read(callback.data)
        if not callback_result:
            logger.error(f"Callback formatter failed to parse inquiry data: {callback.data}")
            await callback.message.answer("⚠️ داده callback نامعتبر است.")
            return

        callback_type, params = callback_result
        logger.debug(f"Parsed inquiry callback: type={callback_type}, params={params}")
        if callback_type != 'inquiry':
            logger.error(f"Unexpected callback type: {callback_type} for data: {callback.data}")
            await callback.message.answer("⚠️ نوع callback نامعتبر است.")
            return

        item_type = params.get('inquiry_type')
        item_id = params.get('item_id')
        if not item_type or not isinstance(item_id, int):
            logger.error(f"Invalid inquiry params: inquiry_type={item_type}, item_id={item_id}, data: {callback.data}")
            await callback.message.answer("⚠️ پارامترهای استعلام نامعتبر هستند.")
            return

        if item_type == 'product':
            await state.update_data(product_id=item_id, service_id=None)
            product = db.get_product(item_id)
            if product and 'name' in product:
                await callback.message.answer(f"شما در حال استعلام قیمت برای محصول «{product['name']}» هستید.")
            else:
                logger.warning(f"No product found for ID: {item_id}")
                await callback.message.answer("شما در حال استعلام قیمت برای یک محصول هستید.")
        else:
            await state.update_data(service_id=item_id, product_id=None)
            service = db.get_service(item_id)
            if service and 'name' in service:
                await callback.message.answer(f"شما در حال استعلام قیمت برای خدمت «{service['name']}» هستید.")
            else:
                logger.warning(f"No service found for ID: {item_id}")
                await callback.message.answer("شما در حال استعلام قیمت برای یک خدمت هستید.")

        await callback.message.answer("لطفاً نام خود را وارد کنید:")
        await state.set_state(UserStates.UserStates.inquiry_name)
        logger.info(f"State set to inquiry_name for user {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Error in inquiry callback: {e}\n{traceback.format_exc()}")
        await callback.message.answer("خطایی در شروع فرآیند استعلام قیمت رخ داد.")

@router.message(UserStates.UserStates.inquiry_name)
async def process_inquiry_name(message: Message, state: FSMContext):
    """Process name input for inquiry"""
    try:
        await state.update_data(name=message.text)
        await message.answer("لطفاً شماره تماس خود را وارد کنید:")
        await state.set_state(UserStates.UserStates.inquiry_phone)
        logger.info(f"User {message.from_user.id} entered inquiry phone state")
    except Exception as e:
        logger.error(f"Error in process_inquiry_name: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ خطا در ثبت نام. لطفاً دوباره تلاش کنید.")

@router.message(UserStates.UserStates.inquiry_phone)
async def process_inquiry_phone(message: Message, state: FSMContext):
    """Process phone input for inquiry"""
    try:
        phone = message.text.strip()
        if not phone.isdigit() or len(phone) < 10:
            await message.answer("لطفاً یک شماره تماس معتبر وارد کنید:")
            return
        await state.update_data(phone=phone)
        await message.answer("لطفاً توضیحات درخواست خود را وارد کنید:")
        await state.set_state(UserStates.UserStates.inquiry_description)
        logger.info(f"User {message.from_user.id} entered inquiry description state")
    except Exception as e:
        logger.error(f"Error in process_inquiry_phone: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ خطا در ثبت شماره تماس. لطفاً دوباره تلاش کنید.")

@router.message(UserStates.UserStates.inquiry_description)
async def process_inquiry_description(message: Message, state: FSMContext):
    """Process description input for inquiry"""
    try:
        await state.update_data(description=message.text)
        inquiry_data = await state.get_data()
        confirmation = (
            "📋 لطفاً اطلاعات درخواست خود را تأیید کنید:\n\n"
            f"👤 نام: {inquiry_data.get('name', 'نامشخص')}\n"
            f"📞 شماره تماس: {inquiry_data.get('phone', 'نامشخص')}\n"
            f"📝 توضیحات: {inquiry_data.get('description', 'بدون توضیحات')}\n\n"
        )
        product_id = inquiry_data.get('product_id')
        service_id = inquiry_data.get('service_id')
        if product_id:
            product = db.get_product(product_id)
            confirmation += f"🛒 محصول: {product['name'] if product and 'name' in product else 'نامشخص'}\n"
        elif service_id:
            service = db.get_service(service_id)
            confirmation += f"🛠️ خدمت: {service['name'] if service and 'name' in service else 'نامشخص'}\n"

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ تأیید", callback_data="confirm_inquiry")
        kb.button(text="❌ انصراف", callback_data="cancel_inquiry")
        kb.adjust(2)
        await message.answer(confirmation, reply_markup=kb.as_markup())
        await state.set_state(UserStates.UserStates.waiting_for_confirmation)
        logger.info(f"User {message.from_user.id} entered inquiry confirmation state")
    except Exception as e:
        logger.error(f"Error formatting inquiry confirmation: {e}\n{traceback.format_exc()}")
        await message.answer("📋 خطا در نمایش اطلاعات درخواست.")

@router.callback_query(lambda c: callback_formatter.read(c.data)[0] == 'confirm_inquiry' if callback_formatter.read(c.data) else False, UserStates.UserStates.waiting_for_confirmation)
async def callback_confirm_inquiry(callback: CallbackQuery, state: FSMContext):
    """Handle inquiry confirmation"""
    await callback.answer()
    logger.debug(f"Confirm inquiry callback received: {callback.data}")
    inquiry_data = await state.get_data()
    try:
        user_id = int(callback.from_user.id)
        name = inquiry_data.get('name', 'نامشخص')
        phone = inquiry_data.get('phone', 'نامشخص')
        description = inquiry_data.get('description', 'بدون توضیحات')
        product_id = inquiry_data.get('product_id')
        service_id = inquiry_data.get('service_id')

        db.add_inquiry(user_id, name, phone, description, product_id, service_id)
        await callback.message.answer(
            "✅ درخواست شما با موفقیت ثبت شد.\nکارشناسان ما در اسرع وقت با شما تماس خواهند گرفت."
        )
        logger.info(f"Inquiry successfully added for user: {user_id}")

        if ADMIN_ID:
            notification = (
                "🔔 استعلام قیمت جدید:\n\n"
                f"👤 نام: {name}\n"
                f"📞 شماره تماس: {phone}\n"
                f"📝 توضیحات: {description}\n\n"
            )
            if product_id:
                product = db.get_product(product_id)
                notification += f"🛒 محصول: {product['name'] if product else 'نامشخص'}\n"
            elif service_id:
                service = db.get_service(service_id)
                notification += f"🛠️ خدمت: {service['name'] if service else 'نامشخص'}\n"
            notification += f"\n📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            await callback.bot.send_message(chat_id=ADMIN_ID, text=notification)

        await state.clear()
        from aiogram.utils.keyboard import InlineKeyboardBuilder
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
        logger.error(f"Error processing inquiry: {e}\n{traceback.format_exc()}")
        await callback.message.answer("❌ خطا در ثبت درخواست.")

@router.callback_query(lambda c: callback_formatter.read(c.data)[0] == 'cancel_inquiry' if callback_formatter.read(c.data) else False)
async def callback_cancel_inquiry(callback: CallbackQuery, state: FSMContext):
    """Handle inquiry cancellation"""
    await callback.answer()
    logger.debug(f"Cancel inquiry callback received: {callback.data}")
    try:
        await state.clear()
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        kb = InlineKeyboardBuilder()
        kb.button(text="🛒 محصولات", callback_data="products")
        kb.button(text="🛠️ خدمات", callback_data="services")
        kb.button(text="📚 محتوای آموزشی", callback_data="educational")
        kb.button(text="📞 تماس با ما", callback_data="contact")
        kb.button(text="ℹ️ درباره ما", callback_data="about")
        kb.adjust(2, 2, 1)
        await callback.message.answer("درخواست استعلام قیمت لغو شد.", 
                                   reply_markup=kb.as_markup())
        logger.info(f"Inquiry cancelled for user: {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Error in cancel_inquiry: {e}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطا در لغو درخواست.")