#!/bin/bash

# ===== اسکریپت تست کامل سیستم RFCBot =====
# این اسکریپت تمام اجزای سیستم را بدون تغییر تست می‌کند
# و لاگ کاملی برای عیب‌یابی تولید می‌کند

# ===== تنظیمات =====
LOG_FILE="/tmp/rfbot_test_$(date +%Y%m%d_%H%M%S).log"
APP_DIR="/var/www/rfbot"
TEST_RESULTS=()

# رنگ‌ها
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ===== توابع =====
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1" | tee -a "$LOG_FILE"
    TEST_RESULTS+=("✅ $1")
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
    TEST_RESULTS+=("⚠️  $1")
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1" | tee -a "$LOG_FILE"
    TEST_RESULTS+=("❌ $1")
}

test_separator() {
    echo -e "\n$1" | tee -a "$LOG_FILE"
    echo "$(printf '%*s' ${#1} '' | tr ' ' '=')" | tee -a "$LOG_FILE"
}

# ===== شروع تست =====
clear
echo "========================================================"
echo "           تست کامل سیستم RFCBot"
echo "========================================================"
echo ""
log_info "فایل لاگ: $LOG_FILE"
echo ""

# اطلاعات سیستم
test_separator "🖥️  اطلاعات سیستم عمومی"
echo "تاریخ و زمان: $(date)" >> "$LOG_FILE"
echo "کاربر اجرا: $(whoami)" >> "$LOG_FILE"
echo "نسخه OS: $(lsb_release -d 2>/dev/null || cat /etc/os-release | head -1)" >> "$LOG_FILE"
echo "RAM موجود: $(free -h | grep '^Mem:' | awk '{print $7}')" >> "$LOG_FILE"
echo "فضای دیسک: $(df -h / | tail -1 | awk '{print $4}')" >> "$LOG_FILE"

# ===== تست 1: پکیج‌های سیستم =====
test_separator "📦 تست پکیج‌های مورد نیاز"

# PostgreSQL
if command -v psql >/dev/null 2>&1; then
    PG_VERSION=$(psql --version 2>&1)
    log_success "PostgreSQL نصب شده - $PG_VERSION"
    echo "PostgreSQL version: $PG_VERSION" >> "$LOG_FILE"
else
    log_error "PostgreSQL نصب نشده"
fi

# Python
if command -v python3 >/dev/null 2>&1; then
    PY_VERSION=$(python3 --version 2>&1)
    log_success "Python3 نصب شده - $PY_VERSION"
    echo "Python version: $PY_VERSION" >> "$LOG_FILE"
else
    log_error "Python3 نصب نشده"
fi

# Nginx
if command -v nginx >/dev/null 2>&1; then
    NGINX_VERSION=$(nginx -v 2>&1)
    log_success "Nginx نصب شده - $NGINX_VERSION"
    echo "Nginx version: $NGINX_VERSION" >> "$LOG_FILE"
else
    log_error "Nginx نصب نشده"
fi

# Git
if command -v git >/dev/null 2>&1; then
    GIT_VERSION=$(git --version 2>&1)
    log_success "Git نصب شده - $GIT_VERSION"
else
    log_warning "Git نصب نشده"
fi

# ===== تست 2: سرویس‌ها =====
test_separator "🔧 تست وضعیت سرویس‌ها"

# PostgreSQL Service
if systemctl is-active --quiet postgresql; then
    log_success "سرویس PostgreSQL فعال است"
    systemctl status postgresql --no-pager >> "$LOG_FILE" 2>&1
else
    log_error "سرویس PostgreSQL غیرفعال است"
    systemctl status postgresql --no-pager >> "$LOG_FILE" 2>&1
fi

# Nginx Service
if systemctl is-active --quiet nginx; then
    log_success "سرویس Nginx فعال است"
    systemctl status nginx --no-pager >> "$LOG_FILE" 2>&1
