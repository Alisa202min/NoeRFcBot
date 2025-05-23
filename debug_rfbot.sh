#!/bin/bash

# ===== اسکریپت عیب‌یابی نصب RFCBot =====
# این اسکریپت مشکلات مربوط به راه‌اندازی پایگاه داده RFCBot را تحلیل می‌کند
# اجرا: sudo bash debug_rfbot.sh

# ===== تنظیمات رنگ‌ها =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ===== مسیرها و فایل‌ها =====
APP_DIR="/var/www/rfbot"
LOG_FILE="/tmp/rfbot_debug_$(date +%Y%m%d_%H%M%S).log"
ENV_FILE="$APP_DIR/.env"
INIT_DB_FILE="$APP_DIR/init_db.py"
APP_PY_FILE="$APP_DIR/app.py"
LATEST_INSTALL_LOG=$(ls -t /tmp/rfbot_install_*.log 2>/dev/null | head -n 1)

# ===== توابع کمکی =====
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# تابع بررسی خطا
check_error() {
    if [ $? -ne 0 ]; then
        print_error "$1"
        return 1
    else
        print_success "$2"
        return 0
    fi
}

# ===== بررسی دسترسی روت =====
if [ "$EUID" -ne 0 ]; then
    print_error "این اسکریپت نیاز به دسترسی روت دارد. لطفاً با sudo اجرا کنید."
    exit 1
fi

# ===== شروع عیب‌یابی =====
clear
echo "========================================================"
echo "        عیب‌یابی نصب سیستم رادیو فرکانس"
echo "========================================================"
echo ""
print_message "فایل لاگ عیب‌یابی در $LOG_FILE ذخیره می‌شود."
echo ""

# ===== 1. بررسی وجود پوشه پروژه =====
print_message "بررسی وجود پوشه پروژه در $APP_DIR..."
if [ ! -d "$APP_DIR" ]; then
    print_error "پوشه $APP_DIR وجود ندارد. لطفاً مطمئن شوید پروژه نصب شده است."
    exit 1
fi
print_success "پوشه پروژه یافت شد."

# ===== 2. بررسی فایل .env =====
print_message "بررسی فایل .env در $ENV_FILE..."
if [ ! -f "$ENV_FILE" ]; then
    print_error "فایل .env یافت نشد. لطفاً اسکریپت نصب را دوباره اجرا کنید."
    exit 1
fi

print_message "چک کردن متغیرهای ضروری در .env..."
DB_URL=$(grep '^DATABASE_URL=' "$ENV_FILE" | cut -d'=' -f2-)
SQLALCHEMY_URI=$(grep '^SQLALCHEMY_DATABASE_URI=' "$ENV_FILE" | cut -d'=' -f2-)
if [ -z "$DB_URL" ] || [ -z "$SQLALCHEMY_URI" ]; then
    print_error "متغیرهای DATABASE_URL یا SQLALCHEMY_DATABASE_URI در $ENV_FILE تنظیم نشده‌اند."
    echo "محتوای فعلی .env:" >> "$LOG_FILE"
    cat "$ENV_FILE" >> "$LOG_FILE" 2>&1
    exit 1
fi
print_success "متغیرهای DATABASE_URL و SQLALCHEMY_DATABASE_URI یافت شدند."

# استخراج اطلاعات دیتابیس
DB_USER=$(echo "$DB_URL" | sed -E 's|postgresql://([^:]+):.*@.*|\1|')
DB_PASS=$(echo "$DB_URL" | sed -E 's|postgresql://[^:]+:([^@]+)@.*|\1|')
DB_NAME=$(echo "$DB_URL" | sed -E 's|postgresql://.*@.*/(.*)|\1|')
print_message "اطلاعات دیتابیس: کاربر=$DB_USER، دیتابیس=$DB_NAME"

# ===== 3. بررسی وضعیت PostgreSQL =====
print_message "بررسی وضعیت سرویس PostgreSQL..."
systemctl status postgresql >> "$LOG_FILE" 2>&1
if systemctl is-active postgresql >/dev/null; then
    print_success "سرویس PostgreSQL در حال اجرا است."
else
    print_error "سرویس PostgreSQL اجرا نمی‌شود. تلاش برای راه‌اندازی..."
    systemctl start postgresql >> "$LOG_FILE" 2>&1
    check_error "راه‌اندازی PostgreSQL با خطا مواجه شد." "PostgreSQL با موفقیت راه‌اندازی شد."
fi

