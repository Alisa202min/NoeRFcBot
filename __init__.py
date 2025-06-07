# __init__.py
from extensions import db  # Import db from extensions.py
from bot import bot, start_polling, setup_webhook
from handlers import register_all_handlers as register_handlers
from handlers import UserStates
from keyboards import (
    get_main_keyboard, 
    get_back_keyboard, 
    get_categories_keyboard,
    get_admin_keyboard
)
from models import (
    User, Product, ProductMedia, Service, ServiceMedia, 
    Inquiry, EducationalContent, EducationalContentMedia, 
    StaticContent, ProductCategory, ServiceCategory, EducationalCategory
)
from configuration import load_config, save_config, reset_to_default  # Changed from config_init to configuration

__all__ = [
    'db',
    'User',
    'Product',
    'ProductMedia',
    'Service',
    'ServiceMedia',
    'Inquiry',
    'EducationalContent',
    'EducationalContentMedia',
    'StaticContent',
    'ProductCategory',
    'ServiceCategory',
    'EducationalCategory',
    'bot', 
    'start_polling', 
    'setup_webhook',
    'register_handlers',
    'UserStates',
    'get_main_keyboard',
    'get_back_keyboard',
    'get_categories_keyboard',
    'get_admin_keyboard',
    'load_config',
    'save_config',
    'reset_to_default'
]