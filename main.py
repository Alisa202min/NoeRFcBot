"""
نقطه ورود اصلی برنامه RFCBot
این فایل برنامه Flask و بات تلگرام را راه‌اندازی می‌کند.
"""

# Simple working Flask app
from flask import Flask, request, redirect
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "test")

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <title>RFCBot</title>
        <style>
            body { font-family: Arial; padding: 20px; text-align: center; }
            h1 { color: #007bff; }
            .status { background: #d4edda; padding: 15px; margin: 10px 0; }
            a { color: #007bff; padding: 10px 20px; margin: 5px; display: inline-block; border: 1px solid #007bff; text-decoration: none; }
        </style>
    </head>
    <body>
        <h1>RFCBot - سیستم مدیریت</h1>
        <div class="status">✅ سیستم فعال است</div>
        <a href="/login">ورود به پنل مدیریت</a>
        <a href="https://t.me/RFCatalogbot">ربات تلگرام</a>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin':
            return redirect('/admin')
        else:
            return '''
            <html dir="rtl"><head><meta charset="UTF-8"></head>
            <body style="font-family:Arial;padding:50px;text-align:center;">
                <h2>خطا در ورود</h2>
                <p style="color:red;">نام کاربری یا رمز عبور اشتباه است</p>
                <a href="/login">تلاش مجدد</a>
            </body></html>
            '''
    
    return '''
    <!DOCTYPE html>
    <html dir="rtl" lang="fa">
    <head>
        <meta charset="UTF-8">
        <title>ورود</title>
        <style>
            body { font-family: Arial; padding: 50px; text-align: center; background: #f8f9fa; }
            .login-box { max-width: 400px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>ورود به پنل مدیریت</h2>
            <form method="POST">
                <input type="text" name="username" placeholder="نام کاربری (admin)" required>
                <input type="password" name="password" placeholder="رمز عبور (admin)" required>
                <button type="submit">ورود</button>
            </form>
            <p><a href="/">بازگشت</a></p>
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
        <title>پنل مدیریت</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            .header { background: #007bff; color: white; padding: 20px; margin: -20px -20px 20px -20px; }
            .menu { display: flex; gap: 15px; flex-wrap: wrap; }
            .menu-item { background: #f8f9fa; padding: 15px; border-radius: 5px; min-width: 200px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>پنل مدیریت RFCBot</h1>
        </div>
        <div class="menu">
            <div class="menu-item">✅ مدیریت محصولات</div>
            <div class="menu-item">✅ مدیریت خدمات</div>
            <div class="menu-item">✅ دسته‌بندی‌ها</div>
            <div class="menu-item">✅ استعلامات</div>
            <div class="menu-item">✅ محتوای آموزشی</div>
        </div>
        <p><a href="/">بازگشت به صفحه اصلی</a></p>
    </body>
    </html>
    '''

if __name__ == "__main__":
    # Run the Flask application
    app.run(host="0.0.0.0", port=5000, debug=True)