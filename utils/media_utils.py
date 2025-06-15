import os
from logging_config import get_logger
from typing import List, Dict, Optional
from aiogram import Bot
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAnimation
from aiogram.exceptions import TelegramAPIError
from extensions import database
from configuration import ADMIN_ID, UPLOAD_FOLDER

logger = get_logger('bot')
db = database

async def is_valid_file_id(bot: Bot, file_id: str) -> bool:
    """Check if a file_id is valid by requesting file info from Telegram."""
    if not isinstance(bot, Bot):
        logger.error(f"Bot parameter must be an aiogram.Bot instance, got: {type(bot)}")
        return False
    try:
        await bot.get_file(file_id)
        return True
    except TelegramAPIError:
        return False

async def send_product_media_and_get_file_id(
    bot: Bot, media_id: int, file_id: str, file_type: str, local_path: Optional[str] = None
) -> str:
    """
    Send product media to admin and return file_id.
    Reuses valid file_id if available; otherwise, uploads local file.
    """
    if not isinstance(bot, Bot):
        logger.error(f"Bot parameter must be an aiogram.Bot instance, got: {type(bot)}")
        return ''

    if not ADMIN_ID:
        logger.error("ADMIN_ID is not defined in configuration")
        return ''

    try:
        # Check if file_id is a valid Telegram file_id
        if file_id and await is_valid_file_id(bot, file_id):
            logger.debug(f"Reusing valid Telegram file_id: {file_id}")
            return file_id

        effective_path = local_path or file_id
        if not effective_path:
            logger.error(f"No local_path or file_id provided for ProductMedia id: {media_id}")
            return ''

        normalized_path = effective_path.lstrip('/')
        if normalized_path.startswith('uploads/'):
            normalized_path = normalized_path[len('uploads/'):]
        full_path = os.path.join(UPLOAD_FOLDER, normalized_path)
        logger.debug(f"Full path for ProductMedia id {media_id}: {full_path}")

        if not os.path.exists(full_path):
            logger.error(f"File not found: {full_path}")
            return ''

        media_source = FSInputFile(full_path)
        if file_type == 'photo':
            sent_message = await bot.send_photo(chat_id=ADMIN_ID, photo=media_source)
            new_file_id = sent_message.photo[-1].file_id
        elif file_type == 'video':
            sent_message = await bot.send_video(chat_id=ADMIN_ID, video=media_source)
            new_file_id = sent_message.video.file_id
        elif file_type == 'animation':
            sent_message = await bot.send_animation(chat_id=ADMIN_ID, animation=media_source)
            new_file_id = sent_message.animation.file_id
        elif file_type == 'document':
            sent_message = await bot.send_document(chat_id=ADMIN_ID, document=media_source)
            new_file_id = sent_message.document.file_id
        else:
            logger.error(f"Invalid file type: {file_type}")
            return ''

        success = db.update_product_media_file_id(media_id, new_file_id)
        if not success:
            logger.error(f"Failed to update file_id for ProductMedia id: {media_id}")
            return ''

        logger.info(f"New file_id {new_file_id} saved for ProductMedia id: {media_id}")
        return new_file_id

    except TelegramAPIError as e:
        logger.error(f"Telegram API error for ProductMedia id {media_id}: {e}")
        return ''
    except Exception as e:
        logger.error(f"Unexpected error in send_product_media_and_get_file_id for media_id {media_id}: {e}", exc_info=True)
        return ''

