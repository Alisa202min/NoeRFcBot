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
    try:
        # استفاده از نام ستون درست product_type
        products = Product.query.filter_by(
            product_type='product', featured=True).limit(6).all()
        services = Product.query.filter_by(
            product_type='service', featured=True).limit(6).all()
        
        # برای اطمینان، اگر محتوا وجود نداشت از یک لیست خالی استفاده می‌کنیم
        if not products:
            products = []
        if not services:
            services = []
            
        # دریافت محتوای آموزشی
        try:
            educational = EducationalContent.query.order_by(
                EducationalContent.created_at.desc()).limit(3).all()
        except Exception as e:
            logger.warning(f"Error loading educational content: {e}")
            educational = []
        
        # دریافت محتوای استاتیک
        try:
            about_content = StaticContent.query.filter_by(content_type='about').first()
            about_text = about_content.content if about_content else ''
        except Exception as e:
            logger.warning(f"Error loading about content: {e}")
            about_text = ''
        
        # بررسی وضعیت ربات
        import subprocess
        import os
        import datetime
        
        try:
            # بررسی وضعیت ربات با پیدا کردن پروسس مربوطه
            result = subprocess.run(['pgrep', '-f', 'python bot.py'], 
                            capture_output=True, text=True)
            bot_status = 'running' if result.stdout.strip() else 'stopped'
            
            # بررسی وضعیت متغیرهای محیطی
            env_status = all([
                os.environ.get('BOT_TOKEN'),
                os.environ.get('DATABASE_URL')
            ])
        except Exception as e:
            logger.warning(f"Error checking bot status: {e}")
            bot_status = 'unknown'
            env_status = False
        
        # بررسی تاریخ آخرین اجرا (اگر فایل لاگ وجود داشته باشد)
        try:
            last_run = datetime.datetime.now()
        except Exception as e:
            logger.warning(f"Error getting last run time: {e}")
            last_run = None
        
        # آماده‌سازی لاگ‌های اولیه برای نمایش
        try:
            log_file = 'bot.log'
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    # خواندن آخرین خطوط
                    lines = f.readlines()
                    bot_logs = lines[-50:] if len(lines) > 50 else lines
            else:
                bot_logs = ['فایل لاگ موجود نیست.']
        except Exception as e:
            logger.warning(f"Error reading log file: {e}")
            bot_logs = [f'خطا در خواندن فایل لاگ: {str(e)}']
        
        return render_template('index.html', 
                              products=products, 
                              services=services, 
                              educational=educational,
                              about_text=about_text,
                              bot_status=bot_status,
                              env_status=env_status,
                              last_run=last_run,
                              datetime=datetime,
                              bot_logs=bot_logs)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        # مطمئن شویم که صفحه خطا بدون مشکل نمایش داده می‌شود
        try:
            return render_template('500.html'), 500
        except Exception as template_error:
            logger.error(f"Error rendering error template: {template_error}")
            return "Internal Server Error", 500

@app.route('/configuration')
@login_required
def loadConfig():
    """صفحه پیکربندی"""
    try:
        from src.config.configuration import load_config
        config = load_config()
        return render_template('configuration.html', 
                            config=config,
                            active_page='configuration')
    except Exception as e:
        logger.error(f"Error in loadConfig route: {e}")
        return render_template('500.html'), 500

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

@app.route('/search')
def search():
    """جستجوی پیشرفته محصولات و خدمات"""
    try:
        query = request.args.get('q', '')
        category_id = request.args.get('category', type=int)
        product_type = request.args.get('type')
        min_price = request.args.get('min_price', type=int)
        max_price = request.args.get('max_price', type=int)
        sort_by = request.args.get('sort_by', 'name')
        
        # بررسی پارامترها و اعمال فیلترها
        filters = {}
        if query:
            filters['query'] = query
        if category_id:
            filters['category_id'] = category_id
        if product_type:
            filters['product_type'] = product_type
        if min_price:
            filters['min_price'] = min_price
        if max_price:
            filters['max_price'] = max_price
        
        # تنظیم فیلتر پایه برای محصولات
        base_query = Product.query
        
        # اعمال فیلترها
        if query:
            search_query = f"%{query}%"
            base_query = base_query.filter(
                db.or_(
                    Product.name.ilike(search_query),
                    Product.description.ilike(search_query),
                    Product.tags.ilike(search_query)
                )
            )
        
        if category_id:
            base_query = base_query.filter(Product.category_id == category_id)
        
        if product_type:
            base_query = base_query.filter(Product.product_type == product_type)
        
        if min_price:
            base_query = base_query.filter(Product.price >= min_price)
        
        if max_price:
            base_query = base_query.filter(Product.price <= max_price)
        
        # مرتب‌سازی
        if sort_by == 'price_asc':
            base_query = base_query.order_by(Product.price.asc())
        elif sort_by == 'price_desc':
            base_query = base_query.order_by(Product.price.desc())
        elif sort_by == 'newest':
            base_query = base_query.order_by(Product.created_at.desc())
        else:  # default: sort by name
            base_query = base_query.order_by(Product.name.asc())
        
        # دریافت دسته‌بندی‌ها برای فیلتر
        categories = Category.query.all()
        
        # اجرای کوئری
        products = base_query.all()
        
        return render_template('search.html', 
                            products=products,
                            categories=categories,
                            filters=filters,
                            query=query,
                            active_page='search')
    except Exception as e:
        logger.error(f"Error in search route: {e}")
        return render_template('500.html'), 500

# ----- Bot Control Routes -----

@app.route('/logs')
def logs():
    """دریافت لاگ‌های ربات"""
    try:
        # تلاش برای خواندن آخرین خطوط فایل لاگ
        log_file = 'bot.log'
        max_lines = 50  # حداکثر تعداد خطوط برای نمایش
        
        try:
            import os
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    # خواندن آخرین خطوط
                    lines = list(f)[-max_lines:] if len(list(f)) > max_lines else list(f)
                    return jsonify({'logs': ''.join(lines)})
            else:
                return jsonify({'logs': 'فایل لاگ موجود نیست.'})
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            return jsonify({'logs': f'خطا در خواندن فایل لاگ: {str(e)}'})
    except Exception as e:
        logger.error(f"Error in logs route: {e}")
        return jsonify({'logs': 'خطای داخلی سرور'})

@app.route('/control/start', methods=['POST'])
@login_required
def control_start():
    """شروع ربات تلگرام"""
    try:
        # راه‌اندازی ربات در یک پروسس جداگانه
        import subprocess
        subprocess.Popen(["python", "bot.py"])
        flash('ربات با موفقیت راه‌اندازی شد.', 'success')
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        flash('خطا در راه‌اندازی ربات.', 'danger')
    
    return redirect(url_for('index'))

@app.route('/control/stop', methods=['POST'])
@login_required
def control_stop():
    """توقف ربات تلگرام"""
    try:
        # توقف ربات با ارسال سیگنال
        import os
        import signal
        import subprocess
        
        # یافتن پروسس‌های پایتون
        result = subprocess.run(['pgrep', '-f', 'python bot.py'], 
                               capture_output=True, text=True)
        
        if result.stdout.strip():
            pid = int(result.stdout.strip())
            os.kill(pid, signal.SIGTERM)
            flash('ربات با موفقیت متوقف شد.', 'success')
        else:
            flash('ربات در حال اجرا نیست.', 'warning')
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        flash('خطا در توقف ربات.', 'danger')
    
    return redirect(url_for('index'))

@app.errorhandler(500)
def server_error(e):
    """صفحه ۵۰۰ - خطای سرور"""
    return render_template('500.html'), 500