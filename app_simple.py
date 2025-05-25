import os
from flask import Flask, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "رمز موقت برای ربات RFCBot")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <title>RFCBot - ربات تلگرام</title>
        <style>
            body { font-family: Arial; padding: 20px; text-align: center; }
            .container { max-width: 800px; margin: auto; }
            h1 { color: #007bff; }
            .status { background: #d4edda; padding: 15px; margin: 10px 0; border-radius: 5px; }
            a { color: #007bff; text-decoration: none; padding: 10px 20px; margin: 5px; display: inline-block; border: 1px solid #007bff; border-radius: 5px; }
            a:hover { background: #007bff; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>RFCBot - سیستم مدیریت محصولات و خدمات</h1>
            <div class="status">
                <h3>وضعیت سیستم</h3>
                <p>✅ تلگرام بات فعال</p>
                <p>✅ پایگاه داده متصل</p>
                <p>✅ وب سرور در حال اجرا</p>
            </div>
            <div>
                <h3>دسترسی‌ها</h3>
                <a href="/login">ورود به پنل مدیریت</a>
                <a href="https://t.me/RFCatalogbot">دسترسی به ربات تلگرام</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin'))
        else:
            return '''
            <!DOCTYPE html>
            <html dir="rtl" lang="fa">
            <head>
                <meta charset="UTF-8">
                <title>خطا - ورود</title>
                <style>
                    body { font-family: Arial; padding: 50px; text-align: center; }
                    .error { color: red; margin: 20px 0; }
                    a { color: #007bff; }
                </style>
            </head>
            <body>
                <h2>خطا در ورود</h2>
                <p class="error">نام کاربری یا رمز عبور اشتباه است</p>
                <a href="/login">تلاش مجدد</a> | <a href="/">صفحه اصلی</a>
            </body>
            </html>
            '''
    
    return '''
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <title>ورود - RFCBot</title>
        <style>
            body { font-family: Arial; padding: 50px; text-align: center; background: #f8f9fa; }
            .login-box { max-width: 400px; margin: auto; background: white; border: 1px solid #ddd; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            button:hover { background: #0056b3; }
            h2 { color: #333; margin-bottom: 30px; }
            .footer { margin-top: 20px; }
            .footer a { color: #007bff; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>ورود به پنل مدیریت RFCBot</h2>
            <form method="POST">
                <input type="text" name="username" placeholder="نام کاربری" required>
                <input type="password" name="password" placeholder="رمز عبور" required>
                <button type="submit">ورود</button>
            </form>
            <div class="footer">
                <a href="/">بازگشت به صفحه اصلی</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/admin')
@login_required
def admin():
    return '''
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <title>پنل مدیریت - RFCBot</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            .header { background: #007bff; color: white; padding: 20px; margin: -20px -20px 20px -20px; }
            .menu { display: flex; gap: 15px; flex-wrap: wrap; }
            .menu-item { background: #f8f9fa; padding: 15px; border: 1px solid #ddd; border-radius: 5px; text-decoration: none; color: #333; display: block; min-width: 200px; }
            .menu-item:hover { background: #e9ecef; }
            .logout { float: left; background: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>پنل مدیریت RFCBot</h1>
            <a href="/logout" class="logout">خروج</a>
        </div>
        <div class="menu">
            <a href="#" class="menu-item">مدیریت محصولات</a>
            <a href="#" class="menu-item">مدیریت خدمات</a>
            <a href="#" class="menu-item">مدیریت دسته‌بندی‌ها</a>
            <a href="#" class="menu-item">استعلامات قیمت</a>
            <a href="#" class="menu-item">محتوای آموزشی</a>
            <a href="#" class="menu-item">مدیریت دیتابیس</a>
            <a href="#" class="menu-item">تنظیمات سیستم</a>
            <a href="#" class="menu-item">نمایش لاگ‌ها</a>
        </div>
    </body>
    </html>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Create database tables and admin user
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)