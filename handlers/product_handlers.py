from aiogram import Router, F, bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from configuration import PRODUCTS_BTN
from logging_config import get_logger
from extensions import database
from bot import bot
from utils.media_utils import send_product_media_group_to_user
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = get_logger('bot')
router = Router(name="products_router")
db = database

async def show_product_categories(message: Message | CallbackQuery, state: FSMContext, parent_id=None):
    """Show product categories"""
    try:
        await state.update_data(cat_type='product')
        logger.info(f"show_product_categories called with parent_id={parent_id}")
        categories = db.get_product_categories(parent_id=parent_id)

        if not categories:
            if parent_id:
                products = db.get_products(parent_id)
                if products:
                    await show_products_list(message, products, parent_id)
                else:
                    await message.answer("محصولی در این دسته‌بندی وجود ندارد.")
            else:
                await message.answer("دسته‌بندی محصولات موجود نیست.")
            return

        kb = InlineKeyboardBuilder()
        for category in categories:
            subcategory_count = category.get('subcategory_count', 0)
            product_count = category.get('product_count', 0)
            total_items = subcategory_count + product_count
            display_name = f"{category['name']} ({total_items})" if total_items > 0 else category['name']
            kb.button(text=display_name, callback_data=f"category:{category['id']}")

        if parent_id:
            parent_category = db.get_product_category(parent_id)
            if parent_category and parent_category.get('parent_id'):
                kb.button(text="🔙 بازگشت", callback_data=f"category:{parent_category['parent_id']}")
            else:
                kb.button(text="🔙 بازگشت به دسته‌بندی‌های اصلی", callback_data="products")
        else:
            kb.button(text="🔙 بازگشت به منوی اصلی", callback_data="back_to_main")
        kb.adjust(1)

        if isinstance(message, CallbackQuery):
            await message.message.answer("دسته‌بندی محصولات را انتخاب کنید:", reply_markup=kb.as_markup())
            await message.answer()
        else:
            await message.answer("دسته‌بندی محصولات را انتخاب کنید:", reply_markup=kb.as_markup())
        await state.set_state(UserStates.browse_categories)
    except Exception as e:
        logger.error(f"Error in show_product_categories: {str(e)}")
        await message.answer("⚠️ خطایی در نمایش دسته‌بندی‌های محصولات رخ داد.")

async def show_products_list(message: Message | CallbackQuery, products, parent_id):
    """Show list of products in a category"""
    kb = InlineKeyboardBuilder()
    for product in products:
        kb.button(text=product['name'], callback_data=f"product:{product['id']}")
    kb.button(text="🔙 بازگشت", callback_data=f"category:{parent_id}")
    kb.adjust(1)
    if isinstance(message, CallbackQuery):
        await message.message.answer("محصولات این دسته‌بندی:", reply_markup=kb.as_markup())
        await message.answer()
    else:
        await message.answer("محصولات این دسته‌بندی:", reply_markup=kb.as_markup())

@router.message(lambda message: message.text == PRODUCTS_BTN)
@router.message(Command("products"))
async def cmd_products(message: Message, state: FSMContext):
    """Handle /products command or Products button"""
    try:
        logger.info(f"Products requested by user: {message.from_user.id}")
        await state.update_data(cat_type='product')
        await show_product_categories(message, state)
    except Exception as e:
        logger.error(f"Error in cmd_products: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

@router.callback_query(F.data == "products")
async def callback_products(callback: CallbackQuery, state: FSMContext):
    """Handle products button click"""
    logger.debug(f"callback_products called with data: {callback.data}")
    await show_product_categories(callback, state)

@router.callback_query(F.data.startswith("category:"))
async def callback_category(callback: CallbackQuery, state: FSMContext):
    """Handle category selection for products"""
    try:
        category_id = int(callback.data.split(':')[1])
        logger.info(f"Category selected: {category_id}")
        user_data = await state.get_data()
        cat_type = user_data.get('cat_type', 'product')

        if cat_type == 'product':
            await show_product_categories(callback, state, parent_id=category_id)
        else:
            from .services import show_service_categories
            await show_service_categories(callback, state, parent_id=category_id)
    except Exception as e:
        logger.error(f"Error in callback_category: {str(e)}")
        await callback.message.answer("⚠️ خطایی در نمایش دسته‌بندی رخ داد.")
        await callback.answer()

@router.callback_query(F.data.startswith("product:"))
async def callback_product(callback: CallbackQuery, state: FSMContext):
    """Handle product selection"""
    try:
        product_id = int(callback.data.split(':')[1])
        logger.info(f"Extracted product_id: {product_id}")

        product = db.get_product(product_id)
        if not product:
            logger.warning(f"Product not found for id: {product_id}")
            await callback.message.answer('متأسفیم، این محصول یافت نشد.')
            await callback.answer()
            return

        await state.update_data(product_id=product_id)
        await state.set_state(UserStates.view_product)

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
            product_text += '⭐️ محصول ویژه\n"

        kb = InlineKeyboardBuilder()
        kb.button(text="🛍️ استعلام قیمت", callback_data=f"inquiry:product:{product_id}")
        kb.button(text="🔙 بازگشت", callback_data=f"category:{product['category_id']}")
        kb.button(text="🏖️ منوی اصلی", callback_data="back_to_main")
        kb.adjust(1)

        media_items = db.get_product_media(product_id)
        await send_product_media_group_to_user(
            bot=bot,
            chat_id=callback.message.chat.id,
            media_items=media_items,
            caption=product_text,
            reply_markup=kb.as_markup()
        )

        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_product: {str(e)}", exc_info=True)
        await callback.message.answer("خطایی رخداد. لطفاً دوباره تلاش کنید.")
        await callback.answer()