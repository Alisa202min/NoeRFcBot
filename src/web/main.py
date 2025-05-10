"""
مسیرهای وب فلسک
این فایل شامل تمام مسیرها و نقاط پایانی وب است.
"""

import os
import logging
import datetime
from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

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
        # محصولات و خدمات در جدول products ذخیره می‌شوند
        products = Product.query.filter_by(product_type='product', featured=True).limit(6).all()
        services = Product.query.filter_by(product_type='service').limit(6).all()
        
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
@app.route('/admin/')
@login_required
def admin_index():
    """پنل مدیریت - داشبورد"""
    try:
        # آمار سیستم
        product_count = Product.query.filter_by(product_type='product').count()
        service_count = Product.query.filter_by(product_type='service').count()
        category_count = Category.query.count()
        inquiry_count = Inquiry.query.count()
        pending_count = Inquiry.query.filter_by(status='pending').count()
        
        # استعلام‌های اخیر
        recent_inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(5).all()
        
        # Add missing parameters required by the template
        now = datetime.datetime.now()
        
        app.logger.debug("Admin index page data loaded successfully")
        return render_template('admin/index.html', 
                            product_count=product_count,
                            service_count=service_count,
                            category_count=category_count,
                            inquiry_count=inquiry_count,
                            pending_count=pending_count,
                            recent_inquiries=recent_inquiries,
                            now=now)
                            
    except Exception as e:
        app.logger.error(f"Error in admin_index: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        
        # Return a simple error page rather than crashing
        return render_template('error.html', 
                            error=str(e),
                            traceback=traceback.format_exc())

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
    """اضافه کردن، ویرایش یا حذف دسته‌بندی"""
    # بررسی نوع عملیات
    action = request.form.get('_action', 'add')
    
    if action == 'delete':
        # حذف دسته‌بندی
        category_id = request.form.get('id')
        if category_id:
            category = Category.query.get_or_404(int(category_id))
            name = category.name
            db.session.delete(category)
            db.session.commit()
            flash(f'دسته‌بندی {name} با موفقیت حذف شد.', 'success')
        return redirect(url_for('admin_categories'))
    
    # دریافت پارامترهای مشترک برای اضافه کردن و ویرایش
    name = request.form.get('name')
    parent_id = request.form.get('parent_id')
    cat_type = request.form.get('cat_type', 'product')
    
    # تبدیل parent_id به None اگر خالی باشد
    if parent_id and parent_id != '':
        parent_id = int(parent_id)
    else:
        parent_id = None
    
    if action == 'edit':
        # ویرایش دسته‌بندی موجود
        category_id = request.form.get('id')
        if category_id:
            category = Category.query.get_or_404(int(category_id))
            category.name = name
            category.parent_id = parent_id
            category.cat_type = cat_type
            db.session.commit()
            flash(f'دسته‌بندی {name} با موفقیت ویرایش شد.', 'success')
    else:
        # اضافه کردن دسته‌بندی جدید
        category = Category(name=name, parent_id=parent_id, cat_type=cat_type)
        db.session.add(category)
        db.session.commit()
        flash(f'دسته‌بندی {name} با موفقیت اضافه شد.', 'success')
        
    return redirect(url_for('admin_categories'))

# ... Routes for products, services, inquiries, etc. ...

# روت‌های مربوط به محصولات
@app.route('/admin/products', methods=['GET', 'POST'])
@login_required
def admin_products():
    """پنل مدیریت - محصولات"""
    action = request.args.get('action')
    product_id = request.args.get('id')
    
    # عملیات POST
    if request.method == 'POST':
        # آپلود رسانه جدید
        if action == 'upload_media':
            product_id = request.form.get('product_id')
            if not product_id:
                flash('شناسه محصول الزامی است.', 'danger')
                return redirect(url_for('admin_products'))
            
            product = Product.query.get_or_404(int(product_id))
            file = request.files.get('file')
            file_type = request.form.get('file_type', 'photo')
            
            if file and file.filename:
                try:
                    # مسیر فایل‌های آپلودی
                    upload_dir = os.path.join('static', 'uploads', 'products', str(product.id))
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # ذخیره فایل
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(upload_dir, filename)
                    file.save(file_path)
                    
                    # افزودن به دیتابیس
                    media = ProductMedia(
                        product_id=product.id,
                        file_id=os.path.join('uploads', 'products', str(product.id), filename),
                        file_type=file_type
                    )
                    db.session.add(media)
                    db.session.commit()
                    
                    flash('رسانه با موفقیت آپلود شد.', 'success')
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error uploading media: {e}")
                    flash(f'خطا در آپلود رسانه: {str(e)}', 'danger')
            else:
                flash('لطفاً یک فایل انتخاب کنید.', 'warning')
                
            return redirect(url_for('admin_products', action='media', id=product_id))
            
        # حذف رسانه
        elif action == 'delete_media':
            media_id = request.form.get('media_id')
            product_id = request.form.get('product_id')
            
            if not media_id or not product_id:
                flash('شناسه رسانه و شناسه محصول الزامی هستند.', 'danger')
                return redirect(url_for('admin_products'))
            
            try:
                media = ProductMedia.query.get(int(media_id))
                if media:
                    # اگر فایل روی فایل سیستم ذخیره شده، آن را حذف می‌کنیم
                    if not media.file_id.startswith('http'):
                        file_path = os.path.join('static', media.file_id)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    
                    db.session.delete(media)
                    db.session.commit()
                    flash('رسانه با موفقیت حذف شد.', 'success')
                else:
                    flash('رسانه مورد نظر یافت نشد.', 'warning')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error deleting media: {e}")
                flash(f'خطا در حذف رسانه: {str(e)}', 'danger')
                
            return redirect(url_for('admin_products', action='media', id=product_id))
    
    # اگر action برابر با 'add' یا 'edit' باشد، فرم نمایش داده می‌شود
    if action == 'add':
        categories = Category.query.filter_by(cat_type='product').all()
        return render_template('admin/product_form.html',
                              title="افزودن محصول جدید",
                              categories=categories)
    elif action == 'edit' and product_id:
        product = Product.query.get_or_404(int(product_id))
        categories = Category.query.filter_by(cat_type='product').all()
        return render_template('admin/product_form.html',
                              title="ویرایش محصول",
                              product=product,
                              categories=categories)
    elif action == 'media' and product_id:
        product = Product.query.get_or_404(int(product_id))
        media = ProductMedia.query.filter_by(product_id=product.id).all()
        return render_template('admin/product_media.html',
                              product=product,
                              media=media)
    
    # نمایش لیست محصولات
    products = Product.query.all()
    categories = Category.query.all()
    
    return render_template('admin/products.html', 
                          products=products,
                          categories=categories)

# روت‌های مربوط به خدمات
@app.route('/admin/services', methods=['GET', 'POST'])
@login_required
def admin_services():
    """پنل مدیریت - خدمات"""
    action = request.args.get('action')
    service_id = request.args.get('id')
    
    # اگر action برابر با 'add' یا 'edit' باشد، فرم نمایش داده می‌شود
    if action == 'add':
        categories = Category.query.filter_by(cat_type='service').all()
        return render_template('admin/service_form.html',
                              title="افزودن خدمت جدید",
                              categories=categories)
    elif action == 'edit' and service_id:
        service = Product.query.filter_by(product_type='service', id=int(service_id)).first_or_404()
        categories = Category.query.filter_by(cat_type='service').all()
        return render_template('admin/service_form.html',
                              title="ویرایش خدمت",
                              service=service,
                              categories=categories)
    elif action == 'media' and service_id:
        service = Product.query.filter_by(product_type='service', id=int(service_id)).first_or_404()
        media = ProductMedia.query.filter_by(product_id=service.id).all()
        return render_template('admin/service_media.html',
                              service=service,
                              media=media)
    
    # نمایش لیست خدمات
    page = request.args.get('page', 1, type=int)
    pagination = Product.query.filter_by(product_type='service').paginate(
        page=page, per_page=10, error_out=False)
    categories = Category.query.all()
    
    return render_template('admin/services.html', 
                          services=pagination,
                          categories=categories)

# روت‌های مربوط به استعلام‌ها
@app.route('/admin/inquiries', methods=['GET', 'POST'])
@login_required
def admin_inquiries():
    """پنل مدیریت - استعلام‌های قیمت"""
    action = request.args.get('action')
    inquiry_id = request.args.get('id')
    
    # عملیات حذف استعلام
    if action == 'delete' and inquiry_id and request.method == 'POST':
        try:
            inquiry = Inquiry.query.get(int(inquiry_id))
            if inquiry:
                db.session.delete(inquiry)
                db.session.commit()
                flash('استعلام قیمت با موفقیت حذف شد.', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting inquiry: {e}")
            flash(f'خطا در حذف استعلام: {str(e)}', 'danger')
        
        return redirect(url_for('admin_inquiries'))
    
    # نمایش جزئیات استعلام
    elif action == 'view' and inquiry_id:
        inquiry = Inquiry.query.get_or_404(int(inquiry_id))
        
        # اطلاعات محصول/خدمت مرتبط
        product = None
        if inquiry.product_id:
            # تمام محصولات و خدمات در جدول Product ذخیره می‌شوند
            product = Product.query.get(inquiry.product_id)
        
        return render_template('admin/inquiry_detail.html',
                             inquiry=inquiry,
                             product=product,
                             active_page='admin')
    
    # به‌روزرسانی وضعیت استعلام
    elif action == 'update_status' and inquiry_id and request.method == 'POST':
        status = request.form.get('status')
        
        try:
            inquiry = Inquiry.query.get(int(inquiry_id))
            if inquiry and status:
                inquiry.status = status
                db.session.commit()
                flash('وضعیت استعلام با موفقیت به‌روزرسانی شد.', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating inquiry status: {e}")
            flash(f'خطا در به‌روزرسانی وضعیت استعلام: {str(e)}', 'danger')
        
        return redirect(url_for('admin_inquiries'))
    
    # نمایش لیست استعلام‌ها با فیلتر
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')
    
    # ساخت کوئری پایه
    query = Inquiry.query
    
    # اعمال فیلترها
    if start_date:
        query = query.filter(Inquiry.created_at >= start_date)
    if end_date:
        query = query.filter(Inquiry.created_at <= end_date + ' 23:59:59')
    if status:
        query = query.filter(Inquiry.status == status)
    
    # خروجی CSV
    if request.args.get('export') == 'csv':
        import csv
        from io import StringIO
        
        # ایجاد فایل CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # هدر فایل
        writer.writerow(['ID', 'تاریخ', 'نام', 'شماره تماس', 'توضیحات', 'وضعیت', 'نوع محصول', 'شناسه محصول'])
        
        # داده‌ها
        inquiries = query.order_by(Inquiry.created_at.desc()).all()
        for inquiry in inquiries:
            writer.writerow([
                inquiry.id,
                inquiry.created_at.strftime('%Y-%m-%d %H:%M') if inquiry.created_at else '-',
                inquiry.name,
                inquiry.phone,
                inquiry.description,
                inquiry.status,
                inquiry.product_type,
                inquiry.product_id
            ])
        
        # ارسال فایل
        output.seek(0)
        return app.response_class(
            output,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=inquiries.csv'}
        )
    
    # مرتب‌سازی و بازیابی داده‌ها
    inquiries = query.order_by(Inquiry.created_at.desc()).all()
    
    return render_template('admin/inquiries.html', 
                          inquiries=inquiries,
                          active_page='admin')

# روت‌های مربوط به محتوای آموزشی
@app.route('/admin/education', methods=['GET', 'POST'])
@login_required
def admin_education():
    """پنل مدیریت - محتوای آموزشی"""
    action = request.args.get('action')
    content_id = request.args.get('id')
    
    # اگر action برابر با 'add' یا 'edit' باشد، فرم نمایش داده می‌شود
    if action == 'add':
        # دریافت لیست دسته‌بندی‌های موجود
        categories = db.session.query(EducationalContent.category).distinct().all()
        categories = [cat[0] for cat in categories if cat[0]] 
        
        return render_template('admin/education_form.html',
                              title="افزودن محتوای آموزشی جدید",
                              categories=categories,
                              active_page='admin')
    
    elif action == 'edit' and content_id:
        # دریافت محتوا برای ویرایش
        content = EducationalContent.query.get_or_404(int(content_id))
        
        # دریافت لیست دسته‌بندی‌های موجود
        categories = db.session.query(EducationalContent.category).distinct().all()
        categories = [cat[0] for cat in categories if cat[0]]
        
        return render_template('admin/education_form.html',
                              title="ویرایش محتوای آموزشی",
                              content=content,
                              categories=categories,
                              active_page='admin')
    
    elif action == 'save' and request.method == 'POST':
        # ذخیره محتوای جدید یا ویرایش شده
        content_id = request.form.get('id')
        title = request.form.get('title')
        category = request.form.get('category')
        content_type = request.form.get('content_type')
        content_text = request.form.get('content')
        
        # اگر دسته‌بندی جدید انتخاب شده، از فیلد new_category استفاده می‌کنیم
        if category == 'new_category':
            category = request.form.get('new_category')
        
        # بررسی آپلود فایل برای محتوای نوع تصویر، ویدیو یا فایل
        uploaded_file = request.files.get('file')
        file_path = None
        
        if uploaded_file and uploaded_file.filename and allowed_file(uploaded_file.filename):
            # ذخیره فایل
            file_path = save_uploaded_file(uploaded_file, 'educational')
        
        try:
            if content_id:
                # ویرایش محتوای موجود
                content = EducationalContent.query.get(int(content_id))
                if content:
                    content.title = title
                    content.category = category
                    content.content_type = content_type
                    
                    # اگر فایل جدید آپلود شده، از آن استفاده می‌کنیم
                    if file_path and (content_type in ['image', 'video', 'file']):
                        content.content = file_path
                    # در غیر این صورت، فقط اگر نوع محتوا متن باشد، متن را به‌روزرسانی می‌کنیم
                    elif content_type == 'text':
                        content.content = content_text
                    
                    db.session.commit()
                    flash('محتوای آموزشی با موفقیت به‌روزرسانی شد.', 'success')
            else:
                # افزودن محتوای جدید
                content = EducationalContent()
                content.title = title
                content.category = category
                content.content_type = content_type
                
                # تنظیم محتوا بر اساس نوع
                if file_path and (content_type in ['image', 'video', 'file']):
                    content.content = file_path
                else:
                    content.content = content_text
                
                db.session.add(content)
                db.session.commit()
                flash('محتوای آموزشی جدید با موفقیت ایجاد شد.', 'success')
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving educational content: {e}")
            flash(f'خطا در ذخیره محتوا: {str(e)}', 'danger')
        
        return redirect(url_for('admin_education'))
    
    elif action == 'delete' and content_id and request.method == 'POST':
        # حذف محتوا
        try:
            content = EducationalContent.query.get(int(content_id))
            if content:
                db.session.delete(content)
                db.session.commit()
                flash('محتوای آموزشی با موفقیت حذف شد.', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting educational content: {e}")
            flash(f'خطا در حذف محتوا: {str(e)}', 'danger')
        
        return redirect(url_for('admin_education'))
    
    # نمایش لیست محتوای آموزشی
    query = request.args.get('q')
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    
    # ساخت کوئری پایه
    base_query = EducationalContent.query
    
    # اعمال فیلترها
    if query:
        base_query = base_query.filter(EducationalContent.title.ilike(f'%{query}%'))
    if category:
        base_query = base_query.filter(EducationalContent.category == category)
    
    # مرتب‌سازی
    base_query = base_query.order_by(EducationalContent.created_at.desc())
    
    # صفحه‌بندی
    pagination = base_query.paginate(page=page, per_page=10, error_out=False)
    educational_content = pagination.items
    
    # دریافت لیست همه دسته‌بندی‌ها برای فیلتر
    categories = db.session.query(EducationalContent.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('admin/education.html',
                          educational_content=educational_content,
                          pagination=pagination,
                          categories=categories,
                          active_page='admin')

# فانکشن مدیریت دیتابیس در پایین فایل تعریف شده است

# روت‌های مربوط به محتوای ثابت
@app.route('/admin/static-content')
@login_required
def admin_static_content():
    """پنل مدیریت - محتوای ثابت"""
    about = StaticContent.query.filter_by(content_type='about').first()
    contact = StaticContent.query.filter_by(content_type='contact').first()
    
    # اگر محتوا وجود نداشته باشد، یک شیء خالی ایجاد می‌کنیم
    about_content = about if about else {'content_type': 'about', 'content': ''}
    contact_content = contact if contact else {'content_type': 'contact', 'content': ''}
    
    return render_template('admin_content.html', 
                          about_content=about_content,
                          contact_content=contact_content)

# روت مدیریت محتوا (برای رفع ارور 404)
@app.route('/admin/content')
@login_required
def admin_content():
    """پنل مدیریت - محتوا"""
    # این روت به صفحه مدیریت محتوای ثابت ریدایرکت می‌کند
    return redirect(url_for('admin_static_content'))

# روت به‌روزرسانی محتوای ثابت
@app.route('/admin/update-static-content', methods=['POST'])
@login_required
def admin_update_static_content():
    """به‌روزرسانی محتوای ثابت (درباره ما / تماس با ما)"""
    try:
        content_type = request.form.get('content_type')
        content_text = request.form.get('content')
        
        if not content_type or content_type not in ['about', 'contact']:
            flash('نوع محتوا نامعتبر است.', 'danger')
            return redirect(url_for('admin_static_content'))
        
        # دریافت رکورد موجود یا ایجاد یکی جدید
        content = StaticContent.query.filter_by(content_type=content_type).first()
        if not content:
            content = StaticContent()
            content.content_type = content_type
            
        content.content = content_text
        content.updated_at = datetime.datetime.now()
        
        db.session.add(content)
        db.session.commit()
        
        flash(f'محتوای {content_type} با موفقیت به‌روزرسانی شد.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating static content: {e}")
        flash(f'خطا در به‌روزرسانی محتوا: {str(e)}', 'danger')
    
    return redirect(url_for('admin_static_content'))

# ---- API routes for bot webhook - NO authentication required ----
@app.route('/api/webhook', methods=['POST'])
def telegram_webhook():
    """دریافت و پردازش وب‌هوک تلگرام"""
    # This endpoint should be configured in your bot.py file
    # and is only a placeholder for the Flask app
    return jsonify({"status": "ok", "method": "webhook"})

# ----- JSON API endpoints -----

@app.route('/api/categories', methods=['GET'])
def api_categories():
    """API دریافت دسته‌بندی‌ها"""
    try:
        cat_type = request.args.get('type', None)
        parent_id = request.args.get('parent_id', type=int)
        
        # فیلتر بر اساس پارامترهای ورودی
        query = Category.query
        
        if cat_type:
            query = query.filter_by(cat_type=cat_type)
        
        if parent_id is not None:
            query = query.filter_by(parent_id=parent_id)
        else:
            # اگر parent_id ارسال نشده باشد، دسته‌های اصلی را برمی‌گرداند
            query = query.filter_by(parent_id=None)
            
        categories = query.all()
        
        # تبدیل به دیکشنری برای پاسخ JSON
        result = []
        for category in categories:
            result.append({
                'id': category.id,
                'name': category.name,
                'type': category.cat_type,
                'parent_id': category.parent_id
            })
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products', methods=['GET'])
def api_products():
    """API دریافت محصولات"""
    try:
        category_id = request.args.get('category_id', type=int)
        featured = request.args.get('featured', type=bool)
        
        # فیلتر بر اساس پارامترهای ورودی
        query = Product.query
        
        if category_id:
            query = query.filter_by(category_id=category_id)
            
        if featured is not None:
            query = query.filter_by(featured=featured)
            
        products = query.all()
        
        # تبدیل به دیکشنری برای پاسخ JSON
        result = []
        for product in products:
            result.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'description': product.description,
                'category_id': product.category_id,
                'photo_url': product.photo_url,
                'featured': product.featured,
                'brand': product.brand,
                'model': product.model,
                'in_stock': product.in_stock,
            })
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/services', methods=['GET'])
def api_services():
    """API دریافت خدمات"""
    try:
        category_id = request.args.get('category_id', type=int)
        featured = request.args.get('featured', type=bool)
        
        # فیلتر بر اساس پارامترهای ورودی
        query = Product.query.filter_by(product_type='service')
        
        if category_id:
            query = query.filter_by(category_id=category_id)
            
        if featured is not None:
            query = query.filter_by(featured=featured)
            
        services = query.all()
        
        # تبدیل به دیکشنری برای پاسخ JSON
        result = []
        for service in services:
            result.append({
                'id': service.id,
                'name': service.name,
                'price': service.price,
                'description': service.description,
                'category_id': service.category_id,
                'photo_url': service.photo_url,
                'featured': service.featured
            })
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/educational', methods=['GET'])
def api_educational():
    """API دریافت محتوای آموزشی"""
    try:
        category = request.args.get('category')
        
        # فیلتر بر اساس پارامترهای ورودی
        query = EducationalContent.query
        
        if category:
            query = query.filter_by(category=category)
            
        contents = query.all()
        
        # تبدیل به دیکشنری برای پاسخ JSON
        result = []
        for content in contents:
            result.append({
                'id': content.id,
                'title': content.title,
                'content': content.content,
                'category': content.category,
                'content_type': content.content_type,
                'created_at': content.created_at.isoformat() if content.created_at else None
            })
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/inquiries', methods=['GET'])
def api_inquiries():
    """API دریافت استعلام‌ها (فقط برای ادمین)"""
    try:
        # چک کردن دسترسی ادمین
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'دسترسی غیرمجاز'}), 403
            
        inquiries = Inquiry.query.all()
        
        # تبدیل به دیکشنری برای پاسخ JSON
        result = []
        for inquiry in inquiries:
            result.append({
                'id': inquiry.id,
                'user_id': inquiry.user_id,
                'name': inquiry.name,
                'phone': inquiry.phone,
                'description': inquiry.description,
                'product_id': inquiry.product_id,
                'product_type': inquiry.product_type,
                'status': inquiry.status,
                'created_at': inquiry.created_at.isoformat() if inquiry.created_at else None
            })
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/telegram_file/<file_id>')
def telegram_file(file_id):
    """سرو فایل‌های آپلود شده از تلگرام"""
    try:
        # جستجوی فایل در جدول ProductMedia
        media = ProductMedia.query.filter_by(file_id=file_id).first()
        
        if not media:
            # جستجو در جدول ProductMedia برای خدمات
            media = ProductMedia.query.join(Product).filter(
                ProductMedia.file_id==file_id, 
                Product.product_type=='service'
            ).first()
            
        if not media or not media.local_path:
            return jsonify({'error': 'فایل پیدا نشد'}), 404
            
        # فایل را از مسیر محلی سرو می‌کنیم
        directory = os.path.dirname(media.local_path)
        filename = os.path.basename(media.local_path)
        
        return send_from_directory(directory, filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ----- Additional Web Routes -----

@app.route('/products')
def products():
    """صفحه محصولات"""
    try:
        category_id = request.args.get('category', type=int)
        
        # دریافت محصولات
        query = Product.query
        if category_id:
            query = query.filter_by(category_id=category_id)
        products_list = query.all()
        
        # دریافت دسته‌بندی‌ها
        categories = Category.query.filter_by(cat_type='product', parent_id=None).all()
        
        return render_template('products.html', 
                              products=products_list,
                              categories=categories,
                              selected_category=category_id)
    except Exception as e:
        flash(f'خطا در نمایش صفحه محصولات: {str(e)}', 'danger')
        return render_template('products.html', products=[], categories=[], selected_category=None)

@app.route('/services')
def services():
    """صفحه خدمات"""
    try:
        category_id = request.args.get('category', type=int)
        
        # دریافت خدمات (در واقع محصولات با نوع service)
        query = Product.query.filter_by(product_type='service')
        if category_id:
            query = query.filter_by(category_id=category_id)
        services_list = query.all()
        
        # دریافت دسته‌بندی‌ها
        categories = Category.query.filter_by(cat_type='service', parent_id=None).all()
        
        return render_template('services.html', 
                              services=services_list,
                              categories=categories,
                              selected_category=category_id)
    except Exception as e:
        flash(f'خطا در نمایش صفحه خدمات: {str(e)}', 'danger')
        return render_template('services.html', services=[], categories=[], selected_category=None)

@app.route('/educational')
def educational():
    """صفحه محتوای آموزشی"""
    try:
        category = request.args.get('category')
        
        # دریافت محتوای آموزشی
        query = EducationalContent.query
        if category:
            query = query.filter_by(category=category)
        contents = query.order_by(EducationalContent.created_at.desc()).all()
        
        # دریافت دسته‌بندی‌های منحصر به فرد
        categories = db.session.query(EducationalContent.category).distinct().all()
        categories = [c[0] for c in categories]
        
        return render_template('educational.html', 
                              contents=contents,
                              categories=categories,
                              selected_category=category)
    except Exception as e:
        flash(f'خطا در نمایش صفحه محتوای آموزشی: {str(e)}', 'danger')
        return render_template('educational.html', contents=[], categories=[], selected_category=None)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """صفحه ورود ادمین"""
    # اگر کاربر قبلاً وارد شده باشد، به پنل ادمین منتقل می‌شود
    if current_user.is_authenticated:
        return redirect(url_for('admin_panel'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next', url_for('admin_panel'))
            return redirect(next_page)
        else:
            flash('نام کاربری یا رمز عبور اشتباه است', 'danger')
            
    return render_template('admin/login.html')

# ----- Common error handlers -----

@app.errorhandler(404)
def page_not_found(e):
    """صفحه ۴۰۴ - صفحه پیدا نشد"""
    return render_template('404.html'), 404

@app.route('/search')
def search():
    """جستجوی پیشرفته محصولات و خدمات"""
    try:
        query_text = request.args.get('q', '')
        category_id = request.args.get('category', type=int)
        product_type = request.args.get('type')
        min_price = request.args.get('min_price', type=int)
        max_price = request.args.get('max_price', type=int)
        sort_by = request.args.get('sort_by', 'name')
        
        # بررسی پارامترها و اعمال فیلترها
        filters = {}
        if query_text:
            filters['query'] = query_text
        if category_id is not None:
            filters['category_id'] = category_id
        if product_type:
            filters['product_type'] = product_type
        if min_price is not None:
            filters['min_price'] = min_price
        if max_price is not None:
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

# ----- Database Management Routes -----

@app.route('/admin/database')
@login_required
def database_management():
    """صفحه مدیریت دیتابیس"""
    try:
        import psycopg2
        
        # دریافت اطلاعات اتصال به دیتابیس
        db_url = os.environ.get('DATABASE_URL', '')
        pg_host = os.environ.get('PGHOST', 'localhost')
        pg_database = os.environ.get('PGDATABASE', 'postgres')
        pg_user = os.environ.get('PGUSER', 'postgres')
        
        # دریافت نسخه PostgreSQL
        conn = None
        try:
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            pg_version = cursor.fetchone()[0].split(',')[0]
            cursor.close()
        except Exception as e:
            logger.error(f"Error getting PostgreSQL version: {e}")
            pg_version = 'نامشخص'
        finally:
            if conn:
                conn.close()
        
        # دریافت لیست جداول و تعداد رکوردها
        table_counts = {}
        model_classes = [
            User, Category, Product, ProductMedia, 
            Inquiry, EducationalContent, StaticContent
        ]
        
        for model in model_classes:
            table_name = model.__tablename__
            count = db.session.query(model).count()
            table_counts[table_name] = count
        
        # دریافت ساختار جداول
        table_structures = {}
        try:
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            for table_name in table_counts.keys():
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position;
                """)
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        'column_name': row[0],
                        'data_type': row[1],
                        'is_nullable': row[2],
                        'column_default': row[3]
                    })
                table_structures[table_name] = columns
            
            cursor.close()
        except Exception as e:
            logger.error(f"Error getting table structures: {e}")
        finally:
            if conn:
                conn.close()
        
        return render_template('database.html', 
                              pg_version=pg_version,
                              pg_host=pg_host,
                              pg_database=pg_database,
                              pg_user=pg_user,
                              table_counts=table_counts,
                              table_structures=table_structures,
                              active_page='admin')
    except Exception as e:
        logger.error(f"Error in database management route: {e}")
        return render_template('500.html'), 500

@app.route('/admin/database/table/<table_name>')
@login_required
def view_table_data(table_name):
    """نمایش محتوای جدول"""
    try:
        # مپ کردن نام جدول به کلاس مدل
        model_map = {
            'users': User,
            'categories': Category,
            'products': Product,
            
            'product_media': ProductMedia,
            
            'inquiries': Inquiry,
            'educational_content': EducationalContent,
            'static_content': StaticContent
        }
        
        if table_name not in model_map:
            flash(f'جدول {table_name} یافت نشد.', 'danger')
            return redirect(url_for('database_management'))
        
        model = model_map[table_name]
        
        # پارامترهای صفحه‌بندی
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # کوئری پایه
        query = db.session.query(model)
        
        # تعداد کل رکوردها
        total_count = query.count()
        
        # اعمال صفحه‌بندی
        offset = (page - 1) * per_page
        items = query.limit(per_page).offset(offset).all()
        
        # دریافت نام ستون‌ها
        columns = [column.name for column in model.__table__.columns]
        
        # تبدیل به دیکشنری
        rows = []
        for item in items:
            row = {}
            for column in columns:
                row[column] = getattr(item, column)
            rows.append(row)
        
        # ساخت اطلاعات صفحه‌بندی
        # محاسبه تعداد صفحات
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        # ساخت URL برای صفحات
        def url_for_page(page):
            return url_for('view_table_data', table_name=table_name, page=page, per_page=per_page)
        
        # ساخت لیست صفحات نمایش داده شده
        # نمایش حداکثر 5 صفحه اطراف صفحه فعلی
        pages = []
        left_edge = max(1, page - 2)
        right_edge = min(total_pages, page + 2)
        
        # اضافه کردن صفحه اول
        if left_edge > 1:
            pages.append(1)
            if left_edge > 2:
                pages.append('...')
        
        # اضافه کردن صفحات میانی
        for p in range(left_edge, right_edge + 1):
            pages.append(p)
        
        # اضافه کردن صفحه آخر
        if right_edge < total_pages:
            if right_edge < total_pages - 1:
                pages.append('...')
            pages.append(total_pages)
        
        # ساخت اطلاعات صفحه‌بندی
        pagination = {
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages,
            'pages': pages,
            'prev_url': url_for_page(page - 1) if page > 1 else None,
            'next_url': url_for_page(page + 1) if page < total_pages else None,
            'url_for_page': url_for_page
        }
        
        return render_template('table_data.html',
                              table_name=table_name,
                              columns=columns,
                              rows=rows,
                              pagination=pagination,
                              active_page='admin')
    except Exception as e:
        logger.error(f"Error in view table data route: {e}")
        return render_template('500.html'), 500

@app.route('/admin/import_export')
@login_required
def admin_import_export():
    """پنل مدیریت - ورود و خروج داده‌ها"""
    message = session.pop('import_export_message', None)
    return render_template('admin_import_export.html', 
                          message=message,
                          active_page='import_export')

@app.route('/admin/export/<entity_type>')
@login_required
def export_entity(entity_type):
    """خروجی داده‌ها به فرمت CSV"""
    import csv
    from io import StringIO
    
    # مپ کردن نوع داده به مدل
    entity_map = {
        'products': Product.query.filter_by(product_type='product'),
        'services': Product.query.filter_by(product_type='service'),
        'categories': Category.query,
        'inquiries': Inquiry.query,
        'educational': EducationalContent.query,
    }
    
    if entity_type not in entity_map:
        flash(f'نوع داده {entity_type} معتبر نیست.', 'danger')
        return redirect(url_for('admin_import_export'))
    
    # ایجاد فایل CSV در حافظه
    output = StringIO()
    writer = csv.writer(output)
    
    # دریافت داده‌ها
    query = entity_map[entity_type]
    items = query.all()
    
    if not items:
        flash(f'داده‌ای برای {entity_type} یافت نشد.', 'warning')
        return redirect(url_for('admin_import_export'))
    
    # نوشتن هدر بر اساس نام ستون‌ها
    sample_item = items[0]
    headers = [c.name for c in sample_item.__table__.columns if c.name != 'id']
    writer.writerow(headers)
    
    # نوشتن داده‌ها
    for item in items:
        row = [getattr(item, header) for header in headers]
        writer.writerow(row)
    
    # تنظیم پاسخ HTTP
    output.seek(0)
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers.set('Content-Disposition', f'attachment; filename={entity_type}.csv')
    
    return response

@app.route('/admin/import', methods=['POST'])
@login_required
def import_entity():
    """ورود داده‌ها از فایل CSV"""
    try:
        entity_type = request.form.get('entity_type')
        if not entity_type:
            flash('لطفا نوع داده را انتخاب کنید.', 'danger')
            return redirect(url_for('admin_import_export'))
            
        # بررسی فایل
        if 'csv_file' not in request.files:
            flash('لطفا یک فایل CSV انتخاب کنید.', 'danger')
            return redirect(url_for('admin_import_export'))
            
        file = request.files['csv_file']
        if file.filename == '':
            flash('فایلی انتخاب نشده است.', 'danger')
            return redirect(url_for('admin_import_export'))
            
        if not file.filename.endswith('.csv'):
            flash('فایل باید فرمت CSV داشته باشد.', 'danger')
            return redirect(url_for('admin_import_export'))
        
        # پردازش فایل CSV
        import csv
        from io import StringIO
        
        content = file.read().decode('utf-8')
        csv_data = StringIO(content)
        reader = csv.DictReader(csv_data)
        
        # تعداد رکوردهای وارد شده
        imported_count = 0
        
        # پردازش بر اساس نوع داده
        for row in reader:
            if entity_type == 'products':
                item = Product(
                    name=row.get('name', ''),
                    price=int(row.get('price', 0)),
                    description=row.get('description', ''),
                    category_id=int(row.get('category_id', 0)),
                    product_type='product',
                    photo_url=row.get('photo_url', None)
                )
                db.session.add(item)
                imported_count += 1
                
            elif entity_type == 'services':
                item = Product(
                    name=row.get('name', ''),
                    price=int(row.get('price', 0)),
                    description=row.get('description', ''),
                    category_id=int(row.get('category_id', 0)),
                    product_type='service',
                    photo_url=row.get('photo_url', None)
                )
                db.session.add(item)
                imported_count += 1
                
            elif entity_type == 'categories':
                item = Category(
                    name=row.get('name', ''),
                    parent_id=int(row.get('parent_id', 0)) if row.get('parent_id') else None,
                    cat_type=row.get('cat_type', 'product')
                )
                db.session.add(item)
                imported_count += 1
                
            elif entity_type == 'educational':
                item = EducationalContent(
                    title=row.get('title', ''),
                    content=row.get('content', ''),
                    category=row.get('category', ''),
                    content_type=row.get('content_type', 'general')
                )
                db.session.add(item)
                imported_count += 1
        
        # ذخیره تغییرات
        db.session.commit()
        
        flash(f'{imported_count} مورد با موفقیت وارد شد.', 'success')
        return redirect(url_for('admin_import_export'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطا در وارد کردن داده‌ها: {str(e)}', 'danger')
        return redirect(url_for('admin_import_export'))

@app.route('/admin/backup')
@login_required
def backup_database():
    """تهیه پشتیبان از دیتابیس"""
    flash('این ویژگی هنوز پیاده‌سازی نشده است.', 'warning')
    return redirect(url_for('admin_import_export'))
    
@app.route('/admin/restore', methods=['POST'])
@login_required
def restore_database():
    """بازیابی دیتابیس از فایل پشتیبان"""
    flash('این ویژگی هنوز پیاده‌سازی نشده است.', 'warning')
    return redirect(url_for('admin_import_export'))

@app.route('/admin/database/export/<table_name>', methods=['POST'])
@login_required
def export_table_csv(table_name):
    """خروجی CSV از جدول"""
    try:
        # مپ کردن نام جدول به کلاس مدل
        model_map = {
            'users': User,
            'categories': Category,
            'products': Product,
            
            'product_media': ProductMedia,
            
            'inquiries': Inquiry,
            'educational_content': EducationalContent,
            'static_content': StaticContent
        }
        
        if table_name not in model_map:
            flash(f'جدول {table_name} یافت نشد.', 'danger')
            return redirect(url_for('database_management'))
        
        model = model_map[table_name]
        
        # پارامترهای خروجی
        export_type = request.form.get('export_type', 'all')
        include_headers = request.form.get('include_headers') == 'on'
        
        # کوئری پایه
        query = db.session.query(model)
        
        # اعمال محدودیت‌ها
        if export_type == 'current':
            page = request.form.get('page', 1, type=int)
            per_page = request.form.get('per_page', 20, type=int)
            offset = (page - 1) * per_page
            query = query.limit(per_page).offset(offset)
        elif export_type == 'custom':
            start_row = request.form.get('start_row', 1, type=int)
            end_row = request.form.get('end_row', None, type=int)
            
            if start_row > 1:
                query = query.offset(start_row - 1)
            
            if end_row:
                limit = end_row - (start_row - 1)
                query = query.limit(limit)
        
        # اجرای کوئری
        items = query.all()
        
        # دریافت نام ستون‌ها
        columns = [column.name for column in model.__table__.columns]
        
        # ایجاد فایل CSV
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        # نوشتن هدر
        if include_headers:
            writer.writerow(columns)
        
        # نوشتن داده‌ها
        for item in items:
            row = []
            for column in columns:
                value = getattr(item, column)
                # تبدیل None به رشته خالی
                if value is None:
                    value = ''
                row.append(value)
            writer.writerow(row)
        
        # ایجاد پاسخ
        output.seek(0)
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment;filename={table_name}_{timestamp}.csv'}
        )
    except Exception as e:
        logger.error(f"Error in export table CSV route: {e}")
        flash(f'خطا در خروجی‌گیری از جدول: {str(e)}', 'danger')
        return redirect(url_for('database_management'))

@app.route('/execute_sql', methods=['POST'])
@login_required
def execute_sql():
    """اجرای کوئری SQL"""
    try:
        if request.is_json:
            data = request.get_json()
            sql_query = data.get('sql_query', '')
        else:
            sql_query = request.form.get('sql_query', '')
        
        if not sql_query.strip():
            return jsonify({'error': 'کوئری خالی است.'})
        
        # بررسی عملیات‌های غیرمجاز (DROP, ALTER, و غیره)
        import re
        import datetime
        dangerous_patterns = [
            r'\bDROP\s+DATABASE\b',
            r'\bDROP\s+SCHEMA\b',
            r'\bTRUNCATE\s+DATABASE\b',
            r'\bALTER\s+DATABASE\b',
            r'\bCREATE\s+DATABASE\b',
            r'\bCREATE\s+USER\b',
            r'\bALTER\s+USER\b',
            r'\bDROP\s+USER\b',
            r'\bGRANT\b',
            r'\bREVOKE\b',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql_query, re.IGNORECASE):
                return jsonify({'error': 'عملیات غیرمجاز. شما اجازه اجرای این نوع کوئری را ندارید.'})
        
        # اجرای کوئری
        import psycopg2
        import psycopg2.extras
        
        db_url = os.environ.get('DATABASE_URL', '')
        conn = psycopg2.connect(db_url)
        cursor = None
        
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(sql_query)
            
            # بررسی نوع کوئری
            sql_type = sql_query.strip().upper().split()[0]
            
            if sql_type in ('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN'):
                # برای کوئری‌های SELECT
                results = cursor.fetchall()
                
                # تبدیل نتایج به لیست دیکشنری‌ها
                column_names = [desc[0] for desc in cursor.description]
                result_dicts = []
                
                for row in results:
                    row_dict = {}
                    for i, value in enumerate(row):
                        # تبدیل مقادیر غیرقابل سریالایز
                        if isinstance(value, (datetime.date, datetime.datetime)):
                            value = value.isoformat()
                        row_dict[column_names[i]] = value
                    result_dicts.append(row_dict)
                
                conn.commit()
                return jsonify({'results': result_dicts})
            else:
                # برای کوئری‌های غیر SELECT (INSERT, UPDATE, DELETE)
                affected_rows = cursor.rowcount
                conn.commit()
                return jsonify({'message': f'{affected_rows} رکورد تحت تأثیر قرار گرفت.', 'affected_rows': affected_rows})
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)})
        finally:
            if cursor:
                cursor.close()
            conn.close()
    except Exception as e:
        logger.error(f"Error executing SQL: {e}")
        return jsonify({'error': str(e)})

# ----- Bot Configuration Routes -----

@app.route('/configuration', methods=['GET', 'POST'])
@login_required
def configuration_page():
    """صفحه تنظیمات ربات"""
    try:
        from configuration import load_config, save_config
        
        if request.method == 'POST':
            config = load_config()
            
            # به‌روزرسانی تنظیمات
            for key in request.form:
                if key in config:
                    config[key] = request.form[key]
            
            save_config(config)
            flash('تنظیمات با موفقیت به‌روزرسانی شد.', 'success')
        
        config = load_config()
        return render_template('configuration.html', config=config, active_page='admin')
    except Exception as e:
        logger.error(f"Error in configuration page: {e}")
        flash('خطا در بارگذاری تنظیمات: ' + str(e), 'danger')
        return redirect(url_for('admin_index'))

# ----- Bot Control Routes -----

@app.route('/logs')
@login_required
def logs():
    """دریافت لاگ‌های ربات"""
    import os
    try:
        # تلاش برای خواندن آخرین خطوط فایل لاگ
        log_file = 'bot.log'
        max_lines = 50  # حداکثر تعداد خطوط برای نمایش
        
        # برای درخواست‌های AJAX، پاسخ JSON برگردان
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        # خواندن آخرین خطوط
                        all_lines = f.readlines()
                        lines = all_lines[-max_lines:] if len(all_lines) > max_lines else all_lines
                        return jsonify({'logs': ''.join(lines)})
                else:
                    return jsonify({'logs': 'فایل لاگ موجود نیست.'})
            except Exception as e:
                logger.error(f"Error reading log file: {e}")
                return jsonify({'logs': f'خطا در خواندن فایل لاگ: {str(e)}'})
        
        # برای درخواست‌های معمولی، صفحه HTML برگردان
        try:
            bot_logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    bot_logs = lines[-50:] if len(lines) > 50 else lines
            else:
                bot_logs = ['فایل لاگ موجود نیست.']
                
            return render_template('logs.html', 
                                 logs=bot_logs,
                                 datetime=datetime,
                                 active_page='logs')
        except Exception as e:
            logger.error(f"Error reading log file for HTML view: {e}")
            bot_logs = [f'خطا در خواندن فایل لاگ: {str(e)}']
            return render_template('logs.html',
                                 logs=bot_logs,
                                 datetime=datetime,
                                 active_page='logs')
    except Exception as e:
        logger.error(f"Error in logs route: {e}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'logs': 'خطای داخلی سرور'})
        else:
            return render_template('error.html', error='خطای داخلی سرور')

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