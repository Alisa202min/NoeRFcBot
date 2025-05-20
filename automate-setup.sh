#!/bin/bash

# ===== اسکریپت نصب خودکار سیستم رادیو فرکانس =====
# این اسکریپت به‌طور خودکار پنل وب و بات تلگرام رادیو فرکانس را نصب می‌کند
# توجه: باید با دسترسی sudo اجرا شود

# ===== تنظیمات رنگ‌های خروجی =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ===== مسیر لاگ =====
LOG_FILE="/tmp/rfbot_install_$(date +%Y%m%d_%H%M%S).log"

# ===== توابع =====
# تابع نمایش پیام‌ها
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# تابع نمایش موفقیت
print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

# تابع نمایش خطا
print_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# تابع نمایش هشدار
print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
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

# ===== بررسی دسترسی روت =====
if [ "$EUID" -ne 0 ]; then
    print_error "این اسکریپت نیاز به دسترسی روت دارد. لطفاً با دستور sudo اجرا کنید."
    exit 1
fi

# ===== نمایش عنوان =====
clear
echo "========================================================"
echo "        نصب خودکار سیستم رادیو فرکانس"
echo "========================================================"
echo ""
print_message "فایل لاگ در مسیر $LOG_FILE ذخیره می‌شود."
echo ""

# ===== دریافت اطلاعات از کاربر =====
echo "لطفاً اطلاعات زیر را وارد کنید:"
echo "--------------------------------"

# دریافت اطلاعات پایگاه داده
read -p "نام کاربری پایگاه داده [rfuser]: " DB_USER
DB_USER=${DB_USER:-rfuser}

read -s -p "رمز عبور پایگاه داده: " DB_PASSWORD
echo ""
if [ -z "$DB_PASSWORD" ]; then
    print_error "رمز عبور پایگاه داده نمی‌تواند خالی باشد."
    exit 1
fi

read -p "نام پایگاه داده [rfbot_db]: " DB_NAME
DB_NAME=${DB_NAME:-rfbot_db}

# دریافت اطلاعات بات تلگرام
read -p "توکن بات تلگرام: " BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then
    print_error "توکن بات تلگرام نمی‌تواند خالی باشد."
    exit 1
fi

read -p "حالت بات تلگرام (polling یا webhook) [polling]: " BOT_MODE
BOT_MODE=${BOT_MODE:-polling}

WEBHOOK_HOST=""
WEBHOOK_PATH="/webhook/telegram"
USE_NGROK="n"

if [ "$BOT_MODE" = "webhook" ]; then
    read -p "آیا می‌خواهید از Ngrok استفاده کنید؟ (y/n) [n]: " USE_NGROK
    USE_NGROK=${USE_NGROK:-n}
    
    if [ "$USE_NGROK" = "y" ] || [ "$USE_NGROK" = "Y" ]; then
        read -p "توکن دسترسی Ngrok: " NGROK_TOKEN
        if [ -z "$NGROK_TOKEN" ]; then
            print_error "توکن دسترسی Ngrok نمی‌تواند خالی باشد."
            exit 1
        fi
    else
        read -p "دامنه برای webhook (مثال: https://example.com): " WEBHOOK_HOST
        if [ -z "$WEBHOOK_HOST" ]; then
            print_error "برای حالت webhook، دامنه ضروری است."
            exit 1
        fi
    fi
fi

# دریافت اطلاعات ادمین
read -p "نام کاربری ادمین [admin]: " ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

read -s -p "رمز عبور ادمین: " ADMIN_PASSWORD
echo ""
if [ -z "$ADMIN_PASSWORD" ]; then
    print_error "رمز عبور ادمین نمی‌تواند خالی باشد."
    exit 1
fi

# تعیین مسیر نصب
APP_DIR="/var/www/rfbot"

# ===== به‌روزرسانی سیستم =====
print_message "در حال به‌روزرسانی سیستم..."
apt update >> "$LOG_FILE" 2>&1
apt upgrade -y >> "$LOG_FILE" 2>&1
check_error "به‌روزرسانی سیستم با خطا مواجه شد." "سیستم با موفقیت به‌روزرسانی شد."

