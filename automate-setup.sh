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
@@ -185,6 +232,9 @@
su -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\"" postgres >> "$LOG_FILE" 2>&1
print_success "پایگاه داده PostgreSQL با موفقیت راه‌اندازی شد."

# تست اتصال به دیتابیس
test_db_connection

# ===== راه‌اندازی پوشه برنامه =====
print_message "در حال راه‌اندازی پوشه برنامه در $APP_DIR..."

@@ -199,7 +249,6 @@
print_message "آدرس مخزن وارد نشده. استفاده از مقدار پیش‌فرض: Alisa202min/NoeRFcBot"
REPO_URL="Alisa202min/NoeRFcBot"
fi
    # Normalize REPO_URL (remove https://github.com/ or .git if present)
REPO_URL=$(echo "$REPO_URL" | sed 's|https://github.com/||; s|\.git$||')
read -p "شاخه مخزن (پیش‌فرض: replit-agent): " GIT_BRANCH
GIT_BRANCH=${GIT_BRANCH:-replit-agent}
@@ -222,8 +271,8 @@
DELETE_DIR=${DELETE_DIR:-n}
if [ "$DELETE_DIR" = "y" ] || [ "$DELETE_DIR" = "Y" ]; then
print_message "در حال حذف پوشه $APP_DIR (تخمین زمان: کمتر از 1 دقیقه)..."
            rm -rf "$APP_DIR" >> "$LOG_FILE" 2>&1 || { print_error "حذف پوشه $APP_DIR با خطا مواجه شد."; exit 1; }
            print_success "پوشه $APP_DIR با موفقیت حذف شد."
            rm -rf "$APP_DIR" >> "$LOG_FILE" 2>&1
            check_error "حذف پوشه $APP_DIR با خطا مواجه شد." "پوشه $APP_DIR با موفقیت حذف شد."
else
print_error "کلون کردن لغو شد زیرا پوشه $APP_DIR از قبل وجود دارد."
exit 1
@@ -245,18 +294,7 @@
fi
CLONE_CMD="$CLONE_CMD $FINAL_URL $APP_DIR"
$CLONE_CMD >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        print_error "کلون کردن مخزن گیت با خطا مواجه شد. جزئیات در $LOG_FILE."
        print_message "دستور پیشنهادی برای بررسی:"
        print_message "  cd /var/www"
        print_message "  $CLONE_CMD"
        print_message "نکات عیب‌یابی:"
        print_message "  1) مطمئن شوید توکن گیت‌هاب معتبر است و دسترسی repo دارد."
        print_message "  2) آدرس مخزن را بررسی کنید: https://github.com/$REPO_URL"
        print_message "  3) برای مشکلات شبکه، از VPN یا DNS عمومی (مثل 8.8.8.8) استفاده کنید."
        exit 1
    fi
    print_success "مخزن گیت با موفقیت کلون شد."
    check_error "کلون کردن مخزن گیت با خطا مواجه شد. جزئیات در $LOG_FILE." "مخزن گیت با موفقیت کلون شد."
