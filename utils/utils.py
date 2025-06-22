
import os
import csv
from logging_config import get_logger
import aiohttp
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from werkzeug.utils import secure_filename
from aiogram import Bot, types
import traceback

logger = get_logger('bot')


def format_price(price: int) -> str:
    """
    قالب‌بندی قیمت با جداکننده هزارگان

    Args:
        price: قیمت به صورت عدد صحیح

    Returns:
        رشته قیمت قالب‌بندی‌شده
    """
    return f"{price:,} تومان"

def format_product_details(product: Dict, media_files: List[Dict] = None) -> str:
    """
    قالب‌بندی جزئیات محصول برای نمایش

    Args:
        product: دیکشنری محصول
        media_files: لیست فایل‌های رسانه (اختیاری)

    Returns:
        جزئیات محصول قالب‌بندی‌شده
    """
    name = product['name']
    price = format_price(product['price'])
    description = product['description'] or "توضیحات موجود نیست"

    result = f"📦 *{name}*\n\n💰 قیمت: {price}\n\n📝 توضیحات:\n{description}"

    # افزودن اطلاعات رسانه در صورت وجود
    if media_files and len(media_files) > 0:
        photo_count = sum(1 for m in media_files if m['file_type'] == 'photo')
        video_count = sum(1 for m in media_files if m['file_type'] == 'video')

        media_info = []
        if photo_count > 0:
            media_info.append(f"🖼 {photo_count} تصویر")
        if video_count > 0:
            media_info.append(f"🎬 {video_count} ویدیو")

        if media_info:
            result += "\n\n" + " | ".join(media_info)

    return result

def format_service_details(service: Dict, media_files: List[Dict] = None) -> str:
    """
    قالب‌بندی جزئیات سرویس برای نمایش

    Args:
        service: دیکشنری سرویس
        media_files: لیست فایل‌های رسانه (اختیاری)

    Returns:
        جزئیات سرویس قالب‌بندی‌شده
    """
    name = service['name']
    price = format_price(service['price']) if service['price'] is not None else "تماس بگیرید"
    description = service['description'] or "توضیحات موجود نیست"

    result = f"🔧 *{name}*\n\n💰 قیمت: {price}\n\n📝 توضیحات:\n{description}"

    # افزودن اطلاعات رسانه در صورت وجود
    if media_files and len(media_files) > 0:
        photo_count = sum(1 for m in media_files if m['file_type'] == 'photo')
        video_count = sum(1 for m in media_files if m['file_type'] == 'video')

        media_info = []
        if photo_count > 0:
            media_info.append(f"🖼 {photo_count} تصویر")
        if video_count > 0:
            media_info.append(f"🎬 {video_count} ویدیو")

        if media_info:
            result += "\n\n" + " | ".join(media_info)

    return result

def format_educational_content(content: Dict, media_files: List[Dict] = None) -> str:
    """
    قالب‌بندی محتوای آموزشی برای نمایش

    Args:
        content: دیکشنری محتوای آموزشی
        media_files: لیست فایل‌های رسانه (اختیاری)

    Returns:
        محتوای آموزشی قالب‌بندی‌شده
    """
    title = content['title']
    content_text = content['content'] or "محتوا موجود نیست"
    category = content['category'] or "بدون دسته‌بندی"

    result = f"📚 *{title}*\n\n📝 محتوا:\n{content_text}\n\n📂 دسته‌بندی: {category}"

    # افزودن اطلاعات رسانه در صورت وجود
    if media_files and len(media_files) > 0:
        photo_count = sum(1 for m in media_files if m['file_type'] == 'photo')
        video_count = sum(1 for m in media_files if m['file_type'] == 'video')

        media_info = []
        if photo_count > 0:
            media_info.append(f"🖼 {photo_count} تصویر")
        if video_count > 0:
            media_info.append(f"🎬 {video_count} ویدیو")

        if media_info:
            result += "\n\n" + " | ".join(media_info)

    return result

def format_inquiry_details(inquiry: Dict) -> str:
    """
    قالب‌بندی جزئیات استعلام برای نمایش

    Args:
        inquiry: دیکشنری استعلام

    Returns:
        جزئیات استعلام قالب‌بندی‌شده
    """
    # قالب‌بندی تاریخ
    date_str = inquiry['date']
    try:
        date_obj = datetime.fromisoformat(date_str)
        formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
    except:
        formatted_date = date_str

    # دریافت نام محصول/سرویس در صورت وجود
    is_service = inquiry.get('product_type') == 'service'
    item_prefix = "🔧 خدمت" if is_service else "🛍 محصول"
    item_info = f"\n{item_prefix}: {inquiry['product_name']}" if inquiry.get('product_name') else ""

    return (
        f"📝 *استعلام قیمت*\n\n"
        f"👤 نام: {inquiry['name']}\n"
        f"📞 شماره تماس: {inquiry['phone']}\n"
        f"📅 تاریخ: {formatted_date}{item_info}\n\n"
        f"توضیحات: {inquiry['description'] or 'بدون توضیحات'}"
    )

