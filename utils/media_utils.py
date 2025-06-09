import os
from logging_config import get_logger
from typing import List, Dict, Optional
from bot import bot
from aiogram.types import InputFile, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAnimation
from aiogram.exceptions import TelegramAPIError
from extensions import database
from configuration import ADMIN_ID, UPLOAD_FOLDER

logger = get_logger('bot')
db = database  # هماهنگ با upload_utils.py

async def is_valid_file_id(bot: bot, file_id: str) -> bool:
    """
    بررسی اعتبار file_id با درخواست اطلاعات فایل از تلگرام.

    Args:
        bot: نمونه Bot
        file_id: شناسه فایل تلگرام

    Returns:
        bool: True اگه file_id معتبر باشه، False در غیر این صورت
    """
    try:
        await bot.get_file(file_id)
        return True
    except TelegramAPIError:
        return False

async def send_product_media_and_get_file_id(bot: bot, media_id: int, file_id: str, file_type: str, local_path: str = None) -> str:
    """
    ارسال رسانه محصول به ادمین تلگرام و دریافت file_id.
    اگه file_id معتبر باشه، همون رو استفاده می‌کنه؛ در غیر این صورت، فایل محلی رو آپلود و file_id جدید رو ذخیره می‌کنه.
    اگه local_path خالی باشه و file_id نامعتبر، از file_id به‌عنوان local_path استفاده می‌کنه.

    Args:
        bot: نمونه Bot
        media_id: شناسه رکورد ProductMedia
        file_id: file_id فعلی (ممکنه نامعتبر یا خالی باشه)
        file_type: نوع رسانه (photo, video, animation, document)
        local_path: مسیر محلی فایل رسانه (اختیاری)

    Returns:
        file_id معتبر یا رشته خالی در صورت خطا
    """
    try:
        if not ADMIN_ID:
            logger.error("ADMIN_ID در تنظیمات تعریف نشده")
            return ''

        # بررسی اعتبار file_id
        if file_id and await is_valid_file_id(bot, file_id):
            logger.debug(f"file_id معتبر بازاستفاده شد: {file_id}")
            return file_id

        # اگه local_path خالی باشه و file_id داده شده (ولی نامعتبر)، از file_id به‌عنوان local_path استفاده کن
        if not local_path and file_id:
            local_path = file_id
            logger.warning(f"استفاده از file_id نامعتبر '{file_id}' به‌عنوان local_path برای ProductMedia id {media_id}")

        if not local_path:
            logger.error(f"هیچ local_path یا file_id برای ProductMedia id: {media_id} ارائه نشده")
            return ''

        # نرمال‌سازی local_path: حذف اسلش‌های ابتدایی و پیشوند 'uploads/'
        normalized_path = local_path.lstrip('/')
        if normalized_path.startswith('uploads/'):
            normalized_path = normalized_path[len('uploads/'):]
        full_path = os.path.join(UPLOAD_FOLDER, normalized_path)
        logger.debug(f"مسیر کامل برای ProductMedia id {media_id}: {full_path}")

        if not os.path.exists(full_path):
            logger.error(f"فایل پیدا نشد: {full_path}")
            return ''

        if file_type == 'photo':
            sent_message = await bot.send_photo(chat_id=ADMIN_ID, photo=InputFile(full_path))
            new_file_id = sent_message.photo[-1].file_id
        elif file_type == 'video':
            sent_message = await bot.send_video(chat_id=ADMIN_ID, video=InputFile(full_path))
            new_file_id = sent_message.video.file_id
        elif file_type == 'animation':
            sent_message = await bot.send_animation(chat_id=ADMIN_ID, animation=InputFile(full_path))
            new_file_id = sent_message.animation.file_id
        elif file_type == 'document':
            sent_message = await bot.send_document(chat_id=ADMIN_ID, document=InputFile(full_path))
            new_file_id = sent_message.document.file_id
        else:
            logger.error(f"نوع فایل نامعتبر: {file_type}")
            return ''

        # به‌روزرسانی file_id در ProductMedia
        success = db.update_product_media_file_id(media_id, new_file_id)
        if not success:
            logger.error(f"خطا در به‌روزرسانی file_id برای ProductMedia id {media_id}")
            return ''

        logger.info(f"file_id جدید {new_file_id} برای ProductMedia id {media_id} ذخیره شد")
        return new_file_id

    except TelegramAPIError as e:
        logger.error(f"خطای API تلگرم برای ProductMedia id {media_id}: {e}")
        return ''
    except Exception as e:
        logger.error(f"خطای غیرمنتظره در send_product_media_and_get_file_id برای media_id {media_id}: {e}", exc_info=True)
        return ''

