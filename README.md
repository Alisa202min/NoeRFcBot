# RFCBot - ربات تلگرام و پنل مدیریت محصولات و خدمات رادیویی

سیستم جامع مدیریت محصولات و خدمات تجهیزات رادیویی بهمراه ربات تلگرام و پنل ادمین

## امکانات کلیدی

- ربات تلگرام با قابلیت‌های کامل نمایش محصولات و خدمات
- کاتالوگ محصولات با ساختار درختی ۴ سطحی
- امکان آپلود چندین عکس و ویدیو برای هر محصول/خدمت
- استفاده از file_id تلگرام برای ذخیره فایل‌ها (صرفه‌جویی در فضا)
- سیستم استعلام قیمت محصولات و خدمات
- بخش محتوای آموزشی با دسته‌بندی‌های مختلف
- مدیریت محتوای استاتیک (درباره‌ما، تماس‌با‌ما)
- پنل ادمین کامل با امکان مدیریت تمام اطلاعات
- جستجوی پیشرفته محصولات و خدمات
- پشتیبانی از زبان فارسی و چیدمان راست به چپ

## ساختار پروژه

### فایل‌های اصلی

- **bot.py** - ربات تلگرام
- **handlers.py** - توابع پردازش فرامین و پیام‌های ربات
- **keyboards.py** - دکمه‌ها و کیبوردهای ربات تلگرام
- **app.py** - پنل ادمین وب
- **models.py** - مدل‌های SQLAlchemy برای دیتابیس
- **configuration.py** - تنظیمات و پیکربندی سیستم
- **database.py** - لایه انتزاعی دسترسی به دیتابیس (کلاس Database)
- **utils.py** - توابع کمکی عمومی
- **utils_upload.py** - توابع کمکی آپلود فایل‌ها

### فایل‌های تست

- **comprehensive_test.py** - تست جامع سیستم
- **simple_test.py** - تست ساده مدل‌های دیتابیس
- **test_database.py** - تست اتصال و عملیات دیتابیس
- **test_telegram_inquiry.py** - تست سیستم استعلام قیمت
- **test_handlers.py** - تست توابع handlers ربات
- **test_telegram_bot.py** - تست اتوماتیک ربات تلگرام

### فایل‌های مهاجرت دیتابیس

- **db_migration.py** - مهاجرت اصلی ساختار دیتابیس
- **db_migration_media.py** - اضافه کردن جدول media
- **db_migration_inquiry.py** - اضافه کردن فیلد status به جدول inquiry
- **db_migration_educational_content.py** - اضافه کردن فیلد content_type به محتوای آموزشی
- **db_migration_static_content.py** - اضافه کردن فیلد content_type به محتوای استاتیک

## راه‌اندازی پروژه

### پیش‌نیازها

- پایتون 3.9 یا بالاتر
- PostgreSQL 14 یا بالاتر
- پکیج‌های مورد نیاز:
  - aiogram 3.7.0+
  - flask
  - sqlalchemy
  - flask-sqlalchemy
  - flask-login
  - psycopg2-binary
  - gunicorn

### مراحل راه‌اندازی

1. کلون کردن مخزن و نصب وابستگی‌ها:

```bash
git clone https://github.com/yourusername/RFCBot.git
cd RFCBot
pip install -e .
```

2. ایجاد فایل .env و تنظیم متغیرهای محیطی:

```
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://username:password@localhost:5432/dbname
```

3. اجرای مهاجرت‌های دیتابیس:

```bash
python db_migration.py
python db_migration_media.py
python db_migration_inquiry.py
python db_migration_educational_content.py
python db_migration_static_content.py
```

4. سیدکردن داده‌های اولیه:

```bash
python seed_database.py
python seed_admin_data.py
```

## اجرای پروژه

### راه‌اندازی ربات تلگرام

ربات را می‌توان در دو حالت اجرا کرد:

1. حالت polling (برای توسعه):

```bash
python bot.py
```

2. حالت webhook (برای محیط تولید):

```bash
python main.py
```

### راه‌اندازی پنل ادمین

برای اجرای پنل ادمین وب:

```bash
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

## اجرای تست‌ها

برای اجرای تست‌های جامع سیستم:

```bash
python comprehensive_test.py
```

برای اجرای تست‌های ساده دیتابیس:

```bash
python simple_test.py
```

برای اجرای تست‌های سیستم استعلام قیمت:

```bash
python test_telegram_inquiry.py
```

## نکات توسعه و استفاده

- امکان تغییر بین مدهای webhook و polling در ربات تلگرام وجود دارد
- برای پاک کردن تنظیمات webhook از اسکریپت delete_webhook.py استفاده کنید
- سیستم دارای تست‌های خودکار برای بررسی عملکرد صحیح است
- با استفاده از فایل utils_upload.py می‌توانید فایل‌های چندرسانه‌ای را مدیریت کنید
- مدیریت کامل استعلام‌های قیمت در بخش ادمین پنل امکان‌پذیر است
- استفاده از FSM (Finite State Machine) برای مدیریت گفتگوی کاربر با ربات
