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

# تابع بررسی و اصلاح app.py برای load_dotenv
ensure_load_dotenv() {
    print_message "بررسی وجود load_dotenv در $APP_DIR/app.py..."
    if ! grep -q "from dotenv import load_dotenv" "$APP_DIR/app.py"; then
        print_warning "load_dotenv در app.py یافت نشد. در حال اضافه کردن..."
        sed -i '1i from dotenv import load_dotenv\nimport os\nload_dotenv()\n' "$APP_DIR/app.py"
        check_error "اضافه کردن load_dotenv به app.py با خطا مواجه شد." "load_dotenv با موفقیت به app.py اضافه شد."
    else
        print_success "load_dotenv در app.py وجود دارد."
    fi
    # اصلاح SQLALCHEMY_DATABASE_URI برای پشتیبانی از هر دو متغیر
    if ! grep -q "SQLALCHEMY_DATABASE_URI.*os.environ.get.*SQLALCHEMY_DATABASE_URI" "$APP_DIR/app.py"; then
        print_message "اصلاح تنظیم SQLALCHEMY_DATABASE_URI در app.py..."
        sed -i 's|app.config\["SQLALCHEMY_DATABASE_URI"\] = os.environ.get("DATABASE_URL")|app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL")|' "$APP_DIR/app.py"
        check_error "اصلاح SQLALCHEMY_DATABASE_URI در app.py با خطا مواجه شد." "SQLALCHEMY_DATABASE_URI با موفقیت اصلاح شد."
    fi
}

# تابع تست اتصال به دیتابیس
test_db_connection() {
    print_message "تست اتصال به دیتابیس $DB_NAME با کاربر $DB_USER..."
    export PGPASSWORD="$DB_PASSWORD"
    psql -U "$DB_USER" -d "$DB_NAME" -h localhost -c "SELECT 1;" >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        print_error "اتصال به دیتابیس با خطا مواجه شد. جزئیات در $LOG_FILE."
        print_message "دستور پیشنهادی برای بررسی:"
        print_message "  export PGPASSWORD='$DB_PASSWORD'"
        print_message "  psql -U $DB_USER -d $DB_NAME -h localhost"
        unset PGPASSWORD
        exit 1
    fi
    print_success "اتصال به دیتابیس موفق بود."
    unset PGPASSWORD
}