else
    log_error "سرویس Nginx غیرفعال است"
    systemctl status nginx --no-pager >> "$LOG_FILE" 2>&1
fi

# RFBot Services
if systemctl list-unit-files | grep -q rfbot-web; then
    if systemctl is-active --quiet rfbot-web; then
        log_success "سرویس RFBot Web فعال است"
    else
        log_error "سرویس RFBot Web غیرفعال است"
    fi
    systemctl status rfbot-web --no-pager >> "$LOG_FILE" 2>&1
else
    log_warning "سرویس RFBot Web تعریف نشده"
fi

if systemctl list-unit-files | grep -q rfbot-telegram; then
    if systemctl is-active --quiet rfbot-telegram; then
        log_success "سرویس RFBot Telegram فعال است"
    else
        log_error "سرویس RFBot Telegram غیرفعال است"
    fi
    systemctl status rfbot-telegram --no-pager >> "$LOG_FILE" 2>&1
else
    log_warning "سرویس RFBot Telegram تعریف نشده"
fi

# ===== تست 3: شبکه و پورت‌ها =====
test_separator "🌐 تست شبکه و پورت‌ها"

# اتصال اینترنت
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    log_success "اتصال به اینترنت برقرار است"
else
    log_error "مشکل در اتصال به اینترنت"
fi

# DNS
if nslookup google.com >/dev/null 2>&1; then
    log_success "DNS کار می‌کند"
else
    log_warning "مشکل در DNS"
fi

# پورت‌های مهم
echo "بررسی پورت‌های باز:" >> "$LOG_FILE"
netstat -tulpn 2>/dev/null >> "$LOG_FILE" || ss -tulpn >> "$LOG_FILE"

PORTS=(80 443 5000 5432 22)
for port in "${PORTS[@]}"; do
    if netstat -tulpn 2>/dev/null | grep -q ":$port " || ss -tulpn | grep -q ":$port "; then
        log_success "پورت $port باز است"
    else
        log_warning "پورت $port بسته است"
    fi
done

# ===== تست 4: فایل‌های پروژه =====
test_separator "📁 تست فایل‌های پروژه"

if [ -d "$APP_DIR" ]; then
    log_success "پوشه پروژه ($APP_DIR) موجود است"
    
    # فایل‌های اصلی
    REQUIRED_FILES=("main.py" "bot.py" "database.py" "handlers.py" "keyboards.py")
    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$APP_DIR/$file" ]; then
            log_success "فایل $file موجود است"
        else
            log_error "فایل $file موجود نیست"
        fi
    done
    
    # پوشه‌های مهم
    REQUIRED_DIRS=("static" "templates" "logs")
    for dir in "${REQUIRED_DIRS[@]}"; do
        if [ -d "$APP_DIR/$dir" ]; then
            log_success "پوشه $dir موجود است"
        else
            log_warning "پوشه $dir موجود نیست"
        fi
    done
    
    # محیط مجازی
    if [ -d "$APP_DIR/venv" ]; then
        log_success "محیط مجازی Python موجود است"
        if [ -f "$APP_DIR/venv/bin/python" ]; then
            VENV_PY_VERSION=$("$APP_DIR/venv/bin/python" --version 2>&1)
            echo "Virtual env Python: $VENV_PY_VERSION" >> "$LOG_FILE"
        fi
    else
        log_error "محیط مجازی Python موجود نیست"
    fi
    
else
    log_error "پوشه پروژه ($APP_DIR) موجود نیست"
fi

# ===== تست 5: فایل‌های تنظیمات =====
test_separator "⚙️  تست فایل‌های تنظیمات"

# فایل .env
if [ -f "$APP_DIR/.env" ]; then
    log_success "فایل .env موجود است"
    echo "محتوای .env (بدون مقادیر حساس):" >> "$LOG_FILE"
    grep -E '^[A-Z_]+=.*' "$APP_DIR/.env" | sed 's/=.*/=***/' >> "$LOG_FILE" 2>&1