async def send_product_media_group_to_user(
    bot: Bot, chat_id: int, media_items: List[Dict], caption: Optional[str] = None, reply_markup=None
):
    """
    Send a group of product media to a user as a media group.
    Expects a list of dictionaries containing media details.
    If reply_markup is provided, sends it with a separate message.
    """
    if not isinstance(bot, Bot):
        logger.error(f"Bot parameter must be an aiogram.Bot instance, got: {type(bot)}")
        return

    if not isinstance(chat_id, int):
        logger.error(f"chat_id must be an integer, got: {type(chat_id)}")
        return

    if not isinstance(media_items, list):
        logger.error(f"media_items must be a list, got: {type(media_items)}")
        if caption:
            await bot.send_message(chat_id=chat_id, text=caption, parse_mode="Markdown", reply_markup=reply_markup)
        return

    if not media_items:
        logger.warning("media_items is empty")
        if caption:
            await bot.send_message(chat_id=chat_id, text=caption, parse_mode="Markdown", reply_markup=reply_markup)
        return

    media_group = []
    valid_file_ids = []
    for idx, item in enumerate(media_items):
        if not isinstance(item, dict):
            logger.error(f"Invalid item in media_items at index {idx}: {item}")
            continue

        media_id = item.get('id')
        file_id = item.get('file_id')
        file_type = item.get('file_type')
        local_path = item.get('local_path')

        if not all([media_id, file_type, file_id]):
            logger.error(f"Incomplete item in media_items at index {idx}: {item}")
            continue

        # Use Telegram file_id if valid
        if await is_valid_file_id(bot, file_id):
            media_source = file_id
            logger.debug(f"Using existing Telegram file_id for ProductMedia id {media_id}: {file_id}")
        else:
            media_source = await send_product_media_and_get_file_id(
                bot=bot, media_id=media_id, file_id=file_id, file_type=file_type, local_path=local_path
            )

        if not media_source:
            effective_path = local_path or file_id
            if effective_path:
                normalized_path = effective_path.lstrip('/')
                if normalized_path.startswith('uploads/'):
                    normalized_path = normalized_path[len('uploads/'):]
                full_path = os.path.join(UPLOAD_FOLDER, normalized_path)
                if os.path.exists(full_path):
                    media_source = FSInputFile(full_path)
                    logger.debug(f"Using local file for ProductMedia id {media_id}: {full_path}")
                else:
                    logger.warning(f"Local file not found for ProductMedia id {media_id}: {full_path}")
                    continue
            else:
                logger.warning(f"No valid local_path or file_id for ProductMedia id {media_id}")
                continue

        if not media_source:
            logger.warning(f"No valid media source for ProductMedia id {media_id}")
            continue

        try:
            if file_type == 'photo':
                media_item = InputMediaPhoto(
                    media=media_source, caption=caption if idx == 0 and caption else '', parse_mode="Markdown"
                )
            elif file_type == 'video':
                media_item = InputMediaVideo(
                    media=media_source, caption=caption if idx == 0 and caption else '', parse_mode="Markdown"
                )
            elif file_type == 'animation':
                media_item = InputMediaAnimation(
                    media=media_source, caption=caption if idx == 0 and caption else '', parse_mode="Markdown"
                )
            elif file_type == 'document':
                media_item = InputMediaDocument(
                    media=media_source, caption=caption if idx == 0 and caption else '', parse_mode="Markdown"
                )
            else:
                logger.warning(f"File type {file_type} not supported for ProductMedia id {media_id}")
                continue
            media_group.append(media_item)
            valid_file_ids.append(media_source)
        except Exception as e:
            logger.error(f"Error creating InputMedia for ProductMedia id {media_id}: {e}")
            continue

    if media_group:
        try:
            logger.debug(f"Sending media group with {len(media_group)} items: {valid_file_ids}")
            await bot.send_media_group(chat_id=chat_id, media=media_group)
            logger.info(f"Media group sent to chat_id {chat_id} with {len(media_group)} items")
            if reply_markup:
                await bot.send_message(chat_id=chat_id, text=".", reply_markup=reply_markup)
        except TelegramAPIError as e:
            logger.error(f"Failed to send media group to chat_id {chat_id}: {e}")
            # Fallback to sending individual media
            for idx, media_item in enumerate(media_group):
                try:
                    if isinstance(media_item, InputMediaPhoto):
                        await bot.send_photo(chat_id=chat_id, photo=media_item.media, caption=caption if idx == 0 else "")
                    elif isinstance(media_item, InputMediaVideo):
                        await bot.send_video(chat_id=chat_id, video=media_item.media, caption=caption if idx == 0 else "")
                    elif isinstance(media_item, InputMediaAnimation):
                        await bot.send_animation(chat_id=chat_id, animation=media_item.media, caption=caption if idx == 0 else "")
                    elif isinstance(media_item, InputMediaDocument):
                        await bot.send_document(chat_id=chat_id, document=media_item.media, caption=caption if idx == 0 else "")
                except TelegramAPIError as e2:
                    logger.error(f"Failed to send individual media item {idx} to chat_id {chat_id}: {e2}")
            if caption and not media_group:
                await bot.send_message(chat_id=chat_id, text=caption, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        logger.warning(f"No valid media items to send to chat_id {chat_id}")
        if caption:
            await bot.send_message(chat_id=chat_id, text=caption, parse_mode="Markdown", reply_markup=reply_markup)