# تابع بررسی جداول دیتابیس
check_db_tables() {
    print_message "بررسی جداول موجود در دیتابیس..."
    export PGPASSWORD="$DB_PASSWORD"
    TABLES=$(psql -U "$DB_USER" -d "$DB_NAME" -h localhost -t -c "\dt" 2>> "$LOG_FILE")
    if [ -z "$TABLES" ]; then
        print_warning "هیچ جدولی در دیتابیس یافت نشد."
    else
        print_success "جداول بررسی شدند. جداول موجود:\n$TABLES"
    fi
    unset PGPASSWORD
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
read -p "نام کاربری پایگاه داده [neondb_owner]: " DB_USER
DB_USER=${DB_USER:-neondb_owner}

read -s -p "رمز عبور پایگاه داده: " DB_PASSWORD
echo ""
DB_PASSWORD=${DB_PASSWORD:-npg_nguJUcZGPX83}
if [ -z "$DB_PASSWORD" ]; then
    print_error "رمز عبور پایگاه داده نمی‌تواند خالی باشد."
    exit 1
fi

read -p "نام پایگاه داده [neondb]: " DB_NAME
DB_NAME=${DB_NAME:-neondb}

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
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
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

# تست اتصال به دیتابیس
test_db_connection

# ===== راه‌اندازی پوشه برنامه =====
print_message "در حال راه‌اندازی پوشه برنامه در $APP_DIR..."

# ===== کلون کردن مخزن گیت =====
print_message "در حال راه‌اندازی فایل‌های پروژه در $APP_DIR..."
read -p "آیا می‌خواهید پروژه را از مخزن گیت دانلود کنید؟ (y/n) [n]: " USE_GIT
USE_GIT=${USE_GIT:-n}

if [ "$USE_GIT" = "y" ] || [ "$USE_GIT" = "Y" ]; then
    read -p "آدرس مخزن گیت (مثال: username/rfcbot یا https://github.com/username/rfcbot.git): " REPO_URL
    if [ -z "$REPO_URL" ]; then
        print_message "آدرس مخزن وارد نشده. استفاده از مقدار پیش‌فرض: Alisa202min/NoeRFcBot"
        REPO_URL="Alisa202min/NoeRFcBot"
    fi
    REPO_URL=$(echo "$REPO_URL" | sed 's|https://github.com/||; s|\.git$||')
    read -p "شاخه مخزن (پیش‌فرض: replit-agent): " GIT_BRANCH
    GIT_BRANCH=${GIT_BRANCH:-replit-agent}
    read -p "آیا می‌خواهید از SSH به جای HTTPS استفاده کنید؟ (y/n) [n]: " USE_SSH
    USE_SSH=${USE_SSH:-n}
    if [ "$USE_SSH" != "y" ] && [ "$USE_SSH" != "Y" ]; then
        read -p "آیا مخزن خصوصی است؟ (y/n) [n]: " PRIVATE_REPO
        PRIVATE_REPO=${PRIVATE_REPO:-n}
        if [ "$PRIVATE_REPO" = "y" ] || [ "$PRIVATE_REPO" = "Y" ]; then
            read -p "توکن دسترسی گیت‌هاب (Personal Access Token): " GIT_TOKEN
            if [ -z "$GIT_TOKEN" ]; then
                print_error "توکن دسترسی گیت‌هاب نمی‌تواند خالی باشد."
                exit 1
            fi
        fi
    fi
    if [ -d "$APP_DIR" ]; then
        print_warning "پوشه $APP_DIR از قبل وجود دارد."
        read -p "آیا می‌خواهید آن را حذف کنید؟ (y/n) [n]: " DELETE_DIR
        DELETE_DIR=${DELETE_DIR:-n}
        if [ "$DELETE_DIR" = "y" ] || [ "$DELETE_DIR" = "Y" ]; then
            print_message "در حال حذف پوشه $APP_DIR (تخمین زمان: کمتر از 1 دقیقه)..."
            rm -rf "$APP_DIR" >> "$LOG_FILE" 2>&1
            check_error "حذف پوشه $APP_DIR با خطا مواجه شد." "پوشه $APP_DIR با موفقیت حذف شد."
        else
            print_error "کلون کردن لغو شد زیرا پوشه $APP_DIR از قبل وجود دارد."
            exit 1
        fi
    fi
    print_message "در حال کلون کردن مخزن گیت (تخمین زمان: 1-3 دقیقه)..."
    cd /var/www || { print_error "تغییر به دایرکتوری /var/www با خطا مواجه شد."; exit 1; }
    mkdir -p "$APP_DIR" >> "$LOG_FILE" 2>&1
    CLONE_CMD="git clone"
    [ -n "$GIT_BRANCH" ] && CLONE_CMD="$CLONE_CMD --branch $GIT_BRANCH"
    if [ "$USE_SSH" = "y" ] || [ "$USE_SSH" = "Y" ]; then
        FINAL_URL="git@github.com:$REPO_URL.git"
    else
        if [ -n "$GIT_TOKEN" ]; then
            FINAL_URL="https://$GIT_TOKEN@github.com/$REPO_URL.git"
        else
            FINAL_URL="https://github.com/$REPO_URL.git"
        fi
    fi
    CLONE_CMD="$CLONE_CMD $FINAL_URL $APP_DIR"
    $CLONE_CMD >> "$LOG_FILE" 2>&1
    check_error "کلون کردن مخزن گیت با خطا مواجه شد. جزئیات در $LOG_FILE." "مخزن گیت با موفقیت کلون شد."
else
    print_message "لطفاً فایل‌های پروژه را به $APP_DIR منتقل کنید."
    read -p "آیا فایل‌های پروژه را منتقل کرده‌اید؟ (y/n) [n]: " FILES_COPIED
    if [ "$FILES_COPIED" != "y" ] && [ "$FILES_COPIED" != "Y" ]; then
        print_error "لطفاً فایل‌های پروژه را منتقل کنید و اسکریپت را دوباره اجرا کنید."
        exit 1
    fi
fi

# ===== بررسی فایل‌های پروژه =====
print_message "در حال بررسی فایل‌های پروژه..."
REQUIRED_FILES=("app.py" "bot.py" "database.py")
MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$APP_DIR/$file" ]; then
        MISSING_FILES+=("$file")
    fi
done
if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    print_error "فایل‌های زیر در $APP_DIR پیدا نشدند: ${MISSING_FILES[*]}"
    exit 1
fi
print_success "همه فایل‌های مورد نیاز پروژه موجود هستند."

# اصلاح app.py برای load_dotenv
ensure_load_dotenv

# ===== راه‌اندازی پوشه برنامه =====
print_message "در حال راه‌اندازی پوشه برنامه در $APP_DIR..."
mkdir -p "$APP_DIR/static/uploads/products" "$APP_DIR/static/uploads/services" "$APP_DIR/static/uploads/services/main" "$APP_DIR/static/media/products" "$APP_DIR/logs" >> "$LOG_FILE" 2>&1
check_error "ایجاد پوشه‌های برنامه با خطا مواجه شد." "پوشه‌های برنامه با موفقیت ایجاد شدند."

# ===== بررسی و نصب پایتون 3.11 =====
print_message "در حال بررسی نسخه‌های پایتون نصب‌شده..."
if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3.11 --version 2>&1)
    print_message "پایتون 3.11 یافت شد: $PYTHON_VERSION"
    PYTHON_EXEC="python3.11"
