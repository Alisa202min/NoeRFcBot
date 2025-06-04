#!/bin/bash

# ===== تنظیمات رنگ‌های خروجی =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ===== مسیر لاگ (پیشنهاد 1) =====
LOG_DIR="/var/log/rfbot"
mkdir -p "$LOG_DIR" >> "/tmp/rfbot_setup_$(date +%Y%m%d_%H%M%S).log" 2>&1
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[WARNING]${NC} ایجاد دایرکتوری $LOG_DIR با خطا مواجه شد." | tee -a "/tmp/rfbot_setup_$(date +%Y%m%d_%H%M%S).log"
fi
LOG_FILE="$LOG_DIR/install_$(date +%Y%m%d_%H%M%S).log"
chown www-data:www-data "$LOG_DIR" >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    print_warning "تنظیم دسترسی $LOG_DIR با خطا مواجه شد."
fi

# ===== توابع کمکی =====
print_message() { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"; }
check_error() {
    if [ $? -ne 0 ]; then
        print_error "$1"
        exit 1
    else
        print_success "$2"
    fi
}
is_installed() { dpkg -l "$1" >/dev/null 2>&1; }

# تابع بررسی و اصلاح main.py برای load_dotenv (پیشنهادات 4, 5, 6)
ensure_load_dotenv() {
    MAIN_PY=$(find "$APP_DIR" -maxdepth 3 -name "main.py" | head -n 1)
    if [ -z "$MAIN_PY" ]; then
        print_error "فایل main.py در $APP_DIR یا زیرپوشه‌های آن یافت نشد."
        exit 1
    fi
    print_message "بررسی وجود load_dotenv در $MAIN_PY..."
    if ! grep -q "from dotenv import load_dotenv" "$MAIN_PY"; then
        print_warning "load_dotenv در main.py یافت نشد. در حال اضافه کردن..."
        cp "$MAIN_PY" "$MAIN_PY.bak" >> "$LOG_FILE" 2>&1
        if [ $? -ne 0 ]; then
            print_warning "ایجاد نسخه پشتیبان از main.py با خطا مواجه شد."
        fi
        sed -i '1i from dotenv import load_dotenv\nimport os\nload_dotenv()\n' "$MAIN_PY"
        check_error "اضافه کردن load_dotenv به main.py با خطا مواجه شد." "load_dotenv با موفقیت به main.py اضافه شد."
    else
        print_success "load_dotenv در main.py وجود دارد."
    fi
    if ! grep -q "app.config\['SQLALCHEMY_DATABASE_URI'\]" "$MAIN_PY"; then
        print_warning "تنظیم SQLALCHEMY_DATABASE_URI در main.py یافت نشد. اضافه کردن دستی ممکن است لازم باشد."
    elif ! grep -q "SQLALCHEMY_DATABASE_URI.*os.environ.get.*SQLALCHEMY_DATABASE_URI" "$MAIN_PY"; then
        print_message "اصلاح تنظیم SQLALCHEMY_DATABASE_URI در main.py..."
        sed -i 's|app.config\["SQLALCHEMY_DATABASE_URI"\] = os.environ.get("DATABASE_URL")|app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL")|' "$MAIN_PY"
        check_error "اصلاح SQLALCHEMY_DATABASE_URI در main.py با خطا مواجه شد." "SQLALCHEMY_DATABASE_URI با موفقیت اصلاح شد."
    fi
}

# تابع تست اتصال به دیتابیس
test_db_connection() {
    print_message "تست اتصال به دیتابیس $DB_NAME با کاربر $DB_USER..."
    export PGPASSWORD="$DB_PASSWORD"
    psql -U "$DB_USER" -d "$DB_NAME" -h localhost -c "SELECT 1;" >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        print_error "اتصال به دیتابیس با خطا مواجه شد. جزئیات در $LOG_FILE."
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

# ===== امکان Rollback (پیشنهاد 20) =====
trap 'print_error "اسکریپت با خطا متوقف شد. پاکسازی..."; rm -f "$APP_DIR/.env" "$SECURE_INIT_SCRIPT"; exit 1' ERR

# ===== بررسی سازگاری سیستم‌عامل (پیشنهاد 17) =====
if ! grep -qi "ubuntu\|debian" /etc/os-release; then
    print_error "این اسکریپت فقط روی اوبونتو یا دبیان تست شده است."
    exit 1
fi

# ===== دریافت اطلاعات از کاربر با مقادیر پیش‌فرض =====
read -p "نام دیتابیس را وارد کنید [rfdb]: " DB_NAME
DB_NAME=${DB_NAME:-rfdb}
read -p "نام کاربر دیتابیس را وارد کنید [rfuser]: " DB_USER
DB_USER=${DB_USER:-rfuser}
read -s -p "رمز دیتابیس را وارد کنید: " DB_PASSWORD
DB_PASSWORD=${DB_PASSWORD:-securepassword123} # بدون اشاره به مقدار
echo
read -p "نام کاربری ادمین را وارد کنید [admin]: " ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
read -s -p "رمز ادمین را وارد کنید: " ADMIN_PASSWORD
ADMIN_PASSWORD=${ADMIN_PASSWORD:-securepassword123} # بدون اشاره به مقدار
echo
read -p "توکن بات تلگرام را وارد کنید: " BOT_TOKEN
BOT_TOKEN=${BOT_TOKEN:-notoken}
read -p "حالت بات (polling/webhook) [polling]: " BOT_MODE
BOT_MODE=${BOT_MODE:-polling}
if [ "$BOT_MODE" = "webhook" ]; then
    read -p "آدرس وب‌هوک (مثل https://example.com) را وارد کنید: " WEBHOOK_HOST
    read -p "مسیر وب‌هوک (مثل /webhook) را وارد کنید: " WEBHOOK_PATH
fi
read -p "آیا از Ngrok استفاده می‌کنید؟ (y/n) [n]: " USE_NGROK
USE_NGROK=${USE_NGROK:-n}
if [ "$USE_NGROK" = "y" ] || [ "$USE_NGROK" = "Y" ]; then
    read -p "توکن Ngrok را وارد کنید: " NGROK_TOKEN
fi
read -p "آیا اطلاعات تست پر شوند؟ (y/n) [y]: " POPULATE_DATA
POPULATE_DATA=${POPULATE_DATA:-y}
read -p "آیا می‌خواهید سیستم به‌روزرسانی شود؟ (y/n) [n]: " UPDATE_SYSTEM
UPDATE_SYSTEM=${UPDATE_SYSTEM:-n}
read -p "آیا پکیج‌های سیستمی نصب شوند؟ (y/n) [n]: " INSTALL_PACKAGES
INSTALL_PACKAGES=${INSTALL_PACKAGES:-n}
read -p "آیا پایتون 3.11 نصب شود؟ (y/n) [y]: " INSTALL_PYTHON
INSTALL_PYTHON=${INSTALL_PYTHON:-y}
read -p "آیا مخزن گیت کلون شود؟ (y/n) [y]: " CLONE_GIT
CLONE_GIT=${CLONE_GIT:-y}
read -p "آیا وابستگی‌های پروژه (requirements.txt) نصب شوند؟ (y/n) [n]: " INSTALL_REQUIREMENTS
INSTALL_REQUIREMENTS=${INSTALL_REQUIREMENTS:-n}
read -p "مسیر نصب برنامه [/var/www/rfbot]: " APP_DIR
APP_DIR=${APP_DIR:-/var/www/rfbot}

# ===== به‌روزرسانی سیستم (وابسته به تأیید، پیش‌فرض خیر) =====
if [ "$UPDATE_SYSTEM" = "y" ] || [ "$UPDATE_SYSTEM" = "Y" ]; then
    print_message "در حال به‌روزرسانی سیستم..."
    apt update >> "$LOG_FILE" 2>&1
    apt upgrade -y >> "$LOG_FILE" 2>&1
    check_error "به‌روزرسانی سیستم با خطا مواجه شد." "سیستم با موفقیت به‌روزرسانی شد."
else
    print_message "به‌روزرسانی سیستم رد شد."
fi

# ===== نصب پکیج‌های سیستمی (وابسته به تأیید، پیش‌فرض خیر) =====
if [ "$INSTALL_PACKAGES" = "y" ] || [ "$INSTALL_PACKAGES" = "Y" ]; then
    print_message "در حال نصب نیازمندی‌های سیستم..."
    PACKAGES=("python3" "python3-pip" "python3-venv" "postgresql" "postgresql-contrib" "nginx" "git" "curl")
    for package in "${PACKAGES[@]}"; do
        if is_installed "$package"; then
            print_message "$package قبلاً نصب شده است."
        else
            print_message "در حال نصب $package..."
            apt install -y "$package" >> "$LOG_FILE" 2>&1
            check_error "نصب $package با خطا مواجه شد." "$package با موفقیت نصب شد."
        fi
    done
else
    print_message "نصب پکیج‌های سیستمی رد شد."
fi

# ===== راه‌اندازی پایگاه داده =====
print_message "در حال راه‌اندازی پایگاه داده..."
if ! systemctl is-active --quiet postgresql; then
    systemctl start postgresql >> "$LOG_FILE" 2>&1
    check_error "راه‌اندازی سرویس PostgreSQL با خطا مواجه شد." "سرویس PostgreSQL راه‌اندازی شد."
fi
if ! su - postgres -c "psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME"; then
    print_message "ایجاد دیتابیس $DB_NAME..."
    su - postgres -c "createdb $DB_NAME" >> "$LOG_FILE" 2>&1
    check_error "ایجاد دیتابیس $DB_NAME با خطا مواجه شد." "دیتابیس $DB_NAME ایجاد شد."
else
    print_message "دیتابیس $DB_NAME از قبل وجود دارد."
fi
if ! su - postgres -c "psql -t -c \"SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'\" | grep -q 1"; then
    print_message "ایجاد کاربر $DB_USER..."
    su - postgres -c "psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\"" >> "$LOG_FILE" 2>&1
    check_error "ایجاد کاربر $DB_USER با خطا مواجه شد." "کاربر $DB_USER ایجاد شد."
else
    print_message "کاربر $DB_USER از قبل وجود دارد."
fi
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\"" >> "$LOG_FILE" 2>&1
check_error "اعطای دسترسی به $DB_USER با خطا مواجه شد." "دسترسی به $DB_USER اعطا شد."

# ===== بررسی و نصب پایتون 3.11 (پیشنهادات 7, 8, 9، وابسته به تأیید، پیش‌فرض بله) =====
if [ "$INSTALL_PYTHON" = "y" ] || [ "$INSTALL_PYTHON" = "Y" ]; then
    print_message "در حال بررسی نسخه‌های پایتون نصب‌شده..."
    if command -v python3.11 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3.11 --version | cut -d' ' -f2)
        print_message "پایتون 3.11 یافت شد: $PYTHON_VERSION"
        if [[ "$PYTHON_VERSION" < "3.11.0" ]]; then
            print_warning "نسخه پایتون ($PYTHON_VERSION) قدیمی است. نصب نسخه جدید..."
            PYTHON_EXEC=""
        else
            read -p "آیا می‌خواهید با پایتون 3.11 موجود ادامه دهید؟ (y/n) [y]: " USE_EXISTING
            USE_EXISTING=${USE_EXISTING:-y}
            if [ "$USE_EXISTING" = "y" ] || [ "$USE_EXISTING" = "Y" ]; then
                PYTHON_EXEC="python3.11"
            else
                PYTHON_EXEC=""
            fi
        fi
    else
        print_message "پایتون 3.11 یافت نشد. در حال نصب..."
        PYTHON_EXEC=""
    fi
    if [ -z "$PYTHON_EXEC" ]; then
        print_message "در حال نصب پایتون 3.11..."
        apt install -y software-properties-common ca-certificates curl gnupg >> "$LOG_FILE" 2>&1
        check_error "نصب ابزارهای لازم با خطا مواجه شد." "ابزارهای لازم نصب شدند."
        timeout 120 add-apt-repository -y ppa:deadsnakes/ppa >> "$LOG_FILE" 2>&1
        if [ $? -ne 0 ]; then
            print_warning "افزودن مخزن deadsnakes با خطا مواجه شد. تلاش برای نصب دستی..."
            if ! ping -c 1 www.python.org >/dev/null 2>&1; then
                print_error "اتصال به www.python.org برقرار نشد. بررسی شبکه یا VPN لازم است."
                exit 1
            fi
            print_message "دانلود و نصب پایتون 3.11.10..."
            PYTHON_VERSION="3.11.10"
            cd /usr/src || { print_error "تغییر به /usr/src با خطا مواجه شد."; exit 1; }
            rm -rf Python-$PYTHON_VERSION* >> "$LOG_FILE" 2>&1
            wget https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tar.xz >> "$LOG_FILE" 2>&1
            tar -xf Python-$PYTHON_VERSION.tar.xz >> "$LOG_FILE" 2>&1 || { print_error "استخراج فایل پایتون با خطا مواجه شد."; exit 1; }
            cd Python-$PYTHON_VERSION || { print_error "تغییر به دایرکتوری Python-$PYTHON_VERSION با خطا مواجه شد."; exit 1; }
            ./configure --enable-optimizations >> "$LOG_FILE" 2>&1 || { print_error "پیکربندی پایتون با خطا مواجه شد."; exit 1; }
            make -j$(nproc) >> "$LOG_FILE" 2>&1 || { print_error "ساخت پایتون با خطا مواجه شد."; exit 1; }
            make altinstall >> "$LOG_FILE" 2>&1 || { print_error "نصب پایتون با خطا مواجه شد."; exit 1; }
            PYTHON_EXEC="python3.11"
        else
            apt update >> "$LOG_FILE" 2>&1
            apt install -y python3.11 python3.11-venv python3.11-dev >> "$LOG_FILE" 2>&1
            check_error "نصب پایتون 3.11 با خطا مواجه شد." "پایتون 3.11 با موفقیت نصب شد."
            PYTHON_EXEC="python3.11"
        fi
    fi
else
    print_message "نصب پایتون 3.11 رد شد."
    PYTHON_EXEC="python3"
fi

# ===== ایجاد دایرکتوری‌های پروژه (پیشنهاد 2) =====
print_message "ایجاد دایرکتوری‌های پروژه..."
mkdir -p "$APP_DIR" "$APP_DIR/static/uploads" "$APP_DIR/logs" >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    print_warning "ایجاد دایرکتوری‌های پروژه با خطا مواجه شد."
fi
chown -R www-data:www-data "$APP_DIR" >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    print_warning "تنظیم دسترسی‌های $APP_DIR با خطا مواجه شد."
fi

# ===== کلون مخزن گیت (وابسته به تأیید، پیش‌فرض بله) =====
if [ "$CLONE_GIT" = "y" ] || [ "$CLONE_GIT" = "Y" ]; then
    print_message "کلون مخزن گیت..."
    rm -rf "$APP_DIR"/* >> "$LOG_FILE" 2>&1
    git clone https://github.com/Alisa202min/NoeRFcBot.git -b replit-agent "$APP_DIR" >> "$LOG_FILE" 2>&1
    check_error "کلون مخزن گیت با خطا مواجه شد." "مخزن گیت با موفقیت کلون شد."
else
    print_message "کلون مخزن گیت رد شد."
fi

# ===== بررسی فایل‌های مورد نیاز =====
print_message "بررسی فایل‌های مورد نیاز..."
REQUIRED_FILES=("main.py" "bot.py" "database.py")
MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$APP_DIR/$file" ]; then
        MISSING_FILES+=("$file")
    fi
done
if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    print_error "فایل‌های زیر یافت نشدند: ${MISSING_FILES[*]}. لطفاً فایل‌ها را به $APP_DIR کپی کنید."
    exit 1
fi

# ===== ایجاد محیط مجازی =====
print_message "ایجاد محیط مجازی..."
$PYTHON_EXEC -m venv "$APP_DIR/venv" >> "$LOG_FILE" 2>&1
check_error "ایجاد محیط مجازی با خطا مواجه شد." "محیط مجازی با موفقیت ایجاد شد."

# ===== نصب وابستگی‌ها (وابسته به تأیید، پیش‌فرض خیر، پیشنهاد 15) =====
if [ "$INSTALL_REQUIREMENTS" = "y" ] || [ "$INSTALL_REQUIREMENTS" = "Y" ]; then
    print_message "در حال نصب وابستگی‌های پروژه از requirements.txt..."
    if [ ! -f "$APP_DIR/requirements.txt" ]; then
        print_warning "فایل requirements.txt در $APP_DIR یافت نشد. ایجاد فایل پیش‌فرض..."
        cat << EOF > "$APP_DIR/requirements.txt"
flask>=3.1.0
Flask-SQLAlchemy>=3.1.1
Flask-Login>=0.6.3
Flask-WTF>=1.2.1
SQLAlchemy>=2.0.35
psycopg2-binary>=2.9.9
Werkzeug>=3.0.4
Jinja2>=3.1.4
gunicorn>=23.0.0
python-telegram-bot>=21.4
aiogram>=3.13.1
aiohttp>=3.10.5
python-dotenv>=1.0.1
Pillow>=10.4.0
email-validator>=2.2.0
pytest>=8.3.2
pytest-flask>=1.3.0
pytest-asyncio>=0.24.0
PyJWT>=2.9.0
oauthlib>=3.2.2
requests>=2.32.3
replit>=3.6.0
locust>=2.31.6
EOF
    fi
    source "$APP_DIR/venv/bin/activate" >> "$LOG_FILE" 2>&1
    pip install --upgrade pip setuptools wheel >> "$LOG_FILE" 2>&1 | tee "$LOG_FILE.pip"
    pip install -r "$APP_DIR/requirements.txt" >> "$LOG_FILE" 2>&1 | tee -a "$LOG_FILE.pip"
    check_error "نصب وابستگی‌ها با خطا مواجه شد." "وابستگی‌های پروژه با موفقیت نصب شدند."
    deactivate
else
    print_message "نصب وابستگی‌های پروژه رد شد."
fi

# ===== راه‌اندازی Ngrok (پیشنهادات 10, 11) =====
WEBHOOK_HOST=${WEBHOOK_HOST:-}
WEBHOOK_PATH=${WEBHOOK_PATH:-}
if [ "$USE_NGROK" = "y" ] || [ "$USE_NGROK" = "Y" ]; then
    print_message "در حال نصب و پیکربندی Ngrok..."
    . /etc/os-release
    echo "deb https://ngrok-agent.s3.amazonaws.com $VERSION_CODENAME main" | \
        tee /etc/apt/sources.list.d/ngrok.list >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        print_warning "ایجاد فایل مخزن Ngrok با خطا مواجه شد."
    fi
    apt update && apt install -y ngrok >> "$LOG_FILE" 2>&1
    ngrok config add-authtoken "$NGROK_TOKEN" >> "$LOG_FILE" 2>&1
    check_error "پیکربندی Ngrok با خطا مواجه شد." "Ngrok با موفقیت پیکربندی شد."
    sleep 5
    for i in {1..10}; do
        WEBHOOK_HOST=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | cut -d'"' -f4)
        [ -n "$WEBHOOK_HOST" ] && break
        print_message "تلاش $i برای دریافت آدرس Ngrok..."
        sleep 2
    done
    if [ -z "$WEBHOOK_HOST" ]; then
        print_warning "نتوانستیم آدرس Ngrok را دریافت کنیم. لطفاً به صورت دستی آن را در فایل .env تنظیم کنید."
    else
        print_success "آدرس Ngrok: $WEBHOOK_HOST"
    fi
fi

# ===== اصلاح load_dotenv =====
ensure_load_dotenv

# ===== ایجاد فایل تنظیمات (پیشنهادات 12, 13, 3) =====
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
$(if [ "$BOT_MODE" = "webhook" ]; then echo "WEBHOOK_URL=${WEBHOOK_HOST}${WEBHOOK_PATH}"; else echo "WEBHOOK_URL="; fi)
ADMIN_USERNAME=$ADMIN_USERNAME
ADMIN_PASSWORD=$ADMIN_PASSWORD
UPLOAD_FOLDER=$APP_DIR/static/uploads
LOG_DIR=$APP_DIR/logs
EOF
chmod 600 "$APP_DIR/.env" >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    print_warning "تنظیم دسترسی فایل .env با خطا مواجه شد."
fi
check_error "ایجاد فایل .env با خطا مواجه شد." "فایل .env با موفقیت ایجاد شد."

# ===== تست اتصال دیتابیس =====
test_db_connection

# ===== راه‌اندازی امن پایگاه داده (پیشنهاد 22) =====
print_message "در حال راه‌اندازی امن جداول پایگاه داده..."
if ! grep -q "app = Flask(__name__)" "$MAIN_PY"; then
    print_error "Flask app در main.py یافت نشد."
    exit 1
fi
if ! grep -q "db = SQLAlchemy(app)" "$MAIN_PY"; then
    print_error "SQLAlchemy db در main.py یافت نشد."
    exit 1
fi
SECURE_INIT_SCRIPT="$APP_DIR/.temp_init_$(date +%s)_$(openssl rand -hex 8).py"
cat > "$SECURE_INIT_SCRIPT" << EOF
import os
from main import app, db
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        db.create_all()
        admin_user = os.environ.get('SETUP_ADMIN_USER')
        admin_pass = os.environ.get('SETUP_ADMIN_PASS')
        if admin_user and admin_pass:
            from models.models import User
            existing_user = User.query.filter_by(username=admin_user).first()
            if not existing_user:
                new_user = User(
                    username=admin_user,
                    password=generate_password_hash(admin_pass, method='pbkdf2:sha256'),
                    is_admin=True
                )
                db.session.add(new_user)
                db.session.commit()

if __name__ == '__main__':
    init_db()
EOF
chmod 600 "$SECURE_INIT_SCRIPT" >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    print_warning "تنظیم دسترسی فایل $SECURE_INIT_SCRIPT با خطا مواجه شد."
fi
export SETUP_ADMIN_USER="$ADMIN_USERNAME"
export SETUP_ADMIN_PASS="$ADMIN_PASSWORD"
source "$APP_DIR/venv/bin/activate" >> "$LOG_FILE" 2>&1
python "$SECURE_INIT_SCRIPT" >> "$LOG_FILE" 2>&1
INIT_RESULT=$?
deactivate
rm -f "$SECURE_INIT_SCRIPT" >> "$LOG_FILE" 2>&1
unset SETUP_ADMIN_USER SETUP_ADMIN_PASS
if [ $INIT_RESULT -ne 0 ]; then
    print_error "راه‌اندازی امن پایگاه داده با خطا مواجه شد."
    exit 1
fi
print_success "راه‌اندازی امن پایگاه داده با موفقیت انجام شد."

# ===== پیکربندی Nginx (پیشنهاد 14) =====
if [ "$BOT_MODE" = "webhook" ] && ! echo "$WEBHOOK_HOST" | grep -q "^https?://"; then
    print_error "WEBHOOK_HOST باید با http:// یا https:// شروع شود."
    exit 1
fi
SERVER_NAME=${WEBHOOK_HOST#*//}
SERVER_NAME="${SERVER_NAME%%/*}" || "_"
cat > /etc/nginx/sites-available/rfbot << EOF
server {
    listen 80;
    server_name $SERVER_NAME;
    client_max_body_size 20M;
    location /static/uploads/ { alias $APP_DIR/static/uploads/; }
    location /static/media/ { alias $APP_DIR/static/media/; }
    location /static/ { alias $APP_DIR/static/; }
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
if [ $? -ne 0 ]; then
    print_warning "ایجاد لینک سمبولیک Nginx با خطا مواجه شد."
fi
nginx -t >> "$LOG_FILE" 2>&1
check_error "تست پیکربندی Nginx با خطا مواجه شد." "پیکربندی Nginx با موفقیت تست شد."
systemctl restart nginx >> "$LOG_FILE" 2>&1
check_error "ری‌استارت Nginx با خطا مواجه شد." "Nginx با موفقیت ری‌استارت شد."

# ===== تنظیم سرویس‌ها =====
print_message "در حال تنظیم سرویس وب..."
cat > /etc/systemd/system/rfbot_web.service << EOF
[Unit]
Description=RF Flask Web App
After=network.target postgresql.service

[Service]
User=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 1 --bind 0.0.0.0:5000 main:app
Restart=always
StandardOutput=append:/var/log/rfbot/gunicorn.log
StandardError=inherit

[Install]
WantedBy=multi-user.target
EOF
print_message "در حال تنظیم سرویس بات تلگرام..."
cat > /etc/systemd/system/rfbot_bot.service << EOF
[Unit]
Description=RF Telegram Bot
After=network.target postgresql.service

[Service]
User=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/main.py
Restart=always
StandardOutput=append:/var/log/rfbot/telebot.log
StandardError=inherit

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload "$LOG_FILE" >/dev/null 2>&1
systemctl enable rfbot_web.service >> "$LOG_FILE" 2>&1
systemctl enable rfbot_bot.service >> "$LOG_FILE" 2>&1
systemctl start rfbot_web.service >> "$LOG_FILE" 2>&1
systemctl start rfbot_bot.service >> "$LOG_FILE" 2>&1
check_error "راه‌اندازی سرویس‌ها با خطا مواجه شد." "سرویس‌ها با موفقیت راه‌اندازی شدند."

# ===== پر کردن اطلاعات تست =====
if [ "$POPULATE_DATA" = "y" ] || [ "$POPULATE_DATA" = "Y" ]; then
    print_message "انتخاب اسکریپت تولید داده..."
    DATA_GENERATORS=("rftest_data_generator.py")
    SELECTED_GENERATOR=""
    for generator in "${DATA_GENERATORS[@]}"; do
        if [ -f "$APP_DIR/$generator" ]; then
            SELECTED_GENERATOR="$generator"
            break
        fi
    done
    if [ -z "$SELECTED_GENERATOR" ]; then
        print_warning "هیچ اسکریپت تولید داده‌ای یافت نشد."
    else
        print_message "اجرای $SELECTED_GENERATOR برای پر کردن اطلاعات تست..."
        source "$APP_DIR/venv/bin/activate" >> "$LOG_FILE" 2>&1
        python "$APP_DIR/$SELECTED_GENERATOR" >> "$LOG_FILE" 2>&1
        if [ $? -ne 0 ]; then
            print_warning "اجرای $SELECTED_GENERATOR با خطا مواجه شد."
        else
            print_success "اطلاعات تست با موفقیت وارد شد."
        fi
        deactivate
    fi
fi

# ===== تست نهایی (پیشنهاد 21) =====
print_message "تست سلامت سرویس‌ها..."
sleep 2
curl -s http://localhost:5000/health_check >/dev/null > "$LOG_FILE" 2>&1 && print_success "سرویس وب در حال اجرا است." || print_warning "سرویس وب کار نمی‌کند."

# ===== نمایش اطلاعات نهایی =====
print_message "===== نصب با موفقیت انجام شد! ====="
print_message "دیتابیس: $DB_NAME"
print_message "کاربر دیتابیس: $DB_USER"
print_message "نام کاربری ادمین: $ADMIN_USERNAME"
print_message "مسیر نصب: $APP_DIR"
print_message "حالت بات: $BOT_MODE"
if [ "$BOT_MODE" = "webhook" ]; then
    print_message "آدرس وب‌هوک: ${WEBHOOK_HOST}${WEBHOOK_PATH}"
fi
if [ "$USE_NGROK" = "y" ] || [ "$USE_NGROK" = "Y" ]; then
    print_message "Ngrok فعال: $WEBHOOK_HOST"
fi
print_message "لاگ نصب: $LOG_FILE"
print_message "لاگ‌های اضافی: $LOG_FILE.pip (در صورت نصب وابستگی‌ها)"
print_success "برای بررسی سرویس‌ها، از دستورات زیر استفاده کنید:"
print_message "  systemctl status rfbot_web"
print_message "  systemctl status rfbot_bot"

# ===== دستورات مفید =====
print_message "===== دستورات مفید برای مدیریت سیستم ====="
print_message "1. تغییر رمز دیتابیس برای کاربر $DB_USER:"
print_message "   su - postgres -c \"psql -c \\\"ALTER USER $DB_USER WITH PASSWORD 'newpassword';\\\"\""
print_message "2. بررسی لاگ‌های سرویس وب:"
print_message "   tail -f /var/log/rfbot/gunicorn.log"
print_message "3. بررسی لاگ‌های بات تلگرام:"
print_message "   tail -f /var/log/rfbot/telebot.log"
print_message "4. ری‌استارت سرویس‌ها:"
print_message "   systemctl restart rfbot_web rfbot_bot"
print_message "5. بررسی لاگ نصب:"
print_message "   less $LOG_FILE"
print_message "6. توقف سرویس‌ها:"
print_message "   systemctl stop rfbot_web rfbot_bot"
print_message "7. غیرفعال کردن سرویس‌ها:"
print_message "   systemctl disable rfbot_web rfbot_bot"

# ===== بررسی نهایی لاگ‌ها =====
print_message "بررسی نهایی لاگ‌ها..."
if [ -f "$LOG_FILE.pip" ]; then
    if grep -qi "error" "$LOG_FILE.pip"; then
        print_warning "خطاهایی در نصب وابستگی‌ها یافت شد. لطفاً $LOG_FILE.pip را بررسی کنید."
    fi
fi
if grep -qi "error" "$LOG_FILE"; then
    print_warning "خطاهایی در فرآیند نصب یافت شد. لطفاً $LOG_FILE را بررسی کنید."
else
    print_success "نصب بدون خطای لاگ شده تکمیل شد."
fi

exit 0