else
    log_error "فایل .env موجود نیست"
fi

# فایل requirements.txt
if [ -f "$APP_DIR/requirements.txt" ]; then
    log_success "فایل requirements.txt موجود است"
    echo "محتوای requirements.txt:" >> "$LOG_FILE"
    cat "$APP_DIR/requirements.txt" >> "$LOG_FILE" 2>&1
else
    log_warning "فایل requirements.txt موجود نیست"
fi

# ===== تست 6: دیتابیس =====
test_separator "🗄️  تست دیتابیس"

# بررسی اتصال PostgreSQL
if command -v psql >/dev/null 2>&1; then
    # تلاش برای اتصال با کاربرهای مختلف
    DB_USERS=("neondb_owner" "postgres" "rfbot")
    DB_NAMES=("neondb" "rfbot" "postgres")
    
    DB_CONNECTION_SUCCESS=false
    for user in "${DB_USERS[@]}"; do
        for dbname in "${DB_NAMES[@]}"; do
            if su -c "psql -U $user -d $dbname -c 'SELECT 1;'" postgres >/dev/null 2>&1; then
                log_success "اتصال به دیتابیس موفق: $user@$dbname"
                echo "Database connection successful: $user@$dbname" >> "$LOG_FILE"
                
                # لیست جداول
                echo "جداول موجود در $dbname:" >> "$LOG_FILE"
                su -c "psql -U $user -d $dbname -c '\dt'" postgres >> "$LOG_FILE" 2>&1
                
                DB_CONNECTION_SUCCESS=true
                break 2
            fi
        done
    done
    
    if [ "$DB_CONNECTION_SUCCESS" = false ]; then
        log_error "اتصال به هیچ دیتابیسی موفق نبود"
    fi
else
    log_error "PostgreSQL در دسترس نیست"
fi

# ===== تست 7: دسترسی‌ها =====
test_separator "🔐 تست دسترسی‌ها"

if [ -d "$APP_DIR" ]; then
    # مالکیت فایل‌ها
    OWNER=$(stat -c '%U' "$APP_DIR" 2>/dev/null)
    GROUP=$(stat -c '%G' "$APP_DIR" 2>/dev/null)
    if [ "$OWNER" = "www-data" ] && [ "$GROUP" = "www-data" ]; then
        log_success "مالکیت فایل‌ها درست است (www-data:www-data)"
    else
        log_warning "مالکیت فایل‌ها: $OWNER:$GROUP (باید www-data:www-data باشد)"
    fi
    
    # مجوزهای پوشه‌ها
    if [ -w "$APP_DIR/logs" ] 2>/dev/null; then
        log_success "دسترسی نوشتن به پوشه logs"
    else
        log_error "عدم دسترسی نوشتن به پوشه logs"
    fi
    
    if [ -w "$APP_DIR/static/uploads" ] 2>/dev/null; then
        log_success "دسترسی نوشتن به پوشه uploads"
    else
        log_error "عدم دسترسی نوشتن به پوشه uploads"
    fi
fi

# ===== تست 8: اتصال HTTP =====
test_separator "🌍 تست اتصال HTTP"

# تست پورت 5000 (Flask)
if curl -s -m 5 http://localhost:5000 >/dev/null 2>&1; then
    log_success "وب سرور Flask (پورت 5000) پاسخ می‌دهد"
    echo "HTTP response از localhost:5000:" >> "$LOG_FILE"
    curl -s -I http://localhost:5000 >> "$LOG_FILE" 2>&1
else
    log_error "وب سرور Flask (پورت 5000) پاسخ نمی‌دهد"
fi

# تست پورت 80 (Nginx)
if curl -s -m 5 http://localhost >/dev/null 2>&1; then
    log_success "وب سرور Nginx (پورت 80) پاسخ می‌دهد"
    echo "HTTP response از localhost:80:" >> "$LOG_FILE"
    curl -s -I http://localhost >> "$LOG_FILE" 2>&1