else
    print_message "پایتون 3.11 یافت نشد. در حال نصب..."
    apt install -y software-properties-common >> "$LOG_FILE" 2>&1
    add-apt-repository -y ppa:deadsnakes/ppa >> "$LOG_FILE" 2>&1
    apt update >> "$LOG_FILE" 2>&1
    apt install -y python3.11 python3.11-venv python3.11-dev >> "$LOG_FILE" 2>&1
    check_error "نصب پایتون 3.11 با خطا مواجه شد." "پایتون 3.11 با موفقیت نصب شد."
    PYTHON_EXEC="python3.11"
fi

print_message "بررسی ماژول venv برای پایتون 3.11..."
$PYTHON_EXEC -m venv --help >/dev/null 2>&1 || apt install -y python3.11-venv >> "$LOG_FILE" 2>&1
check_error "نصب python3.11-venv با خطا مواجه شد." "python3.11-venv آماده است."

print_message "در حال ایجاد محیط مجازی با پایتون 3.11..."
cd "$APP_DIR" || { print_error "تغییر به $APP_DIR با خطا مواجه شد."; exit 1; }
rm -rf venv >> "$LOG_FILE" 2>&1
$PYTHON_EXEC -m venv venv >> "$LOG_FILE" 2>&1
check_error "ایجاد محیط مجازی با خطا مواجه شد." "محیط مجازی با موفقیت ایجاد شد."

# ===== ایجاد فایل .env =====
print_message "در حال ایجاد فایل .env..."
SESSION_SECRET=$(openssl rand -hex 32)
cat > "$APP_DIR/.env" << EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
SQLALCHEMY_DATABASE_URI=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
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

# ===== نصب وابستگی‌ها =====
print_message "در حال نصب وابستگی‌های پروژه..."
source "$APP_DIR/venv/bin/activate" >> "$LOG_FILE" 2>&1
pip install --upgrade pip >> "$LOG_FILE" 2>&1
pip install -r "$APP_DIR/requirements.txt" >> "$LOG_FILE" 2>&1 || {
    print_error "نصب وابستگی‌ها با خطا مواجه شد. جزئیات در $LOG_FILE."
    deactivate
    exit 1
}
print_success "وابستگی‌های پروژه با موفقیت نصب شدند."
deactivate

