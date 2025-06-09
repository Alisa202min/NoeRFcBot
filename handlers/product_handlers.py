from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from configuration import PRODUCTS_BTN, PRODUCT_PREFIX
from logging_config import get_logger
from extensions import database
from bot import bot
from utils.media_utils import send_product_media_group_to_user
from keyboards import product_categories_keyboard, product_content_keyboard, product_detail_keyboard
from aiogram.filters import Command
import traceback
from handlers.handlers_utils import format_price

logger = get_logger('bot')
router = Router(name="products_router")
db = database

@router.message(lambda message: message.text == PRODUCTS_BTN)
@router.message(Command("products"))
async def cmd_products(message: Message, state: FSMContext):
    """Handle /products command or Products button"""
    try:
        logger.info(f"Products requested by user: {message.from_user.id}")
        categories = db.get_product_categories()
        if not categories:
            await message.answer("⚠️ دسته‌بندی محصولات در حال حاضر در دسترس نیست. لطفا بعدا تلاش کنید.")
            logger.warning("No product categories found in database")
            return

        keyboard = product_categories_keyboard(categories)
        await message.answer(
            "🛍️ *دسته‌بندی محصولات*\n\nلطفا یکی از دسته‌بندی‌های زیر را انتخاب کنید:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Product categories sent: {len(categories)} categories")
    except Exception as e:
        logger.error(f"Error in cmd_products: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

@router.callback_query(F.data == "products")
async def callback_products(callback: CallbackQuery):
    """Handle products button click"""
    await callback.answer()
    try:
        categories = db.get_product_categories()
        if not categories:
            await callback.message.answer("در حال حاضر دسته‌بندی محصولات موجود نیست.")
            return

        for category in categories:
            category_id = category['id']
            subcategory_count = int(category.get('subcategory_count', 0))
            product_count = int(category.get('product_count', 0))
            category['content_count'] = subcategory_count + product_count

        keyboard = product_categories_keyboard(categories)
        await callback.message.answer("🛍️ دسته‌بندی محصولات را انتخاب کنید:",
                                   reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in callback_products: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش دسته‌بندی محصولات رخ داد.")

@router.callback_query(F.data.startswith(f"{PRODUCT_PREFIX}cat_"))
async def callback_product_category(callback: CallbackQuery):
    """Handle product category selection"""
    await callback.answer()
    try:
        category_id = int(callback.data.replace(f"{PRODUCT_PREFIX}cat_", ""))
        logger.info(f"Selected product category ID: {category_id}")
        category_info = db.get_product_category(category_id)
        if not category_info:
            logger.error(f"Product category not found for ID: {category_id}")
            await callback.message.answer("⚠️ دسته‌بندی مورد نظر یافت نشد.")
            return

        products = db.get_products(category_id=category_id)
        if not products:
            logger.warning(f"No products found for category ID: {category_id}")
            await callback.message.answer(f"⚠️ محصولی برای دسته‌بندی '{category_info['name']}' موجود نیست.")
            return

        keyboard = product_content_keyboard(products, category_id)
        await callback.message.answer(f"🛍️ محصولات در دسته‌بندی '{category_info['name']}':",
                                   reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in callback_product_category: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش محصولات رخ داد.")

@router.callback_query(F.data == f"{PRODUCT_PREFIX}categories")
async def callback_product_categories(callback: CallbackQuery):
    """Handle going back to product categories"""
    await callback.answer()
    try:
        categories = db.get_product_categories()
        if not categories:
            await callback.message.answer("در حال حاضر دسته‌بندی محصولات موجود نیست.")
            return

        keyboard = product_categories_keyboard(categories)
        await callback.message.answer("🛍️ دسته‌بندی محصولات را انتخاب کنید:",
                                   reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in callback_product_categories: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش دسته‌بندی‌ها رخ داد.")

@router.callback_query(F.data.startswith(f"{PRODUCT_PREFIX}:"))
async def callback_product(callback: CallbackQuery, state: FSMContext):
    """Handle product selection"""
    await callback.answer()
    try:
        product_id = int(callback.data.replace(f"{PRODUCT_PREFIX}:", ""))
        logger.info(f"Selected product ID: {product_id}")
        product = db.get_product(product_id)
        if not product:
            logger.error(f"Product not found for ID: {product_id}")
            await callback.message.answer("⚠️ محصول مورد نظر یافت نشد.")
            return

        category_id = product.get('category_id', 0)
        keyboard = product_detail_keyboard(product_id, category_id)
        product_text = (
            f"📦 *{product['name']}*\n\n"
            f"💰 قیمت: {format_price(product['price'])}\n\n"
            f"📝 توضیحات:\n{product['description'] or 'بدون توضیحات'}\n"
        )
        if product.get('brand'):
            product_text += f"🏭 برند: {product['brand']}\n"
        if product.get('model'):
            product_text += f"📱 مدل: {product['model']}\n"
        if product.get('model_number'):
            product_text += f"📋 شماره مدل: {product['model_number']}\n"
        if product.get('manufacturer'):
            product_text += f"🏭 سازنده: {product['manufacturer']}\n"
        if product.get('tags'):
            product_text += f"🏷️ برچسب‌ها: {product['tags']}\n"
        if product.get('in_stock'):
            product_text += "✅ موجود در انبار\n"
        else:
            product_text += "❌ ناموجود\n"
        if product.get('featured'):
            product_text += "⭐️ محصول ویژه\n"

        media_items = db.get_product_media(product_id)
        await send_product_media_group_to_user(
            bot=bot,
            chat_id=callback.message.chat.id,
            media_items=media_items,
            caption=product_text,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in callback_product: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش محصول رخ داد.")

