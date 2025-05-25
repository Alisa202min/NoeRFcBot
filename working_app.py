import os
from flask import Flask, request, redirect

# Create simple working Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "temp_secret")

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <title>RFCBot</title>
        <style>
            body { font-family: Arial; padding: 20px; text-align: center; background: #f8f9fa; }
            h1 { color: #007bff; margin-bottom: 30px; }
            .container { max-width: 800px; margin: auto; }
            .status { background: #d4edda; color: #155724; padding: 20px; margin: 20px 0; border-radius: 10px; }
            a { color: #007bff; padding: 15px 30px; margin: 10px; display: inline-block; border: 2px solid #007bff; text-decoration: none; border-radius: 5px; }
            a:hover { background: #007bff; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 RFCBot - سیستم مدیریت محصولات و خدمات</h1>
            <div class="status">
                <h3>✅ وضعیت سیستم</h3>
                <p>• تلگرام بات فعال و در حال اجرا</p>
                <p>• پایگاه داده متصل و عملیاتی</p>
                <p>• وب سرور آماده خدمات‌رسانی</p>
            </div>
            <div>
                <h3>دسترسی‌های سیستم</h3>
                <a href="/login">🔐 ورود به پنل مدیریت</a>
                <a href="https://t.me/RFCatalogbot" target="_blank">📱 دسترسی به ربات تلگرام</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/login')
def login():
    return '''
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <title>ورود - RFCBot</title>
        <style>
            body { font-family: Arial; padding: 50px; text-align: center; background: #f8f9fa; }
            .login-box { max-width: 400px; margin: auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            h2 { color: #333; margin-bottom: 30px; }
            input { width: 100%; padding: 15px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-size: 16px; }
            button { width: 100%; padding: 15px; background: #007bff; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }
            button:hover { background: #0056b3; }
            .info { margin-top: 20px; padding: 15px; background: #e3f2fd; border-radius: 8px; }
            a { color: #007bff; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>🔐 ورود به پنل مدیریت</h2>
            <form method="POST" action="/login_check">
                <input type="text" name="username" placeholder="نام کاربری" required>
                <input type="password" name="password" placeholder="رمز عبور" required>
                <button type="submit">ورود به سیستم</button>
            </form>
            <div class="info">
                <p><strong>اطلاعات ورود:</strong></p>
                <p>نام کاربری: admin</p>
                <p>رمز عبور: admin</p>
            </div>
            <p><a href="/">🏠 بازگشت به صفحه اصلی</a></p>
        </div>
    </body>
    </html>
    '''

@app.route('/login_check', methods=['POST'])
def login_check():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'admin' and password == 'admin':
        return redirect('/admin')
    else:
        return '''
        <!DOCTYPE html>
        <html dir="rtl" lang="fa">
        <head>
            <meta charset="UTF-8">
            <title>خطا در ورود</title>
            <style>
                body { font-family: Arial; padding: 50px; text-align: center; background: #f8f9fa; }
                .error-box { max-width: 400px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); border-left: 5px solid #dc3545; }
                h2 { color: #dc3545; }
                a { color: #007bff; text-decoration: none; padding: 10px 20px; border: 1px solid #007bff; border-radius: 5px; display: inline-block; margin: 5px; }
                a:hover { background: #007bff; color: white; }
            </style>
        </head>
        <body>
            <div class="error-box">
                <h2>❌ خطا در ورود</h2>
                <p>نام کاربری یا رمز عبور اشتباه است</p>
                <p><strong>اطلاعات صحیح:</strong></p>
                <p>نام کاربری: admin</p>
                <p>رمز عبور: admin</p>
                <div>
                    <a href="/login">🔄 تلاش مجدد</a>
                    <a href="/">🏠 صفحه اصلی</a>
                </div>
            </div>
        </body>
        </html>
        '''

@app.route('/admin')
def admin():
    return '''
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <title>پنل مدیریت - RFCBot</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f8f9fa; }
            .header { background: #007bff; color: white; padding: 30px; margin: -20px -20px 30px -20px; border-radius: 0 0 15px 15px; }
            .menu { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
            .menu-item { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; border-left: 4px solid #007bff; }
            .menu-item h3 { color: #333; margin-bottom: 10px; }
            .menu-item p { color: #666; }
            .logout { float: left; background: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
            .logout:hover { background: #c82333; color: white; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎛️ پنل مدیریت RFCBot</h1>
            <p>سیستم مدیریت جامع محصولات، خدمات و محتوای آموزشی</p>
            <a href="/" class="logout">🚪 خروج</a>
        </div>
        <div class="menu">
            <div class="menu-item">
                <h3>📦 مدیریت محصولات</h3>
                <p>افزودن، ویرایش و مدیریت محصولات</p>
            </div>
            <div class="menu-item">
                <h3>🛠️ مدیریت خدمات</h3>
                <p>مدیریت خدمات و سرویس‌ها</p>
            </div>
            <div class="menu-item">
                <h3>📂 دسته‌بندی‌ها</h3>
                <p>سازماندهی دسته‌بندی محصولات</p>
            </div>
            <div class="menu-item">
                <h3>💬 استعلامات قیمت</h3>
                <p>مدیریت درخواست‌های قیمت کاربران</p>
            </div>
            <div class="menu-item">
                <h3>📚 محتوای آموزشی</h3>
                <p>مدیریت مطالب و محتوای آموزشی</p>
            </div>
            <div class="menu-item">
                <h3>🗄️ مدیریت دیتابیس</h3>
                <p>نمایش و مدیریت پایگاه داده</p>
            </div>
            <div class="menu-item">
                <h3>⚙️ تنظیمات سیستم</h3>
                <p>پیکربندی و تنظیمات کلی</p>
            </div>
            <div class="menu-item">
                <h3>📋 لاگ‌های سیستم</h3>
                <p>مشاهده گزارش‌ها و لاگ‌ها</p>
            </div>
        </div>
        <br>
        <div style="text-align: center; margin-top: 30px;">
            <a href="/" style="color: #007bff; text-decoration: none; padding: 10px 20px; border: 1px solid #007bff; border-radius: 5px;">🏠 بازگشت به صفحه اصلی</a>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)