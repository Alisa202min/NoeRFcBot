"""
ماژول بات تلگرام
این ماژول شامل کلاس‌ها و توابعی برای ارتباط با API تلگرام است.
"""

from .bot import bot, dp, start_polling, setup_webhook
from .handlers import register_all_handlers as register_handlers
from .handlers import UserStates
from .keyboards import (
    get_main_keyboard, 
    get_back_keyboard, 
    get_categories_keyboard,
    get_admin_keyboard
)

__all__ = [
    'bot', 
    'dp', 
    'start_polling', 
    'setup_webhook',
    'register_handlers',
    'UserStates',
    'get_main_keyboard',
    'get_back_keyboard',
    'get_categories_keyboard',
    'get_admin_keyboard'
]