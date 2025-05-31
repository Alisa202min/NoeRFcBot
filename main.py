from app import app
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Product, Service, EducationalContent, Inquiry
import datetime
import os

@app.route('/')
def index():
    """صفحه اصلی"""
    try:
        products = Product.query.filter_by(featured=True).limit(6).all() or []
        services = Service.query.filter_by(featured=True).limit(6).all() or []
        educational = EducationalContent.query.order_by(EducationalContent.created_at.desc()).limit(3).all() or []
        
        return render_template('index.html',
                             products=products,
                             services=services,
                             educational=educational,
                             bot_status='running' if os.path.exists('bot.log') else 'stopped',
                             datetime=datetime)
    except Exception as e:
        app.logger.error(f"Error in index route: {e}")
        return render_template('index.html',
                             products=[], services=[], educational=[],
                             bot_status='error', datetime=datetime)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحه ورود"""
    if current_user.is_authenticated:
        return redirect(url_for('admin_index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin_index'))
            else:
                flash('شما دسترسی ادمین ندارید.', 'danger')
                return redirect(url_for('index'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """خروج از حساب کاربری"""
    logout_user()
    flash('با موفقیت خارج شدید.', 'success')
    return redirect(url_for('index'))

@app.route('/admin/')
@login_required
def admin_index():
    """پنل مدیریت"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'danger')
        return redirect(url_for('index'))
    
    try:
        product_count = Product.query.count()
        service_count = Service.query.count()
        inquiry_count = Inquiry.query.count()
        pending_count = Inquiry.query.filter_by(status='pending').count()
        
        return render_template('admin/index.html',
                             product_count=product_count,
                             service_count=service_count,
                             inquiry_count=inquiry_count,
                             pending_count=pending_count,
                             datetime=datetime)
    except Exception as e:
        app.logger.error(f"Error in admin index: {e}")
        return render_template('admin/index.html',
                             product_count=0, service_count=0,
                             inquiry_count=0, pending_count=0,
                             datetime=datetime)

@app.route('/products')
def products():
    """صفحه محصولات"""
    try:
        products = Product.query.all()
        return render_template('products.html', products=products)
    except Exception as e:
        app.logger.error(f"Error loading products: {e}")
        return render_template('products.html', products=[])

@app.route('/services')
def services():
    """صفحه خدمات"""
    try:
        services = Service.query.all()
        return render_template('services.html', services=services)
    except Exception as e:
        app.logger.error(f"Error loading services: {e}")
        return render_template('services.html', services=[])

@app.route('/admin/database')
@login_required
def admin_database():
    """پنل مدیریت دیتابیس"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'danger')
        return redirect(url_for('index'))
    return render_template('database.html')

@app.route('/admin/products')
@login_required
def admin_products():
    """مدیریت محصولات"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'danger')
        return redirect(url_for('index'))
    
    products = Product.query.all()
    return render_template('admin_products.html', products=products)

@app.route('/admin/services')
@login_required
def admin_services():
    """مدیریت خدمات"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'danger')
        return redirect(url_for('index'))
    
    services = Service.query.all()
    return render_template('admin_services.html', services=services)

@app.route('/admin/inquiries')
@login_required
def admin_inquiries():
    """مدیریت استعلامات"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'danger')
        return redirect(url_for('index'))
    
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    return render_template('admin_inquiries.html', inquiries=inquiries)

@app.route('/control/start', methods=['POST'])
@login_required
def control_start():
    """شروع بات"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'danger')
        return redirect(url_for('index'))
    
    flash('درخواست شروع بات ارسال شد', 'info')
    return redirect(url_for('index'))

@app.route('/control/stop', methods=['POST'])
@login_required
def control_stop():
    """توقف بات"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'danger')
        return redirect(url_for('index'))
    
    flash('درخواست توقف بات ارسال شد', 'info')
    return redirect(url_for('index'))

@app.route('/control/restart', methods=['POST'])
@login_required
def control_restart():
    """راه‌اندازی مجدد بات"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'danger')
        return redirect(url_for('index'))
    
    flash('درخواست راه‌اندازی مجدد بات ارسال شد', 'info')
    return redirect(url_for('index'))

@app.route('/logs')
@login_required
def logs():
    """صفحه لاگ‌ها"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز', 'danger')
        return redirect(url_for('index'))
    
    try:
        if os.path.exists('bot.log'):
            with open('bot.log', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                bot_logs = lines[-50:] if len(lines) > 50 else lines
        else:
            bot_logs = ['فایل لاگ موجود نیست.']
        
        return render_template('logs.html', logs=bot_logs, datetime=datetime)
    except Exception as e:
        app.logger.error(f"Error reading logs: {e}")
        return render_template('logs.html', logs=['خطا در خواندن لاگ‌ها'], datetime=datetime)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)