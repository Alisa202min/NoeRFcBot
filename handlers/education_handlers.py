
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InputMediaVideo
from configuration import EDUCATION_BTN, EDUCATION_PREFIX, ADMIN_ID
from logging_config import get_logger
from extensions import database
from aiogram.exceptions import TelegramBadRequest
from bot import bot
from keyboards import education_categories_keyboard, education_content_keyboard, education_detail_keyboard
from .handlers_utils import is_valid_telegram_file_id, upload_file_to_telegram
from aiogram.filters import Command
from utils.utils import create_telegraph_page
import os
import traceback
from models import EducationalContentMedia

logger = get_logger('bot')
router = Router(name="educational_router")
db = database

@router.message(lambda message: message.text == EDUCATION_BTN)
@router.message(Command("education"))
async def cmd_education(message: Message):
    """Handle Education button or /education command"""
    try:
        logger.info(f"Educational content requested by user: {message.from_user.id}")
        categories = db.get_educational_categories()
        if not categories:
            await message.answer("⚠️ محتوای آموزشی در حال حاضر در دسترس نیست. لطفا بعدا تلاش کنید.")
            logger.warning("No educational categories found in database")
            return

        keyboard = education_categories_keyboard(categories)
        await message.answer(
            "📚 *محتوای آموزشی*\n\nلطفا یکی از دسته‌بندی‌های زیر را انتخاب کنید:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Educational categories sent: {len(categories)} categories")
    except Exception as e:
        logger.error(f"Error in cmd_education: {str(e)}\n{traceback.format_exc()}")
        await message.answer("⚠️ متأسفانه در پردازش درخواست شما خطایی رخ داد. لطفا مجددا تلاش کنید.")