# ===== راه‌اندازی پایگاه داده =====
print_message "در حال راه‌اندازی جداول پایگاه داده..."
source "$APP_DIR/venv/bin/activate" >> "$LOG_FILE" 2>&1

# ایجاد اسکریپت init_db.py
cat << EOF > "$APP_DIR/init_db.py"
from dotenv import load_dotenv
import os
from app import app, db
from models import User
load_dotenv()
with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Database tables created successfully.")
    admin = User.query.filter_by(username='$ADMIN_USERNAME').first()
    if not admin:
        print("Creating admin user...")
        admin = User(username='$ADMIN_USERNAME', email='admin@example.com', is_admin=True)
        admin.set_password('$ADMIN_PASSWORD')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully.")
EOF

python "$APP_DIR/init_db.py" >> "$LOG_FILE" 2>&1
check_error "ایجاد جداول پایگاه داده با خطا مواجه شد. جزئیات در $LOG_FILE." "جداول پایگاه داده با موفقیت ایجاد شدند."

# بررسی جداول
check_db_tables

# اجرای اسکریپت‌های اولیه
for script in seed_admin_data.py seed_categories.py; do
    if [ -f "$APP_DIR/$script" ]; then
        print_message "در حال اجرای $script..."
        python "$APP_DIR/$script" >> "$LOG_FILE" 2>&1 || print_warning "اجرای $script با خطا مواجه شد."
    fi
done

deactivate

# ===== ایجاد سرویس‌ها =====
print_message "در حال ایجاد سرویس‌های سیستمی..."
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

# ===== پیکربندی Nginx =====
print_message "در حال پیکربندی Nginx..."
SERVER_NAME=${WEBHOOK_HOST#*//}
SERVER_NAME=${SERVER_NAME%%/*}
SERVER_NAME=${SERVER_NAME:-_}
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

# ===== تنظیم دسترسی‌ها و راه‌اندازی سرویس‌ها =====
print_message "در حال تنظیم دسترسی‌های فایل‌ها..."
chown -R www-data:www-data "$APP_DIR" >> "$LOG_FILE" 2>&1
check_error "تنظیم دسترسی‌های فایل‌ها با خطا مواجه شد." "دسترسی‌های فایل‌ها با موفقیت تنظیم شدند."

print_message "در حال راه‌اندازی سرویس‌ها..."
systemctl daemon-reload >> "$LOG_FILE" 2>&1
systemctl enable rfbot-web rfbot-telegram >> "$LOG_FILE" 2>&1
systemctl start rfbot-web rfbot-telegram >> "$LOG_FILE" 2>&1
systemctl restart nginx >> "$LOG_FILE" 2>&1
check_error "راه‌اندازی سرویس‌ها با خطا مواجه شد." "سرویس‌ها با موفقیت راه‌اندازی شدند."

# ===== نمایش اطلاعات نهایی =====
echo "================== نصب با موفقیت انجام شد! =================="
echo "🌐 اطلاعات دسترسی:"
if [ "$SERVER_NAME" = "_" ]; then
    echo "   آدرس پنل ادمین: http://SERVER_IP/admin"
else
    echo "   آدرس پنل ادمین: http://$SERVER_NAME/admin"
fi
echo "   نام کاربری ادمین: $ADMIN_USERNAME"
echo "   رمز عبور ادمین: (همان رمزی که وارد کردید)"
echo "🤖 اطلاعات بات تلگرام:"
echo "   حالت راه‌اندازی: $BOT_MODE"
if [ "$BOT_MODE" = "webhook" ]; then
    echo "   آدرس webhook: ${WEBHOOK_HOST}${WEBHOOK_PATH}"
fi
echo "📂 مسیرهای مهم:"
echo "   پوشه پروژه: $APP_DIR"
echo "   فایل لاگ نصب: $LOG_FILE"
echo "⚙️ دستورات مفید:"
echo "   مشاهده لاگ‌های وب: sudo journalctl -u rfbot-web -f"
echo "   مشاهده لاگ‌های بات: sudo journalctl -u rfbot-telegram -f"
echo "✅ سیستم با موفقیت نصب شد."
exit 0