# ===== نصب نیازمندی‌ها =====
print_message "در حال نصب نیازمندی‌های سیستم..."
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
        print_message "$package قبلاً نصب شده است."
    else
        print_message "در حال نصب $package..."
        apt install -y "$package" >> "$LOG_FILE" 2>&1
        check_error "نصب $package با خطا مواجه شد." "$package با موفقیت نصب شد."
    fi
done

# ===== راه‌اندازی پایگاه داده =====
print_message "در حال راه‌اندازی پایگاه داده PostgreSQL..."

# بررسی وضعیت سرویس PostgreSQL
systemctl start postgresql >> "$LOG_FILE" 2>&1
systemctl enable postgresql >> "$LOG_FILE" 2>&1

# ایجاد کاربر پایگاه داده
su -c "psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\"" postgres >> "$LOG_FILE" 2>&1 || true
print_message "کاربر پایگاه داده ایجاد شد یا قبلاً وجود داشت."

# ایجاد پایگاه داده
su -c "psql -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\"" postgres >> "$LOG_FILE" 2>&1 || true
print_message "پایگاه داده ایجاد شد یا قبلاً وجود داشت."

# اعطای دسترسی‌ها
su -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\"" postgres >> "$LOG_FILE" 2>&1
print_success "پایگاه داده PostgreSQL با موفقیت راه‌اندازی شد."

# ===== راه‌اندازی پوشه برنامه =====
print_message "در حال راه‌اندازی پوشه برنامه در $APP_DIR..."

# ایجاد پوشه‌های لازم
mkdir -p "$APP_DIR" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/static/uploads/products" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/static/uploads/services" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/static/uploads/services/main" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/static/media/products" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/logs" >> "$LOG_FILE" 2>&1
check_error "ایجاد پوشه‌های برنامه با خطا مواجه شد." "پوشه‌های برنامه با موفقیت ایجاد شدند."

# ===== کپی یا کلون کردن فایل‌های پروژه =====
read -p "آیا می‌خواهید پروژه را از مخزن گیت دانلود کنید؟ (y/n) [n]: " USE_GIT
USE_GIT=${USE_GIT:-n}

if [ "$USE_GIT" = "y" ] || [ "$USE_GIT" = "Y" ]; then
    read -p "آدرس مخزن گیت: " GIT_REPO
    print_message "در حال کلون کردن مخزن گیت..."
    git clone "$GIT_REPO" "$APP_DIR" >> "$LOG_FILE" 2>&1
    check_error "کلون کردن مخزن گیت با خطا مواجه شد." "مخزن گیت با موفقیت کلون شد."
else
    print_message "لطفاً فایل‌های پروژه را به پوشه $APP_DIR منتقل کنید و سپس کلید Enter را فشار دهید."
    read -p "آیا فایل‌های پروژه را منتقل کرده‌اید؟ (y/n) [n]: " FILES_COPIED
    FILES_COPIED=${FILES_COPIED:-n}
    
    if [ "$FILES_COPIED" != "y" ] && [ "$FILES_COPIED" != "Y" ]; then
        print_error "لطفاً ابتدا فایل‌های پروژه را منتقل کنید و سپس اسکریپت را دوباره اجرا نمایید."
        exit 1
    fi
fi

# ===== ایجاد محیط مجازی پایتون =====
print_message "در حال ایجاد محیط مجازی پایتون..."
cd "$APP_DIR" || exit 1
python3 -m venv venv >> "$LOG_FILE" 2>&1
check_error "ایجاد محیط مجازی با خطا مواجه شد." "محیط مجازی با موفقیت ایجاد شد."

print_message "در حال نصب وابستگی‌های پایتون..."
source "$APP_DIR/venv/bin/activate"

if [ -f "$APP_DIR/requirements.txt" ]; then
    pip install -r requirements.txt >> "$LOG_FILE" 2>&1
    check_error "نصب وابستگی‌ها با خطا مواجه شد." "وابستگی‌ها با موفقیت نصب شدند."
