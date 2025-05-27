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
            "START_TEXT": """🌟 به ربات جامع محصولات و خدمات خوش آمدید! 

            این ربات امکانات زیر را در اختیار شما قرار می‌دهد:

            📦 محصولات:
            • مشاهده محصولات در دسته‌بندی‌های مختلف
            • جزئیات کامل هر محصول شامل قیمت و توضیحات
            • امکان مشاهده تصاویر محصولات

            🛠 خدمات:
            • دسترسی به لیست خدمات قابل ارائه
            • اطلاعات کامل هر خدمت و شرایط ارائه
            • امکان استعلام قیمت مستقیم

            📝 استعلام قیمت:
            • درخواست استعلام قیمت برای محصولات و خدمات
            • فرم ساده و سریع برای ثبت درخواست
            • پیگیری آسان درخواست‌ها

            📚 مطالب آموزشی:
            • دسترسی به محتوای آموزشی دسته‌بندی شده
            • مقالات و راهنماهای کاربردی
            • به‌روزرسانی مستمر محتوا

            🔍 امکانات دیگر:
            • جستجو در محصولات و خدمات
            • تماس مستقیم با پشتیبانی
            • اطلاعات تماس و درباره ما

            لطفاً از منوی زیر بخش مورد نظر خود را انتخاب کنید:""",
            "NOT_FOUND_TEXT": "موردی یافت نشد.",
            "CONTACT_DEFAULT": "با ما از طریق شماره 1234567890+ یا ایمیل info@example.com در تماس باشید.",
            "ABOUT_DEFAULT": "ما یک شرکت فعال در زمینه تجهیزات الکترونیکی هستیم.",
            "INQUIRY_START": "لطفاً فرم استعلام قیمت را کامل کنید. نام خود را وارد کنید:",
            "INQUIRY_PHONE": "لطفاً شماره تماس خود را وارد کنید:",
            "INQUIRY_DESC": "لطفاً توضیحات بیشتر را وارد کنید (اختیاری):",
            "INQUIRY_COMPLETE": "استعلام قیمت شما با موفقیت ثبت شد. به زودی با شما تماس خواهیم گرفت.",
            "ADMIN_WELCOME": "به پنل مدیریت خوش آمدید. لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            "ADMIN_ACCESS_DENIED": "شما دسترسی به پنل مدیریت ندارید.",
            "SEARCH_PROMPT": "لطفاً عبارت جستجو را وارد کنید:",
            "ERROR_MESSAGE": "خطایی رخ داد. لطفاً دوباره تلاش کنید."
        }
        os.makedirs("data", exist_ok=True)
        with open(DEFAULT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        shutil.copy(DEFAULT_CONFIG_PATH, CONFIG_PATH)    

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def reset_to_default():
    shutil.copy(DEFAULT_CONFIG_PATH, CONFIG_PATH)

config = load_config()
# Use get() to provide default values if keys don't exist
BOT_TOKEN = config.get("BOT_TOKEN", os.environ.get("BOT_TOKEN", ""))
ADMIN_ID = int(config.get("ADMIN_ID", "0"))
DB_TYPE = config.get("DB_TYPE", "postgresql")
DATA_DIR = config.get("DATA_DIR", "data")
DB_PATH = config.get("DB_PATH", os.path.join("data", "database.db"))
CSV_PATH = config.get("CSV_PATH", os.path.join("data", "initial_data.csv"))
PRODUCT_PREFIX = config.get("PRODUCT_PREFIX", "product_")
SERVICE_PREFIX = config.get("SERVICE_PREFIX", "service_")
CATEGORY_PREFIX = config.get("CATEGORY_PREFIX", "category_")
BACK_PREFIX = config.get("BACK_PREFIX", "back_")
INQUIRY_PREFIX = config.get("INQUIRY_PREFIX", "inquiry_")
EDUCATION_PREFIX = config.get("EDUCATION_PREFIX", "edu_")
ADMIN_PREFIX = config.get("ADMIN_PREFIX", "admin_")
PRODUCTS_BTN = config.get("PRODUCTS_BTN", "محصولات 🛍")
SERVICES_BTN = config.get("SERVICES_BTN", "خدمات 🔧")
INQUIRY_BTN = config.get("INQUIRY_BTN", "استعلام قیمت 💰")
EDUCATION_BTN = config.get("EDUCATION_BTN", "محتوای آموزشی 📚")
CONTACT_BTN = config.get("CONTACT_BTN", "تماس با ما ☎️")
ABOUT_BTN = config.get("ABOUT_BTN", "درباره ما ℹ️")
BACK_BTN = config.get("BACK_BTN", "بازگشت به منوی اصلی 🏠")
SEARCH_BTN = config.get("SEARCH_BTN", "جستجو 🔍")
ADMIN_BTN = config.get("ADMIN_BTN", "پنل مدیریت 👨‍💼")
START_TEXT = config.get("START_TEXT", "به ربات خوش آمدید!")
NOT_FOUND_TEXT = config.get("NOT_FOUND_TEXT", "موردی یافت نشد.")
CONTACT_DEFAULT = config.get("CONTACT_DEFAULT", "با ما از طریق شماره تماس در تماس باشید.")
ABOUT_DEFAULT = config.get("ABOUT_DEFAULT", "ربات محصولات و خدمات")
INQUIRY_START = config.get("INQUIRY_START", "لطفاً نام خود را وارد کنید:")
INQUIRY_PHONE = config.get("INQUIRY_PHONE", "لطفاً شماره تماس خود را وارد کنید:")
INQUIRY_DESC = config.get("INQUIRY_DESC", "لطفاً توضیحات بیشتر را وارد کنید:")
INQUIRY_COMPLETE = config.get("INQUIRY_COMPLETE", "استعلام شما با موفقیت ثبت شد.")
ADMIN_WELCOME = config.get("ADMIN_WELCOME", "به پنل مدیریت خوش آمدید.")
ADMIN_ACCESS_DENIED = config.get("ADMIN_ACCESS_DENIED", "شما دسترسی به پنل مدیریت ندارید.")
SEARCH_PROMPT = config.get("SEARCH_PROMPT", "لطفاً عبارت جستجو را وارد کنید:")
ERROR_MESSAGE = config.get("ERROR_MESSAGE", "خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)