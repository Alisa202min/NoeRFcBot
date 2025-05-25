#!/bin/bash

# اسکریپت سریع برای رفع مشکلات باقی‌مونده rfbot
# اجرا با: sudo bash quick_fix_rfbot.sh

LOG_FILE="/tmp/rfbot_quick_fix_$(date +%F_%H%M%S).log"
echo "شروع رفع سریع rfbot - $(date)" > "$LOG_FILE"

# تابع برای لاگ
log() {
    echo "$1" | tee -a "$LOG_FILE"
}

# تابع برای اجرای دستور
run_cmd() {
    echo "اجرای: $1" >> "$LOG_FILE"
    eval "$1" >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        log "✓ موفقیت: $2"
    else
        log "✗ خطا: $2"
    fi
}

# 1. رفع تداخل Nginx
log "رفع تداخل Nginx..."
run_cmd "sudo rm /etc/nginx/sites-enabled/default" "حذف فایل default"
run_cmd "sudo sed -i 's/server_name _/server_name 185.10.75.180/' /etc/nginx/sites-available/rfbot" "اصلاح server_name"
run_cmd "sudo nginx -t" "تست تنظیمات Nginx"
run_cmd "sudo systemctl restart nginx" "ری‌استارت Nginx"

# 2. باز کردن پورت 80
log "باز کردن پورت 80..."
run_cmd "sudo ufw allow 80" "باز کردن پورت 80 در ufw"
run_cmd "sudo ss -tuln | grep :80" "چک کردن پورت 80"

# 3. نصب flask-admin
log "نصب flask-admin..."
run_cmd "source /var/www/rfbot/venv/bin/activate && pip install flask-admin" "نصب flask-admin"

# 4. ری‌استارت سرویس
log "ری‌استارت سرویس..."
run_cmd "sudo systemctl restart rfbot-web" "ری‌استارت rfbot-web"

# 5. تست دسترسی
log "تست دسترسی..."
run_cmd "curl -v http://185.10.75.180/admin" "تست curl به /admin"
run_cmd "curl -v http://localhost:5000/admin" "تست curl به localhost"

# 6. چک کردن دیتابیس
log "چک کردن دیتابیس..."
run_cmd "export PGPASSWORD=npg_nguJUcZGPX83 && psql -U neondb_owner -d neondb -h localhost -c 'SELECT count(*) FROM products;'" "شمارش محصولات"
run_cmd "export PGPASSWORD=npg_nguJUcZGPX83 && psql -U neondb_owner -d neondb -h localhost -c 'SELECT count(*) FROM services;'" "شمارش خدمات"

log "------------------------------------"
log "رفع سریع تمام شد. لاگ‌ها در $LOG_FILE ذخیره شدند."
log "لطفاً وب پنل را در مرورگر تست کنید: http://185.10.75.180/admin"