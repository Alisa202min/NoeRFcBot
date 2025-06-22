
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from configuration import EDUCATION_BTN
from logging_config import get_logger
from extensions import database
from bot import bot
from utils.media_utils import send_educational_media_group_to_user
from keyboards import education_categories_keyboard, education_content_keyboard, education_detail_keyboard
from aiogram.filters import Command
from utils.utils import create_telegraph_page
import traceback
from callback_formatter import callback_formatter

logger = get_logger('bot')
router = Router(name="educational_router")
db = database

@router.message(lambda message: message.text == EDUCATION_BTN)
@router.message(Command("education"))
async def cmd_education(message: Message, state: FSMContext):
    """Handle /education command or Education button"""
    try:
        logger.info(f"Educational content requested by user: {message.from_user.id}")
        categories = db.get_educational_categories()
        if not categories:
            await message.answer("⚠️ دسته‌بندی محتوای آموزشی در حال حاضر در دسترس نیست. لطفا بعدا تلاش کنید.")
            logger.warning("No educational categories found in database")
            return

        keyboard = education_categories_keyboard(categories)
        await message.answer(
            "📚 *دسته‌بندی محتوای آموزشی*\n\nلطفا یکی از دسته‌بندی‌های زیر را انتخاب کنید:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Educational categories sent: {len(categories)} categories")
    except Exception as e:
        logger.error(f"Error in cmd_education: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

@router.callback_query(F.data == callback_formatter.write('educational'))
async def callback_educational(callback: CallbackQuery):
    """Handle educational content button click"""
    await callback.answer()
    try:
        categories = db.get_educational_categories()
        if not categories:
            await callback.message.answer("در حال حاضر دسته‌بندی محتوای آموزشی موجود نیست.")
            logger.warning("No educational categories found")
            return

        for category in categories:
            category_id = category['id']
            subcategory_count = int(category.get('subcategory_count', 0))
            content_count = int(category.get('content_count', 0))
            category['content_count'] = subcategory_count + content_count

        keyboard = education_categories_keyboard(categories)
        await callback.message.answer("📚 دسته‌بندی محتوای آموزشی را انتخاب کنید:",
                                     reply_markup=keyboard)
        logger.info(f"Educational categories sent to user: {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Error in callback_educational: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش دسته‌بندی محتوای آموزشی رخ داد.")

@router.callback_query(lambda c: callback_formatter.read(c.data)[0] == 'educational_category' if callback_formatter.read(c.data) else False)
async def callback_educational_category(callback: CallbackQuery):
    """Handle educational category selection"""
    await callback.answer()
    try:
        result = callback_formatter.read(callback.data)
        if not result or result[0] != 'educational_category':
            logger.error(f"Invalid callback data: {callback.data}")
            await callback.message.answer("⚠️ داده نامعتبر است.")
            return

        _, params = result
        category_id = params['category_id']
        logger.info(f"Selected educational category ID: {category_id} by user: {callback.from_user.id}")
        category_info = db.get_educational_category(category_id)
        if not category_info:
            logger.error(f"Educational category not found for ID: {category_id}")
            await callback.message.answer("⚠️ دسته‌بندی مورد نظر یافت نشد.")
            return

        contents = db.get_all_educational_content(category_id=category_id)
        if not contents:
            logger.warning(f"No educational content found for category ID: {category_id}")
            await callback.message.answer(f"⚠️ محتوایی برای دسته‌بندی '{category_info['name']}' موجود نیست.")
            return

        keyboard = education_content_keyboard(contents, category_id)
        await callback.message.answer(f"📚 محتوای آموزشی در دسته‌بندی '{category_info['name']}':",
                                     reply_markup=keyboard)
        logger.info(f"Educational content sent for category ID: {category_id}")
    except Exception as e:
        logger.error(f"Error in callback_educational_category: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش محتوای آموزشی رخ داد.")

@router.callback_query(F.data == callback_formatter.write('educational'))
async def callback_educational_categories(callback: CallbackQuery):
    """Handle going back to educational categories"""
    await callback.answer()
    try:
        categories = db.get_educational_categories()
        if not categories:
            await callback.message.answer("در حال حاضر دسته‌بندی محتوای آموزشی موجود نیست.")
            logger.warning("No educational categories found")
            return

        keyboard = education_categories_keyboard(categories)
        await callback.message.answer("📚 دسته‌بندی محتوای آموزشی را انتخاب کنید:",
                                     reply_markup=keyboard)
        logger.info(f"Educational categories sent to user: {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Error in callback_educational_categories: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش دسته‌بندی‌ها رخ داد.")

@router.callback_query(lambda c: callback_formatter.read(c.data)[0] == 'educational_content' if callback_formatter.read(c.data) else False)
async def callback_educational_content(callback: CallbackQuery):
    """Handle educational content selection"""
    await callback.answer()
    try:
        result = callback_formatter.read(callback.data)
        if not result or result[0] != 'educational_content':
            logger.error(f"Invalid callback data: {callback.data}")
            await callback.message.answer("⚠️ داده نامعتبر است.")
            return

        _, params = result
        content_id = params['content_id']
        logger.info(f"Selected educational content ID: {content_id} by user: {callback.from_user.id}")
        content = db.get_educational_content(content_id)
        if not content:
            logger.error(f"Educational content not found for ID: {content_id}")
            await callback.message.answer("⚠️ محتوای آموزشی مورد نظر یافت نشد.")
            return

        # Build detailed caption with relevant fields
        additional_info = []
        if content.get('title'):
            additional_info.append(f"📚 *{content['title']}*")
        if content.get('content'):
            additional_info.append(f"📝 محتوا: {content['content']}")
        if content.get('tags'):
            additional_info.append(f"🏷️ برچسب‌ها: {content['tags']}")
        if content.get('featured', False):
            additional_info.append("⭐ محتوای ویژه")

        # Handle long content with Telegraph
        MAX_CAPTION_LENGTH = 850
        text = "\n\n".join(additional_info) if additional_info else "ℹ️ اطلاعات محتوای آموزشی در دسترس نیست."
        telegraph_url = None
        if len(text) > MAX_CAPTION_LENGTH:
            short_text = text[:MAX_CAPTION_LENGTH] + "...\n\n[(متن کامل)](https://telegra.ph/temp-link)"
            try:
                telegraph_url = await create_telegraph_page(
                    title=content.get('title', 'Educational Content'),
                    content=text,
                    author="RFCatalogbot"
                )
                logger.info(f"Created Telegraph page: {telegraph_url}")
                if telegraph_url:
                    text = short_text.replace("https://telegra.ph/temp-link", telegraph_url)
            except Exception as e:
                logger.error(f"Failed to create Telegraph page: {str(e)}\n{traceback.format_exc()}")
                text = text[:MAX_CAPTION_LENGTH] + "..."

        keyboard = education_detail_keyboard(content_id, content.get('category_id'))
        chat_id = callback.message.chat.id

        media = db.get_educational_content_media(content_id)
        logger.debug(f"Raw media from db.get_educational_content_media for content {content_id}: {media}")

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
            logger.warning(f"هیچ مدیایی برای محتوای آموزشی {content_id} پیدا نشد")
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
            return
        if not isinstance(media, list):
            logger.error(f"media باید لیست باشد، نوع: {type(media)}")
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
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
        logger.debug(f"Initial media_items for content {content_id}: {media_items}")

        # Filter out incomplete media items
        media_items = [item for item in media_items if item['id'] and item['file_type'] and (item['file_id'] or item['local_path'])]
        logger.debug(f"Filtered media_items for content {content_id}: {media_items}")

        if not media_items:
            logger.warning(f"media_items خالی یا ناقص است برای محتوای آموزشی {content_id}")
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
            return

        # Call the function
        logger.debug(f"Calling send_educational_media_group_to_user with bot: {type(bot)}, chat_id: {chat_id}, media_items: {media_items}, caption: {text}")
        await send_educational_media_group_to_user(
            bot=bot,
            chat_id=chat_id,
            media_items=media_items,
            caption=text,
            reply_markup=keyboard
        )
        logger.info(f"Educational content {content_id} sent to chat_id: {chat_id}")
    except Exception as e:
        logger.error(f"Error in callback_educational_content: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش محتوای آموزشی رخ داد.")