@router.callback_query(F.data == "educational")
async def callback_educational(callback: CallbackQuery):
    """Handle educational content button click"""
    await callback.answer()
    try:
        categories = db.get_educational_categories()
        if not categories:
            await callback.message.answer("در حال حاضر محتوای آموزشی موجود نیست.")
            return

        for category in categories:
            category_id = category['id']
            legacy_content = db.get_all_educational_content(category_id=category_id)
            legacy_count = len(legacy_content) if legacy_content else 0
            content_count = int(category.get('content_count', 0))
            category['content_count'] = content_count + legacy_count

        keyboard = education_categories_keyboard(categories)
        await callback.message.answer("🎓 دسته‌بندی محتوای آموزشی را انتخاب کنید:",
                                   reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in callback_educational: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش محتوای آموزشی رخ داد.")

@router.callback_query(F.data.startswith(f"{EDUCATION_PREFIX}cat_"))
async def callback_educational_category(callback: CallbackQuery):
    """Handle educational category selection"""
    await callback.answer()
    try:
        category_id = int(callback.data.replace(f"{EDUCATION_PREFIX}cat_", ""))
        logger.info(f"Selected educational category ID: {category_id}")
        category_info = db.get_educational_category(category_id)
        if not category_info:
            logger.error(f"Category not found for ID: {category_id}")
            await callback.message.answer("⚠️ دسته‌بندی مورد نظر یافت نشد.")
            return

        content_list = db.get_all_educational_content(category_id=category_id)
        if not content_list:
            logger.warning(f"No educational content found for category ID: {category_id}")
            await callback.message.answer(f"⚠️ محتوای آموزشی برای دسته‌بندی '{category_info['name']}' موجود نیست.")
            return

        keyboard = education_content_keyboard(content_list, category_id)
        await callback.message.answer(f"📚 محتوای آموزشی در دسته‌بندی '{category_info['name']}':",
                                   reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in callback_educational_category: {str(e)}\n{traceback.format_exc()}")
        await callback.message.answer("⚠️ خطایی در نمایش محتوای آموزشی رخ داد.")

@router.callback_query(F.data == f"{EDUCATION_PREFIX}categories")
async def callback_educational_categories(callback: CallbackQuery):
    """Handle going back to educational categories"""
    await callback.answer()
    categories = db.get_educational_categories()
    if not categories:
        await callback.message.answer("در حال حاضر محتوای آموزشی موجود نیست.")
        return

    keyboard = education_categories_keyboard(categories)
    await callback.message.answer("🎓 دسته‌بندی محتوای آموزشی را انتخاب کنید:",
                               reply_markup=keyboard)

@router.callback_query(F.data.startswith(f"{EDUCATION_PREFIX}:"))
async def callback_educational_content(callback: CallbackQuery):
    """Handle educational content selection"""
    await callback.answer()
    try:
        content_id = int(callback.data.replace(f"{EDUCATION_PREFIX}:", ""))
        logger.info(f"Selected educational content ID: {content_id}")
        content = db.get_educational_content(content_id)
        if not content:
            logger.error(f"Educational content not found for ID: {content_id}")
            await callback.message.answer("⚠️ محتوای آموزشی مورد نظر یافت نشد.")
            if ADMIN_ID:
                await bot.send_message(ADMIN_ID, f"Content not found: ID {content_id}")
            return

        category_id = content.get('category_id', 0)
        keyboard = education_detail_keyboard(category_id)
        title = content['title']
        content_text = content.get('content', '')
        MAX_CAPTION_LENGTH = 850
        caption_text = f"📖 *{title}*\n\n"
        telegraph_url = None

        if len(content_text) > MAX_CAPTION_LENGTH:
            short_text = content_text[:MAX_CAPTION_LENGTH] + "...\n\n[(متن کامل)](https://telegra.ph/temp-link)"
            caption_text += short_text
            try:
                telegraph_url = await create_telegraph_page(
                    title=title, content=content_text, author="RFCatalogbot"
                )
                if telegraph_url:
                    caption_text = caption_text.replace("https://telegra.ph/temp-link", telegraph_url)
            except Exception as e:
                logger.error(f"Failed to create Telegraph page: {str(e)}\n{traceback.format_exc()}")
                caption_text = f"📖 *{title}*\n\n{content_text[:MAX_CAPTION_LENGTH]}..."
        else:
            caption_text += content_text

        media_files = db.get_educational_content_media(content_id)
        media_group = []
        for idx, media in enumerate(media_files):
            media_item = await process_media_file(media, idx, bot, caption_text)
            if media_item:
                media_group.append(media_item)

        if media_group:
            try:
                await bot.send_media_group(
                    chat_id=callback.message.chat.id,
                    media=media_group
                )
                await bot.send_message(
                    chat_id=callback.message.chat.id,
                    text="🔍 گزینه‌های مرتبط با محتوای آموزشی:",
                    reply_markup=keyboard
                )
            except TelegramBadRequest as e:
                logger.error(f"Failed to send media group for content {content_id}: {str(e)}")
                content_text = f"📖 *{title}*\n\n{content_text}"
                if telegraph_url:
                    content_text += f"\n\n[متن کامل]({telegraph_url})"
                await callback.message.answer(
                    content_text, parse_mode="Markdown", reply_markup=keyboard
                )
                if ADMIN_ID:
                    await bot.send_message(
                        ADMIN_ID,
                        f"Failed to send media group for content {content_id}: {str(e)}"
                    )
        else:
            content_text = f"📖 *{title}*\n\n{content_text}"
            if telegraph_url:
                content_text += f"\n\n[متن کامل]({telegraph_url})"
            await callback.message.answer(
                content_text, parse_mode="Markdown", reply_markup=keyboard
            )
            if ADMIN_ID:
                await bot.send_message(
                    ADMIN_ID,
                    f"No valid media for content {content_id}: {media_files}"
                )
    except Exception as e:
        logger.error(f"Error processing educational content: {str(e)}")
        await callback.message.answer("⚠️ خطایی در نمایش محتوا رخ داد.")
        if ADMIN_ID:
            await bot.send_message(ADMIN_ID, f"Error displaying content {content_id}: {str(e)}")

async def process_media_file(media, idx, bot, caption_text):
    """Process a media file for educational content"""
    media_id = media.get('id')
    file_id = media.get('file_id')
    local_path = media.get('local_path', '')
    file_type = media.get('file_type', 'photo')

    logger.info(f"Processing media {media_id}: file_id={file_id}, local_path={local_path}, type={file_type}")

    if not file_id or file_id.startswith('educational_content_image_'):
        if not local_path:
            logger.error(f"No local path for media {media_id} with file_id {file_id}")
            return None

        full_path = local_path if local_path.startswith('static/') else f"static/{local_path}"
        if not os.path.exists(full_path):
            logger.error(f"Local file not found: {full_path} for media {media_id}")
            return None

        try:
            telegram_file_id = await upload_file_to_telegram(full_path, bot, file_type)
            if not telegram_file_id or not is_valid_telegram_file_id(telegram_file_id):
                logger.error(f"Invalid file_id returned from upload: {telegram_file_id}")
                return None

            session = db.Session()
            try:
                media_record = session.query(EducationalContentMedia).filter_by(id=media_id).first()
                if media_record:
                    media_record.file_id = telegram_file_id
                    session.commit()
                    logger.info(f"Updated file_id for media {media_id} to {telegram_file_id}")
                    file_id = telegram_file_id
                else:
                    logger.error(f"Media record {media_id} not found")
                    return None
            except Exception as e:
                logger.error(f"Failed to update database for media {media_id}: {str(e)}")
                session.rollback()
                return None
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error uploading local file {full_path}: {str(e)}")
            return None
    else:
        try:
            await bot.get_file(file_id)
            logger.info(f"Validated file_id {file_id} for media {media_id}")
        except TelegramBadRequest as e:
            logger.warning(f"File_id {file_id} inaccessible: {str(e)}")
            if not local_path:
                logger.warning(f"No local path for media {media_id}")
                return None

            full_path = local_path if local_path.startswith('static/') else f"static/{local_path}"
            if not os.path.exists(full_path):
                logger.error(f"Local file not found: {full_path}")
                return None

            try:
                telegram_file_id = await upload_file_to_telegram(full_path, bot, file_type)
                if not telegram_file_id or not is_valid_telegram_file_id(telegram_file_id):
                    logger.error(f"Invalid file_id from upload: {telegram_file_id}")
                    return None

                session = db.Session()
                try:
                    media_record = session.query(EducationalContentMedia).filter_by(id=media_id).first()
                    if media_record:
                        media_record.file_id = telegram_file_id
                        session.commit()
                        logger.info(f"Updated file_id for media {media_id} to {telegram_file_id}")
                        file_id = telegram_file_id
                    else:
                        logger.error(f"Media record {media_id} not found")
                        return None
                except Exception as e:
                    logger.error(f"Failed to update database for media {media_id}: {str(e)}")
                    session.rollback()
                    return None
                finally:
                    session.close()
            except Exception as e:
                logger.error(f"Error re-uploading file {full_path}: {str(e)}")
                return None

    try:
        if file_type == 'photo':
            return InputMediaPhoto(
                media=file_id,
                caption=caption_text if idx == 0 else "",
                parse_mode="Markdown"
            )
        elif file_type == 'video':
            return InputMediaVideo(
                media=file_id,
                caption=caption_text if idx == 0 else "",
                parse_mode="Markdown"
            )
        else:
            logger.error(f"Unsupported file type {file_type} for media {media_id}")
            return None
    except Exception as e:
        logger.error(f"Failed to create media item for file_id {file_id}: {str(e)}")
        return None
