#!/bin/bash

# Logging setup
LOG_FILE="/tmp/rfbot_fix_$(date +%Y-%m-%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "شروع رفع مشکلات rfbot - $(date)"

# Step 1: Check and fix app.py if needed
echo "بررسی و اصلاح app.py..."
if ! grep -q "from flask_admin import Admin" /var/www/rfbot/src/web/app.py; then
    echo "بکاپ و اصلاح app.py..."
    cp /var/www/rfbot/src/web/app.py /var/www/rfbot/src/web/app.py.bak || { echo "خطا در بکاپ app.py"; exit 1; }
    cat << 'EOF' > /var/www/rfbot/src/web/app.py
from dotenv import load_dotenv
import os
load_dotenv()

import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

class Base(DeclarativeBase):
    pass

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

db = SQLAlchemy(model_class=Base)

app = Flask(__name__,
            static_folder='../../static',
            template_folder='../../templates')
app.secret_key = os.environ.get("SESSION_SECRET", "رمز موقت برای ربات RFCBot")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL")
if not app.config["SQLALCHEMY_DATABASE_URI"]:
    raise ValueError("SQLALCHEMY_DATABASE_URI is not set in .env file")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "connect_args": {
        "sslmode": "prefer",
        "application_name": "RFCBot",
        "connect_timeout": 10
    }
}

from src.utils.utils_upload import UploadSet, IMAGES, VIDEO, configure_uploads

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
app.config['UPLOADED_MEDIA_DEST'] = 'static/uploads'
app.config['UPLOADS_DEFAULT_DEST'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

media_files = UploadSet('media', IMAGES + VIDEO)

db.init_app(app)
configure_uploads(app, media_files)

os.makedirs(app.config['UPLOADED_MEDIA_DEST'], exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    from src.models.models import User
    return User.query.get(int(user_id))

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

with app.app_context():
    from src.models import models
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
EOF
    echo "app.py اصلاح شد"
else
    echo "app.py نیازی به اصلاح ندارد"
fi

echo "بررسی سینتکس app.py..."
python3 -m compileall /var/www/rfbot/src/web/app.py || { echo "خطا در سینتکس app.py"; exit 1; }
echo "✓ موفقیت: app.py معتبر است"

# Step 2: Fix seed_admin_data.py
echo "اصلاح seed_admin_data.py..."
cat << 'EOF' > /var/www/rfbot/src/web/seed_admin_data.py
import os
import sys
sys.path.append('/var/www/rfbot')
from src.web.app import db
from src.models.models import User

with db.app.app_context():
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(username='admin', password='admin123', role='admin')
        db.session.add(admin_user)
        try:
            db.session.commit()
            print("کاربر ادمین اضافه شد.")
        except Exception as e:
            db.session.rollback()
            print(f"خطا در افزودن کاربر ادمین: {e}")
    else:
        print("کاربر ادمین قبلاً وجود دارد.")
EOF

echo "اجرای seed_admin_data.py..."
source /var/www/rfbot/venv/bin/activate
python /var/www/rfbot/src/web/seed_admin_data.py > /tmp/seed_admin_data.log 2>&1
if grep -q "کاربر ادمین" /tmp/seed_admin_data.log; then
    echo "✓ موفقیت: seed_admin_data.py اجرا شد"
    cat /tmp/seed_admin_data.log
else
    echo "✗ خطا در اجرای seed_admin_data.py"
    cat /tmp/seed_admin_data.log
    exit 1
fi

# Step 3: Restart services
echo "ری‌استارت سرویس‌ها..."
sudo systemctl daemon-reload
sudo systemctl restart rfbot-web
sudo systemctl restart nginx

echo "بررسی وضعیت سرویس rfbot-web..."
if sudo systemctl is-active --quiet rfbot-web; then
    echo "✓ موفقیت: سرویس rfbot-web فعال است"
else
    echo "✗ خطا: سرویس rfbot-web غیرفعال است"
    sudo journalctl -u rfbot-web -n 50
    exit 1
fi

echo "بررسی وضعیت سرویس nginx..."
if sudo systemctl is-active --quiet nginx; then
    echo "✓ موفقیت: سرویس nginx فعال است"
else
    echo "✗ خطا: سرویس nginx غیرفعال است"
    sudo journalctl -u nginx -n 50
    exit 1
fi

# Step 4: Test access
echo "تست دسترسی..."
curl -v http://localhost:5000/admin > /tmp/curl_local_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "✓ موفقیت: تست curl به localhost:5000/admin"
else
    echo "✗ خطا: تست curl به localhost:5000/admin"
    cat /tmp/curl_local_test.log
fi

curl -v http://185.10.75.180/admin > /tmp/curl_external_test.log 2>&1
if [ $? -eq 0 ]; then
    echo "✓ موفقیت: تست curl به 185.10.75.180/admin"
else
    echo "✗ خطا: تست curl به 185.10.75.180/admin"
    cat /tmp/curl_external_test.log
fi

# Step 5: Check database
echo "بررسی دیتابیس..."
export PGPASSWORD=npg_nguJUcZGPX83
psql -U neondb_owner -d neondb -h localhost -c "SELECT * FROM users;" > /tmp/db_users.log
if [ $? -eq 0 ]; then
    echo "✓ موفقیت: بررسی جدول users"
    cat /tmp/db_users.log
else
    echo "✗ خطا: بررسی جدول users"
    exit 1
fi

# Final message
echo "------------------------------------"
echo "رفع مشکلات تمام شد. لاگ‌ها در $LOG_FILE ذخیره شدند."
echo "لطفاً وب پنل را در مرورگر تست کنید: http://185.10.75.180/admin"
echo "نام کاربری: admin | رمز: admin123"
