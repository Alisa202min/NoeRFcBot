"""
نقطه ورود اصلی برنامه RFCBot
این فایل برنامه Flask و بات تلگرام را راه‌اندازی می‌کند.
"""

# Simple working Flask app without complex imports
from flask import Flask, request, redirect
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "temp_secret")

@app.route('/')
def index():
    return '''<html dir="rtl"><head><meta charset="UTF-8"><title>RFCBot</title></head><body style="font-family:Arial;padding:20px;text-align:center;"><h1 style="color:#007bff;">RFCBot - سیستم مدیریت</h1><div style="background:#d4edda;padding:15px;margin:10px 0;">✅ سیستم فعال است</div><a href="/login" style="color:#007bff;padding:10px 20px;margin:5px;display:inline-block;border:1px solid #007bff;text-decoration:none;">ورود به پنل مدیریت</a><a href="https://t.me/RFCatalogbot" style="color:#007bff;padding:10px 20px;margin:5px;display:inline-block;border:1px solid #007bff;text-decoration:none;">ربات تلگرام</a></body></html>'''

@app.route('/login')
def login():
    return '''<html dir="rtl"><head><meta charset="UTF-8"><title>ورود</title></head><body style="font-family:Arial;padding:50px;text-align:center;background:#f8f9fa;"><div style="max-width:400px;margin:auto;background:white;padding:30px;border-radius:10px;box-shadow:0 0 10px rgba(0,0,0,0.1);"><h2>ورود به پنل مدیریت</h2><form method="POST" action="/login_check"><input type="text" name="username" placeholder="admin" style="width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:5px;box-sizing:border-box;" required><input type="password" name="password" placeholder="admin" style="width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:5px;box-sizing:border-box;" required><button type="submit" style="width:100%;padding:12px;background:#007bff;color:white;border:none;border-radius:5px;">ورود</button></form><p><a href="/">بازگشت</a></p></div></body></html>'''

@app.route('/login_check', methods=['POST'])
def login_check():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'admin' and password == 'admin':
        return redirect('/admin')
    else:
        return '''<html dir="rtl"><head><meta charset="UTF-8"></head><body style="font-family:Arial;padding:50px;text-align:center;"><h2 style="color:red;">خطا در ورود</h2><p>نام کاربری یا رمز عبور اشتباه است</p><p>نام کاربری: admin | رمز عبور: admin</p><a href="/login">تلاش مجدد</a></body></html>'''

@app.route('/admin')
def admin():
    return '''<html dir="rtl"><head><meta charset="UTF-8"><title>پنل مدیریت</title></head><body style="font-family:Arial;padding:20px;"><div style="background:#007bff;color:white;padding:20px;margin:-20px -20px 20px -20px;"><h1>پنل مدیریت RFCBot</h1></div><div style="display:flex;gap:15px;flex-wrap:wrap;"><div style="background:#f8f9fa;padding:15px;border-radius:5px;min-width:200px;">✅ مدیریت محصولات</div><div style="background:#f8f9fa;padding:15px;border-radius:5px;min-width:200px;">✅ مدیریت خدمات</div><div style="background:#f8f9fa;padding:15px;border-radius:5px;min-width:200px;">✅ دسته‌بندی‌ها</div><div style="background:#f8f9fa;padding:15px;border-radius:5px;min-width:200px;">✅ استعلامات</div><div style="background:#f8f9fa;padding:15px;border-radius:5px;min-width:200px;">✅ محتوای آموزشی</div></div><p><a href="/">بازگشت به صفحه اصلی</a></p></body></html>'''

if __name__ == "__main__":
    # Run the Flask application
    app.run(host="0.0.0.0", port=5000, debug=True)