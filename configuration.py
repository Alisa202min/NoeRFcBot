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
            "SERVICES_BTN": "خدمات 🛠",
            "INQUIRY_BTN": "استعلام قیمت 📝",
            "EDUCATION_BTN": "مطالب آموزشی 📚",
            "CONTACT_BTN": "تماس با ما 📞",
            "ABOUT_BTN": "درباره ما ℹ️",
            "BACK_BTN": "بازگشت ↩️",
            "SEARCH_BTN": "جستجو 🔍",
            "ADMIN_BTN": "پنل ادمین 👤",
            "START_TEXT": "🌟 به ربات جامع محصولات و خدمات خوش آمدید! \n\n            این ربات امکانات زیر را در اختیار شما قرار می‌دهد:\n\n            📦 محصولات:\n            • مشاهده محصولات در دسته‌بندی‌های مختلف\n            • جزئیات کامل هر محصول شامل قیمت و توضیحات\n            • امکان مشاهده تصاویر محصولات\n\n            🛠 خدمات:\n            • دسترسی به لیست خدمات قابل ارائه\n            • اطلاعات کامل هر خدمت و شرایط ارائه\n            • امکان استعلام قیمت مستقیم\n\n            📝 استعلام قیمت:\n            • درخواست استعلام قیمت برای محصولات و خدمات\n            • فرم ساده و سریع برای ثبت درخواست\n            • پیگیری آسان درخواست‌ها\n\n            📚 مطالب آموزشی:\n            • دسترسی به محتوای آموزشی دسته‌بندی شده\n            • مقالات و راهنماهای کاربردی\n            • به‌روزرسانی مستمر محتوا\n\n            🔍 امکانات دیگر:\n            • جستجو در محصولات و خدمات\n            • تماس مستقیم با پشتیبانی\n            • اطلاعات تماس و درباره ما\n\n            لطفاً از منوی زیر بخش مورد نظر خود را انتخاب کنید:",
            "NOT_FOUND_TEXT": "موردی یافت نشد.",
            "CONTACT_DEFAULT": "با ما از طریق ایمیل info@example.com در تماس باشید.",
            "ABOUT_DEFAULT": "ما یک شرکت فعال در زمینه تجهیزات الکترونیکی هستیم.",
            "INQUIRY_START": "لطفاً فرم استعلام قیمت را کامل کنید. نام خود را وارد کنید:",
            "INQUIRY_PHONE": "لطفاً شماره تماس خود را وارد کنید:",
            "INQUIRY_DESC": "لطفاً توضیحات بیشتر را وارد کنید (اختیاری):",
            "INQUIRY_COMPLETE": "استعلام قیمت شما با موفقیت ثبت شد. به زودی با شما تماس خواهیم گرفت.",
            "ADMIN_WELCOME": "به پنل مدیریت خوش آمدید. لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            "ADMIN_ACCESS_DENIED": "شما دسترسی به پنل مدیریت ندارید.",
            "SEARCH_PROMPT": "لطفاً عبارت جستجو را وارد کنید:",
            "ERROR_MESSAGE": "خطایی رخ داد. لطفاً دوباره تلاش کنید.",
            "WEBHOOK_HOST": os.environ.get("WEBHOOK_HOST", "https://example.com"),
            "WEBHOOK_PATH": os.environ.get("WEBHOOK_PATH", "/api/webhook"),
            "DATABASE_URL": os.environ.get("DATABASE_URL"),
            "LOG_LEVEL": os.environ.get("LOG_LEVEL", "DEBUG"),
            "UPLOAD_FOLDER": os.environ.get("UPLOAD_FOLDER", "static/uploads"),
            "ALLOWED_FILE_TYPES": ["photo", "video", "animation", "document"]  # انواع فایل‌های مجاز
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
UPLOAD_FOLDER = config.get("UPLOAD_FOLDER",os.environ.get("UPLOAD_FOLDER","static/uploads")) 
ADMIN_ID = config.get("ADMIN_ID", os.environ.get("ADMIN_ID"))
ALLOWED_FILE_TYPES = config.get("ALLOWED_FILE_TYPES", ["photo", "video", "animation", "document"])  # انواع فایل‌های مجاز