# ===== 4. تست اتصال به دیتابیس =====
print_message "تست اتصال به دیتابیس $DB_NAME با کاربر $DB_USER..."
export PGPASSWORD="$DB_PASS"
psql -U "$DB_USER" -d "$DB_NAME" -h localhost -c "\dt" >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    print_error "اتصال به دیتابیس با خطا مواجه شد. جزئیات در $LOG_FILE."
    print_message "تلاش برای بازسازی کاربر و دیتابیس..."
    su -c "psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';\"" postgres >> "$LOG_FILE" 2>&1 || true
    su -c "psql -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\"" postgres >> "$LOG_FILE" 2>&1 || true
    su -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\"" postgres >> "$LOG_FILE" 2>&1
    psql -U "$DB_USER" -d "$DB_NAME" -h localhost -c "\dt" >> "$LOG_FILE" 2>&1
    check_error "بازسازی دیتابیس با خطا مواجه شد." "دیتابیس با موفقیت بازسازی شد."
else
    print_success "اتصال به دیتابیس موفق بود."
fi
unset PGPASSWORD

# ===== 5. بررسی فایل app.py =====
print_message "بررسی تنظیمات Flask-SQLAlchemy در $APP_PY_FILE..."
if [ ! -f "$APP_PY_FILE" ]; then
    print_error "فایل $APP_PY_FILE یافت نشد."
    exit 1
fi

LOAD_DOTENV=$(grep -n "load_dotenv()" "$APP_PY_FILE" | head -n 1)
SQLALCHEMY_CONFIG=$(grep -n "app.config.*SQLALCHEMY_DATABASE_URI" "$APP_PY_FILE" | head -n 1)
DB_INIT=$(grep -n "db.init_app(app)" "$APP_PY_FILE" | head -n 1)

if [ -z "$LOAD_DOTENV" ]; then
    print_warning "load_dotenv() در $APP_PY_FILE یافت نشد. لطفاً اضافه کنید:"
    print_message "  from dotenv import load_dotenv"
    print_message "  load_dotenv()"
fi
if [ -z "$SQLALCHEMY_CONFIG" ]; then
    print_error "تنظیم SQLALCHEMY_DATABASE_URI در $APP_PY_FILE یافت نشد. لطفاً اضافه کنید:"
    print_message "  app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')"
    exit 1
fi
if [ -z "$DB_INIT" ]; then
    print_error "db.init_app(app) در $APP_PY_FILE یافت نشد."
    exit 1
fi
print_success "تنظیمات اولیه Flask-SQLAlchemy در $APP_PY_FILE یافت شد."

# بررسی ترتیب تنظیمات
LOAD_DOTENV_LINE=$(echo "$LOAD_DOTENV" | cut -d: -f1)
SQLALCHEMY_LINE=$(echo "$SQLALCHEMY_CONFIG" | cut -d: -f1)
DB_INIT_LINE=$(echo "$DB_INIT" | cut -d: -f1)
if [ -n "$LOAD_DOTENV_LINE" ] && [ -n "$SQLALCHEMY_LINE" ] && [ -n "$DB_INIT_LINE" ]; then
    if [ "$LOAD_DOTENV_LINE" -gt "$SQLALCHEMY_LINE" ] || [ "$SQLALCHEMY_LINE" -gt "$DB_INIT_LINE" ]; then
        print_warning "ترتیب تنظیمات در $APP_PY_FILE نادرست است. باید به این صورت باشد:"
        print_message "  1) load_dotenv()"
        print_message "  2) app.config['SQLALCHEMY_DATABASE_URI']"
        print_message "  3) db.init_app(app)"
    fi
fi

# ===== 6. بررسی پکیج‌ها =====
print_message "بررسی پکیج‌های نصب‌شده در محیط مجازی..."
if [ ! -d "$APP_DIR/venv" ]; then
    print_error "محیط مجازی در $APP_DIR/venv یافت نشد."
    exit 1
fi
source "$APP_DIR/venv/bin/activate" >> "$LOG_FILE" 2>&1
check_error "فعال‌سازی محیط مجازی با خطا مواجه شد." "محیط مجازی فعال شد."

print_message "لیست پکیج‌ها:"
pip list >> "$LOG_FILE" 2>&1
REQUIRED_PACKAGES=("Flask-SQLAlchemy" "psycopg2-binary" "python-dotenv")
for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! pip show "$pkg" >/dev/null 2>&1; then
        print_warning "$pkg نصب نیست. نصب آن..."
        pip install "$pkg" >> "$LOG_FILE" 2>&1
        check_error "نصب $pkg با خطا مواجه شد." "$pkg با موفقیت نصب شد."
    fi
done
print_success "همه پکیج‌های ضروری نصب هستند."
deactivate >> "$LOG_FILE" 2>&1

# ===== 7. اجرای init_db.py =====
print_message "اجرای $INIT_DB_FILE برای ایجاد جداول..."
if [ ! -f "$INIT_DB_FILE" ]; then
    print_message "فایل $INIT_DB_FILE یافت نشد. ایجاد آن..."
    cat << EOF > "$INIT_DB_FILE"