async def send_product_media_group_to_user(bot: bot, chat_id: int, media_items: List[Dict], caption: str = None, reply_markup=None):
    """
    ارسال گروه رسانه‌های محصول به کاربر به صورت media group.
    بررسی اعتبار file_idها، آپلود فایل‌های محلی به ادمین در صورت نیاز، و به‌روزرسانی دیتابیس با file_idهای جدید.
    اگه file_id در دسترس نباشه، فایل مستقیماً از local_path ارسال می‌شه.

    Args:
        bot: نمونه Bot
        chat_id: شناسه چت مقصد
        media_items: لیست دیکشنری‌های رسانه‌های محصول شامل id، file_id، file_type، local_path
        caption: کپشن برای اولین آیتم رسانه
        reply_markup: کیبورد اختیاری
    """
    try:
        media_group = []
        for idx, item in enumerate(media_items):
            media_id = item['id']
            file_id = item.get('file_id')
            file_type = item.get('file_type')
            local_path = item.get('local_path')

            # دریافت file_id معتبر برای رسانه محصول
            valid_file_id = await send_product_media_and_get_file_id(
                bot=bot,
                media_id=media_id,
                file_id=file_id,
                file_type=file_type,
                local_path=local_path
            )

            # اگه file_id معتبر نیست، از local_path یا file_id به‌عنوان local_path استفاده کن
            media_source = valid_file_id
            if not valid_file_id:
                effective_local_path = local_path or file_id
                if effective_local_path:
                    normalized_path = effective_local_path.lstrip('/')
                    if normalized_path.startswith('uploads/'):
                        normalized_path = normalized_path[len('uploads/'):]
                    full_path = os.path.join(UPLOAD_FOLDER, normalized_path)
                    logger.debug(f"مسیر پیشنهادی برای ProductMedia id {media_id}: {full_path}")
                    if os.path.exists(full_path):
                        media_source = InputFile(full_path)
                        logger.debug(f"استفاده از فایل محلی برای ProductMedia id {media_id}: {full_path}")
                    else:
                        logger.warning(f"فایل محلی پیدا نشد برای ProductMedia id {media_id}: {full_path}")
                        continue
                else:
                    logger.warning(f"هیچ local_path یا file_id معتبر برای ProductMedia id {media_id}")
                    continue

            if not media_source:
                logger.warning(f"هیچ منبع رسانه‌ای معتبر برای ProductMedia id {media_id}")
                continue

            # ساخت آیتم مدیا با کپشن فقط برای اولین آیتم
            try:
                if file_type == 'photo':
                    media_item = InputMediaPhoto(
                        media=media_source,
                        caption=caption if idx == 0 and caption else '',
                        parse_mode="Markdown"
                    )
                elif file_type == 'video':
                    media_item = InputMediaVideo(
                        media=media_source,
                        caption=caption if idx == 0 and caption else '',
                        parse_mode="Markdown"
                    )
                elif file_type == 'animation':
                    media_item = InputMediaAnimation(
                        media=media_source,
                        caption=caption if idx == 0 and caption else '',
                        parse_mode="Markdown"
                    )
                elif file_type == 'document':
                    media_item = InputMediaDocument(
                        media=media_source,
                        caption=caption if idx == 0 and caption else '',
                        parse_mode="Markdown"
                    )
                else:
                    logger.warning(f"نوع فایل {file_type} برای ProductMedia id {media_id} پشتیبانی نمی‌شود")
                    continue
            except Exception as e:
                logger.error(f"خطا در ساخت InputMedia برای ProductMedia id {media_id}: {e}")
                continue

            media_group.append(media_item)

        if media_group:
            await bot.send_media_group(
                chat_id=chat_id,
                media=media_group,
                reply_markup=reply_markup
            )
            logger.info(f"گروه رسانه‌ای محصول به chat_id {chat_id} با {len(media_group)} آیتم ارسال شد")
        else:
            logger.warning(f"هیچ آیتم رسانه‌ای معتبر برای ارسال به chat_id {chat_id}")
            # ارسال پیام متنی در صورت نبود رسانه
            if caption:
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )

    except Exception as e:
        logger.error(f"خطا در ارسال گروه رسانه‌ای محصول به chat_id {chat_id}: {e}", exc_info=True)
        # ارسال پیام متنی به‌عنوان فال‌بک
        try:
            if caption:
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
        except TelegramAPIError as e2:
            logger.error(f"خطا در ارسال پیام فال‌بک به chat_id {chat_id}: {e2}")