def is_valid_phone_number(phone: str) -> bool:
    """
    اعتبارسنجی فرمت شماره تلفن

    Args:
        phone: شماره تلفن برای اعتبارسنجی

    Returns:
        True اگر معتبر باشد، False در غیر این صورت
    """
    # اعتبارسنجی ساده: باید حداقل 10 رقم باشد
    digits = ''.join(filter(str.isdigit, phone))
    return len(digits) >= 10

def get_category_path(db, category_id: int) -> str:
    """
    دریافت مسیر کامل دسته‌بندی

    Args:
        db: نمونه پایگاه داده
        category_id: شناسه دسته‌بندی

    Returns:
        مسیر کامل دسته‌بندی (مثال: "تجهیزات الکترونیکی > سنسورها > سنسور دما")
    """
    path = []
    current_id = category_id

    while current_id is not None:
        category = db.get_category(current_id)
        if category:
            path.append(category['name'])
            current_id = category['parent_id']
        else:
            break

    # معکوس کردن برای ترتیب از بالا به پایین
    path.reverse()
    return " > ".join(path)

def create_sample_data(db) -> None:
    """
    ایجاد داده‌های نمونه برای راه‌اندازی اولیه

    Args:
        db: نمونه پایگاه داده
    """
    # ایجاد دسته‌بندی‌های محصول
    electronics_id = db.add_category("تجهیزات الکترونیکی", None, 'product')
    sensors_id = db.add_category("سنسورها", electronics_id, 'product')
    temp_sensors_id = db.add_category("سنسور دما", sensors_id, 'product')

    # ایجاد محصولات
    db.add_product(
        name="سنسور دما حرفه‌ای",
        price=500000,
        description="سنسور دمای دقیق با قابلیت اندازه‌گیری دما از -50 تا 150 درجه سانتیگراد",
        category_id=temp_sensors_id,
        photo_url="https://example.com/temp_sensor.jpg"
    )

    db.add_product(
        name="سنسور رطوبت",
        price=350000,
        description="سنسور رطوبت با دقت بالا",
        category_id=sensors_id,
        photo_url="https://example.com/humidity_sensor.jpg"
    )

    # ایجاد دسته‌بندی‌های سرویس
    services_id = db.add_category("خدمات فنی", None, 'service')
    repair_id = db.add_category("تعمیرات", services_id, 'service')

    # ایجاد سرویس‌ها
    db.add_product(
        name="تعمیر سنسور",
        price=200000,
        description="تعمیر انواع سنسورهای الکترونیکی",
        category_id=repair_id
    )

    # ایجاد محتوای آموزشی
    db.add_educational_content(
        title="اصول کار با سنسورها",
        content="در این مطلب با اصول کار با سنسورهای الکترونیکی آشنا می‌شوید.",
        category="آموزش سنسورها",
        content_type="text"
    )

    db.add_educational_content(
        title="ویدیوی آموزشی نصب سنسور",
        content="https://example.com/sensor_installation_video",
        category="آموزش سنسورها",
        content_type="link"
    )

def import_initial_data(db, csv_path: str = None) -> Tuple[int, int]:
    """
    وارد کردن داده‌های اولیه از فایل CSV

    Args:
        db: نمونه پایگاه داده
        csv_path: مسیر فایل CSV، یا None برای استفاده از پیش‌فرض

    Returns:
        تاپل (تعداد موفقیت‌ها، تعداد خطاها)
    """
    from config import CSV_PATH

    if csv_path is None:
        csv_path = CSV_PATH

    if not os.path.exists(csv_path):
        logger.warning(f"فایل CSV پیدا نشد: {csv_path}")
        return (0, 0)

    try:
        # تشخیص نوع موجودیت از CSV
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames

            if 'price' in headers:
                entity_type = 'products'
            elif 'parent_id' in headers:
                entity_type = 'categories'
            elif 'content' in headers:
                entity_type = 'educational'
            else:
                logger.error("فرمت CSV ناشناخته")
                return (0, 0)

        # وارد کردن داده‌ها
        return db.import_from_csv(entity_type, csv_path)
    except Exception as e:
        logger.error(f"خطا در وارد کردن داده‌ها از CSV: {e}")
        return (0, 0)

def generate_csv_template(output_path: str, entity_type: str) -> bool:
    """
    تولید فایل قالب CSV

    Args:
        output_path: مسیر ذخیره فایل CSV
        entity_type: نوع موجودیت (products/categories/educational)

    Returns:
        True اگر موفق، False در غیر این صورت
    """
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            if entity_type == 'products':
                fieldnames = ['name', 'price', 'description', 'photo_url', 'category_name']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                # افزودن ردیف نمونه
                writer.writerow({
                    'name': 'سنسور دما',
                    'price': '500000',
                    'description': 'سنسور دقیق برای دما',
                    'photo_url': 'https://example.com/photo1.jpg',
                    'category_name': 'سنسورها'
                })

            elif entity_type == 'categories':
                fieldnames = ['name', 'parent_name', 'type']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                # افزودن ردیف‌های نمونه
                writer.writerow({
                    'name': 'تجهیزات الکترونیکی',
                    'parent_name': '',
                    'type': 'product'
                })
                writer.writerow({
                    'name': 'سنسورها',
                    'parent_name': 'تجهیزات الکترونیکی',
                    'type': 'product'
                })

            elif entity_type == 'educational':
                fieldnames = ['title', 'content', 'category', 'type']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                # افزودن ردیف نمونه
                writer.writerow({
                    'title': 'اصول کار با سنسورها',
                    'content': 'در این مطلب با اصول کار با سنسورهای الکترونیکی آشنا می‌شوید.',
                    'category': 'آموزش سنسورها',
                    'type': 'text'
                })

        return True
    except Exception as e:
        logger.error(f"خطا در تولید قالب CSV: {e}")
        return False