else
    print_message "فایل requirements.txt پیدا نشد. در حال نصب وابستگی‌های اصلی..."
    pip install flask flask-sqlalchemy aiogram gunicorn psycopg2-binary python-dotenv pillow flask-login flask-wtf email_validator >> "$LOG_FILE" 2>&1
    check_error "نصب وابستگی‌ها با خطا مواجه شد." "وابستگی‌های اصلی با موفقیت نصب شدند."
fi

# ===== راه‌اندازی Ngrok (اختیاری) =====
if [ "$USE_NGROK" = "y" ] || [ "$USE_NGROK" = "Y" ]; then
    print_message "در حال نصب و پیکربندی Ngrok..."
    
    # نصب Ngrok
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
        tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
        echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
        tee /etc/apt/sources.list.d/ngrok.list && \
        apt update && apt install -y ngrok >> "$LOG_FILE" 2>&1
    
    # پیکربندی Ngrok
    ngrok config add-authtoken "$NGROK_TOKEN" >> "$LOG_FILE" 2>&1
    check_error "پیکربندی Ngrok با خطا مواجه شد." "Ngrok با موفقیت پیکربندی شد."
    
    # ایجاد سرویس Ngrok
    cat > /etc/systemd/system/ngrok.service << EOF
[Unit]
Description=ngrok
After=network.target

[Service]
ExecStart=/usr/local/bin/ngrok http 5000
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    
    # فعال‌سازی سرویس Ngrok
    systemctl enable ngrok.service >> "$LOG_FILE" 2>&1
    systemctl start ngrok.service >> "$LOG_FILE" 2>&1
    
    # کمی صبر می‌کنیم تا Ngrok شروع به کار کند
    sleep 5
    
    # دریافت آدرس عمومی Ngrok
    WEBHOOK_HOST=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | cut -d'"' -f4)
    
    if [ -z "$WEBHOOK_HOST" ]; then
        print_warning "نتوانستیم آدرس Ngrok را دریافت کنیم. لطفاً به صورت دستی آن را در فایل .env تنظیم کنید."
    else
        print_success "آدرس Ngrok: $WEBHOOK_HOST"
    fi
fi

# ===== ایجاد فایل تنظیمات =====
print_message "در حال ایجاد فایل .env..."

# ایجاد یک کلید تصادفی برای SESSION_SECRET
SESSION_SECRET=$(openssl rand -hex 32)

# ایجاد فایل .env
cat > "$APP_DIR/.env" << EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
SESSION_SECRET=$SESSION_SECRET
BOT_TOKEN=$BOT_TOKEN
BOT_MODE=$BOT_MODE
WEBHOOK_HOST=$WEBHOOK_HOST
WEBHOOK_PATH=$WEBHOOK_PATH
WEBHOOK_URL=${WEBHOOK_HOST}${WEBHOOK_PATH}
ADMIN_USERNAME=$ADMIN_USERNAME
ADMIN_PASSWORD=$ADMIN_PASSWORD
UPLOAD_FOLDER=$APP_DIR/static/uploads
EOF

check_error "ایجاد فایل .env با خطا مواجه شد." "فایل .env با موفقیت ایجاد شد."

# ===== راه‌اندازی پایگاه داده =====
print_message "در حال راه‌اندازی جداول پایگاه داده..."

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
if [ -f "$APP_DIR/seed_admin_data.py" ]; then
    print_message "در حال اجرای اسکریپت seed_admin_data.py..."
    python "$APP_DIR/seed_admin_data.py" >> "$LOG_FILE" 2>&1
fi

if [ -f "$APP_DIR/seed_categories.py" ]; then
    print_message "در حال اجرای اسکریپت seed_categories.py..."
    python "$APP_DIR/seed_categories.py" >> "$LOG_FILE" 2>&1
fi

# ===== ایجاد سرویس‌ها =====
print_message "در حال ایجاد سرویس‌های سیستمی..."

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

