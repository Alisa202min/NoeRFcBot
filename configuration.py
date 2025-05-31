"""
ماژول تنظیمات و پیکربندی
این ماژول تنظیمات پیش‌فرض و امکان بارگذاری و ذخیره پیکربندی را فراهم می‌کند.
"""

import json
import os
import shutil
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if it exists (for initial setup if no config.json exists)
load_dotenv()

CONFIG_PATH = "data/current_config.json"
DEFAULT_CONFIG_PATH = "data/default_config.json"

def load_config():
    """Load configuration from JSON file or create default if not exists"""
    if not os.path.exists(CONFIG_PATH):
        # Create default config if it doesn't exist
        default_config = {
            "BOT_TOKEN": os.environ.get("BOT_TOKEN"),
            "ADMIN_ID": os.environ.get("ADMIN_ID", "0"),
            "DB_TYPE": os.environ.get("DB_TYPE", "postgresql").lower(),
            "DATA_DIR": "data",
            "DB_PATH": os.path.join("data", "database.db"),
            "CSV_PATH": os.path.join("data", "initial_data.csv"),
            "PRODUCT_PREFIX": "product_",
            "SERVICE_PREFIX": "service_",
            "CATEGORY_PREFIX": "category_",
            "BACK_PREFIX": "back_",
            "INQUIRY_PREFIX": "inquiry_",
            "EDUCATION_PREFIX": "edu_",
            "ADMIN_PREFIX": "admin_",
            "PRODUCTS_BTN": "محصولات 🛍",
            "SERVICES_BTN": "خدمات 🔧",
            "INQUIRY_BTN": "استعلام قیمت 💰",
            "EDUCATION_BTN": "محتوای آموزشی 📚",
            "CONTACT_BTN": "تماس با ما ☎️",
            "ABOUT_BTN": "درباره ما ℹ️",
            "BACK_BTN": "بازگشت به منوی اصلی 🏠",
            "SEARCH_BTN": "جستجو 🔍",
            "ADMIN_BTN": "پنل مدیریت 👨‍💼",
            "WEBHOOK_HOST": os.environ.get("WEBHOOK_HOST", "https://example.com"),
            "WEBHOOK_PATH": os.environ.get("WEBHOOK_PATH", "/api/webhook"),
            "DATABASE_URL": os.environ.get("DATABASE_URL"),
            "LOG_LEVEL": os.environ.get("LOG_LEVEL", "INFO"),
            "UPLOAD_FOLDER": os.environ.get("UPLOAD_FOLDER", "data/uploads")
        }

        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)

        # Save default config
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)

        # Also save a copy as default_config.json for reset purposes
        with open(DEFAULT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)

        return default_config
    else:
        # Load existing config
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Update with any new environment variables
            if os.environ.get("BOT_TOKEN"):
                config["BOT_TOKEN"] = os.environ.get("BOT_TOKEN")
            if os.environ.get("DATABASE_URL"):
                config["DATABASE_URL"] = os.environ.get("DATABASE_URL")

            return config
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            return {}

def save_config(config):
    """Save configuration to JSON file"""
    try:
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)

        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logging.error(f"Error saving configuration: {e}")
        return False

def reset_to_default():
    """Reset configuration to default values"""
    if os.path.exists(DEFAULT_CONFIG_PATH):
        try:
            shutil.copy(DEFAULT_CONFIG_PATH, CONFIG_PATH)
            return True
        except Exception as e:
            logging.error(f"Error resetting configuration: {e}")
            return False
    else:
        # If default config doesn't exist, create a new one
        load_config()
        return True

# Directly export commonly used configuration constants
# This allows importing them directly from configuration module
config = load_config()

# Button text
PRODUCTS_BTN = config.get("PRODUCTS_BTN", "محصولات 🛍")
SERVICES_BTN = config.get("SERVICES_BTN", "خدمات 🔧")
INQUIRY_BTN = config.get("INQUIRY_BTN", "استعلام قیمت 💰")
EDUCATION_BTN = config.get("EDUCATION_BTN", "محتوای آموزشی 📚")
CONTACT_BTN = config.get("CONTACT_BTN", "تماس با ما ☎️")
ABOUT_BTN = config.get("ABOUT_BTN", "درباره ما ℹ️")
BACK_BTN = config.get("BACK_BTN", "بازگشت به منوی اصلی 🏠")
SEARCH_BTN = config.get("SEARCH_BTN", "جستجو 🔍")
ADMIN_BTN = config.get("ADMIN_BTN", "پنل مدیریت 👨‍💼")

# Callback prefixes
PRODUCT_PREFIX = config.get("PRODUCT_PREFIX", "product_")
SERVICE_PREFIX = config.get("SERVICE_PREFIX", "service_")
CATEGORY_PREFIX = config.get("CATEGORY_PREFIX", "category_")
BACK_PREFIX = config.get("BACK_PREFIX", "back_")
INQUIRY_PREFIX = config.get("INQUIRY_PREFIX", "inquiry_")
EDUCATION_PREFIX = config.get("EDUCATION_PREFIX", "edu_")
ADMIN_PREFIX = config.get("ADMIN_PREFIX", "admin_")

# Other settings
WEBHOOK_HOST = config.get("WEBHOOK_HOST", "https://example.com")
WEBHOOK_PATH = config.get("WEBHOOK_PATH", "/api/webhook")
DATABASE_URL = config.get("DATABASE_URL", os.environ.get("DATABASE_URL"))
UPLOAD_FOLDER = config.get("UPLOAD_FOLDER", "data/uploads")