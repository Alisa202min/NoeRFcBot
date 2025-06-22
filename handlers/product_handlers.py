from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from configuration import PRODUCTS_BTN
from logging_config import get_logger
from extensions import database
from bot import bot
from utils.media_utils import send_product_media_group_to_user
from keyboards import product_categories_keyboard, product_content_keyboard, product_detail_keyboard, main_menu_keyboard
from aiogram.filters import Command
import traceback
from handlers.handlers_utils import format_price
from callback_formatter import callback_formatter

logger = get_logger('bot')
router = Router(name="products_router")
db = database

# Debug log to confirm router initialization
logger.info(f"Product handlers router initialized with {len(router.callback_query.handlers)} callback handlers")

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
        logger.info(f"Product categories sent: {len(categories)} categories to user: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in cmd_products: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

@router.callback_query(F.data == callback_formatter.write('products'))
async def callback_products(callback: CallbackQuery):
    """Handle products button click"""
    await callback.answer()
    try:
        categories = db.get_product_categories()
        if not categories:
            await callback.message.answer("در حال حاضر دسته‌بندی محصولات موجود نیست.")
            logger.warning("No product categories found")
            return

        for category in categories:
            category_id = category['id']
            subcategory_count = int(category.get('subcategory_count', 0))
            product_count = int(category.get('product_count', 0))
            category['content_count'] = subcategory_count + product_count

        keyboard = product_categories_keyboard(categories)
        await callback.message.answer("🛍️ دسته‌بندی محصولات را انتخاب کنید:",
                                     reply_markup=keyboard)
        logger.info(f"Product categories sent to user: {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Error in callback_products: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش دسته‌بندی محصولات رخ داد.")

@router.callback_query(lambda c: callback_formatter.read(c.data)[0] == 'product_category' if callback_formatter.read(c.data) else False)
async def callback_product_category(callback: CallbackQuery):
    """Handle product category selection"""
    await callback.answer()
    try:
        result = callback_formatter.read(callback.data)
        if not result or result[0] != 'product_category':
            logger.error(f"Invalid callback data: {callback.data}")
            await callback.message.answer("⚠️ داده نامعتبر است.")
            return

        _, params = result
        category_id = params['category_id']
        logger.info(f"Selected product category ID: {category_id} by user: {callback.from_user.id}")
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
        logger.info(f"Products sent for category ID: {category_id} to user: {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Error in callback_product_category: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش محصولات رخ داد.")

@router.callback_query(F.data == callback_formatter.write('products'))
async def callback_product_categories(callback: CallbackQuery):
    """Handle going back to product categories"""
    await callback.answer()
    try:
        categories = db.get_product_categories()
        if not categories:
            await callback.message.answer("در حال حاضر دسته‌بندی محصولات موجود نیست.")
            logger.warning("No product categories found")
            return

        keyboard = product_categories_keyboard(categories)
        await callback.message.answer("🛍️ دسته‌بندی محصولات را انتخاب کنید:",
                                     reply_markup=keyboard)
        logger.info(f"Product categories sent to user: {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Error in callback_product_categories: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش دسته‌بندی‌ها رخ داد.")

@router.callback_query(lambda c: callback_formatter.read(c.data)[0] == 'product_item' if callback_formatter.read(c.data) else False)
async def callback_product(callback: CallbackQuery):
    """Handle product selection"""
    await callback.answer()
    try:
        result = callback_formatter.read(callback.data)
        if not result or result[0] != 'product_item':
            logger.error(f"Invalid callback data: {callback.data}")
            await callback.message.answer("⚠️ داده نامعتبر است.")
            return

        _, params = result
        product_id = params['product_id']
        logger.info(f"Selected product ID: {product_id} by user: {callback.from_user.id}")
        product = db.get_product(product_id)
        if not product:
            logger.error(f"Product not found for ID: {product_id}")
            await callback.message.answer("⚠️ محصول مورد نظر یافت نشد.")
            return

        # Build detailed caption with all relevant fields
        additional_info = []
        if product.get('name'):
            additional_info.append(f"🛍️ *{product['name']}*")
        if product.get('price'):
            additional_info.append(f"💰 قیمت: {format_price(product['price'])}")
        if product.get('description'):
            additional_info.append(f"📝 توضیحات: {product['description']}")
        if product.get('brand'):
            additional_info.append(f"🏢 برند: {product['brand']}")
        if product.get('model'):
            additional_info.append(f"📱 مدل: {product['model']}")
        if product.get('model_number'):
            additional_info.append(f"📋 شماره مدل: {product['model_number']}")
        if product.get('manufacturer'):
            additional_info.append(f"🏭 سازنده: {product['manufacturer']}")
        if product.get('tags'):
            additional_info.append(f"🏷️ برچسب‌ها: {product['tags']}")
        if product.get('in_stock'):
            additional_info.append("✅ موجود در انبار")
        if product.get('featured'):
            additional_info.append("⭐ محصول ویژه")

        text = "\n\n".join(additional_info) if additional_info else "ℹ️ اطلاعات محصول در دسترس نیست."
        keyboard = product_detail_keyboard(product_id, product.get('category_id'))
        chat_id = callback.message.chat.id

        media = db.get_product_media(product_id)
        logger.debug(f"Raw media from db.get_product_media for product {product_id}: {media}")

        # Validate inputs
        if not isinstance(bot, Bot):
            logger.error(f"bot must be a Bot instance, got: {type(bot)}")
            await callback.message.answer("⚠️ خطای داخلی سرور. لطفا بعداً تلاش کنید.")
            return
        if not isinstance(chat_id, int):
            logger.error(f"chat_id must be an integer, got: {type(chat_id)}")
            await callback.message.answer("⚠️ خطای داخلی سرور. لطفا بعداً تلاش کنید.")
            return
        if not media:
            logger.warning(f"No media found for product {product_id}")
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
            logger.info(f"Product {product_id} sent to chat_id {chat_id} without media")
            return
        if not isinstance(media, list):
            logger.error(f"media must be a list, got: {type(media)}")
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
            logger.info(f"Product {product_id} sent to chat_id {chat_id} without media")
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
        logger.debug(f"Initial media_items for product {product_id}: {media_items}")

        # Filter out incomplete media items
        media_items = [item for item in media_items if item['id'] and item['file_type'] and (item['file_id'] or item['local_path'])]
        logger.debug(f"Filtered media_items for product {product_id}: {media_items}")

        if not media_items:
            logger.warning(f"No valid media_items for product {product_id}")
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
            logger.info(f"Product {product_id} sent to chat_id {chat_id} without media")
            return

        # Send media group
        logger.debug(f"Calling send_product_media_group_to_user with bot: {type(bot)}, chat_id: {chat_id}, media_items: {media_items}, caption: {text}")
        await send_product_media_group_to_user(
            bot=bot,
            chat_id=chat_id,
            media_items=media_items,
            caption=text,
            reply_markup=keyboard
        )
        logger.info(f"Product {product_id} sent to chat_id {chat_id} with media and keyboard")
    except Exception as e:
        logger.error(f"Error in callback_product: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش محصول رخ داد.")

@router.callback_query(lambda c: callback_formatter.read(c.data)[0] == 'inquiry' if callback_formatter.read(c.data) else False)
async def callback_inquiry(callback: CallbackQuery):
    """Handle price inquiry button click"""
    await callback.answer()
    try:
        logger.debug(f"Processing inquiry callback: {callback.data}")
        result = callback_formatter.read(callback.data)
        if not result or result[0] != 'inquiry':
            logger.error(f"Invalid inquiry callback data: {callback.data}")
            await callback.message.answer("⚠️ داده نامعتبر است.")
            return

        _, params = result
        inquiry_type = params['inquiry_type']
        item_id = params['item_id']
        logger.info(f"Inquiry requested for {inquiry_type} ID: {item_id} by user: {callback.from_user.id}")

        if inquiry_type == 'product':
            product = db.get_product(item_id)
            if not product:
                logger.error(f"Product not found for ID: {item_id}")
                await callback.message.answer("⚠️ محصول مورد نظر یافت نشد.")
                return
            await callback.message.answer(
                f"📝 درخواست استعلام قیمت برای محصول '{product['name']}' ثبت شد. به زودی با شما تماس خواهیم گرفت.",
                parse_mode="Markdown"
            )
            logger.info(f"Price inquiry for product ID: {item_id} sent to user: {callback.from_user.id}")
        else:
            logger.warning(f"Unsupported inquiry type: {inquiry_type}")
            await callback.message.answer("⚠️ نوع استعلام پشتیبانی نمی‌شود.")
    except Exception as e:
        logger.error(f"Error in callback_inquiry: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در پردازش استعلام رخ داد.")

@router.callback_query(lambda c: callback_formatter.read(c.data)[0] == 'back_to_main' if callback_formatter.read(c.data) else False)
async def callback_back_to_main(callback: CallbackQuery):
    """Handle return to main menu button click"""
    await callback.answer()
    try:
        logger.debug(f"Processing back_to_main callback: {callback.data}")
        logger.info(f"Return to main menu requested by user: {callback.from_user.id}")
        keyboard = main_menu_keyboard()
        await callback.message.answer(
            "🏠 به منوی اصلی خوش آمدید!\nلطفا یک گزینه را انتخاب کنید:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Main menu sent to user: {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Error in callback_back_to_main: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در بازگشت به منوی اصلی رخ داد.")