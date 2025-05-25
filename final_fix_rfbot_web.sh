#!/bin/bash

# اسکریپت نهایی برای رفع مشکلات rfbot
# اجرا با: sudo bash final_fix_rfbot.sh

LOG_FILE="/tmp/rfbot_final_fix_$(date +%F_%H%M%S).log"
echo "شروع رفع نهایی rfbot - $(date)" > "$LOG_FILE"

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

# 1. چک کردن .env
log "چک کردن .env..."
if ! grep -q "SQLALCHEMY_DATABASE_URI" /var/www/rfbot/.env; then
    echo "SQLALCHEMY_DATABASE_URI=postgresql://neondb_owner:npg_nguJUcZGPX83@localhost/neondb" | sudo tee -a /var/www/rfbot/.env
    run_cmd "sudo chown www-data:www-data /var/www/rfbot/.env" "تنظیم مالکیت .env"
    run_cmd "sudo chmod 640 /var/www/rfbot/.env" "تنظیم دسترسی .env"
fi

# 2. نصب دوباره flask-admin
log "نصب flask-admin..."
run_cmd "source /var/www/rfbot/venv/bin/activate && pip install flask-admin" "نصب flask-admin"

# 3. اصلاح app.py برای Flask-Admin
log "اصلاح app.py برای Flask-Admin..."
if ! grep -q "flask_admin" /var/www/rfbot/src/web/app.py; then
    cat << 'EOF' | sudo tee -a /var/www/rfbot/src/web/app.py
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

admin = Admin(app, name='RF Bot Admin', template_mode='bootstrap4')

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    category_id = db.Column(db.Integer)

class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    category_id = db.Column(db.Integer)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))

admin.add_view(ModelView(Product, db.session))
admin.add_view(ModelView(Service, db.session))
admin.add_view(ModelView(User, db.session))
EOF
fi

# 4. ری‌استارت سرویس
log "ری‌استارت سرویس..."
run_cmd "sudo systemctl restart rfbot-web" "ری‌استارت rfbot-web"

# 5. تست دسترسی
log "تست دسترسی..."
run_cmd "curl -v http://localhost:5000/admin" "تست curl به localhost"
run_cmd "curl -v http://185.10.75.180/admin" "تست curl به /admin"

# 6. چک کردن دیتابیس
log "چک کردن دیتابیس..."
run_cmd "export PGPASSWORD=npg_nguJUcZGPX83 && psql -U neondb_owner -d neondb -h localhost -c 'SELECT count(*) FROM products;'" "شمارش محصولات"
run_cmd "export PGPASSWORD=npg_nguJUcZGPX83 && psql -U neondb_owner -d neondb -h localhost -c 'SELECT count(*) FROM services;'" "شمارش خدمات"
run_cmd "export PGPASSWORD=npg_nguJUcZGPX83 && psql -U neondb_owner -d neondb -h localhost -c 'SELECT count(*) FROM users;'" "شمارش کاربران"

# 7. اضافه کردن کاربر ادمین
log "اضافه کردن کاربر ادمین..."
cat << 'EOF' | sudo tee /var/www/rfbot/src/web/seed_admin_data.py
from src.web.app import db
from src.web.models import User

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))

admin_user = User(username='admin', password='admin123', role='admin')
db.session.add(admin_user)
db.session.commit()
print("کاربر ادمین اضافه شد.")
EOF
run_cmd "source /var/www/rfbot/venv/bin/activate && python /var/www/rfbot/src/web/seed_admin_data.py" "اجرای seed_admin_data"

log "------------------------------------"
log "رفع نهایی تمام شد. لاگ‌ها در $LOG_FILE ذخیره شدند."
log "لطفاً وب پنل را در مرورگر تست کنید: http://185.10.75.180/admin"
log "نام کاربری: admin | رمز: admin123"