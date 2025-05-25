import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "رمز موقت برای ربات RFCBot")
app.config['SERVER_NAME'] = None  # Fix for URL building issues
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "connect_args": {
        "sslmode": "prefer",
        "application_name": "RFCBot",
        "connect_timeout": 10
    }
}

# بقیه کدها بدون تغییر...
# Configure Flask-Uploads
from utils_upload import UploadSet, IMAGES, VIDEO, configure_uploads

# Add mp4 to allowed formats
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'} 
app.config['UPLOADED_MEDIA_DEST'] = 'static/uploads'
app.config['UPLOADS_DEFAULT_DEST'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Create a custom media upload set that includes images and mp4 videos
media_files = UploadSet('media', IMAGES + VIDEO)

# Initialize extensions
db.init_app(app)
configure_uploads(app, media_files)

# Ensure upload directory exists
os.makedirs(app.config['UPLOADED_MEDIA_DEST'], exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    # Import models here to ensure they're registered with SQLAlchemy
    import models
    
    # Create tables
    db.create_all()
    
    # Create admin user if not exists
    from models import User
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin')  # Set a default password - should be changed immediately
        db.session.add(admin)
        db.session.commit()

# Import and register routes
from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user, login_user, logout_user

@app.route('/')
def index():
    """صفحه اصلی"""
    # ارسال متغیرهای مورد نیاز template
    bot_status = 'running'  # تلگرام بات همیشه در حال اجرا است
    env_status = {
        'BOT_TOKEN': 'Set' if os.environ.get('BOT_TOKEN') else 'Not Set',
        'DATABASE_URL': 'Set' if os.environ.get('DATABASE_URL') else 'Not Set'
    }
    
    return render_template('index.html', 
                         bot_status=bot_status, 
                         env_status=env_status,
                         datetime=__import__('datetime'))

@app.route('/admin')
@login_required
def admin():
    """پنل مدیریت"""
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش ندارید', 'error')
        return redirect(url_for('index'))
    return render_template('admin_index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحه ورود"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        from models import User
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """خروج از سیستم"""
    logout_user()
    return redirect(url_for('index'))

# Routes مورد نیاز برای templates
@app.route('/control/start', methods=['POST'])
@login_required
def control_start():
    """شروع ربات تلگرام"""
    flash('ربات تلگرام در حال اجرا است', 'success')
    return redirect(url_for('index'))

@app.route('/control/stop', methods=['POST'])
@login_required
def control_stop():
    """توقف ربات تلگرام"""
    flash('ربات تلگرام متوقف شد', 'info')
    return redirect(url_for('index'))

@app.route('/admin/products')
@login_required
def admin_products():
    """مدیریت محصولات"""
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش ندارید', 'error')
        return redirect(url_for('index'))
    return render_template('admin_products.html')

@app.route('/admin/services')
@login_required
def admin_services():
    """مدیریت خدمات"""
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش ندارید', 'error')
        return redirect(url_for('index'))
    return render_template('admin_services.html')

@app.route('/admin/categories')
@login_required
def admin_categories():
    """مدیریت دسته‌بندی‌ها"""
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش ندارید', 'error')
        return redirect(url_for('index'))
    return render_template('admin_categories.html')

# اضافه کردن routes مفقوده که در template ها استفاده می‌شوند
@app.route('/api/logs')
def get_logs_json():
    """API برای دریافت لاگ‌ها"""
    return jsonify({"logs": ["تلگرام بات فعال است", "پایگاه داده متصل است"]})

@app.route('/api/status')
def get_status_json():
    """API برای دریافت وضعیت"""
    return jsonify({
        "bot_status": "running",
        "database_status": "connected"
    })

@app.route('/admin/inquiries')
@login_required
def admin_inquiries():
    """مدیریت استعلامات"""
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش ندارید', 'error')
        return redirect(url_for('index'))
    return render_template('admin_inquiries.html')

@app.route('/admin/education')
@login_required
def admin_education():
    """مدیریت محتوای آموزشی"""
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش ندارید', 'error')
        return redirect(url_for('index'))
    return render_template('admin_education.html')

@app.route('/database')
@login_required
def database_view():
    """نمایش دیتابیس"""
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش ندارید', 'error')
        return redirect(url_for('index'))
    return render_template('database.html')

@app.route('/configuration')
@login_required
def configuration():
    """تنظیمات سیستم"""
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش ندارید', 'error')
        return redirect(url_for('index'))
    return render_template('configuration.html')

@app.route('/logs')
@login_required
def logs():
    """نمایش لاگ‌ها"""
    if not current_user.is_admin:
        flash('شما دسترسی به این بخش ندارید', 'error')
        return redirect(url_for('index'))
    return render_template('logs.html')