async def create_telegraph_page(title: str, content: str, author: str = "RFCatalogbot") -> Optional[str]:
    """
    ایجاد صفحه تلگراف برای محتوای آموزشی طولانی

    Args:
        title: عنوان صفحه
        content: محتوای صفحه (می‌تواند شامل HTML ساده باشد)
        author: نام نویسنده (پیش‌فرض: "RFCatalogbot")

    Returns:
        URL صفحه ایجادشده، یا None در صورت شکست
    """
    try:
        # قالب‌بندی محتوا برای تلگراف (تبدیل به گره‌های HTML)
        html_content = []
        for paragraph in content.split('\n\n'):
            if paragraph.strip():
                html_content.append({
                    'tag': 'p',
                    'children': [paragraph.strip()]
                })

        # ایجاد حساب تلگراف برای دریافت توکن دسترسی
        create_account_url = 'https://api.telegra.ph/createAccount'
        account_data = {
            'short_name': author,
            'author_name': author
        }

        async with aiohttp.ClientSession() as session:
            # مرحله 1: ایجاد حساب و دریافت توکن دسترسی
            async with session.post(create_account_url, data=account_data) as response:
                if response.status == 200:
                    account_result = await response.json()
                    if not account_result.get('ok'):
                        logger.error(f"خطای API تلگراف در ایجاد حساب: {account_result}")
                        return None

                    access_token = account_result.get('result', {}).get('access_token')
                    if not access_token:
                        logger.error("هیچ توکن دسترسی از API تلگراف دریافت نشد")
                        return None

                    # مرحله 2: ایجاد صفحه با استفاده از توکن دسترسی
                    create_page_url = 'https://api.telegra.ph/createPage'

                    # تولید مسیر از عنوان (slugify ساده)
                    import re
                    path = re.sub(r'[^\w\s-]', '', title.lower())
                    path = re.sub(r'[\s_-]+', '-', path)

                    # آماده‌سازی داده‌های ایجاد صفحه
                    page_data = {
                        'access_token': access_token,
                        'title': title,
                        'author_name': author,
                        'content': json.dumps(html_content),
                        'return_content': False
                    }

                    # ایجاد صفحه
                    async with session.post(create_page_url, data=page_data) as page_response:
                        if page_response.status == 200:
                            page_result = await page_response.json()
                            if page_result.get('ok'):
                                page_url = page_result.get('result', {}).get('url')
                                if page_url:
                                    logger.info(f"صفحه تلگراف ایجاد شد: {page_url}")
                                    return page_url

                            logger.error(f"خطای API تلگراف در ایجاد صفحه: {page_result}")
                        else:
                            logger.error(f"خطای HTTP API تلگراف: {page_response.status}")
                else:
                    logger.error(f"خطای HTTP API تلگراف در ایجاد حساب: {response.status}")

        return None
    except Exception as e:
        logger.error(f"خطا در ایجاد صفحه تلگراف: {str(e)}")
        return None

def allowed_file(filename):
    """
    بررسی مجاز بودن پسوند فایل

    Args:
        filename: نام فایل

    Returns:
        bool: آیا فایل مجاز است
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, upload_dir):
    """
    ذخیره فایل آپلودشده

    Args:
        file: فایل آپلودشده
        upload_dir: دایرکتوری مقصد

    Returns:
        str: مسیر فایل ذخیره‌شده یا None
    """
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        return file_path
    return None

def create_directory(directory):
    """
    ایجاد دایرکتوری

    Args:
        directory: مسیر دایرکتوری
    """
    os.makedirs(directory, exist_ok=True)

async def upload_file_to_telegram(file_path: str, bot: Bot, file_type: str = 'photo') -> str:
    """
    آپلود فایل به تلگرام

    Args:
        file_path: مسیر فایل
        bot: نمونه بات تلگرام
        file_type: نوع فایل ('photo' یا 'video')، پیش‌فرض: 'photo'

    Returns:
        str: شناسه فایل یا None در صورت شکست
    """
    logger.debug(f"آپلود فایل به تلگرام: {file_path}، نوع: {file_type}")
    try:
        with open(file_path, 'rb') as file:
            if file_type == 'video':
                response = await bot.send_video(chat_id=bot.id, video=file)
                return response.video.file_id
            else:
                response = await bot.send_photo(chat_id=bot.id, photo=file)
                return response.photo[-1].file_id
    except Exception as e:
        logger.error(f"خطا در آپلود فایل {file_path}: {str(e)}\n{traceback.format_exc()}")
        return None