else
print_message "لطفاً فایل‌های پروژه را به $APP_DIR منتقل کنید."
read -p "آیا فایل‌های پروژه را منتقل کرده‌اید؟ (y/n) [n]: " FILES_COPIED
@@ -277,194 +315,47 @@
done
if [ ${#MISSING_FILES[@]} -ne 0 ]; then
print_error "فایل‌های زیر در $APP_DIR پیدا نشدند: ${MISSING_FILES[*]}"
    print_message "محتوای فعلی پوشه $APP_DIR:"
    ls -la "$APP_DIR" >> "$LOG_FILE" 2>&1
    cat "$LOG_FILE" | tail -n 10
    print_message "لطفاً مطمئن شوید پروژه RFCBot به درستی کلون یا منتقل شده است."
    print_message "نکات: 1) بررسی کنید که مخزن درست باشد (https://github.com/Alisa202min/NoeRFcBot.git)."
    print_message "      2) اگر فایل‌ها در شاخه دیگری هستند (مثل dev)، شاخه درست را مشخص کنید."
    print_message "      3) فایل‌ها را به صورت دستی به $APP_DIR منتقل کنید (یا ZIP آپلود کنید)."
exit 1
fi
print_success "همه فایل‌های مورد نیاز پروژه موجود هستند."


# اصلاح app.py برای load_dotenv
ensure_load_dotenv

# ===== راه‌اندازی پوشه برنامه =====
print_message "در حال راه‌اندازی پوشه برنامه در $APP_DIR..."

# ایجاد پوشه‌های لازم
mkdir -p "$APP_DIR" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/static/uploads/products" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/static/uploads/services" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/static/uploads/services/main" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/static/media/products" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/logs" >> "$LOG_FILE" 2>&1
mkdir -p "$APP_DIR/static/uploads/products" "$APP_DIR/static/uploads/services" "$APP_DIR/static/uploads/services/main" "$APP_DIR/static/media/products" "$APP_DIR/logs" >> "$LOG_FILE" 2>&1
check_error "ایجاد پوشه‌های برنامه با خطا مواجه شد." "پوشه‌های برنامه با موفقیت ایجاد شدند."

# ===== بررسی فایل‌های پروژه =====
print_message "در حال بررسی فایل‌های پروژه..."
REQUIRED_FILES=("app.py" "bot.py" "database.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$APP_DIR/$file" ]; then
        print_error "فایل $file در $APP_DIR پیدا نشد. لطفاً مطمئن شوید پروژه کامل منتقل یا کلون شده است."
        exit 1
    fi
done
print_success "همه فایل‌های مورد نیاز پروژه موجود هستند."


# ===== بررسی و نصب پایتون 3.11 برای محیط مجازی =====
# ===== بررسی و نصب پایتون 3.11 =====
print_message "در حال بررسی نسخه‌های پایتون نصب‌شده..."
if command -v python3.11 >/dev/null 2>&1; then
PYTHON_VERSION=$(python3.11 --version 2>&1)
print_message "پایتون 3.11 یافت شد: $PYTHON_VERSION"
    read -p "آیا می‌خواهید با پایتون 3.11 موجود ادامه دهید؟ (y/n) [y]: " USE_EXISTING
    USE_EXISTING=${USE_EXISTING:-y}
    if [ "$USE_EXISTING" = "y" ] || [ "$USE_EXISTING" = "Y" ]; then
        print_message "ادامه با پایتون 3.11 موجود..."
        PYTHON_EXEC="python3.11"
    else
        print_message "شما انتخاب کردید پایتون 3.11 را دوباره نصب کنید."
        PYTHON_EXEC=""
    fi
    PYTHON_EXEC="python3.11"
else
    print_message "پایتون 3.11 یافت نشد. آماده‌سازی برای نصب..."
    PYTHON_EXEC=""
fi

if [ -z "$PYTHON_EXEC" ]; then
    print_message "در حال نصب پایتون 3.11..."
    print_message "مرحله 1: به‌روزرسانی مخازن و نصب ابزارهای لازم (تخمین زمان: 2-5 دقیقه)"
    apt clean >> "$LOG_FILE" 2>&1
    apt update >> "$LOG_FILE" 2>&1 || { print_warning "به‌روزرسانی مخازن با خطا مواجه شد. ادامه با مخازن فعلی..."; }
    apt install -y software-properties-common ca-certificates curl gnupg >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        print_error "نصب ابزارهای لازم (software-properties-common) با خطا مواجه شد. جزئیات در $LOG_FILE."
        exit 1
    fi
    print_success "ابزارهای لازم با موفقیت نصب شدند."

    print_message "مرحله 2: افزودن مخزن deadsnakes PPA (تخمین زمان: 1-3 دقیقه)"
    timeout 120 add-apt-repository -y ppa:deadsnakes/ppa >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        print_warning "افزودن مخزن deadsnakes با خطا مواجه شد. تلاش برای نصب دستی پایتون 3.11..."
        print_message "مرحله 2.1: نصب وابستگی‌های مورد نیاز برای نصب دستی (تخمین زمان: 2-5 دقیقه)"
        apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev curl libbz2-dev libsqlite3-dev liblzma-dev tk-dev uuid-dev >> "$LOG_FILE" 2>&1
        if [ $? -ne 0 ]; then
            print_error "نصب وابستگی‌ها با خطا مواجه شد. جزئیات در $LOG_FILE."
            exit 1
        fi
        print_success "وابستگی‌ها با موفقیت نصب شدند."

        print_message "مرحله 2.2: دانلود و استخراج پایتون 3.11 (تخمین زمان: 1-3 دقیقه)"
        cd /usr/src || { print_error "تغییر به /usr/src با خطا مواجه شد."; exit 1; }
        rm -rf Python-3.11.10* >> "$LOG_FILE" 2>&1
        wget https://www.python.org/ftp/python/3.11.10/Python-3.11.10.tar.xz >> "$LOG_FILE" 2>&1
        tar -xf Python-3.11.10.tar.xz >> "$LOG_FILE" 2>&1 || { print_error "استخراج فایل پایتون با خطا مواجه شد."; exit 1; }
        cd Python-3.11.10 || { print_error "تغییر به دایرکتوری Python-3.11.10 با خطا مواجه شد."; exit 1; }
        print_success "دانلود و استخراج با موفقیت انجام شد."

        print_message "مرحله 2.3: پیکربندی پایتون (تخمین زمان: 2-5 دقیقه)"
        ./configure --enable-optimizations >> "$LOG_FILE" 2>&1 || { print_error "پیکربندی پایتون با خطا مواجه شد."; exit 1; }
        print_success "پیکربندی با موفقیت انجام شد."

        print_message "مرحله 2.4: ساخت پایتون (تخمین زمان: 5-15 دقیقه، بسته به سخت‌افزار)"
        make -j$(nproc) >> "$LOG_FILE" 2>&1 || { print_error "ساخت پایتون با خطا مواجه شد."; exit 1; }
        print_success "ساخت پایتون با موفقیت انجام شد."

        print_message "مرحله 2.5: نصب پایتون (تخمین زمان: 1-3 دقیقه)"
        make altinstall >> "$LOG_FILE" 2>&1 || { print_error "نصب پایتون با خطا مواجه شد."; exit 1; }
        print_success "پایتون 3.11 با موفقیت نصب شد."
        PYTHON_EXEC="python3.11"
    else
        print_message "مرحله 3: نصب پایتون 3.11 از مخزن deadsnakes (تخمین زمان: 2-5 دقیقه)"
        apt update >> "$LOG_FILE" 2>&1
        apt install -y python3.11 python3.11-venv python3.11-dev >> "$LOG_FILE" 2>&1
        if [ $? -ne 0 ]; then
            print_error "نصب پایتون 3.11 با خطا مواجه شد. جزئیات در $LOG_FILE."
            exit 1
        fi
        print_success "پایتون 3.11 با موفقیت نصب شد."
        PYTHON_EXEC="python3.11"
    fi
    print_message "پایتون 3.11 یافت نشد. در حال نصب..."
    apt install -y software-properties-common >> "$LOG_FILE" 2>&1
    add-apt-repository -y ppa:deadsnakes/ppa >> "$LOG_FILE" 2>&1
    apt update >> "$LOG_FILE" 2>&1
    apt install -y python3.11 python3.11-venv python3.11-dev >> "$LOG_FILE" 2>&1
    check_error "نصب پایتون 3.11 با خطا مواجه شد." "پایتون 3.11 با موفقیت نصب شد."
    PYTHON_EXEC="python3.11"
fi

print_message "بررسی ماژول venv برای پایتون 3.11..."
if ! $PYTHON_EXEC -m venv --help >/dev/null 2>&1; then
    print_message "نصب بسته python3.11-venv (تخمین زمان: 1-2 دقیقه)..."
    apt install -y python3.11-venv >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        print_error "نصب بسته python3.11-venv با خطا مواجه شد."
        exit 1
    fi
    print_success "بسته python3.11-venv با موفقیت نصب شد."
fi
$PYTHON_EXEC -m venv --help >/dev/null 2>&1 || apt install -y python3.11-venv >> "$LOG_FILE" 2>&1
check_error "نصب python3.11-venv با خطا مواجه شد." "python3.11-venv آماده است."

print_message "در حال ایجاد محیط مجازی با پایتون 3.11 (تخمین زمان: 1 دقیقه)..."
print_message "در حال ایجاد محیط مجازی با پایتون 3.11..."
cd "$APP_DIR" || { print_error "تغییر به $APP_DIR با خطا مواجه شد."; exit 1; }
rm -rf venv >> "$LOG_FILE" 2>&1
$PYTHON_EXEC -m venv venv >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    print_error "ایجاد محیط مجازی با پایتون 3.11 با خطا مواجه شد."
    exit 1
fi
print_success "محیط مجازی با موفقیت ایجاد شد."


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
print_message "در حال ایجاد فایل .env (تخمین زمان: کمتر از 1 دقیقه)..."
check_error "ایجاد محیط مجازی با خطا مواجه شد." "محیط مجازی با موفقیت ایجاد شد."

# ایجاد یک کلید تصادفی برای SESSION_SECRET
# ===== ایجاد فایل .env =====
print_message "در حال ایجاد فایل .env..."
SESSION_SECRET=$(openssl rand -hex 32)

# ایجاد فایل .env
cat > "$APP_DIR/.env" << EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
SQLALCHEMY_DATABASE_URI=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
@@ -478,146 +369,63 @@
ADMIN_PASSWORD=$ADMIN_PASSWORD
UPLOAD_FOLDER=$APP_DIR/static/uploads
EOF
if [ $? -ne 0 ]; then
    print_error "ایجاد فایل .env با خطا مواجه شد."
    exit 1
fi
print_success "فایل .env با موفقیت ایجاد شد."

# ===== نصب وابستگی‌های پروژه =====
print_message "در حال نصب وابستگی‌های پروژه از requirements.txt (تخمین زمان: 2-5 دقیقه)..."
if [ ! -f "$APP_DIR/requirements.txt" ]; then
    print_warning "فایل requirements.txt در $APP_DIR یافت نشد. ایجاد فایل پیش‌فرض..."
    cat << EOF > "$APP_DIR/requirements.txt"
flask==3.1.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.2
SQLAlchemy==2.0.40
psycopg2-binary==2.9.10
Werkzeug==3.1.3
Jinja2==3.1.6
gunicorn==23.0.0
python-telegram-bot==20.7
aiogram==3.20.0
aiohttp==3.11.18
python-dotenv==1.1.0
Pillow==11.2.1
email-validator==2.2.0
pytest==8.3.5
pytest-flask==1.3.0
pytest-asyncio==0.26.0
PyJWT==2.10.1
oauthlib==3.2.2
requests==2.32.3
replit==4.1.1
locust==2.37.1
EOF
fi
check_error "ایجاد فایل .env با خطا مواجه شد." "فایل .env با موفقیت ایجاد شد."

# ===== نصب وابستگی‌ها =====
print_message "در حال نصب وابستگی‌های پروژه..."
source "$APP_DIR/venv/bin/activate" >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    print_error "فعال‌سازی محیط مجازی با خطا مواجه شد. لطفاً مطمئن شوید که $APP_DIR/venv وجود دارد."
    exit 1
fi
pip install --upgrade pip >> "$LOG_FILE" 2>&1
pip install -r "$APP_DIR/requirements.txt" >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
pip install -r "$APP_DIR/requirements.txt" >> "$LOG_FILE" 2>&1 || {
print_error "نصب وابستگی‌ها با خطا مواجه شد. جزئیات در $LOG_FILE."
    print_message "دستور پیشنهادی برای بررسی:"
    print_message "  source $APP_DIR/venv/bin/activate"
    print_message "  pip install -r $APP_DIR/requirements.txt"
deactivate
exit 1
fi
}
print_success "وابستگی‌های پروژه با موفقیت نصب شدند."
deactivate

# ===== راه‌اندازی پایگاه داده ============================
print_message "در حال راه‌اندازی جداول پایگاه داده (تخمین زمان: 1-2 دقیقه)..."

# فعال‌سازی محیط مجازی اگر فعال نیست
if ! command -v python | grep -q "$APP_DIR/venv" 2>/dev/null; then
    source "$APP_DIR/venv/bin/activate" >> "$LOG_FILE" 2>&1
fi
# ===== راه‌اندازی پایگاه داده =====
print_message "در حال راه‌اندازی جداول پایگاه داده..."
source "$APP_DIR/venv/bin/activate" >> "$LOG_FILE" 2>&1

# ایجاد اسکریپت موقت برای راه‌اندازی جداول
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

# بررسی وجود فایل app.py
if [ -f "$APP_DIR/app.py" ]; then
    python "$APP_DIR/init_db.py" >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        print_error "ایجاد جداول پایگاه داده با خطا مواجه شد. جزئیات در $LOG_FILE."
        print_message "دستور پیشنهادی برای بررسی:"
        print_message "  cd $APP_DIR"
        print_message "  source venv/bin/activate"
        print_message "  python init_db.py"
        print_message "نکات عیب‌یابی:"
        print_message "  1) فایل $APP_DIR/.env را بررسی کنید (حاوی SQLALCHEMY_DATABASE_URI)."
        print_message "  2) مطمئن شوید PostgreSQL در حال اجرا است: sudo systemctl status postgresql"
        print_message "  3) اتصال به دیتابیس را تست کنید: psql -U $DB_USER -d $DB_NAME -h localhost"
        deactivate
        exit 1
    fi
    print_success "جداول پایگاه داده با موفقیت ایجاد شدند."
elif [ -f "$APP_DIR/src/web/app.py" ]; then
    # اگر از ساختار ماژولار استفاده می‌شود
    export PYTHONPATH="$APP_DIR"
    python "$APP_DIR/init_db.py" >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        print_error "ایجاد جداول پایگاه داده با خطا مواجه شد. جزئیات در $LOG_FILE."
        print_message "دستور پیشنهادی برای بررسی:"
        print_message "  cd $APP_DIR"
        print_message "  source venv/bin/activate"
        print_message "  export PYTHONPATH=$APP_DIR"
        print_message "  python init_db.py"
        print_message "نکات عیب‌یابی:"
        print_message "  1) فایل $APP_DIR/.env را بررسی کنید (حاوی SQLALCHEMY_DATABASE_URI)."
        print_message "  2) مطمئن شوید PostgreSQL در حال اجرا است: sudo systemctl status postgresql"
        print_message "  3) اتصال به دیتابیس را تست کنید: psql -U $DB_USER -d $DB_NAME -h localhost"
        deactivate
        exit 1
    fi
    print_success "جداول پایگاه داده با موفقیت ایجاد شدند."
else
    print_warning "فایل app.py پیدا نشد. لطفاً به صورت دستی جداول پایگاه داده را ایجاد کنید."
    deactivate
    exit 1
fi
python "$APP_DIR/init_db.py" >> "$LOG_FILE" 2>&1
check_error "ایجاد جداول پایگاه داده با خطا مواجه شد. جزئیات در $LOG_FILE." "جداول پایگاه داده با موفقیت ایجاد شدند."

# اجرای اسکریپت‌های تنظیمات اولیه
if [ -f "$APP_DIR/seed_admin_data.py" ]; then
    print_message "در حال اجرای اسکریپت seed_admin_data.py (تخمین زمان: کمتر از 1 دقیقه)..."
    python "$APP_DIR/seed_admin_data.py" >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        print_warning "اجرای seed_admin_data.py با خطا مواجه شد. جزئیات در $LOG_FILE."
    else
        print_success "اسکریپت seed_admin_data.py با موفقیت اجرا شد."
    fi
fi
# بررسی جداول
check_db_tables

if [ -f "$APP_DIR/seed_categories.py" ]; then
    print_message "در حال اجرای اسکریپت seed_categories.py (تخمین زمان: کمتر از 1 دقیقه)..."
    python "$APP_DIR/seed_categories.py" >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        print_warning "اجرای seed_categories.py با خطا مواجه شد. جزئیات در $LOG_FILE."
    else
        print_success "اسکریپت seed_categories.py با موفقیت اجرا شد."
# اجرای اسکریپت‌های اولیه
for script in seed_admin_data.py seed_categories.py; do
    if [ -f "$APP_DIR/$script" ]; then
        print_message "در حال اجرای $script..."
        python "$APP_DIR/$script" >> "$LOG_FILE" 2>&1 || print_warning "اجرای $script با خطا مواجه شد."
fi
fi
done

deactivate

deactivate >> "$LOG_FILE" 2>&1
# ===== ایجاد سرویس‌ها =====
print_message "در حال ایجاد سرویس‌های سیستمی..."

# سرویس وب
cat > /etc/systemd/system/rfbot-web.service << EOF
[Unit]
Description=Gunicorn instance to serve RF Web Panel
@@ -635,7 +443,6 @@
WantedBy=multi-user.target
EOF

# سرویس بات تلگرام
cat > /etc/systemd/system/rfbot-telegram.service << EOF
[Unit]
Description=RF Telegram Bot
@@ -653,38 +460,26 @@
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
@@ -694,30 +489,24 @@
   }
}
EOF

