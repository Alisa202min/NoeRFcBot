import traceback
import os
from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, InlineKeyboardMarkup, FSInputFile
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from logging_config import get_logger

logger = get_logger('bot')

async def send_product_media_group_to_user(
    bot: Bot,
    chat_id: int,
    media_items: list,
    caption: str = None,
    reply_markup: InlineKeyboardMarkup = None,
    parse_mode: str = "Markdown"
):
    """Send a media group for a product to user with caption and optional reply markup."""
    try:
        # Validate bot instance
        if not isinstance(bot, Bot):
            logger.error(f"Invalid bot instance in send_product_media_group: expected aiogram.Bot, got {type(bot)}")
            raise ValueError("Bot instance must be of type aiogram.Bot")

        logger.debug(f"Preparing to send product media group to chat_id: {chat_id}, media_items: {len(media_items)}")

        # Validate media items
        if not media_items:
            logger.warning(f"No media items provided for product to chat_id: {chat_id}")
            if caption:
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                logger.info(f"Sent fallback text message for product to chat_id: {chat_id} with reply_markup: {reply_markup is not None}")
            return

        # Build media group
        media_group = []
        for idx, item in enumerate(media_items):
            file_type = item.get('file_type')
            file_id = item.get('file_id')
            local_path = item.get('local_path')

            if not file_type:
                logger.warning(f"Skipping invalid product media item (missing file_type): {item}")
                continue

            # Use local_path if provided, otherwise check file_id
            effective_path = local_path
            media_source = None

            # If file_id exists, check if it's a valid Telegram file ID
            if file_id:
                try:
                    file = await bot.get_file(file_id)
                    if file.file_path:
                        media_source = file_id
                        logger.debug(f"Valid Telegram file_id for product item: {file_id}")
                except (TelegramBadRequest, TelegramAPIError) as e:
                    logger.debug(f"Invalid Telegram file_id for product item: {file_id}, error: {str(e)}")
                    # If file_id is invalid and local_path is empty, use file_id as local path
                    if not local_path:
                        effective_path = file_id

            # Handle local file if no valid file_id or local_path is set
            if not media_source and effective_path:
                if not effective_path.startswith('static/'):
                    corrected_path = os.path.join('static', effective_path)
                else:
                    corrected_path = effective_path
                if not os.path.exists(corrected_path):
                    logger.warning(f"Skipping product media item with non-existent local file: {corrected_path}")
                    continue
                try:
                    media_source = FSInputFile(corrected_path)
                except (IOError, OSError) as e:
                    logger.warning(f"Skipping product media item due to file access error: {corrected_path}, error: {str(e)}")
                    continue

            if not media_source:
                logger.warning(f"Skipping invalid product media item (no valid file_id or local file): {item}")
                continue

            media_kwargs = {'caption': caption if idx == 0 else None, 'parse_mode': parse_mode}
            try:
                if file_type == 'photo':
                    media_group.append(InputMediaPhoto(media=media_source, **media_kwargs))
                elif file_type == 'video':
                    media_group.append(InputMediaVideo(media=media_source, **media_kwargs))
                elif file_type == 'document':
                    media_group.append(InputMediaDocument(media=media_source, **media_kwargs))
                else:
                    logger.warning(f"Unsupported media type for product: {file_type} for item: {item}")
                    continue
            except Exception as e:
                logger.error(f"Error creating product media item {item}: {str(e)}")
                continue

        if not media_group:
            logger.warning(f"No valid media items to send for product to chat_id: {chat_id}")
            if caption:
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                logger.info(f"Sent fallback text message for product to chat_id: {chat_id} with reply_markup: {reply_markup is not None}")
            return

        # Send media group
        logger.debug(f"Sending product media group with {len(media_group)} items: {[m.media.path if hasattr(m.media, 'path') else m.media for m in media_group]}")
        await bot.send_media_group(chat_id=chat_id, media=media_group)

        # Send reply markup separately if provided
        if reply_markup:
            try:
                buttons = [[btn.text + f" ({btn.callback_data})" for btn in row] for row in reply_markup.inline_keyboard]
                logger.debug(f"Sending product reply markup to chat_id: {chat_id} with buttons: {buttons}")
            except Exception as e:
                logger.error(f"Error logging reply_markup for chat_id: {chat_id}: {str(e)}")
            await bot.send_message(
                chat_id=chat_id,
                text="گزینه‌های موجود:",
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            logger.info(f"Sent product reply markup to chat_id: {chat_id}")

    except TelegramAPIError as e:
        logger.error(f"Telegram API error sending product media group to chat_id: {chat_id}: {str(e)}")
        if caption:
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            logger.info(f"Sent fallback text message for product due to Telegram API error to chat_id: {chat_id}")
    except Exception as e:
        logger.error(f"Error in send_product_media_group_to_user for chat_id: {chat_id}: {str(e)}\n{traceback.format_exc()}")
        if caption:
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            logger.info(f"Sent fallback text message for product due to error to chat_id: {chat_id}")

async def send_service_media_group_to_user(
    bot: Bot,
    chat_id: int,
    media_items: list,
    caption: str = None,
    reply_markup: InlineKeyboardMarkup = None,
    parse_mode: str = "Markdown"
):
    """Send a media group for a service to user with caption and optional reply markup."""
    try:
        # Validate bot instance
        if not isinstance(bot, Bot):
            logger.error(f"Invalid bot instance in send_service_media_group: expected aiogram.Bot, got {type(bot)}")
            raise ValueError("Bot instance must be of type aiogram.Bot")

        logger.debug(f"Preparing to send service media group to chat_id: {chat_id}, media_items: {len(media_items)}")

        # Validate media items
        if not media_items:
            logger.warning(f"No media items provided for service to chat_id: {chat_id}")
            if caption:
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                logger.info(f"Sent fallback text message for service to chat_id: {chat_id} with reply_markup: {reply_markup is not None}")
            return

        # Build media group
        media_group = []
        for idx, item in enumerate(media_items):
            file_type = item.get('file_type')
            file_id = item.get('file_id')
            local_path = item.get('local_path')

            if not file_type:
                logger.warning(f"Skipping invalid service media item (missing file_type): {item}")
                continue

            # Use local_path if provided, otherwise check file_id
            effective_path = local_path
            media_source = None

            # If file_id exists, check if it's a valid Telegram file ID
            if file_id:
                try:
                    file = await bot.get_file(file_id)
                    if file.file_path:
                        media_source = file_id
                        logger.debug(f"Valid Telegram file_id for service item: {file_id}")
                except (TelegramBadRequest, TelegramAPIError) as e:
                    logger.debug(f"Invalid Telegram file_id for service item: {file_id}, error: {str(e)}")
                    # If file_id is invalid and local_path is empty, use file_id as local path
                    if not local_path:
                        effective_path = file_id

            # Handle local file if no valid file_id or local_path is set
            if not media_source and effective_path:
                if not effective_path.startswith('static/'):
                    corrected_path = os.path.join('static', effective_path)
                else:
                    corrected_path = effective_path
                if not os.path.exists(corrected_path):
                    logger.warning(f"Skipping service media item with non-existent local file: {corrected_path}")
                    continue
                try:
                    media_source = FSInputFile(corrected_path)
                except (IOError, OSError) as e:
                    logger.warning(f"Skipping service media item due to file access error: {corrected_path}, error: {str(e)}")
                    continue

            if not media_source:
                logger.warning(f"Skipping invalid service media item (no valid file_id or local file): {item}")
                continue

            media_kwargs = {'caption': caption if idx == 0 else None, 'parse_mode': parse_mode}
            try:
                if file_type == 'photo':
                    media_group.append(InputMediaPhoto(media=media_source, **media_kwargs))
                elif file_type == 'video':
                    media_group.append(InputMediaVideo(media=media_source, **media_kwargs))
                elif file_type == 'document':
                    media_group.append(InputMediaDocument(media=media_source, **media_kwargs))
                else:
                    logger.warning(f"Unsupported media type for service: {file_type} for item: {item}")
                    continue
            except Exception as e:
                logger.error(f"Error creating service media item {item}: {str(e)}")
                continue

        if not media_group:
            logger.warning(f"No valid media items to send for service to chat_id: {chat_id}")
            if caption:
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                logger.info(f"Sent fallback text message for service to chat_id: {chat_id} with reply_markup: {reply_markup is not None}")
            return

        # Send media group
        logger.debug(f"Sending service media group with {len(media_group)} items: {[m.media.path if hasattr(m.media, 'path') else m.media for m in media_group]}")
        await bot.send_media_group(chat_id=chat_id, media=media_group)

        # Send reply markup separately if provided
        if reply_markup:
            try:
                buttons = [[btn.text + f" ({btn.callback_data})" for btn in row] for row in reply_markup.inline_keyboard]
                logger.debug(f"Sending service reply markup to chat_id: {chat_id} with buttons: {buttons}")
            except Exception as e:
                logger.error(f"Error logging reply_markup for chat_id: {chat_id}: {str(e)}")
            await bot.send_message(
                chat_id=chat_id,
                text="گزینه‌های موجود:",
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            logger.info(f"Sent service reply markup to chat_id: {chat_id}")

    except TelegramAPIError as e:
        logger.error(f"Telegram API error sending service media group to chat_id: {chat_id}: {str(e)}")
        if caption:
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            logger.info(f"Sent fallback text message for service due to Telegram API error to chat_id: {chat_id}")
    except Exception as e:
        logger.error(f"Error in send_service_media_group_to_user for chat_id: {chat_id}: {str(e)}\n{traceback.format_exc()}")
        if caption:
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            logger.info(f"Sent fallback text message for service due to error to chat_id: {chat_id}")

async def send_educational_media_group_to_user(
    bot: Bot,
    chat_id: int,
    media_items: list,
    caption: str = None,
    reply_markup: InlineKeyboardMarkup = None,
    parse_mode: str = "Markdown"
):
    """Send a media group for educational content to user with caption and optional reply markup."""
    try:
        # Validate bot instance
        if not isinstance(bot, Bot):
            logger.error(f"Invalid bot instance in send_educational_media_group: expected aiogram.Bot, got {type(bot)}")
            raise ValueError("Bot instance must be of type aiogram.Bot")

        logger.debug(f"Preparing to send educational media group to chat_id: {chat_id}, media_items: {len(media_items)}")

        # Validate media items
        if not media_items:
            logger.warning(f"No media items provided for educational content to chat_id: {chat_id}")
            if caption:
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                logger.info(f"Sent fallback text message for educational content to chat_id: {chat_id} with reply_markup: {reply_markup is not None}")
            return

        # Build media group
        media_group = []
        for idx, item in enumerate(media_items):
            file_type = item.get('file_type')
            file_id = item.get('file_id')
            local_path = item.get('local_path')

            if not file_type:
                logger.warning(f"Skipping invalid educational media item (missing file_type): {item}")
                continue

            # Use local_path if provided, otherwise check file_id
            effective_path = local_path
            media_source = None

            # If file_id exists, check if it's a valid Telegram file ID
            if file_id:
                try:
                    file = await bot.get_file(file_id)
                    if file.file_path:
                        media_source = file_id
                        logger.debug(f"Valid Telegram file_id for educational item: {file_id}")
                except (TelegramBadRequest, TelegramAPIError) as e:
                    logger.debug(f"Invalid Telegram file_id for educational item: {file_id}, error: {str(e)}")
                    # If file_id is invalid and local_path is empty, use file_id as local path
                    if not local_path:
                        effective_path = file_id

            # Handle local file if no valid file_id or local_path is set
            if not media_source and effective_path:
                if not effective_path.startswith('static/'):
                    corrected_path = os.path.join('static', effective_path)
                else:
                    corrected_path = effective_path
                if not os.path.exists(corrected_path):
                    logger.warning(f"Skipping educational media item with non-existent local file: {corrected_path}")
                    continue
                try:
                    media_source = FSInputFile(corrected_path)
                except (IOError, OSError) as e:
                    logger.warning(f"Skipping educational media item due to file access error: {corrected_path}, error: {str(e)}")
                    continue

            if not media_source:
                logger.warning(f"Skipping invalid educational media item (no valid file_id or local file): {item}")
                continue

            media_kwargs = {'caption': caption if idx == 0 else None, 'parse_mode': parse_mode}
            try:
                if file_type == 'photo':
                    media_group.append(InputMediaPhoto(media=media_source, **media_kwargs))
                elif file_type == 'video':
                    media_group.append(InputMediaVideo(media=media_source, **media_kwargs))
                elif file_type == 'document':
                    media_group.append(InputMediaDocument(media=media_source, **media_kwargs))
                else:
                    logger.warning(f"Unsupported media type for educational content: {file_type} for item: {item}")
                    continue
            except Exception as e:
                logger.error(f"Error creating educational media item {item}: {str(e)}")
                continue

        if not media_group:
            logger.warning(f"No valid media items to send for educational content to chat_id: {chat_id}")
            if caption:
                await bot.send_message(
                    chat_id=chat_id,
                    text=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                logger.info(f"Sent fallback text message for educational content to chat_id: {chat_id} with reply_markup: {reply_markup is not None}")
            return

        # Send media group
        logger.debug(f"Sending educational media group with {len(media_group)} items: {[m.media.path if hasattr(m.media, 'path') else m.media for m in media_group]}")
        await bot.send_media_group(chat_id=chat_id, media=media_group)

        # Send reply markup separately if provided
        if reply_markup:
            try:
                buttons = [[btn.text + f" ({btn.callback_data})" for btn in row] for row in reply_markup.inline_keyboard]
                logger.debug(f"Sending educational reply markup to chat_id: {chat_id} with buttons: {buttons}")
            except Exception as e:
                logger.error(f"Error logging reply_markup for chat_id: {chat_id}: {str(e)}")
            await bot.send_message(
                chat_id=chat_id,
                text="گزینه‌های موجود:",
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            logger.info(f"Sent educational reply markup to chat_id: {chat_id}")

    except TelegramAPIError as e:
        logger.error(f"Telegram API error sending educational media group to chat_id: {chat_id}: {str(e)}")
        if caption:
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            logger.info(f"Sent fallback text message for educational content due to Telegram API error to chat_id: {chat_id}")
    except Exception as e:
        logger.error(f"Error in send_educational_media_group_to_user for chat_id: {chat_id}: {str(e)}\n{traceback.format_exc()}")
        if caption:
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            logger.info(f"Sent fallback text message for educational content due to error to chat_id: {chat_id}")