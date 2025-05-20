#!/bin/bash

# ===== رادیو فرکانس - اسکریپت نصب خودکار =====
# نویسنده: تیم رادیو فرکانس
# تاریخ: تیر 1404
# توضیحات: این اسکریپت به طور خودکار پنل وب و بات تلگرام رادیو فرکانس را روی اوبونتو 24.04 نصب می‌کند

# ===== تنظیمات =====
# رنگ‌ها برای خروجی زیباتر
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # بدون رنگ

# مسیر لاگ
LOG_FILE="/tmp/rfbot_install_$(date +%Y%m%d_%H%M%S).log"

# ===== توابع =====
# تابع لاگ کردن
log() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo -e "${timestamp} - $1" | tee -a "$LOG_FILE"
}

# تابع نمایش عنوان
print_header() {
    echo -e "\n${BOLD}${CYAN}$1${NC}" | tee -a "$LOG_FILE"
    echo -e "${CYAN}$(printf '=%.0s' {1..50})${NC}" | tee -a "$LOG_FILE"
}

# تابع نمایش اطلاعات
print_info() {
    echo -e "${BLUE}[اطلاعات]${NC} $1" | tee -a "$LOG_FILE"
}

# تابع نمایش موفقیت
print_success() {
    echo -e "${GREEN}[موفق]${NC} $1" | tee -a "$LOG_FILE"
}

# تابع نمایش هشدار
print_warning() {
    echo -e "${YELLOW}[هشدار]${NC} $1" | tee -a "$LOG_FILE"
}

# تابع نمایش خطا
print_error() {
    echo -e "${RED}[خطا]${NC} $1" | tee -a "$LOG_FILE"
}

# تابع بررسی خطا
check_error() {
    if [ $? -ne 0 ]; then
        print_error "$1"
        exit 1
    else
        print_success "$2"
    fi
}