ln -sf /etc/nginx/sites-available/rfbot /etc/nginx/sites-enabled/ >> "$LOG_FILE" 2>&1
nginx -t >> "$LOG_FILE" 2>&1
check_error "تست پیکربندی Nginx با خطا مواجه شد." "پیکربندی Nginx با موفقیت تست شد."

# ===== تنظیم دسترسی‌ها =====
# ===== تنظیم دسترسی‌ها و راه‌اندازی سرویس‌ها =====
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
systemctl enable rfbot-web rfbot-telegram >> "$LOG_FILE" 2>&1
systemctl start rfbot-web rfbot-telegram >> "$LOG_FILE" 2>&1
systemctl restart nginx >> "$LOG_FILE" 2>&1
check_error "راه‌اندازی سرویس‌ها با خطا مواجه شد." "سرویس‌ها با موفقیت راه‌اندازی شدند."

# ===== نمایش اطلاعات نهایی =====
echo ""
echo "================== نصب با موفقیت انجام شد! =================="
echo ""
echo "🌐 اطلاعات دسترسی:"
if [ "$SERVER_NAME" = "_" ]; then
echo "   آدرس پنل ادمین: http://SERVER_IP/admin"
@@ -726,33 +515,16 @@
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

echo "✅ سیستم با موفقیت نصب شد."
exit 0
