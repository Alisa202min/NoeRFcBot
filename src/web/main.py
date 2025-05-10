"""
مسیرهای وب فلسک
این فایل شامل تمام مسیرها و نقاط پایانی وب است.
"""

import os
import logging
from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user

from src.web.app import app, db, media_files
from src.models.models import User, Category, Product, ProductMedia, Inquiry, EducationalContent, StaticContent
from src.utils.utils import allowed_file, save_uploaded_file, create_directory
from src.utils.utils_upload import handle_media_upload, remove_file, serve_file

logger = logging.getLogger(__name__)

# ----- Main Routes -----

@app.route('/')
def index():
    """صفحه اصلی"""
    products = Product.query.filter_by(
        cat_type='product', featured=True).limit(6).all()
    services = Product.query.filter_by(
        cat_type='service', featured=True).limit(6).all()
    educational = EducationalContent.query.order_by(
        EducationalContent.created_at.desc()).limit(3).all()
    
    # دریافت محتوای استاتیک
    about_content = StaticContent.query.filter_by(content_type='about').first()
    about_text = about_content.content if about_content else ''
    
    return render_template('index.html', 
                          products=products, 
                          services=services, 
                          educational=educational,
                          about_text=about_text)

# ----- Authentication Routes -----

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحه ورود"""
    if current_user.is_authenticated:
        return redirect(url_for('admin_index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            
            # اگر کاربر ادمین است، به پنل ادمین هدایت شود
            if user.is_admin:
                if next_page:
                    return redirect(next_page)
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

# ----- Admin Panel Routes -----

@app.route('/admin')
@login_required
def admin_index():
    """پنل مدیریت - داشبورد"""
    # آمار سیستم
    product_count = Product.query.filter_by(cat_type='product').count()
    service_count = Product.query.filter_by(cat_type='service').count()
    category_count = Category.query.count()
    inquiry_count = Inquiry.query.count()
    pending_count = Inquiry.query.filter_by(status='pending').count()
    
    # استعلام‌های اخیر
    recent_inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(5).all()
    
    return render_template('admin/index.html', 
                          product_count=product_count,
                          service_count=service_count,
                          category_count=category_count,
                          inquiry_count=inquiry_count,
                          pending_count=pending_count,
                          recent_inquiries=recent_inquiries)

@app.route('/admin/categories')
@login_required
def admin_categories():
    """پنل مدیریت - دسته‌بندی‌ها"""
    # دریافت تمام دسته‌بندی‌ها
    categories = Category.query.all()
    
    # تبدیل به ساختار درختی
    category_tree = build_category_tree(categories)
    
    return render_template('admin/categories.html', 
                          categories=categories,
                          category_tree=category_tree)

def build_category_tree(categories, parent_id=None):
    """ساخت ساختار درختی از دسته‌بندی‌ها"""
    tree = []
    for category in categories:
        if category.parent_id == parent_id:
            children = build_category_tree(categories, category.id)
            tree.append({
                'id': category.id,
                'name': category.name,
                'children': children,
                'cat_type': category.cat_type
            })
    return tree

@app.route('/admin/categories/add', methods=['POST'])
@login_required
def admin_add_category():
    """اضافه کردن دسته‌بندی جدید"""
    name = request.form.get('name')
    parent_id = request.form.get('parent_id')
    cat_type = request.form.get('cat_type', 'product')
    
    # تبدیل parent_id به None اگر خالی باشد
    if parent_id and parent_id != '':
        parent_id = int(parent_id)
    else:
        parent_id = None
    
    category = Category(name=name, parent_id=parent_id, cat_type=cat_type)
    db.session.add(category)
    db.session.commit()
    
    flash(f'دسته‌بندی {name} با موفقیت اضافه شد.', 'success')
    return redirect(url_for('admin_categories'))

# ... Routes for products, services, inquiries, etc. ...

# روت‌های مربوط به محصولات
@app.route('/admin/products')
@login_required
def admin_products():
    """پنل مدیریت - محصولات"""
    products = Product.query.filter_by(cat_type='product').all()
    categories = Category.query.filter_by(cat_type='product').all()
    
    return render_template('admin/products.html', 
                          products=products,
                          categories=categories)

# روت‌های مربوط به خدمات
@app.route('/admin/services')
@login_required
def admin_services():
    """پنل مدیریت - خدمات"""
    services = Product.query.filter_by(cat_type='service').all()
    categories = Category.query.filter_by(cat_type='service').all()
    
    return render_template('admin/services.html', 
                          services=services,
                          categories=categories)

# روت‌های مربوط به استعلام‌ها
@app.route('/admin/inquiries')
@login_required
def admin_inquiries():
    """پنل مدیریت - استعلام‌های قیمت"""
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    
    return render_template('admin/inquiries.html', 
                          inquiries=inquiries)

# روت‌های مربوط به محتوای آموزشی
@app.route('/admin/educational')
@login_required
def admin_educational():
    """پنل مدیریت - محتوای آموزشی"""
    contents = EducationalContent.query.all()
    
    return render_template('admin/educational.html', 
                          contents=contents)

# روت‌های مربوط به محتوای ثابت
@app.route('/admin/static-content')
@login_required
def admin_static_content():
    """پنل مدیریت - محتوای ثابت"""
    about = StaticContent.query.filter_by(content_type='about').first()
    contact = StaticContent.query.filter_by(content_type='contact').first()
    
    about_content = about.content if about else ''
    contact_content = contact.content if contact else ''
    
    return render_template('admin/static_content.html', 
                          about_content=about_content,
                          contact_content=contact_content)

# ---- API routes for bot webhook - NO authentication required ----
@app.route('/api/webhook', methods=['POST'])
def telegram_webhook():
    """دریافت و پردازش وب‌هوک تلگرام"""
    # This endpoint should be configured in your bot.py file
    # and is only a placeholder for the Flask app
    return jsonify({"status": "ok", "method": "webhook"})

# ----- Common error handlers -----

@app.errorhandler(404)
def page_not_found(e):
    """صفحه ۴۰۴ - صفحه پیدا نشد"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """صفحه ۵۰۰ - خطای سرور"""
    return render_template('500.html'), 500