#!/bin/bash

# اسکریپت رفع مشکل وب پنل rfbot
# اجرا با: sudo bash fix_rfbot_web.sh

# رنگ‌ها برای خروجی
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# مسیرها
SERVICE_FILE="/etc/systemd/system/rfbot-web.service"
ENV_FILE="/var/www/rfbot/.env"
APP_PY="/var/www/rfbot/src/web/app.py"
MAIN_PY="/var/www/rfbot/main.py"
LOG_FILE="/tmp/rfbot_fix_$(date +%F_%H%M%S).log"

# شروع لاگ
echo "شروع رفع مشکل rfbot - $(date)" > "$LOG_FILE"
echo "------------------------------------" >> "$LOG_FILE"

# تابع برای لاگ و خروجی
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# تابع برای اجرای دستور و بررسی خطا
run_cmd() {
    echo "اجرای: $1" >> "$LOG_FILE"
    eval "$1" >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        log "${GREEN}✓ موفقیت: $2${NC}"
    else
        log "${RED}✗ خطا: $2${NC}"
        return 1
    fi
}

# 1. اصلاح فایل سرویس rfbot-web
log "اصلاح فایل سرویس rfbot-web..."
cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=Gunicorn instance to serve RF Web Panel
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/rfbot
Environment="PATH=/var/www/rfbot/venv/bin"
EnvironmentFile=/var/www/rfbot/.env
ExecStart=/var/www/rfbot/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 --timeout 120 src.web.app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
run_cmd "sudo systemctl daemon-reload" "ری‌لود systemd"
run_cmd "sudo systemctl restart rfbot-web" "ری‌استارت سرویس rfbot-web"

# 2. بررسی و اصلاح فایل .env
log "بررسی فایل .env..."
if [ ! -f "$ENV_FILE" ]; then
    log "${RED}✗ فایل .env وجود ندارد، ایجاد فایل...${NC}"
    cat > "$ENV_FILE" << 'EOF'
DATABASE_URL=postgresql://neondb_owner:npg_nguJUcZGPX83@localhost/neondb
SQLALCHEMY_DATABASE_URI=postgresql://neondb_owner:npg_nguJUcZGPX83@localhost/neondb
SESSION_SECRET=supersecretkey1234567890
BOT_TOKEN=7630601243:AAF2Xtot-K55wzrnbkxS9bo_tBTj8Dq6uGs
BOT_MODE=polling
UPLOAD_FOLDER=/var/www/rfbot/static/uploads
EOF
else
    log "${GREEN}✓ فایل .env وجود دارد، بررسی محتوا...${NC}"
    grep -q "SQLALCHEMY_DATABASE_URI" "$ENV_FILE" || echo "SQLALCHEMY_DATABASE_URI=postgresql://neondb_owner:npg_nguJUcZGPX83@localhost/neondb" >> "$ENV_FILE"
    grep -q "DATABASE_URL" "$ENV_FILE" || echo "DATABASE_URL=postgresql://neondb_owner:npg_nguJUcZGPX83@localhost/neondb" >> "$ENV_FILE"
fi

# تنظیم دسترسی .env
run_cmd "sudo chown www-data:www-data $ENV_FILE" "تنظیم مالکیت .env"
run_cmd "sudo chmod 640 $ENV_FILE" "تنظیم دسترسی .env"

# 3. نصب python-dotenv اگه لازم باشه
log "نصب python-dotenv..."
run_cmd "source /var/www/rfbot/venv/bin/activate && pip install python-dotenv" "نصب python-dotenv"

# 4. اصلاح app.py برای لود .env
log "اصلاح app.py برای لود .env..."
if [ -f "$APP_PY" ]; then
    if ! grep -q "from dotenv import load_dotenv" "$APP_PY"; then
        sed -i '1i from dotenv import load_dotenv\nimport os\nload_dotenv()\n' "$APP_PY"
        log "${GREEN}✓ اضافه کردن load_dotenv به app.py${NC}"
    else
        log "${GREEN}✓ load_dotenv قبلاً در app.py وجود دارد${NC}"
    fi
    # اطمینان از تنظیم SQLALCHEMY_DATABASE_URI
    if ! grep -q "SQLALCHEMY_DATABASE_URI.*raise ValueError" "$APP_PY"; then
        sed -i '/SQLALCHEMY_DATABASE_URI/c\app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL")\nif not app.config["SQLALCHEMY_DATABASE_URI"]:\n    raise ValueError("SQLALCHEMY_DATABASE_URI is not set in .env file")' "$APP_PY"
        log "${GREEN}✓ اصلاح تنظیمات SQLALCHEMY_DATABASE_URI در app.py${NC}"
    fi