# تابع بررسی نصب بودن یک پکیج
is_installed() {
    if dpkg -l "$1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# ===== شروع اسکریپت =====
clear
print_header "اسکریپت نصب خودکار رادیو فرکانس"
log "شروع اسکریپت نصب"

print_info "فایل لاگ در مسیر $LOG_FILE ذخیره می‌شود"

# بررسی دسترسی روت
if [ "$EUID" -ne 0 ]; then
    print_error "این اسکریپت نیاز به دسترسی روت دارد. لطفاً با دستور sudo اجرا کنید."
    exit 1
fi

# بررسی نسخه اوبونتو
print_info "در حال بررسی نسخه سیستم عامل..."
if grep -q "Ubuntu 24.04" /etc/os-release; then
    print_success "اوبونتو 24.04 تشخیص داده شد."
else
    print_warning "اوبونتو 24.04 شناسایی نشد. ممکن است با نسخه‌های دیگر مشکلاتی وجود داشته باشد."
    sleep 2
fi

# ===== خواندن ورودی‌های کاربر =====
print_header "تنظیمات نصب"

# دریافت اطلاعات
read -p "نام کاربری پایگاه داده [rfuser]: " DB_USER
DB_USER=${DB_USER:-rfuser}

read -s -p "رمز عبور پایگاه داده: " DB_PASSWORD
echo
if [ -z "$DB_PASSWORD" ]; then
    print_error "رمز عبور پایگاه داده نمی‌تواند خالی باشد."
    exit 1
fi

read -p "نام پایگاه داده [rfdb]: " DB_NAME
DB_NAME=${DB_NAME:-rfdb}

read -p "توکن بات تلگرام: " BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then
    print_error "توکن بات تلگرام نمی‌تواند خالی باشد."
    exit 1
fi

read -p "حالت بات تلگرام (webhook یا polling) [polling]: " BOT_MODE
BOT_MODE=${BOT_MODE:-polling}

if [ "$BOT_MODE" = "webhook" ]; then
    read -p "دامنه برای webhook (مثال: https://example.com): " WEBHOOK_HOST
    if [ -z "$WEBHOOK_HOST" ]; then
        print_error "برای حالت webhook، دامنه ضروری است."
        exit 1
    fi
fi

read -p "آیا گواهی SSL نصب شود؟ (y/n) [y]: " INSTALL_SSL
INSTALL_SSL=${INSTALL_SSL:-y}

read -p "نام کاربری ادمین [admin]: " ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

read -s -p "رمز عبور ادمین: " ADMIN_PASSWORD
echo
if [ -z "$ADMIN_PASSWORD" ]; then
    print_error "رمز عبور ادمین نمی‌تواند خالی باشد."
    exit 1
fi

# تأیید اطلاعات
print_header "خلاصه تنظیمات"
print_info "کاربر پایگاه داده: $DB_USER"
print_info "نام پایگاه داده: $DB_NAME"
print_info "حالت بات تلگرام: $BOT_MODE"
if [ "$BOT_MODE" = "webhook" ]; then
    print_info "دامنه webhook: $WEBHOOK_HOST"
fi
print_info "نصب SSL: $INSTALL_SSL"
print_info "نام کاربری ادمین: $ADMIN_USERNAME"

read -p "آیا تنظیمات فوق صحیح است؟ (y/n) [y]: " CONFIRM
CONFIRM=${CONFIRM:-y}
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    print_error "نصب لغو شد."
    exit 1
fi

# ===== به‌روزرسانی سیستم =====
print_header "به‌روزرسانی سیستم"
print_info "در حال به‌روزرسانی لیست بسته‌ها..."
apt update >> "$LOG_FILE" 2>&1
check_error "به‌روزرسانی لیست بسته‌ها با خطا مواجه شد." "لیست بسته‌ها با موفقیت به‌روزرسانی شد."

print_info "در حال به‌روزرسانی بسته‌های نصب شده..."
apt upgrade -y >> "$LOG_FILE" 2>&1
check_error "به‌روزرسانی بسته‌ها با خطا مواجه شد." "بسته‌ها با موفقیت به‌روزرسانی شدند."

# ===== نصب بسته‌های مورد نیاز =====
print_header "نصب بسته‌های مورد نیاز"
print_info "در حال نصب بسته‌های ضروری..."

PACKAGES=(
    "python3"
    "python3-pip"
    "python3-venv"
    "postgresql"
    "postgresql-contrib"
    "nginx"
    "git"
    "curl"
)

for package in "${PACKAGES[@]}"; do
    if is_installed "$package"; then
        print_info "$package قبلاً نصب شده است."
    else
        print_info "در حال نصب $package..."
        apt install -y "$package" >> "$LOG_FILE" 2>&1
        check_error "نصب $package با خطا مواجه شد." "$package با موفقیت نصب شد."
    fi
done

# ===== راه‌اندازی پایگاه داده =====
print_header "راه‌اندازی پایگاه داده PostgreSQL"
print_info "در حال بررسی سرویس PostgreSQL..."

# اطمینان از روشن بودن سرویس PostgreSQL
systemctl start postgresql >> "$LOG_FILE" 2>&1
systemctl enable postgresql >> "$LOG_FILE" 2>&1
check_error "راه‌اندازی PostgreSQL با خطا مواجه شد." "PostgreSQL با موفقیت راه‌اندازی شد."

print_info "در حال ایجاد کاربر و پایگاه داده..."
# ایجاد کاربر و پایگاه داده به صورت ایمن
su - postgres -c "psql -v ON_ERROR_STOP=1 -c \"DO \\\$\\\$ BEGIN CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD'; EXCEPTION WHEN DUPLICATE_OBJECT THEN RAISE NOTICE 'User already exists'; END \\\$\\\$;\"" >> "$LOG_FILE" 2>&1
check_error "ایجاد کاربر پایگاه داده با خطا مواجه شد." "کاربر پایگاه داده با موفقیت ایجاد شد."

su - postgres -c "psql -v ON_ERROR_STOP=1 -c \"SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec\"" >> "$LOG_FILE" 2>&1
check_error "ایجاد پایگاه داده با خطا مواجه شد." "پایگاه داده با موفقیت ایجاد شد."

su - postgres -c "psql -v ON_ERROR_STOP=1 -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\"" >> "$LOG_FILE" 2>&1
check_error "اعطای دسترسی‌های پایگاه داده با خطا مواجه شد." "دسترسی‌های پایگاه داده با موفقیت اعطا شد."

# ===== کلون و راه‌اندازی پروژه =====
print_header "راه‌اندازی برنامه رادیو فرکانس"
APP_DIR="/var/www/rfbot"
print_info "در حال راه‌اندازی پوشه‌های برنامه در $APP_DIR..."

# ایجاد پوشه‌های لازم
mkdir -p "$APP_DIR" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/static/uploads/products" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/static/uploads/services" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/static/uploads/services/main" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/static/media/products" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/logs" >> "$LOG_FILE" 2>&1
check_error "ایجاد پوشه‌های برنامه با خطا مواجه شد." "پوشه‌های برنامه با موفقیت ایجاد شدند."

# آیا از گیت استفاده می‌کنیم یا فایل‌ها را کپی می‌کنیم؟
read -p "آیا می‌خواهید پروژه را از مخزن گیت دانلود کنید؟ (y/n) [n]: " USE_GIT
USE_GIT=${USE_GIT:-n}

if [ "$USE_GIT" = "y" ] || [ "$USE_GIT" = "Y" ]; then
    print_info "لطفاً آدرس مخزن گیت را وارد کنید:"
    read GIT_REPO
    print_info "در حال کلون کردن مخزن $GIT_REPO..."
    git clone "$GIT_REPO" "$APP_DIR" >> "$LOG_FILE" 2>&1
    check_error "کلون کردن مخزن گیت با خطا مواجه شد." "مخزن گیت با موفقیت کلون شد."
else
    print_info "لطفاً فایل‌های پروژه را به پوشه $APP_DIR منتقل کنید و سپس کلید Enter را فشار دهید."
    read -p "آیا فایل‌های پروژه را به پوشه $APP_DIR منتقل کرده‌اید؟ (y/n) [n]: " FILES_COPIED
    FILES_COPIED=${FILES_COPIED:-n}
    
    if [ "$FILES_COPIED" != "y" ] && [ "$FILES_COPIED" != "Y" ]; then
        print_error "لطفاً ابتدا فایل‌های پروژه را منتقل کنید و سپس اسکریپت را دوباره اجرا نمایید."
        exit 1
    fi
fi

# ===== ایجاد محیط مجازی پایتون =====
print_info "در حال ایجاد محیط مجازی پایتون..."
cd "$APP_DIR" || exit 1
python3 -m venv venv >> "$LOG_FILE" 2>&1
check_error "ایجاد محیط مجازی با خطا مواجه شد." "محیط مجازی با موفقیت ایجاد شد."

print_info "در حال نصب وابستگی‌ها..."
# فعال‌سازی محیط مجازی
source "$APP_DIR/venv/bin/activate"

if [ -f "$APP_DIR/requirements.txt" ]; then
    pip install -r requirements.txt >> "$LOG_FILE" 2>&1
    check_error "نصب وابستگی‌ها با خطا مواجه شد." "وابستگی‌ها با موفقیت نصب شدند."
else
    print_info "فایل requirements.txt پیدا نشد. در حال نصب وابستگی‌های اصلی..."
    pip install flask flask-sqlalchemy aiogram python-dotenv gunicorn psycopg2-binary pillow flask-login flask-wtf email_validator >> "$LOG_FILE" 2>&1
    check_error "نصب وابستگی‌ها با خطا مواجه شد." "وابستگی‌های اصلی با موفقیت نصب شدند."
fi

# ===== ایجاد فایل‌های تنظیمات =====
print_header "ایجاد فایل‌های تنظیمات"
print_info "در حال ایجاد فایل .env..."

# ایجاد یک کلید تصادفی برای SESSION_SECRET
SESSION_SECRET=$(openssl rand -hex 32)

# تنظیم مسیر webhook اگر از webhook استفاده می‌شود
WEBHOOK_PATH="/webhook/telegram"
WEBHOOK_URL=""
if [ "$BOT_MODE" = "webhook" ]; then
    WEBHOOK_URL="${WEBHOOK_HOST}${WEBHOOK_PATH}"
fi

# ایجاد فایل .env
cat > "$APP_DIR/.env" << EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
SESSION_SECRET=$SESSION_SECRET
BOT_TOKEN=$BOT_TOKEN
BOT_MODE=$BOT_MODE
WEBHOOK_HOST=$WEBHOOK_HOST
WEBHOOK_PATH=$WEBHOOK_PATH
WEBHOOK_URL=$WEBHOOK_URL
ADMIN_USERNAME=$ADMIN_USERNAME
ADMIN_PASSWORD=$ADMIN_PASSWORD
UPLOAD_FOLDER=$APP_DIR/static/uploads
EOF

check_error "ایجاد فایل .env با خطا مواجه شد." "فایل .env با موفقیت ایجاد شد."

# ===== راه‌اندازی پایگاه داده =====
print_header "راه‌اندازی جداول پایگاه داده"
print_info "در حال ایجاد جداول پایگاه داده..."

# فعال‌سازی محیط مجازی اگر فعال نیست
if ! command -v python | grep -q "$APP_DIR/venv" 2>/dev/null; then
    source "$APP_DIR/venv/bin/activate"
fi

# بررسی می‌کنیم که آیا فایل اصلی وجود دارد
if [ -f "$APP_DIR/app.py" ]; then
    python -c "from app import db; db.create_all()" >> "$LOG_FILE" 2>&1
    check_error "ایجاد جداول پایگاه داده با خطا مواجه شد." "جداول پایگاه داده با موفقیت ایجاد شدند."
elif [ -f "$APP_DIR/src/web/app.py" ]; then
    # اگر از ساختار ماژولار استفاده می‌شود
    export PYTHONPATH="$APP_DIR"
    python -c "from src.web.app import db; db.create_all()" >> "$LOG_FILE" 2>&1
    check_error "ایجاد جداول پایگاه داده با خطا مواجه شد." "جداول پایگاه داده با موفقیت ایجاد شدند."
else
    print_warning "فایل app.py پیدا نشد. لطفاً به صورت دستی جداول پایگاه داده را ایجاد کنید."
fi

# اجرای اسکریپت‌های تنظیمات اولیه
print_info "در حال اجرای اسکریپت‌های تنظیمات اولیه..."

# اسکریپت سید ادمین
if [ -f "$APP_DIR/seed_admin_data.py" ]; then
    python "$APP_DIR/seed_admin_data.py" >> "$LOG_FILE" 2>&1
    print_info "اسکریپت seed_admin_data.py اجرا شد."
fi

# اسکریپت سید دسته‌ها
if [ -f "$APP_DIR/seed_categories.py" ]; then
    python "$APP_DIR/seed_categories.py" >> "$LOG_FILE" 2>&1
    print_info "اسکریپت seed_categories.py اجرا شد."
fi

# ===== ایجاد سرویس‌ها =====
print_header "ایجاد سرویس‌های سیستمی"
print_info "در حال ایجاد سرویس پنل وب..."

# سرویس وب
cat > /etc/systemd/system/rfbot-web.service << EOF
[Unit]
Description=Gunicorn instance to serve RF Web Panel
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 --timeout 120 main:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

check_error "ایجاد سرویس وب با خطا مواجه شد." "سرویس وب با موفقیت ایجاد شد."

print_info "در حال ایجاد سرویس بات تلگرام..."

# سرویس بات تلگرام
cat > /etc/systemd/system/rfbot-telegram.service << EOF
[Unit]
Description=RF Telegram Bot
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

check_error "ایجاد سرویس بات تلگرام با خطا مواجه شد." "سرویس بات تلگرام با موفقیت ایجاد شد."

# ===== پیکربندی Nginx =====
print_header "پیکربندی Nginx"
print_info "در حال ایجاد پیکربندی Nginx..."

SERVER_NAME=${WEBHOOK_HOST#*//}
SERVER_NAME=${SERVER_NAME%%/*}

# پیکربندی Nginx
cat > /etc/nginx/sites-available/rfbot << EOF
server {
    listen 80;
    server_name $SERVER_NAME;

    client_max_body_size 20M;

    location /static {
        alias $APP_DIR/static;
    }

    location $WEBHOOK_PATH {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

check_error "ایجاد پیکربندی Nginx با خطا مواجه شد." "پیکربندی Nginx با موفقیت ایجاد شد."

print_info "در حال فعال کردن پیکربندی Nginx..."
ln -sf /etc/nginx/sites-available/rfbot /etc/nginx/sites-enabled/ >> "$LOG_FILE" 2>&1
nginx -t >> "$LOG_FILE" 2>&1
check_error "تست پیکربندی Nginx با خطا مواجه شد." "پیکربندی Nginx با موفقیت تست شد."

# ===== تنظیم دسترسی‌ها =====
print_header "تنظیم دسترسی‌ها"
print_info "در حال تنظیم مالکیت فایل‌ها..."

chown -R www-data:www-data "$APP_DIR" >> "$LOG_FILE" 2>&1
check_error "تنظیم مالکیت فایل‌ها با خطا مواجه شد." "مالکیت فایل‌ها با موفقیت تنظیم شد."

# ===== نصب SSL (اختیاری) =====
if [ "$INSTALL_SSL" = "y" ] || [ "$INSTALL_SSL" = "Y" ]; then
    print_header "نصب گواهی SSL"
    print_info "در حال نصب Certbot..."
    
    apt install -y certbot python3-certbot-nginx >> "$LOG_FILE" 2>&1
    check_error "نصب Certbot با خطا مواجه شد." "Certbot با موفقیت نصب شد."
    
    print_info "در حال دریافت گواهی SSL..."
    certbot --nginx -d "$SERVER_NAME" --non-interactive --agree-tos --email "admin@$SERVER_NAME" --redirect >> "$LOG_FILE" 2>&1
    
    if [ $? -ne 0 ]; then
        print_warning "دریافت خودکار گواهی SSL با خطا مواجه شد. لطفاً به صورت دستی تلاش کنید: certbot --nginx -d $SERVER_NAME"
    else
        print_success "گواهی SSL با موفقیت دریافت و پیکربندی شد."
    fi
fi

# ===== راه‌اندازی سرویس‌ها =====
print_header "راه‌اندازی سرویس‌ها"
print_info "در حال راه‌اندازی سرویس‌ها..."

systemctl daemon-reload >> "$LOG_FILE" 2>&1
systemctl enable rfbot-web >> "$LOG_FILE" 2>&1
systemctl start rfbot-web >> "$LOG_FILE" 2>&1
check_error "راه‌اندازی سرویس وب با خطا مواجه شد." "سرویس وب با موفقیت راه‌اندازی شد."

systemctl enable rfbot-telegram >> "$LOG_FILE" 2>&1
systemctl start rfbot-telegram >> "$LOG_FILE" 2>&1
check_error "راه‌اندازی سرویس بات تلگرام با خطا مواجه شد." "سرویس بات تلگرام با موفقیت راه‌اندازی شد."

systemctl restart nginx >> "$LOG_FILE" 2>&1
check_error "راه‌اندازی مجدد Nginx با خطا مواجه شد." "Nginx با موفقیت راه‌اندازی مجدد شد."

# ===== نمایش اطلاعات نهایی =====
print_header "نصب با موفقیت انجام شد!"

echo -e "${GREEN}=== اطلاعات دسترسی ===${NC}"
echo -e "${BOLD}آدرس پنل ادمین:${NC} http://$SERVER_NAME/admin"
if [ "$INSTALL_SSL" = "y" ] || [ "$INSTALL_SSL" = "Y" ]; then
    echo -e "${BOLD}آدرس پنل ادمین (SSL):${NC} https://$SERVER_NAME/admin"
fi
echo -e "${BOLD}نام کاربری ادمین:${NC} $ADMIN_USERNAME"
echo -e "${BOLD}رمز عبور ادمین:${NC} (همان رمزی که وارد کردید)"
echo

echo -e "${BLUE}=== وضعیت سرویس‌ها ===${NC}"
systemctl status rfbot-web --no-pager | grep "Active:" | tee -a "$LOG_FILE"
systemctl status rfbot-telegram --no-pager | grep "Active:" | tee -a "$LOG_FILE"
systemctl status nginx --no-pager | grep "Active:" | tee -a "$LOG_FILE"
echo

echo -e "${YELLOW}=== دستورات مفید ===${NC}"
echo -e "${BOLD}مشاهده لاگ‌های وب:${NC} sudo journalctl -u rfbot-web -f"
echo -e "${BOLD}مشاهده لاگ‌های بات:${NC} sudo journalctl -u rfbot-telegram -f"
echo -e "${BOLD}ری‌استارت سرویس وب:${NC} sudo systemctl restart rfbot-web"
echo -e "${BOLD}ری‌استارت سرویس بات:${NC} sudo systemctl restart rfbot-telegram"
echo -e "${BOLD}مسیر فایل‌های پروژه:${NC} $APP_DIR"
echo

print_info "فایل لاگ نصب در مسیر $LOG_FILE ذخیره شده است."
print_success "سیستم با موفقیت نصب و راه‌اندازی شد."

exit 0