print_success "سرویس‌های سیستمی با موفقیت ایجاد شدند."

# ===== پیکربندی Nginx =====
print_message "در حال پیکربندی Nginx..."

SERVER_NAME=${WEBHOOK_HOST#*//}
SERVER_NAME=${SERVER_NAME%%/*}

if [ -z "$SERVER_NAME" ]; then
    SERVER_NAME="_" # اگر دامنه مشخص نشده باشد، از IP استفاده می‌کنیم
fi

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

ln -sf /etc/nginx/sites-available/rfbot /etc/nginx/sites-enabled/ >> "$LOG_FILE" 2>&1
nginx -t >> "$LOG_FILE" 2>&1
check_error "تست پیکربندی Nginx با خطا مواجه شد." "پیکربندی Nginx با موفقیت تست شد."

# ===== تنظیم دسترسی‌ها =====
print_message "در حال تنظیم دسترسی‌های فایل‌ها..."
chown -R www-data:www-data "$APP_DIR" >> "$LOG_FILE" 2>&1
check_error "تنظیم دسترسی‌های فایل‌ها با خطا مواجه شد." "دسترسی‌های فایل‌ها با موفقیت تنظیم شدند."

# ===== راه‌اندازی سرویس‌ها =====
print_message "در حال راه‌اندازی سرویس‌ها..."
systemctl daemon-reload >> "$LOG_FILE" 2>&1
systemctl enable rfbot-web >> "$LOG_FILE" 2>&1
systemctl start rfbot-web >> "$LOG_FILE" 2>&1
systemctl enable rfbot-telegram >> "$LOG_FILE" 2>&1
systemctl start rfbot-telegram >> "$LOG_FILE" 2>&1
systemctl restart nginx >> "$LOG_FILE" 2>&1
check_error "راه‌اندازی سرویس‌ها با خطا مواجه شد." "سرویس‌ها با موفقیت راه‌اندازی شدند."

# ===== نمایش اطلاعات نهایی =====
echo ""
echo "================== نصب با موفقیت انجام شد! =================="
echo ""
echo "🌐 اطلاعات دسترسی:"
if [ "$SERVER_NAME" = "_" ]; then
    echo "   آدرس پنل ادمین: http://SERVER_IP/admin"
else
    echo "   آدرس پنل ادمین: http://$SERVER_NAME/admin"
fi
echo "   نام کاربری ادمین: $ADMIN_USERNAME"
echo "   رمز عبور ادمین: (همان رمزی که وارد کردید)"
echo ""

echo "🤖 اطلاعات بات تلگرام:"
echo "   حالت راه‌اندازی: $BOT_MODE"
if [ "$BOT_MODE" = "webhook" ]; then
    echo "   آدرس webhook: ${WEBHOOK_HOST}${WEBHOOK_PATH}"
    if [ "$USE_NGROK" = "y" ] || [ "$USE_NGROK" = "Y" ]; then
        echo "   توجه: آدرس Ngrok بعد از هر راه‌اندازی مجدد سرور تغییر می‌کند."
    fi
fi
echo ""

echo "📂 مسیرهای مهم:"
echo "   پوشه پروژه: $APP_DIR"
echo "   فایل تنظیمات: $APP_DIR/.env"
echo "   فایل لاگ نصب: $LOG_FILE"
echo ""

echo "⚙️ دستورات مفید:"
echo "   مشاهده لاگ‌های وب: sudo journalctl -u rfbot-web -f"
echo "   مشاهده لاگ‌های بات: sudo journalctl -u rfbot-telegram -f"
echo "   ری‌استارت سرویس وب: sudo systemctl restart rfbot-web"
echo "   ری‌استارت سرویس بات: sudo systemctl restart rfbot-telegram"
echo ""

echo "✅ سیستم با موفقیت نصب و راه‌اندازی شد."
echo "   اگر سؤالی دارید، به راهنمای استقرار (DEPLOYMENT.txt) مراجعه کنید."
echo ""

exit 0