else
    log "${RED}✗ فایل app.py پیدا نشد!${NC}"
    exit 1
fi

# 5. بکاپ و غیرفعال کردن main.py
log "مدیریت main.py..."
if [ -f "$MAIN_PY" ]; then
    run_cmd "sudo mv $MAIN_PY $MAIN_PY.bak" "بکاپ main.py"
else
    log "${GREEN}✓ main.py وجود ندارد، نیازی به تغییر نیست${NC}"
fi

# 6. ری‌استارت سرویس‌ها
log "ری‌استارت سرویس‌ها..."
run_cmd "sudo systemctl restart rfbot-web" "ری‌استارت rfbot-web"
run_cmd "sudo systemctl restart nginx" "ری‌استارت nginx"

# 7. تست اتصال به دیتابیس
log "تست اتصال به دیتابیس..."
run_cmd "export PGPASSWORD=npg_nguJUcZGPX83 && psql -U neondb_owner -d neondb -h localhost -c 'SELECT 1;'" "تست اتصال psql"

# 8. جمع‌آوری لاگ‌ها و وضعیت
log "جمع‌آوری وضعیت و لاگ‌ها..."
run_cmd "sudo systemctl status rfbot-web" "وضعیت rfbot-web" >> "$LOG_FILE"
run_cmd "sudo journalctl -u rfbot-web -n 200" "لاگ‌های rfbot-web" >> "$LOG_FILE"
run_cmd "sudo systemctl status nginx" "وضعیت nginx" >> "$LOG_FILE"
run_cmd "sudo journalctl -u nginx -n 100" "لاگ‌های nginx" >> "$LOG_FILE"
run_cmd "curl -v http://localhost:5000" "تست curl localhost" >> "$LOG_FILE"
run_cmd "curl -v http://$(hostname -I | awk '{print $1}')" "تست curl IP" >> "$LOG_FILE"

# 9. بررسی داده‌های دیتابیس
log "بررسی داده‌های دیتابیس..."
run_cmd "export PGPASSWORD=npg_nguJUcZGPX83 && psql -U neondb_owner -d neondb -h localhost -c '\dt'" "لیست جداول" >> "$LOG_FILE"
run_cmd "export PGPASSWORD=npg_nguJUcZGPX83 && psql -U neondb_owner -d neondb -h localhost -c 'SELECT * FROM products LIMIT 5;'" "نمایش 5 محصول" >> "$LOG_FILE"
run_cmd "export PGPASSWORD=npg_nguJUcZGPX83 && psql -U neondb_owner -d neondb -h localhost -c 'SELECT * FROM services LIMIT 5;'" "نمایش 5 خدمت" >> "$LOG_FILE"

# 10. تست دستی Gunicorn
log "تست دستی Gunicorn..."
echo "اجرای Gunicorn در پس‌زمینه..." >> "$LOG_FILE"
source /var/www/rfbot/venv/bin/activate
/var/www/rfbot/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 --timeout 120 src.web.app:app >> "$LOG_FILE" 2>&1 &
GUNICORN_PID=$!
sleep 5
if ps -p $GUNICORN_PID > /dev/null; then
    log "${GREEN}✓ Gunicorn اجرا شد، تست دسترسی...${NC}"
    run_cmd "curl http://localhost:5000" "تست دسترسی به Gunicorn"
    kill $GUNICORN_PID
else
    log "${RED}✗ Gunicorn اجرا نشد، لاگ‌ها را چک کنید${NC}"
fi

# پایان
log "------------------------------------"
log "رفع مشکل تمام شد. لاگ‌ها در $LOG_FILE ذخیره شدند."
log "لطفاً وب پنل را در مرورگر تست کنید: http://$(hostname -I | awk '{print $1}')/admin"
log "نام کاربری: admin | رمز: admin123"
log "اگر مشکل حل نشد، فایل $LOG_FILE را بررسی کنید و خروجی‌ها را بفرستید."