from dotenv import load_dotenv
import os
import logging
from app import app, db
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
load_dotenv()
logger.debug("SQLALCHEMY_DATABASE_URI: %s", os.getenv('SQLALCHEMY_DATABASE_URI'))
with app.app_context():
    logger.debug("Creating database tables...")
    db.create_all()
    logger.debug("Database tables created successfully.")
EOF
fi

source "$APP_DIR/venv/bin/activate" >> "$LOG_FILE" 2>&1
python "$INIT_DB_FILE" >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    print_error "اجرای $INIT_DB_FILE با خطا مواجه شد. جزئیات در $LOG_FILE."
else
    print_success "جداول پایگاه داده با موفقیت ایجاد شدند."
fi
deactivate >> "$LOG_FILE" 2>&1

# ===== 8. بررسی جداول دیتابیس =====
print_message "بررسی جداول موجود در دیتابیس..."
export PGPASSWORD="$DB_PASS"
psql -U "$DB_USER" -d "$DB_NAME" -h localhost -c "\dt" >> "$LOG_FILE" 2>&1
check_error "بررسی جداول با خطا مواجه شد." "جداول بررسی شدند."
unset PGPASSWORD

# ===== 9. بررسی لاگ نصب قبلی =====
if [ -n "$LATEST_INSTALL_LOG" ] && [ -f "$LATEST_INSTALL_LOG" ]; then
    print_message "بررسی آخرین لاگ نصب ($LATEST_INSTALL_LOG)..."
    echo "آخرین خطاهای لاگ نصب:" >> "$LOG_FILE"
    grep -i "error" "$LATEST_INSTALL_LOG" >> "$LOG_FILE" 2>&1
    echo "آخرین 20 خط لاگ:" >> "$LOG_FILE"
    tail -n 20 "$LATEST_INSTALL_LOG" >> "$LOG_FILE" 2>&1
else
    print_warning "لاگ نصب قبلی یافت نشد."
fi

# ===== 10. تولید گزارش نهایی =====
print_message "تولید گزارش نهایی..."
echo "" >> "$LOG_FILE"
echo "===== گزارش عیب‌یابی RFCBot =====" >> "$LOG_FILE"
echo "تاریخ و زمان: $(date)" >> "$LOG_FILE"
echo "وضعیت پروژه:" >> "$LOG_FILE"
[ -d "$APP_DIR" ] && echo "  - پوشه پروژه: موجود" >> "$LOG_FILE" || echo "  - پوشه پروژه: غایب" >> "$LOG_FILE"
[ -f "$ENV_FILE" ] && echo "  - فایل .env: موجود" >> "$LOG_FILE" || echo "  - فایل .env: غایب" >> "$LOG_FILE"
[ -f "$APP_PY_FILE" ] && echo "  - فایل app.py: موجود" >> "$LOG_FILE" || echo "  - فایل app.py: غایب" >> "$LOG_FILE"
echo "وضعیت PostgreSQL:" >> "$LOG_FILE"
systemctl is-active postgresql >/dev/null && echo "  - سرویس: در حال اجرا" >> "$LOG_FILE" || echo "  - سرویس: متوقف" >> "$LOG_FILE"
echo "اتصال دیتابیس:" >> "$LOG_FILE"
export PGPASSWORD="$DB_PASS"
psql -U "$DB_USER" -d "$DB_NAME" -h localhost -c "\dt" >/dev/null 2>&1 && echo "  - اتصال: موفق" >> "$LOG_FILE" || echo "  - اتصال: ناموفق" >> "$LOG_FILE"
unset PGPASSWORD
echo "پیشنهادات:" >> "$LOG_FILE"
echo "  1) فایل $LOG_FILE را برای جزئیات بررسی کنید." >> "$LOG_FILE"
echo "  2) اگر اتصال دیتابیس ناموفق است، رمز عبور و دسترسی‌های کاربر $DB_USER را بررسی کنید." >> "$LOG_FILE"
echo "  3) اگر app.py مشکل دارد، تنظیمات load_dotenv و SQLALCHEMY_DATABASE_URI را چک کنید." >> "$LOG_FILE"
echo "  4) برای پشتیبانی، لاگ $LOG_FILE و $LATEST_INSTALL_LOG را به اشتراک بگذارید." >> "$LOG_FILE"

# ===== نمایش گزارش =====
echo ""
echo "================== عیب‌یابی کامل شد =================="
echo ""
print_message "گزارش کامل در $LOG_FILE ذخیره شد."
print_message "لطفاً فایل لاگ را بررسی کنید و پیشنهادات را دنبال کنید."
print_message "دستورات پیشنهادی بعدی:"
print_message "  cat $LOG_FILE"
print_message "  cat $LATEST_INSTALL_LOG"
echo ""

exit 0