else
    log_error "وب سرور Nginx (پورت 80) پاسخ نمی‌دهد"
fi

# ===== تست 9: فایروال =====
test_separator "🛡️  تست فایروال"

if command -v ufw >/dev/null 2>&1; then
    UFW_STATUS=$(ufw status 2>&1)
    echo "وضعیت UFW:" >> "$LOG_FILE"
    echo "$UFW_STATUS" >> "$LOG_FILE"
    
    if echo "$UFW_STATUS" | grep -q "Status: active"; then
        log_success "UFW فایروال فعال است"
        if echo "$UFW_STATUS" | grep -q "80/tcp"; then
            log_success "پورت 80 در فایروال باز است"
        else
            log_warning "پورت 80 در فایروال بسته است"
        fi
    else
        log_warning "UFW فایروال غیرفعال است"
    fi
else
    log_warning "UFW نصب نشده"
fi

# ===== تست 10: لاگ‌ها =====
test_separator "📋 بررسی لاگ‌ها"

# لاگ‌های سیستم
if [ -f "/var/log/nginx/error.log" ]; then
    log_success "لاگ خطای Nginx موجود است"
    echo "آخرین خطاهای Nginx:" >> "$LOG_FILE"
    tail -10 /var/log/nginx/error.log >> "$LOG_FILE" 2>&1
else
    log_warning "لاگ خطای Nginx موجود نیست"
fi

# لاگ‌های پروژه
if [ -f "$APP_DIR/bot.log" ]; then
    log_success "لاگ بات تلگرام موجود است"
    echo "آخرین لاگ‌های بات:" >> "$LOG_FILE"
    tail -10 "$APP_DIR/bot.log" >> "$LOG_FILE" 2>&1
else
    log_warning "لاگ بات تلگرام موجود نیست"
fi

# ===== خلاصه نتایج =====
test_separator "📊 خلاصه نتایج تست"

PASS_COUNT=$(printf '%s\n' "${TEST_RESULTS[@]}" | grep -c "✅")
WARN_COUNT=$(printf '%s\n' "${TEST_RESULTS[@]}" | grep -c "⚠️")
FAIL_COUNT=$(printf '%s\n' "${TEST_RESULTS[@]}" | grep -c "❌")
TOTAL_COUNT=${#TEST_RESULTS[@]}

echo ""
echo "نتایج نهایی:"
echo "=============="
echo -e "${GREEN}موفق: $PASS_COUNT${NC}"
echo -e "${YELLOW}هشدار: $WARN_COUNT${NC}"
echo -e "${RED}خطا: $FAIL_COUNT${NC}"
echo "کل: $TOTAL_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    if [ $WARN_COUNT -eq 0 ]; then
        echo -e "${GREEN}🎉 سیستم کاملاً سالم است!${NC}"
    else
        echo -e "${YELLOW}⚠️  سیستم عمدتاً سالم است ولی نیاز به بررسی دارد.${NC}"
    fi
else
    echo -e "${RED}❌ سیستم مشکلاتی دارد که نیاز به حل فوری دارند.${NC}"
fi

echo ""
echo "جزئیات کامل در فایل لاگ: $LOG_FILE"
echo ""
echo "برای ارسال به توسعه‌دهنده:"
echo "cat $LOG_FILE"

# اطلاعات سیستم نهایی
echo -e "\n=== اطلاعات سیستم برای عیب‌یابی ===" >> "$LOG_FILE"
echo "Uptime: $(uptime)" >> "$LOG_FILE"
echo "Load average: $(cat /proc/loadavg)" >> "$LOG_FILE"
echo "Memory usage: $(free -m)" >> "$LOG_FILE"
echo "Disk usage: $(df -h)" >> "$LOG_FILE"
echo "Active connections: $(netstat -an | grep ESTABLISHED | wc -l)" >> "$LOG_FILE"