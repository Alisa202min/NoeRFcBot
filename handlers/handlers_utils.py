
import os
from logging_config import get_logger
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest

logger = get_logger('bot')

def is_valid_telegram_file_id(file_id: str) -> bool:
    """Validate if a Telegram file_id is valid."""
    if not file_id or not isinstance(file_id, str):
        return False
    file_id = file_id.strip()
    return len(file_id) > 20 and all(c.isalnum() or c in ['-', '_', '.'] for c in file_id)

async def upload_file_to_telegram(file_path: str, bot, file_type: str = 'photo') -> str:
    """Upload a local file to Telegram and return its file_id."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None

    try:
        file = FSInputFile(file_path)
        if file_type == 'photo':
            sent_message = await bot.send_photo(chat_id=bot.id, photo=file)
            file_id = sent_message.photo[-1].file_id
        elif file_type == 'video':
            sent_message = await bot.send_video(chat_id=bot.id, video=file)
            file_id = sent_message.video.file_id
        else:
            logger.error(f"Unsupported file type: {file_type}")
            return None

        logger.info(f"File uploaded successfully: {file_path}, file_id: {file_id}")
        return file_id
    except TelegramBadRequest as e:
        logger.error(f"Failed to upload file {file_path}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error uploading file {file_path}: {str(e)}")
        return None

def format_price(price: float | int) -> str:
    """Format price with thousand separators and currency."""
    try:
        return f"{int(price):,} تومان"
    except (TypeError, ValueError) as e:
        logger.error(f"Error formatting price: {price}, error: {str(e)}")
        return "نامشخص"
