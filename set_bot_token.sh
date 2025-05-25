#!/bin/bash

# ===== اسکریپت تنظیم توکن بات تلگرام =====
# این اسکریپت توکن بات تلگرام را از کاربر دریافت کرده و در فایل .env پروژه تنظیم می‌کند
# توجه: باید با دسترسی sudo اجرا شود

# ===== تنظیمات رنگ‌های خروجی =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ===== مسیر لاگ =====
LOG_FILE="/tmp/rfbot_set_token_$(date +%Y%m%d_%H%M%S).log"

# ===== مسیر پروژه =====
APP_DIR="/var/www/rfbot"
ENV_FILE="$APP_DIR/.env"

# ===== توابع =====
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

check_error() {
    if [ $? -ne 0 ]; then
        print_error "$1"
    else
        print_success "$2"
    fi
}

# ===== بررسی دسترسی روت =====
if [ "$EUID" -ne 0 ]; then
    print_error "این اسکریپت نیاز به دسترسی روت دارد. لطفاً با دستور sudo اجرا کنید."
fi

# ===== نمایش عنوان =====
clear
echo "========================================================"
echo "        تنظیم توکن بات تلگرام سیستم رادیو فرکانس"
echo "========================================================"
echo ""
print_message "فایل لاگ در مسیر $LOG_FILE ذخیره می‌شود."
echo ""

# ===== بررسی وجود فایل .env =====
if [ ! -f "$ENV_FILE" ]; then
    print_error "فایل $ENV_FILE یافت نشد. لطفاً مطمئن شوید پروژه در $APP_DIR نصب شده است."
fi

# ===== دریافت توکن از کاربر =====
echo "لطفاً توکن بات تلگرام را وارد کنید:"
echo "--------------------------------"
read -p "توکن بات تلگرام: " TELEGRAM_BOT_TOKEN
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    print_error "توکن بات تلگرام نمی‌تواند خالی باشد."
fi

# ===== به‌روزرسانی فایل .env =====
print_message "در حال به‌روزرسانی فایل $ENV_FILE..."

# پشتیبان‌گیری از فایل .env
BACKUP_FILE="${ENV_FILE}.backup_$(date +%Y%m%d_%H%M%S)"
cp "$ENV_FILE" "$BACKUP_FILE" >> "$LOG_FILE" 2>&1
check_error "ایجاد نسخه پشتیبان از $ENV_FILE با خطا مواجه شد." "نسخه پشتیبان در $BACKUP_FILE ایجاد شد."

# بررسی وجود TELEGRAM_BOT_TOKEN در فایل .env
if grep -q "^TELEGRAM_BOT_TOKEN=" "$ENV_FILE"; then
    # جایگزینی مقدار TELEGRAM_BOT_TOKEN
    sed -i "s|^TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN|" "$ENV_FILE" >> "$LOG_FILE" 2>&1
    check_error "به‌روزرسانی TELEGRAM_BOT_TOKEN در $ENV_FILE با خطا مواجه شد." "TELEGRAM_BOT_TOKEN با موفقیت به‌روزرسانی شد."
else
    # افزودن TELEGRAM_BOT_TOKEN به انتهای فایل
    echo "TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN" >> "$ENV_FILE" >> "$LOG_FILE" 2>&1
    check_error "افزودن TELEGRAM_BOT_TOKEN به $ENV_FILE با خطا مواجه شد." "TELEGRAM_BOT_TOKEN با موفقیت اضافه شد."
fi

# ===== تنظیم دسترسی‌های فایل .env =====
print_message "در حال تنظیم دسترسی‌های فایل $ENV_FILE..."
chown www-data:www-data "$ENV_FILE" >> "$LOG_FILE" 2>&1
chmod 640 "$ENV_FILE" >> "$LOG_FILE" 2>&1
check_error "تنظیم دسترسی‌های $ENV_FILE با خطا مواجه شد." "دسترسی‌های $ENV_FILE با موفقیت تنظیم شد."

# ===== ری‌استارت سرویس بات =====
print_message "در حال ری‌استارت سرویس rfbot-telegram..."
systemctl restart rfbot-telegram >> "$LOG_FILE" 2>&1
check_error "ری‌استارت سرویس rfbot-telegram با خطا مواجه شد." "سرویس rfbot-telegram با موفقیت ری‌استارت شد."

# ===== بررسی وضعیت سرویس =====
print_message "در حال بررسی وضعیت سرویس rfbot-telegram..."
if systemctl is-active --quiet rfbot-telegram; then
    print_success "سرویس rfbot-telegram در حال اجرا است."
else
    print_error "سرویس rfbot-telegram اجرا نشد. جزئیات در $LOG_FILE و لاگ‌های سرویس."
    print_message "دستور پیشنهادی برای بررسی:"
    print_message "  sudo journalctl -u rfbot-telegram -n 50"
fi

# ===== نمایش اطلاعات نهایی =====
echo ""
echo "================== تنظیم توکن با موفقیت انجام شد! =================="
echo ""
echo "🤖 اطلاعات بات تلگرام:"
echo "   توکن بات: $TELEGRAM_BOT_TOKEN"
echo "   مسیر فایل تنظیمات: $ENV_FILE"
echo "   فایل لاگ: $LOG_FILE"
echo ""
echo "⚙️ دستورات مفید:"
echo "   مشاهده لاگ‌های بات: sudo journalctl -u rfbot-telegram -f"
echo "   ری‌استارت سرویس بات: sudo systemctl restart rfbot-telegram"
echo ""
echo "✅ توکن بات با موفقیت تنظیم شد."
echo ""

exit 0
