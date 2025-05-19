"""
مسیرهای وب فلسک
این فایل شامل تمام مسیرها و نقاط پایانی وب است.
"""

import os
import logging
import datetime
import time
from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import text

from src.web.app import app, db, media_files
from src.models.models import (
    User, Product, ProductMedia, Service, ServiceMedia, Inquiry,
    EducationalContent, StaticContent, EducationalCategory, EducationalContentMedia,
    ProductCategory, ServiceCategory
)
from src.utils.utils import allowed_file, save_uploaded_file, create_directory
from src.utils.utils_upload import handle_media_upload, remove_file, serve_file
import shutil

# تنظیم لاگر
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# تنظیم لاگر برای ذخیره لاگ‌ها در فایل
file_handler = logging.FileHandler('logs/rfcbot.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# ----- Utility Functions for Media Management -----

def delete_media_file(file_path):
    """
    حذف فیزیکی فایل رسانه‌ای از سیستم فایل
    
    Args:
        file_path: مسیر فایل برای حذف
    
    Returns:
        bool: موفقیت یا عدم موفقیت عملیات
    """
    try:
        # بررسی اینکه آیا فایل وجود دارد
        if file_path and os.path.exists(file_path):
            # حذف فایل
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
            logger.info(f"File deleted successfully: {file_path}")
            return True
        else:
            logger.warning(f"File not found for deletion: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        return False

# ----- Main Routes -----

@app.route('/')
def index():
    """صفحه اصلی"""
    try:
        # محصولات و خدمات حالا از جداول جداگانه دریافت می‌شوند
        products = Product.query.filter_by(featured=True).limit(6).all()
        services = Service.query.filter_by(featured=True).limit(6).all()
        
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
            
        # دریافت محتوای ثابت (درباره ما)
        try:
            about_content = StaticContent.query.filter_by(content_type='about').first()
            if about_content:
                about = about_content.content
            else:
                about = "محتوای درباره ما وجود ندارد"
        except Exception as e:
            logger.warning(f"Error loading about content: {e}")
            about = "خطا در بارگذاری محتوای درباره ما"
        
        # برای نمایش وضعیت متغیرهای محیطی
        env_status = {
            'BOT_TOKEN': 'Set' if os.environ.get('BOT_TOKEN') else 'Not Set',
            'DATABASE_URL': 'Set' if os.environ.get('DATABASE_URL') else 'Not Set',
            'ADMIN_ID': 'Set' if os.environ.get('ADMIN_ID') else 'Not Set'
        }
            
        return render_template('index.html', products=products, services=services, 
                            educational=educational, about=about, env_status=env_status)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        # برای نمایش وضعیت متغیرهای محیطی
        env_status = {
            'BOT_TOKEN': 'Set' if os.environ.get('BOT_TOKEN') else 'Not Set',
            'DATABASE_URL': 'Set' if os.environ.get('DATABASE_URL') else 'Not Set',
            'ADMIN_ID': 'Set' if os.environ.get('ADMIN_ID') else 'Not Set'
        }
        return render_template('index.html', products=[], services=[], 
                            educational=[], about="خطا در بارگذاری محتوا", env_status=env_status)
        
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
            
@app.route('/api/logs')
def get_logs_json():
    """دریافت لاگ‌های ربات برای درخواست‌های AJAX"""
    try:
        log_file = 'bot.log'
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # فقط آخرین ۵۰ خط را برمی‌گردانیم تا حجم داده زیاد نباشد
                bot_logs = lines[-50:] if len(lines) > 50 else lines
                # تبدیل آرایه خطوط به یک رشته با جداکننده خط جدید
                logs_text = ''.join(bot_logs)
        else:
            logs_text = 'فایل لاگ موجود نیست.'
        
        # برگرداندن پاسخ JSON برای درخواست‌های AJAX
        return jsonify({'logs': logs_text})
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return jsonify({'error': str(e)}), 500

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

# ----- Media Deletion Route -----

@app.route('/admin/delete_media', methods=['POST'])
@login_required
def delete_media():
    """
    حذف فایل رسانه‌ای از سیستم
    
    این مسیر برای حذف فایل‌های رسانه‌ای از محصولات، خدمات و محتوای آموزشی استفاده می‌شود.
    هم رکورد پایگاه داده و هم فایل فیزیکی حذف می‌شوند.
    """
    if not current_user.is_admin:
        logger.warning(f"Non-admin user {current_user.id} attempted to delete media")
        return jsonify({'success': False, 'error': 'دسترسی مجاز نیست'}), 403
    
    try:
        content_type = request.args.get('type')
        content_id = request.args.get('content_id')
        media_id = request.args.get('media_id')
        media_type = request.args.get('media_type')
        
        if not all([content_type, content_id, media_id]):
            logger.error(f"Missing parameters in delete_media request: {request.args}")
            return jsonify({'success': False, 'error': 'پارامترهای ناقص'}), 400
        
        # تبدیل به اعداد صحیح
        try:
            content_id = int(content_id)
            media_id = int(media_id)
        except ValueError:
            logger.error(f"Invalid ID format in delete_media request: content_id={content_id}, media_id={media_id}")
            return jsonify({'success': False, 'error': 'فرمت شناسه نامعتبر است'}), 400
        
        # حذف بر اساس نوع محتوا
        if content_type == 'product':
            # حذف رسانه محصول
            media = ProductMedia.query.get(media_id)
            if not media or media.product_id != content_id:
                logger.warning(f"Product media not found or mismatch: media_id={media_id}, product_id={content_id}")
                return jsonify({'success': False, 'error': 'رسانه محصول یافت نشد'}), 404
            
            # حذف فایل فیزیکی
            file_path = None
            if hasattr(media, 'local_path') and media.local_path and os.path.exists(media.local_path):
                file_path = media.local_path
            elif media.file_id:
                # تلاش برای پیدا کردن مسیر فایل از file_id
                file_path = os.path.join('static', 'uploads', 'products', f"{media.file_id.split('_')[-1]}")
            
            # حذف فایل فیزیکی
            delete_result = delete_media_file(file_path) if file_path else False
            
            # حذف رکورد از پایگاه داده
            db.session.delete(media)
            db.session.commit()
            
            logger.info(f"Product media deleted: id={media_id}, product_id={content_id}, file_path={file_path}, file_deleted={delete_result}")
            return jsonify({'success': True})
            
        elif content_type == 'service':
            # حذف رسانه خدمت
            media = ServiceMedia.query.get(media_id)
            if not media or media.service_id != content_id:
                logger.warning(f"Service media not found or mismatch: media_id={media_id}, service_id={content_id}")
                return jsonify({'success': False, 'error': 'رسانه خدمت یافت نشد'}), 404
            
            # حذف فایل فیزیکی
            file_path = None
            if hasattr(media, 'local_path') and media.local_path and os.path.exists(media.local_path):
                file_path = media.local_path
            elif media.file_id:
                # تلاش برای پیدا کردن مسیر فایل از file_id
                file_path = os.path.join('static', 'uploads', 'services', f"{media.file_id.split('_')[-1]}")
            
            # حذف فایل فیزیکی
            delete_result = delete_media_file(file_path) if file_path else False
            
            # حذف رکورد از پایگاه داده
            db.session.delete(media)
            db.session.commit()
            
            logger.info(f"Service media deleted: id={media_id}, service_id={content_id}, file_path={file_path}, file_deleted={delete_result}")
            return jsonify({'success': True})
            
        elif content_type == 'educational':
            # حذف رسانه محتوای آموزشی
            media = EducationalContentMedia.query.get(media_id)
            if not media or media.content_id != content_id:
                logger.warning(f"Educational content media not found or mismatch: media_id={media_id}, content_id={content_id}")
                return jsonify({'success': False, 'error': 'رسانه محتوای آموزشی یافت نشد'}), 404
            
            # حذف فایل فیزیکی
            file_path = None
            if hasattr(media, 'local_path') and media.local_path and os.path.exists(media.local_path):
                file_path = media.local_path
            elif media.file_id:
                # تلاش برای پیدا کردن مسیر فایل از file_id
                file_path = os.path.join('static', 'uploads', 'educational', f"{media.file_id.split('_')[-1]}")
                if not os.path.exists(file_path):
                    file_path = os.path.join('media', 'educational', f"{media.file_id.split('_')[-1]}")
            
            # حذف فایل فیزیکی
            delete_result = delete_media_file(file_path) if file_path else False
            
            # حذف رکورد از پایگاه داده
            db.session.delete(media)
            db.session.commit()
            
            logger.info(f"Educational content media deleted: id={media_id}, content_id={content_id}, file_path={file_path}, file_deleted={delete_result}")
            return jsonify({'success': True})
            
        else:
            logger.error(f"Invalid content type in delete_media request: {content_type}")
            return jsonify({'success': False, 'error': 'نوع محتوا نامعتبر است'}), 400
            
    except Exception as e:
        logger.error(f"Error in delete_media: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ----- Admin Dashboard Routes -----

@app.route('/admin')
@app.route('/admin/')
@login_required
def admin_index():
    """پنل مدیریت - داشبورد"""
    try:
        # آمار سیستم
        product_count = Product.query.count()
        service_count = Service.query.count()
        product_category_count = ProductCategory.query.count()
        service_category_count = ServiceCategory.query.count()
        educational_category_count = EducationalCategory.query.count()
        category_count = product_category_count + service_category_count + educational_category_count
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
    # دریافت دسته‌بندی‌های محصول
    product_categories = ProductCategory.query.all()
    product_tree = build_category_tree(product_categories)
    
    # دریافت دسته‌بندی‌های خدمات
    service_categories = ServiceCategory.query.all()
    service_tree = build_category_tree(service_categories)
    
    # دریافت دسته‌بندی‌های محتوای آموزشی
    educational_categories = EducationalCategory.query.all()
    educational_tree = build_category_tree(educational_categories)
    
    # دسته‌بندی‌های قدیمی دیگر استفاده نمی‌شوند
    categories = []
    category_tree = []
    
    return render_template('admin/categories.html', 
                          product_categories=product_categories,
                          service_categories=service_categories,
                          educational_categories=educational_categories,
                          product_tree=product_tree,
                          service_tree=service_tree,
                          educational_tree=educational_tree,
                          # برای سازگاری با سیستم قدیمی
                          categories=categories,
                          category_tree=category_tree)

def build_category_tree(categories, parent_id=None):
    """ساخت ساختار درختی از دسته‌بندی‌ها"""
    tree = []
    for category in categories:
        if category.parent_id == parent_id:
            children = build_category_tree(categories, category.id)
            category_data = {
                'id': category.id,
                'name': category.name,
                'children': children
            }
            # افزودن cat_type فقط اگر در مدل موجود باشد (برای سازگاری با مدل قدیمی Category)
            if hasattr(category, 'cat_type'):
                category_data['cat_type'] = category.cat_type
            
            tree.append(category_data)
    return tree

@app.route('/admin/categories/add', methods=['POST'])
@login_required
def admin_add_category():
    """اضافه کردن، ویرایش یا حذف دسته‌بندی"""
    try:
        # بررسی نوع عملیات و نوع دسته‌بندی
        action = request.form.get('_action', 'add')
        category_type = request.form.get('category_type')
        
        # دریافت پارامترهای مشترک برای اضافه کردن و ویرایش
        name = request.form.get('name')
        parent_id = request.form.get('parent_id')
        
        # تبدیل parent_id به None اگر خالی باشد
        if parent_id and parent_id != '':
            parent_id = int(parent_id)
        else:
            parent_id = None
        
        # تعیین مدل دسته‌بندی بر اساس نوع
        if category_type == 'product':
            CategoryModel = ProductCategory
        elif category_type == 'service':
            CategoryModel = ServiceCategory
        elif category_type == 'educational':
            CategoryModel = EducationalCategory
        else:
            # اگر نوع نامشخص باشد، محصول در نظر گرفته می‌شود
            CategoryModel = ProductCategory
        
        # عملیات حذف
        if action == 'delete':
            category_id = request.form.get('id')
            if category_id:
                category = CategoryModel.query.get_or_404(int(category_id))
                name = category.name
                db.session.delete(category)
                db.session.commit()
                flash(f'دسته‌بندی {name} با موفقیت حذف شد.', 'success')
        
        # عملیات ویرایش
        elif action == 'edit':
            category_id = request.form.get('id')
            if category_id and name:
                category = CategoryModel.query.get_or_404(int(category_id))
                category.name = name
                category.parent_id = parent_id
                
                # فیلد cat_type دیگر استفاده نمی‌شود
                
                db.session.commit()
                flash(f'دسته‌بندی {name} با موفقیت ویرایش شد.', 'success')
        
        # عملیات اضافه کردن
        else:  # action == 'add'
            if name:
                # ایجاد دسته‌بندی جدید
                category = CategoryModel()
                category.name = name
                category.parent_id = parent_id
                
                db.session.add(category)
                db.session.commit()
                flash(f'دسته‌بندی {name} با موفقیت اضافه شد.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in admin_add_category: {e}")
        flash(f'خطا در عملیات دسته‌بندی: {str(e)}', 'danger')
    
    return redirect(url_for('admin_categories'))

# ... Routes for products, services, inquiries, etc. ...

# تابع کمکی برای تبدیل مسیر فایل تصویر
def get_photo_url(photo_url):
    """
    تبدیل مسیر photo_url به مسیر قابل استفاده در url_for
    
    اگر photo_url با static/ شروع شود، مسیر بدون static/ برگردانده می‌شود
    اگر photo_url با uploads/ شروع شود، مسیر همان‌طور برگردانده می‌شود
    اگر photo_url خالی یا None باشد، None برگردانده می‌شود
    """
    if not photo_url:
        return None
    
    if photo_url.startswith('static/'):
        return photo_url[7:]  # حذف 'static/' از ابتدای مسیر
    
    return photo_url

# روت‌های مربوط به محصولات
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """صفحه جزئیات محصول"""
    product = Product.query.get_or_404(product_id)
    # محصولات مرتبط که در همان دسته‌بندی هستند اما ID متفاوتی دارند
    related_products = Product.query.filter_by(category_id=product.category_id).filter(Product.id != product.id).limit(4).all()
    media = ProductMedia.query.filter_by(product_id=product.id).all()
    
    # تبدیل مسیر photo_url برای استفاده در url_for
    photo_url = get_photo_url(product.photo_url)
    
    # تبدیل مسیر photo_url برای محصولات مرتبط
    for related in related_products:
        related.formatted_photo_url = get_photo_url(related.photo_url)
    
    return render_template('product_detail.html', 
                          product=product,
                          photo_url=photo_url,
                          related_products=related_products,
                          media=media)

@app.route('/admin/products', methods=['GET', 'POST'])
@login_required
def admin_products():
    """پنل مدیریت - محصولات"""
    action = request.args.get('action')
    product_id = request.args.get('id')
    
    # عملیات POST
    if request.method == 'POST':
        # حذف محصول
        if action == 'delete':
            product_id = request.form.get('product_id')
            if not product_id:
                flash('شناسه محصول الزامی است.', 'danger')
                return redirect(url_for('admin_products'))
                
            try:
                product = Product.query.get_or_404(int(product_id))
                
                # حذف تمام رسانه‌های مرتبط با محصول و فایل‌ها از دیسک
                media_files = ProductMedia.query.filter_by(product_id=product.id).all()
                for media in media_files:
                    # حذف فایل از دیسک اگر محلی باشد
                    if media.file_id and not media.file_id.startswith('http'):
                        file_path = os.path.join('static', media.file_id)
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                logger.info(f"Removed file from disk: {file_path}")
                            except Exception as e:
                                logger.warning(f"Could not remove file {file_path}: {e}")
                
                # حذف محصول از دیتابیس (رسانه‌ها به دلیل CASCADE خودکار حذف می‌شوند)
                db.session.delete(product)
                db.session.commit()
                
                flash(f'محصول "{product.name}" با موفقیت حذف شد.', 'success')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error deleting product: {e}")
                flash(f'خطا در حذف محصول: {str(e)}', 'danger')
                
            return redirect(url_for('admin_products'))
            
        # آپلود رسانه جدید
        elif action == 'upload_media':
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
                    
                    # استفاده از تابع handle_media_upload برای مدیریت آپلود
                    success, file_path = handle_media_upload(
                        file=file,
                        directory=upload_dir,
                        file_type=file_type,
                        custom_filename=None  # استفاده از نام اصلی فایل (با تغییر امن)
                    )
                    
                    if success and file_path:
                        # تبدیل مسیر کامل به مسیر نسبی برای ذخیره در دیتابیس
                        relative_path = file_path.replace('static/', '', 1) if file_path.startswith('static/') else file_path
                        logger.info(f"Product media relative path: {relative_path}")
                        
                        # افزودن به دیتابیس
                        media = ProductMedia(
                            product_id=product.id,
                            file_id=relative_path,
                            file_type=file_type,
                            local_path=file_path  # ذخیره مسیر کامل برای استفاده بعدی
                        )
                        db.session.add(media)
                        db.session.commit()
                        
                        logger.info(f"Media uploaded successfully: {file_path}")
                        flash('رسانه با موفقیت آپلود شد.', 'success')
                    else:
                        flash('خطا در آپلود فایل. لطفاً دوباره تلاش کنید.', 'danger')
                        logger.error(f"File upload failed - no file path returned")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error uploading media: {e}")
                    logger.error(f"Exception details: {str(e)}")
                    flash(f'خطا در آپلود رسانه: {str(e)}', 'danger')
            else:
                flash('لطفاً یک فایل انتخاب کنید.', 'warning')
                
            return redirect(url_for('admin_products', action='media', id=product_id))
            
        # ذخیره محصول جدید یا ویرایش محصول موجود
        elif action == 'save':
            # دریافت داده‌های فرم
            product_id = request.form.get('id')
            name = request.form.get('name')
            price = request.form.get('price', 0)
            description = request.form.get('description', '')
            category_id = request.form.get('category_id')
            brand = request.form.get('brand', '')
            model = request.form.get('model', '')
            in_stock = 'in_stock' in request.form
            tags = request.form.get('tags', '')
            featured = 'featured' in request.form
            model_number = request.form.get('model_number', '')
            manufacturer = request.form.get('manufacturer', '')
            
            # تبدیل داده‌ها به نوع مناسب
            if price:
                try:
                    price = int(price)
                except ValueError:
                    price = 0
                    
            if category_id:
                try:
                    category_id = int(category_id)
                except ValueError:
                    category_id = None
            else:
                category_id = None
                
            try:
                # قبل از ذخیره در دیتابیس، مطمئن شویم که category_id معتبر است
                # اگر category_id خالی است، بررسی می‌کنیم آیا دسته‌بندی پیش‌فرضی وجود دارد یا نه
                if category_id is None:
                    # سعی می‌کنیم دسته‌بندی پیش‌فرض برای محصولات پیدا کنیم
                    default_category = ProductCategory.query.first()
                    if default_category:
                        category_id = default_category.id
                        logger.info(f"Using default product category ID: {category_id}")
                    else:
                        # اگر هیچ دسته‌بندی وجود ندارد، یک دسته‌بندی پیش‌فرض ایجاد می‌کنیم
                        new_category = ProductCategory(name="دسته‌بندی پیش‌فرض محصولات")
                        db.session.add(new_category)
                        db.session.flush()  # برای دریافت ID
                        category_id = new_category.id
                        logger.info(f"Created new default product category ID: {category_id}")
                
                # اگر شناسه محصول وجود داشته باشد، ویرایش می‌کنیم
                if product_id:
                    product = Product.query.get_or_404(int(product_id))
                    product.name = name
                    product.price = price
                    product.description = description
                    product.category_id = category_id # اکنون مطمئن هستیم که این مقدار NULL نیست
                    product.brand = brand
                    product.model = model
                    product.in_stock = in_stock
                    product.tags = tags
                    product.featured = featured
                    product.model_number = model_number
                    product.manufacturer = manufacturer
                    
                    logger.info(f"Updating product ID: {product_id}, Name: {name}")
                    flash('محصول با موفقیت به‌روزرسانی شد.', 'success')
                else:
                    # ایجاد محصول جدید
                    product = Product(
                        name=name,
                        price=price,
                        description=description,
                        category_id=category_id,  # اکنون مطمئن هستیم که این مقدار NULL نیست
                        brand=brand,
                        model=model,
                        in_stock=in_stock,
                        tags=tags,
                        featured=featured,
                        model_number=model_number,
                        manufacturer=manufacturer
                    )
                    db.session.add(product)
                    logger.info(f"Creating new product, Name: {name}")
                    flash('محصول جدید با موفقیت ثبت شد.', 'success')
                
                # آپلود تصویر اصلی محصول
                photo = request.files.get('photo')
                if photo and photo.filename:
                    # مسیر فایل‌های آپلودی
                    upload_dir = os.path.join('static', 'uploads', 'products', 'main')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # استفاده از تابع handle_media_upload برای مدیریت آپلود
                    success, file_path = handle_media_upload(
                        file=photo,
                        directory=upload_dir,
                        file_type='photo',
                        custom_filename=None  # استفاده از نام اصلی فایل (با تغییر امن)
                    )
                    
                    if success and file_path:
                        # تبدیل مسیر کامل به مسیر نسبی برای ذخیره در دیتابیس
                        relative_path = file_path.replace('static/', '', 1) if file_path.startswith('static/') else file_path
                        
                        # ذخیره مسیر در محصول
                        product.photo_url = relative_path
                        logger.info(f"Uploaded main photo for product, path: {relative_path}")
                
                db.session.commit()
                
                if not product_id:
                    # اگر محصول جدید بود، حالا ID آن مشخص شده، مسیر تصویر اصلی را به‌روزرسانی می‌کنیم
                    if photo and photo.filename and success and file_path:
                        # ایجاد دایرکتوری اختصاصی محصول
                        product_upload_dir = os.path.join('static', 'uploads', 'products', str(product.id))
                        os.makedirs(product_upload_dir, exist_ok=True)
                        
                        # انتقال فایل به دایرکتوری اختصاصی محصول
                        new_file_path = os.path.join(product_upload_dir, os.path.basename(file_path))
                        import shutil
                        shutil.move(file_path, new_file_path)
                        
                        # به‌روزرسانی مسیر در دیتابیس
                        new_relative_path = new_file_path.replace('static/', '', 1) if new_file_path.startswith('static/') else new_file_path
                        product.photo_url = new_relative_path
                        db.session.commit()
                        
                        logger.info(f"Moved product photo to dedicated directory: {new_file_path}")
                
                return redirect(url_for('admin_products'))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving product: {str(e)}")
                flash(f'خطا در ذخیره محصول: {str(e)}', 'danger')
                categories = ProductCategory.query.all()
                
                if product_id:
                    # در صورت خطا در ویرایش، به فرم ویرایش برمی‌گردیم
                    product = Product.query.get(int(product_id))
                    return render_template('admin/product_form.html',
                                          title="ویرایش محصول",
                                          product=product,
                                          categories=categories)
                else:
                    # در صورت خطا در افزودن، به فرم افزودن برمی‌گردیم
                    return render_template('admin/product_form.html',
                                          title="افزودن محصول جدید",
                                          categories=categories)
        
        # حذف رسانه
        elif action == 'delete_media':
            media_id = request.form.get('media_id')
            product_id = request.form.get('product_id')
            
            if not media_id or not product_id:
                flash('شناسه رسانه و شناسه محصول الزامی هستند.', 'danger')
                return redirect(url_for('admin_products'))
            
            try:
                # استفاده از ServiceMedia به جای ProductMedia
                media = ServiceMedia.query.get(int(media_id))
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
        categories = ProductCategory.query.all()
        return render_template('admin/product_form.html',
                              title="افزودن محصول جدید",
                              categories=categories)
    elif action == 'edit' and product_id:
        product = Product.query.get_or_404(int(product_id))
        categories = ProductCategory.query.all()
        return render_template('admin/product_form.html',
                              title="ویرایش محصول",
                              product=product,
                              categories=categories)
    elif action == 'media':
        if not product_id:
            # اگر شناسه محصول وجود نداشت، خطا نمایش داده می‌شود
            flash('شناسه محصول الزامی است.', 'danger')
            return redirect(url_for('admin_products'))
            
        product = Product.query.get_or_404(int(product_id))
        media = ProductMedia.query.filter_by(product_id=product.id).all()
        return render_template('admin/product_media.html',
                              product=product,
                              media=media,
                              active_page='products')
    
    # نمایش لیست محصولات
    products = Product.query.all()
    categories = ProductCategory.query.all()
    
    # تبدیل مسیر photo_url برای استفاده در url_for
    for product in products:
        product.formatted_photo_url = get_photo_url(product.photo_url)
    
    return render_template('admin/products.html', 
                          products=products,
                          categories=categories)

# روت‌های مربوط به خدمات
@app.route('/service/<int:service_id>')
def service_detail(service_id):
    """صفحه جزئیات خدمت"""
    # استفاده از مدل Service به جای فیلتر بر روی محصول
    service = Service.query.filter_by(id=service_id).first_or_404()
    # استفاده از جدول Service برای سرویس‌های مرتبط
    related_services = Service.query.filter_by(category_id=service.category_id).filter(Service.id != service.id).limit(4).all()
    # استفاده از ServiceMedia به جای ProductMedia
    media = ServiceMedia.query.filter_by(service_id=service.id).all()
    
    # تبدیل مسیر photo_url برای استفاده در url_for
    photo_url = get_photo_url(service.photo_url)
    
    # تبدیل مسیر photo_url برای خدمات مرتبط
    for related in related_services:
        related.formatted_photo_url = get_photo_url(related.photo_url)
    
    return render_template('service_detail.html', 
                          service=service,
                          photo_url=photo_url,
                          related_services=related_services,
                          media=media)

@app.route('/admin/services', methods=['GET', 'POST'])
@login_required
def admin_services():
    """پنل مدیریت - خدمات"""
    action = request.args.get('action')
    service_id = request.args.get('id')
    
    # عملیات POST
    if request.method == 'POST':
        # حذف خدمت
        if action == 'delete':
            service_id = request.form.get('service_id')
            if not service_id:
                flash('شناسه خدمت الزامی است.', 'danger')
                return redirect(url_for('admin_services'))
                
            try:
                service = Service.query.get_or_404(int(service_id))
                
                # حذف تمام رسانه‌های مرتبط با خدمت و فایل‌ها از دیسک
                media_files = ServiceMedia.query.filter_by(service_id=service.id).all()
                for media in media_files:
                    # حذف فایل از دیسک اگر محلی باشد
                    if media.file_id and not media.file_id.startswith('http'):
                        file_path = os.path.join('static', media.file_id)
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                logger.info(f"Removed file from disk: {file_path}")
                            except Exception as e:
                                logger.warning(f"Could not remove file {file_path}: {e}")
                
                # حذف خدمت از دیتابیس (رسانه‌ها به دلیل CASCADE خودکار حذف می‌شوند)
                db.session.delete(service)
                db.session.commit()
                
                flash(f'خدمت "{service.name}" با موفقیت حذف شد.', 'success')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error deleting service: {e}")
                flash(f'خطا در حذف خدمت: {str(e)}', 'danger')
                
            return redirect(url_for('admin_services'))
            
        # ذخیره خدمت جدید یا ویرایش خدمت موجود
        elif action == 'save':
            # دریافت داده‌های فرم
            service_id = request.form.get('id')
            name = request.form.get('name')
            price = request.form.get('price', 0)
            description = request.form.get('description', '')
            category_id = request.form.get('category_id')
            tags = request.form.get('tags', '')
            featured = 'featured' in request.form
            
            # تبدیل داده‌ها به نوع مناسب
            if price:
                try:
                    price = int(price)
                except ValueError:
                    price = 0
                    
            if category_id:
                try:
                    category_id = int(category_id)
                except ValueError:
                    category_id = None
            else:
                category_id = None
                
            try:
                # قبل از ذخیره در دیتابیس، مطمئن شویم که category_id معتبر است
                # اگر category_id خالی است، بررسی می‌کنیم آیا دسته‌بندی پیش‌فرضی وجود دارد یا نه
                if category_id is None:
                    # سعی می‌کنیم دسته‌بندی پیش‌فرض برای خدمات پیدا کنیم
                    default_category = ServiceCategory.query.first()
                    if default_category:
                        category_id = default_category.id
                        logger.info(f"Using default service category ID: {category_id}")
                    else:
                        # اگر هیچ دسته‌بندی وجود ندارد، یک دسته‌بندی پیش‌فرض ایجاد می‌کنیم
                        new_category = ServiceCategory(name="دسته‌بندی پیش‌فرض")
                        db.session.add(new_category)
                        db.session.flush()  # برای دریافت ID
                        category_id = new_category.id
                        logger.info(f"Created new default service category ID: {category_id}")
                
                # اگر شناسه خدمت وجود داشته باشد، ویرایش می‌کنیم
                if service_id:
                    service = Service.query.get_or_404(int(service_id))
                    service.name = name
                    service.price = price
                    service.description = description
                    service.category_id = category_id
                    service.tags = tags
                    service.featured = featured
                    
                    logger.info(f"Updating service ID: {service_id}, Name: {name}, Category: {category_id}")
                    flash('خدمت با موفقیت به‌روزرسانی شد.', 'success')
                else:
                    # ایجاد خدمت جدید
                    service = Service(
                        name=name,
                        price=price,
                        description=description,
                        category_id=category_id,  # اکنون مطمئن هستیم که این مقدار NULL نیست
                        tags=tags,
                        featured=featured
                    )
                    db.session.add(service)
                    logger.info(f"Creating new service, Name: {name}")
                    flash('خدمت جدید با موفقیت ثبت شد.', 'success')
                
                # آپلود تصویر اصلی خدمت
                photo = request.files.get('photo')
                if photo and photo.filename:
                    # مسیر فایل‌های آپلودی
                    upload_dir = os.path.join('static', 'uploads', 'services', 'main')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # استفاده از تابع handle_media_upload برای مدیریت آپلود
                    success, file_path = handle_media_upload(
                        file=photo,
                        directory=upload_dir,
                        file_type='photo',
                        custom_filename=None  # استفاده از نام اصلی فایل (با تغییر امن)
                    )
                    
                    if success and file_path:
                        # تبدیل مسیر کامل به مسیر نسبی برای ذخیره در دیتابیس
                        relative_path = file_path.replace('static/', '', 1) if file_path.startswith('static/') else file_path
                        
                        # ذخیره مسیر در خدمت
                        service.photo_url = relative_path
                        logger.info(f"Uploaded main photo for service, path: {relative_path}")
                
                db.session.commit()
                
                if not service_id:
                    # اگر خدمت جدید بود، حالا ID آن مشخص شده، مسیر تصویر اصلی را به‌روزرسانی می‌کنیم
                    if photo and photo.filename and success and file_path:
                        # ایجاد دایرکتوری اختصاصی خدمت
                        service_upload_dir = os.path.join('static', 'uploads', 'services', str(service.id))
                        os.makedirs(service_upload_dir, exist_ok=True)
                        
                        # انتقال فایل به دایرکتوری اختصاصی خدمت
                        new_file_path = os.path.join(service_upload_dir, os.path.basename(file_path))
                        import shutil
                        shutil.move(file_path, new_file_path)
                        
                        # به‌روزرسانی مسیر در دیتابیس
                        new_relative_path = new_file_path.replace('static/', '', 1) if new_file_path.startswith('static/') else new_file_path
                        service.photo_url = new_relative_path
                        db.session.commit()
                        
                        logger.info(f"Moved service photo to dedicated directory: {new_file_path}")
                
                return redirect(url_for('admin_services'))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving service: {str(e)}")
                flash(f'خطا در ذخیره خدمت: {str(e)}', 'danger')
                # استفاده از ServiceCategory به جای Category با فیلتر cat_type
                categories = ServiceCategory.query.all()
                
                if service_id:
                    # استفاده از جدول Service به جای Product با فیلتر product_type
                    service = Service.query.filter_by(id=int(service_id)).first_or_404()
                    return render_template('admin/service_form.html',
                                          title="ویرایش خدمت",
                                          service=service,
                                          categories=categories)
                else:
                    # در صورت خطا در افزودن، به فرم افزودن برمی‌گردیم
                    return render_template('admin/service_form.html',
                                          title="افزودن خدمت جدید",
                                          categories=categories)

        # آپلود رسانه جدید
        elif action == 'upload_media':
            service_id = request.form.get('service_id')
            if not service_id:
                flash('شناسه خدمت الزامی است.', 'danger')
                return redirect(url_for('admin_services'))
            
            # استفاده از جدول Service به جای Product با فیلتر product_type
            service = Service.query.filter_by(id=int(service_id)).first_or_404()
            file = request.files.get('file')
            file_type = request.form.get('file_type', 'photo')
            
            if file and file.filename:
                try:
                    # مسیر فایل‌های آپلودی
                    upload_dir = os.path.join('static', 'uploads', 'services', str(service.id))
                    
                    # استفاده از تابع handle_media_upload برای مدیریت آپلود
                    success, file_path = handle_media_upload(
                        file=file,
                        directory=upload_dir,
                        file_type=file_type,
                        custom_filename=None  # استفاده از نام اصلی فایل (با تغییر امن)
                    )
                    
                    if success and file_path:
                        # تبدیل مسیر کامل به مسیر نسبی برای ذخیره در دیتابیس
                        relative_path = file_path.replace('static/', '', 1) if file_path.startswith('static/') else file_path
                        logger.info(f"Service media relative path: {relative_path}")
                        
                        # افزودن به دیتابیس - استفاده از ServiceMedia به جای ProductMedia
                        media = ServiceMedia(
                            service_id=service.id,
                            file_id=relative_path,
                            file_type=file_type
                        )
                        
                        # بعد از ایجاد رکورد، تلاش می‌کنیم local_path را تنظیم کنیم
                        try:
                            media.local_path = file_path  # ذخیره مسیر کامل برای استفاده بعدی
                        except Exception as ex:
                            logger.warning(f"Could not set local_path attribute: {ex}")
                        db.session.add(media)
                        db.session.commit()
                        
                        logger.info(f"Service media uploaded successfully: {file_path}")
                        flash('رسانه با موفقیت آپلود شد.', 'success')
                    else:
                        flash('خطا در آپلود فایل. لطفاً دوباره تلاش کنید.', 'danger')
                        logger.error(f"Service file upload failed - no file path returned")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error uploading service media: {e}")
                    logger.error(f"Exception details: {str(e)}")
                    flash(f'خطا در آپلود رسانه: {str(e)}', 'danger')
            else:
                flash('لطفاً یک فایل انتخاب کنید.', 'warning')
                
            return redirect(url_for('admin_services', action='media', id=service_id))
            
        # حذف رسانه
        elif action == 'delete_media':
            media_id = request.form.get('media_id')
            service_id = request.form.get('service_id')
            
            if not media_id or not service_id:
                flash('شناسه رسانه و شناسه خدمت الزامی هستند.', 'danger')
                return redirect(url_for('admin_services'))
            
            try:
                # استفاده از ServiceMedia به جای ProductMedia
                media = ServiceMedia.query.get(int(media_id))
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
                logger.error(f"Error deleting service media: {e}")
                flash(f'خطا در حذف رسانه: {str(e)}', 'danger')
            
            return redirect(url_for('admin_services', action='media', id=service_id))
    
    # اگر action برابر با 'add' یا 'edit' باشد، فرم نمایش داده می‌شود
    if action == 'add':
        # استفاده از ServiceCategory به جای Category با فیلتر cat_type
        categories = ServiceCategory.query.all()
        return render_template('admin/service_form.html',
                              title="افزودن خدمت جدید",
                              categories=categories)
    elif action == 'edit' and service_id:
        # استفاده از جدول Service به جای Product با فیلتر product_type
        service = Service.query.filter_by(id=int(service_id)).first_or_404()
        categories = ServiceCategory.query.all()
        return render_template('admin/service_form.html',
                              title="ویرایش خدمت",
                              service=service,
                              categories=categories)
    elif action == 'media' and service_id:
        # استفاده از جدول Service به جای Product با فیلتر product_type
        service = Service.query.filter_by(id=int(service_id)).first_or_404()
        # استفاده از ServiceMedia به جای ProductMedia
        media = ServiceMedia.query.filter_by(service_id=service.id).all()
        
        # تبدیل مسیر photo_url برای استفاده در url_for
        service.formatted_photo_url = get_photo_url(service.photo_url)
        
        # برای هر رسانه، file_id را به عنوان formatted_file_id تنظیم می‌کنیم
        for item in media:
            # اگر local_path وجود دارد و معتبر است، آن را استفاده می‌کنیم
            if hasattr(item, 'local_path') and item.local_path:
                if item.local_path.startswith('static/'):
                    item.formatted_file_id = item.local_path.replace('static/', '', 1)
                else:
                    item.formatted_file_id = item.local_path
            else:
                # در غیر این صورت از file_id استفاده می‌کنیم
                item.formatted_file_id = item.file_id
        
        return render_template('admin/service_media.html',
                              service=service,
                              media=media)
    
    # نمایش لیست خدمات
    page = request.args.get('page', 1, type=int)
    
    # استفاده از جدول Service به جای Product
    pagination = Service.query.paginate(
        page=page, per_page=10, error_out=False)
    
    # دریافت دسته‌بندی‌های خدمات
    categories = ServiceCategory.query.all()
    
    # تبدیل مسیر photo_url برای استفاده در url_for
    for service in pagination.items:
        service.formatted_photo_url = get_photo_url(service.photo_url)
    
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
            # محصول از جدول Product
            product = Product.query.get(inquiry.product_id)
        elif inquiry.service_id:
            # خدمت از جدول Service
            product = Service.query.get(inquiry.service_id)
        
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
        # نوشتن هدر
        writer.writerow([
            'شناسه', 'تاریخ', 'نام', 'تلفن', 'توضیحات', 'وضعیت', 'شناسه محصول/خدمت'
        ])
        
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
                inquiry.product_id if inquiry.product_id else inquiry.service_id
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
        # دریافت لیست دسته‌بندی‌های آموزشی که فرزند ندارند
        try:
            # بررسی وجود جدول educational_categories
            educational_cats = []
            try:
                # دریافت دسته‌بندی‌هایی که فرزند ندارند
                query = """
                    SELECT id, name 
                    FROM educational_categories ec 
                    WHERE NOT EXISTS (
                        SELECT 1 FROM educational_categories 
                        WHERE parent_id = ec.id
                    )
                """
                educational_cats = db.session.execute(text(query)).fetchall()
                educational_cats = [cat[1] for cat in educational_cats]  # فقط نام دسته‌بندی‌ها
                logger.info(f"دسته‌بندی‌های آموزشی بدون فرزند: {educational_cats}")
            except Exception as e:
                logger.error(f"خطا در دریافت دسته‌بندی‌های آموزشی: {str(e)}")
                
            # اگر از جدول دسته‌بندی‌ها نتوانستیم اطلاعات بگیریم، از دسته‌بندی‌های استفاده شده قبلی استفاده می‌کنیم
            if not educational_cats:
                categories = db.session.query(EducationalContent.category).distinct().all()
                categories = [cat[0] for cat in categories if cat[0]] 
            else:
                categories = educational_cats
        except Exception as e:
            logger.error(f"خطا در دریافت دسته‌بندی‌ها: {str(e)}")
            categories = []
            
        return render_template('admin/education_form.html',
                              title="افزودن محتوای آموزشی جدید",
                              categories=categories,
                              active_page='admin')
    
    elif action == 'edit' and content_id:
        # دریافت محتوا برای ویرایش
        content = EducationalContent.query.get_or_404(int(content_id))
        
        # تبدیل محتوای media به لیست
        media_list = content.media.all()
        
        # افزودن redirect_url برای هر media
        for media in media_list:
            # برای استفاده در تمپلیت
            if hasattr(media, 'file_id') and media.file_id:
                media.redirect_url = url_for('telegram_file', file_id=media.file_id)
            else:
                # اگر file_id نداشت، یک مسیر پیش‌فرض تنظیم می‌کنیم
                media.redirect_url = url_for('static', filename='images/no-image.png')
        
        # دریافت لیست دسته‌بندی‌های موجود
        categories = db.session.query(EducationalContent.category).distinct().all()
        categories = [cat[0] for cat in categories if cat[0]]
        
        return render_template('admin/education_form.html',
                              title="ویرایش محتوای آموزشی",
                              content=content,
                              media_list=media_list,
                              categories=categories,
                              active_page='admin')
    
    elif action == 'save' and request.method == 'POST':
        # ذخیره محتوای جدید یا ویرایش شده
        content_id = request.form.get('id')
        title = request.form.get('title')
        category = request.form.get('category')
        content_text = request.form.get('content')
        
        # اگر دسته‌بندی جدید انتخاب شده، از فیلد new_category استفاده می‌کنیم
        if category == 'new_category':
            category = request.form.get('new_category')
        
        # بررسی آپلود فایل‌ها
        uploaded_files = request.files.getlist('file')
        logger.info(f"تعداد فایل‌های آپلود شده: {len(uploaded_files)}")
        
        file_paths = []
        
        # پردازش تمام فایل‌های آپلود شده
        for uploaded_file in uploaded_files:
            if uploaded_file and uploaded_file.filename and allowed_file(uploaded_file.filename):
                # ذخیره فایل
                success, file_path = save_uploaded_file(uploaded_file, 'educational')
                if success and file_path:
                    file_paths.append(file_path)
                
                logger.info(f"فایل ذخیره شد: {file_path}")
        
        try:
            if content_id:
                # ویرایش محتوای موجود
                content = EducationalContent.query.get(int(content_id))
                if content:
                    content.title = title
                    content.category = category
                    content.content = content_text
                    
                    # همه فایل‌ها را به EducationalContentMedia اضافه می‌کنیم
                    if file_paths:
                        for idx, current_file_path in enumerate(file_paths):
                            timestamp = int(time.time()) + idx  # زمان + ایندکس برای جلوگیری از تکرار
                            
                            # تشخیص نوع فایل براساس پسوند
                            file_type = 'photo'  # پیش‌فرض
                            media_file_id = f"educational_content_image_{content.id}_{timestamp}"
                            
                            if current_file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                                file_type = 'video'
                                media_file_id = f"educational_content_video_{content.id}_{timestamp}"
                            elif not current_file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                file_type = 'file'
                                media_file_id = f"educational_content_file_{content.id}_{timestamp}"
                                
                            # ساخت رکورد جدید فایل
                            media = EducationalContentMedia(
                                educational_content_id=content.id,
                                file_id=media_file_id,
                                file_type=file_type
                            )
                            
                            media.local_path = current_file_path
                            logger.info(f"local_path تنظیم شد: {current_file_path}")
                            
                            db.session.add(media)
                            logger.info(f"فایل رسانه اضافه شد: {media_file_id} - {current_file_path}")
                    db.session.commit()
                    flash('محتوای آموزشی با موفقیت به‌روزرسانی شد.', 'success')
            else:
                # افزودن محتوای جدید
                content = EducationalContent()
                content.title = title
                content.category = category
                content.content = content_text
                content.type = 'text'  # تنظیم مقدار پیش‌فرض برای فیلد type
                content.content_type = 'text'  # تنظیم content_type هم برای اطمینان
                
                db.session.add(content)
                db.session.commit()
                
                # ذخیره فایل های آپلود شده برای محتوای جدید
                if file_paths:
                    for idx, current_file_path in enumerate(file_paths):
                        timestamp = int(time.time()) + idx
                        
                        # تشخیص نوع فایل براساس پسوند
                        file_type = 'photo'  # پیش‌فرض
                        media_file_id = f"educational_content_image_{content.id}_{timestamp}"
                        
                        if current_file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                            file_type = 'video'
                            media_file_id = f"educational_content_video_{content.id}_{timestamp}"
                        elif not current_file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            file_type = 'file'
                            media_file_id = f"educational_content_file_{content.id}_{timestamp}"
                            
                        # ساخت رکورد جدید فایل
                        media = EducationalContentMedia(
                            educational_content_id=content.id,
                            file_id=media_file_id,
                            file_type=file_type
                        )
                        
                        media.local_path = current_file_path
                        logger.info(f"local_path تنظیم شد: {current_file_path}")
                        
                        db.session.add(media)
                        logger.info(f"فایل رسانه اضافه شد: {media_file_id} - {current_file_path}")
                    
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
        cat_type = request.args.get('type', 'product')
        parent_id = request.args.get('parent_id', type=int)
        
        # انتخاب مدل مناسب بر اساس نوع دسته‌بندی
        if cat_type == 'product':
            model = ProductCategory
        elif cat_type == 'service':
            model = ServiceCategory
        elif cat_type == 'educational':
            model = EducationalCategory
        else:
            return jsonify({"error": "نوع دسته‌بندی نامعتبر است"}), 400
        
        # فیلتر بر اساس پارامترهای ورودی
        query = model.query
        
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
                'type': cat_type,  # نوع دسته‌بندی را از پارامتر ورودی می‌گیریم
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
        query = Service.query
        
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

@app.route('/api/telegram_file/<path:file_id>')
def telegram_file(file_id):
    """سرو فایل‌های آپلود شده از تلگرام یا فایل‌های محلی"""
    import os  # ماژول os را اینجا import می‌کنیم تا در این تابع قابل دسترسی باشد
    
    try:
        logger.info(f"Requested file_id: {file_id}")
        
        # راه حل اول: استفاده از مسیر کامل برای سرو فایل
        
        # بررسی اگر file_id یک مسیر محلی است
        if '/' in file_id and file_id.startswith('uploads/'):
            # مسیر کامل فایل را می‌سازیم
            file_path = os.path.join('static', file_id)
            logger.info(f"Path looks like a local file path, full path: {file_path}")
            
            # بررسی وجود فایل
            if os.path.exists(file_path):
                logger.info(f"File exists at: {file_path}")
                # مستقیماً از مسیر url_for استفاده می‌کنیم
                return redirect(url_for('static', filename=file_id))
            else:
                logger.warning(f"File does NOT exist at: {file_path}")
        
        # جستجوی فایل در جدول ProductMedia, ServiceMedia و EducationalContentMedia
        try:
            # ابتدا در جدول ProductMedia جستجو می‌کنیم
            media = ProductMedia.query.filter_by(file_id=file_id).first()
            logger.info(f"Direct ProductMedia lookup result: {media}")
            
            media_source = 'product'
        
            # اگر در ProductMedia پیدا نشد، در ServiceMedia جستجو می‌کنیم
            if not media:
                media = ServiceMedia.query.filter_by(file_id=file_id).first()
                logger.info(f"ServiceMedia lookup result: {media}")
                media_source = 'service'
                
            # اگر در ServiceMedia هم پیدا نشد، در EducationalContentMedia جستجو می‌کنیم
            if not media:
                media = EducationalContentMedia.query.filter_by(file_id=file_id).first()
                logger.info(f"EducationalContentMedia lookup result: {media}")
                media_source = 'educational'
            
            # اگر هنوز پیدا نشد، در همه جدول‌ها با جستجوی وسیع‌تر تلاش می‌کنیم
            if not media:
                # جستجو در جدول ProductMedia با الگوی وسیع‌تر
                logger.info("Trying broader search...")
                media = ProductMedia.query.filter(
                    ProductMedia.file_id.like(f"%{file_id}%")
                ).first()
                if media:
                    media_source = 'product'
                
                # اگر در ProductMedia پیدا نشد، در ServiceMedia با الگوی وسیع‌تر جستجو می‌کنیم
                if not media:
                    media = ServiceMedia.query.filter(
                        ServiceMedia.file_id.like(f"%{file_id}%")
                    ).first()
                    if media:
                        media_source = 'service'
                        
                # اگر در ServiceMedia هم پیدا نشد، در EducationalContentMedia با الگوی وسیع‌تر جستجو می‌کنیم
                if not media:
                    media = EducationalContentMedia.query.filter(
                        EducationalContentMedia.file_id.like(f"%{file_id}%")
                    ).first()
                    if media:
                        media_source = 'educational'
                
                logger.info(f"Broader search result: {media} (source: {media_source})")
                
            # اگر رکورد مدیا پیدا شد و local_path دارد، مستقیماً فایل را سرو می‌کنیم
            if media and hasattr(media, 'local_path') and media.local_path:
                if os.path.exists(os.path.join('static', media.local_path)):
                    logger.info(f"Serving media from local_path: {media.local_path}")
                    return redirect(url_for('static', filename=media.local_path))
                else:
                    logger.warning(f"Media has local_path but file doesn't exist: {media.local_path}")
        except Exception as e:
            logger.error(f"Database error when searching for file_id '{file_id}': {str(e)}")
            return jsonify({'error': f"Database error: {str(e)}"}), 500
            
        if not media:
            logger.warning(f"No media record found for file_id: {file_id}")
            
            # بررسی فایل در مسیر media
            # برای محصولات
            if file_id.startswith('product_image_'):
                product_media_path = os.path.join('static', 'media', 'products', f"{file_id}.jpg")
                if os.path.exists(product_media_path):
                    logger.info(f"Found product media file: {product_media_path}")
                    return redirect(url_for('static', filename=f"media/products/{file_id}.jpg"))
            
            # برای خدمات
            elif file_id.startswith('service_image_'):
                service_media_path = os.path.join('static', 'media', 'services', f"{file_id}.jpg")
                if os.path.exists(service_media_path):
                    logger.info(f"Found service media file: {service_media_path}")
                    return redirect(url_for('static', filename=f"media/services/{file_id}.jpg"))
                    
            # برای محتوای آموزشی - تمام حالت‌های ممکن
            elif file_id.startswith('educational_'):
                # بررسی اینکه media record تنظیم شده یا خیر
                if media:
                    logger.info(f"Media record type: EducationalContentMedia")
                    attr_names = [attr for attr in dir(media) if not attr.startswith('_') and not callable(getattr(media, attr))]
                    logger.info(f"Media record details: {{'id': {media.id}, 'file_id': '{media.file_id}', 'attr_names': {attr_names}}}")
                    logger.info(f"This is an EducationalContentMedia record")
                
                # حالت video یا فایل را بررسی می‌کنیم
                if 'video' in file_id:
                    # بررسی با پسوند mp4
                    edu_media_path = os.path.join('static', 'media', 'educational', f"{file_id}.mp4")
                    if os.path.exists(edu_media_path):
                        logger.info(f"Found educational content video file: {edu_media_path}")
                        return redirect(url_for('static', filename=f"media/educational/{file_id}.mp4"))
                elif file_id.startswith('educational_content_image_'):
                    # فرمت استاندارد برای تصاویر محتوای آموزشی
                    logger.info(f"Using standard educational media path: media/educational/{file_id}.jpg")
                    edu_media_path = os.path.join('static', 'media', 'educational', f"{file_id}.jpg")
                    if os.path.exists(edu_media_path):
                        logger.info(f"Found educational content image file: {edu_media_path}")
                        return redirect(url_for('static', filename=f"media/educational/{file_id}.jpg"))
                elif file_id.startswith('educational_image_'):
                    # فرمت قدیمی برای تصاویر محتوای آموزشی
                    logger.warning(f"Unusual educational media file_id format: {file_id}")
                    
                    # در دو مسیر مختلف بررسی می‌کنیم
                    # 1. مسیر استاندارد با پسوند jpg
                    edu_media_path = os.path.join('static', 'media', 'educational', f"{file_id}.jpg")
                    if os.path.exists(edu_media_path):
                        logger.info(f"Found educational image file: {edu_media_path}")
                        return redirect(url_for('static', filename=f"media/educational/{file_id}.jpg"))
                    
                    # 2. محتوای فایل را از رکورد دیتابیس بررسی می‌کنیم
                    if media and hasattr(media, 'content'):
                        content_path = media.content
                        if content_path and os.path.exists(os.path.join('static', content_path)):
                            logger.info(f"Using content path from database: {content_path}")
                            return redirect(url_for('static', filename=content_path))
                    
                    # 3. پسوندهای دیگر را بررسی می‌کنیم
                    for ext in ['.png', '.gif', '.jpeg']:
                        alt_path = os.path.join('static', 'media', 'educational', f"{file_id}{ext}")
                        if os.path.exists(alt_path):
                            rel_path = f"media/educational/{file_id}{ext}"
                            logger.info(f"Found educational image with different extension: {alt_path}")
                            return redirect(url_for('static', filename=rel_path))
                else:
                    # سایر فرمت‌های محتوای آموزشی
                    logger.warning(f"Unknown educational content file_id format: {file_id}")
                    for ext in ['.jpg', '.png', '.mp4', '.pdf']:
                        potential_path = os.path.join('static', 'media', 'educational', f"{file_id}{ext}")
                        if os.path.exists(potential_path):
                            logger.info(f"Found educational file: {potential_path}")
                            return redirect(url_for('static', filename=f"media/educational/{file_id}{ext}"))
                    
                    # جستجوی گسترده‌تر در کل دایرکتوری رسانه‌ها
                    media_dir = os.path.join('static', 'media', 'educational')
                    if os.path.exists(media_dir):
                        # تلاش برای یافتن فایلی که با file_id شروع می‌شود
                        file_matches = []
                        for filename in os.listdir(media_dir):
                            if filename.startswith(file_id):
                                file_matches.append(filename)
                                
                        if file_matches:
                            # اولین فایل یافت شده را استفاده می‌کنیم
                            match_file = file_matches[0]
                            logger.info(f"Found matching file in educational media dir: {match_file}")
                            return redirect(url_for('static', filename=f"media/educational/{match_file}"))
            
            # تلاش نهایی - بررسی اینکه آیا این یک مسیر فایل است
            potential_path = os.path.join('static', file_id)
            if os.path.exists(potential_path):
                logger.info(f"Found file as a direct path: {potential_path}")
                return redirect(url_for('static', filename=file_id))
            
            # اگر فایل آموزشی است، فایل موقت ایجاد می‌کنیم
            if file_id.startswith('educational_'):
                # ایجاد دایرکتوری media/educational اگر وجود ندارد
                edu_media_dir = os.path.join('static', 'media', 'educational')
                os.makedirs(edu_media_dir, exist_ok=True)
                
                # نام فایل را با پسوند مناسب می‌سازیم
                file_ext = '.jpg'  # پیش‌فرض
                if 'video' in file_id:
                    file_ext = '.mp4'
                
                # مسیر کامل فایل
                file_path = os.path.join(edu_media_dir, f"{file_id}{file_ext}")
                
                # اگر فایل وجود ندارد، از تصویر پیش‌فرض کپی می‌کنیم
                if not os.path.exists(file_path):
                    from PIL import Image, ImageDraw, ImageFont
                    import os
                    
                    # تصویر خالی ایجاد می‌کنیم
                    img = Image.new('RGB', (800, 600), color=(240, 240, 240))
                    d = ImageDraw.Draw(img)
                    
                    # نوشتن متن روی تصویر
                    # سعی می‌کنیم فونت مناسب پیدا کنیم
                    font_size = 40
                    try:
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except IOError:
                        try:
                            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
                        except IOError:
                            font = ImageFont.load_default()
                    
                    # متن را در مرکز تصویر قرار می‌دهیم
                    text = f"تصویر {file_id}"
                    text_width, text_height = d.textsize(text, font=font) if hasattr(d, 'textsize') else (400, 40)
                    position = ((800-text_width)//2, (600-text_height)//2)
                    
                    # متن را به تصویر اضافه می‌کنیم
                    d.text(position, text, fill=(100, 100, 100), font=font)
                    
                    # ذخیره تصویر
                    img.save(file_path)
                    logger.info(f"Created placeholder image at {file_path}")
                
                # بازگرداندن مسیر نسبی فایل به کلاینت
                rel_path = os.path.join('media', 'educational', f"{file_id}{file_ext}")
                return redirect(url_for('static', filename=rel_path))
            
            # اگر هیچ چیزی پیدا نشد، تصویر پیش‌فرض را نمایش می‌دهیم
            logger.warning(f"Could not find any file for {file_id}, using default image")
            
            # ایجاد دایرکتوری static/images اگر وجود ندارد
            default_img_dir = os.path.join('static', 'images')
            os.makedirs(default_img_dir, exist_ok=True)
            
            # کپی کردن تصویر پیش‌فرض از attached_assets به static/images اگر وجود ندارد
            default_img_path = os.path.join(default_img_dir, 'no-image.png')
            if not os.path.exists(default_img_path):
                fallback_img = os.path.join('attached_assets', 'show.jpg')
                if os.path.exists(fallback_img):
                    import shutil
                    shutil.copy(fallback_img, default_img_path)
                    logger.info(f"Created default image at {default_img_path}")
                else:
                    # اگر فایل show.jpg هم وجود ندارد، تصویر جدید می‌سازیم
                    from PIL import Image, ImageDraw, ImageFont
                    
                    # تصویر خالی ایجاد می‌کنیم
                    img = Image.new('RGB', (800, 600), color=(240, 240, 240))
                    d = ImageDraw.Draw(img)
                    
                    # متن "تصویر پیش‌فرض" را روی آن می‌نویسیم
                    try:
                        font = ImageFont.truetype("arial.ttf", 40)
                    except IOError:
                        try:
                            font = ImageFont.truetype("DejaVuSans.ttf", 40)
                        except IOError:
                            font = ImageFont.load_default()
                    
                    d.text((250, 250), "تصویر پیش‌فرض", fill=(100, 100, 100), font=font)
                    
                    # ذخیره تصویر
                    img.save(default_img_path)
                    logger.info(f"Created new default image at {default_img_path}")
            
            # اگر تصویر پیش‌فرض وجود دارد، آن را نمایش می‌دهیم
            if os.path.exists(default_img_path):
                return redirect(url_for('static', filename='images/no-image.png'))
            else:
                return jsonify({'error': 'فایل پیدا نشد'}), 404
        
        try:
            # بررسی نوع آبجکت media برای کمک به عیب‌یابی
            logger.info(f"Media record type: {type(media).__name__}")
            
            # نمایش همه اطلاعات موجود در آبجکت media
            media_info = {
                'id': media.id, 
                'file_id': media.file_id,
                'attr_names': [attr for attr in dir(media) if not attr.startswith('_')]
            }
            
            # بررسی اگر local_path یکی از ویژگی‌های مدل است
            try:
                media_info['local_path'] = media.local_path
                logger.info(f"local_path found: {media.local_path}")
            except Exception as e:
                logger.warning(f"Could not access local_path: {e}")
            
            logger.info(f"Media record details: {media_info}")
            
            # بررسی نوع فایل و اقدام متناسب
            if isinstance(media, ServiceMedia):
                # برای فایل‌های خدمات
                logger.info("This is a ServiceMedia record")
                
                # ساخت مسیر استاندارد برای فایل‌های خدمات
                if media.file_id.startswith('service_image_'):
                    service_path = f"media/services/{media.file_id}.jpg"
                    logger.info(f"Using standard service media path: {service_path}")
                    return redirect(url_for('static', filename=service_path))
                elif '/' in media.file_id and (media.file_id.startswith('uploads/') or media.file_id.startswith('services/')):
                    # اگر file_id خودش مسیر فایل است
                    logger.info(f"Service media file_id is a path itself: {media.file_id}")
                    return redirect(url_for('static', filename=media.file_id))
                else:
                    # اگر file_id شکل غیرمعمول دارد
                    logger.warning(f"Unusual service media file_id format: {media.file_id}")
                    # سعی می‌کنیم با فرض یک مسیر استاندارد فایل را پیدا کنیم
                    return redirect(url_for('static', filename=f"media/services/{media.file_id}.jpg"))
                    
            elif isinstance(media, ProductMedia):
                # برای فایل‌های محصولات
                logger.info("This is a ProductMedia record")
                
                # اگر ProductMedia دارای local_path است، از آن استفاده می‌کنیم
                if hasattr(media, 'local_path') and media.local_path:
                    media_path = media.local_path
                    logger.info(f"Using ProductMedia local_path: {media_path}")
                    
                    # اگر local_path با static شروع می‌شود
                    if media_path.startswith('static/'):
                        relative_path = media_path.replace('static/', '', 1)
                        logger.info(f"Serving product media with static route: {relative_path}")
                        return redirect(url_for('static', filename=relative_path))
                else:
                    # اگر local_path وجود ندارد، از file_id استفاده می‌کنیم
                    # بررسی اگر این فایل محصول در مسیر media/products وجود دارد
                    product_path = f"media/products/{media.file_id}.jpg"
                    logger.info(f"ProductMedia without local_path, trying standard path: {product_path}")
                    return redirect(url_for('static', filename=product_path))
                    
            elif isinstance(media, EducationalContentMedia):
                # برای فایل‌های محتوای آموزشی
                logger.info("This is an EducationalContentMedia record")
                
                # چک کردن برای local_path
                try:
                    # اگر فایل محلی وجود دارد، از آن استفاده می‌کنیم
                    if hasattr(media, 'local_path') and media.local_path and media.local_path.strip():
                        logger.info(f"Using EducationalContentMedia local_path: {media.local_path}")
                        
                        # اگر local_path با static/ شروع می‌شود
                        if media.local_path.startswith('static/'):
                            relative_path = media.local_path.replace('static/', '', 1)
                            logger.info(f"Serving educational media with static route: {relative_path}")
                            return redirect(url_for('static', filename=relative_path))
                        
                        # اگر قبلاً ذخیره شده و full path نیست
                        full_path = f"media/educational/{media.local_path}" if not media.local_path.startswith("media/") else media.local_path
                        logger.info(f"Serving educational media with full path: {full_path}")
                        if os.path.exists(os.path.join('static', full_path)):
                            return redirect(url_for('static', filename=full_path))
                        elif os.path.exists(os.path.join('static', media.local_path)):
                            return redirect(url_for('static', filename=media.local_path))
                except Exception as e:
                    logger.warning(f"Error accessing local_path: {e}")
                
                # چک کردن با ساختارهای مسیر مختلف
                
                # ساخت مسیر استاندارد برای فایل‌های محتوای آموزشی
                if media.file_id.startswith('educational_content_image_'):
                    # مسیر استاندارد برای عکس‌های محتوای آموزشی - اولویت اول
                    standard_path = f"media/educational/{media.file_id}.jpg"
                    logger.info(f"Checking standard educational media path: {standard_path}")
                    
                    if os.path.exists(os.path.join('static', standard_path)):
                        logger.info(f"Found file at standard path: {standard_path}")
                        return redirect(url_for('static', filename=standard_path))
                    
                    # چک کردن مسیرهای جایگزین
                    alt_path = f"educational/{media.file_id.replace('educational_content_image_', '')}.jpg"
                    if os.path.exists(os.path.join('static', alt_path)):
                        logger.info(f"Found file at alternative path: {alt_path}")
                        return redirect(url_for('static', filename=alt_path))
                        
                    # چک کردن فایل در مسیر uploads
                    uploads_path = f"uploads/{media.file_id.replace('educational_content_image_', '')}.jpg"
                    if os.path.exists(os.path.join('static', uploads_path)):
                        logger.info(f"Found file at uploads path: {uploads_path}")
                        return redirect(url_for('static', filename=uploads_path))
                    
                    # چک کردن مسیر آپلود عمومی
                    upload_dir = "static/uploads"
                    if os.path.isdir(upload_dir):
                        for file in os.listdir(upload_dir):
                            if file.startswith(media.file_id) or media.file_id in file:
                                logger.info(f"Found matching file in uploads: {file}")
                                return redirect(url_for('static', filename=f"uploads/{file}"))
                                
                    # اگر هنوز فایل پیدا نشده، از مسیر استاندارد استفاده می‌کنیم
                    logger.info(f"Using standard path as fallback: {standard_path}")
                    return redirect(url_for('static', filename=standard_path))
                
                elif media.file_id.startswith('educational_content_video_'):
                    # مسیر استاندارد برای ویدیوهای محتوای آموزشی
                    education_path = f"media/educational/{media.file_id}.mp4"
                    
                    # ابتدا چک کنیم آیا فایل موجود است
                    if os.path.exists(os.path.join('static', education_path)):
                        logger.info(f"Found video at path: {education_path}")
                        return redirect(url_for('static', filename=education_path))
                    
                    # چک کردن مسیرهای جایگزین
                    alt_paths = [
                        f"uploads/{media.file_id}.mp4",
                        f"uploads/{media.file_id.replace('educational_content_video_', '')}.mp4",
                        f"media/videos/{media.file_id}.mp4"
                    ]
                    
                    for path in alt_paths:
                        if os.path.exists(os.path.join('static', path)):
                            logger.info(f"Found video at alternative path: {path}")
                            return redirect(url_for('static', filename=path))
                    
                    logger.info(f"Using standard educational video path as fallback: {education_path}")
                    return redirect(url_for('static', filename=education_path))
                
                elif '/' in media.file_id and (media.file_id.startswith('uploads/') or media.file_id.startswith('educational/')):
                    # اگر file_id خودش مسیر فایل است
                    logger.info(f"Educational media file_id is a path itself: {media.file_id}")
                    return redirect(url_for('static', filename=media.file_id))
                
                else:
                    # اگر file_id شکل غیرمعمول دارد
                    logger.warning(f"Unusual educational media file_id format: {media.file_id}")
                    
                    # سعی می‌کنیم فایل را بر اساس نوع آن پیدا کنیم
                    if media.file_type == 'video':
                        return redirect(url_for('static', filename=f"media/educational/{media.file_id}.mp4"))
                    else:
                        # برای فایل‌های تصویری، چندین مسیر احتمالی را بررسی می‌کنیم
                        paths_to_check = [
                            f"media/educational/{media.file_id}.jpg",
                            f"educational/{media.file_id}.jpg",
                            f"uploads/{media.file_id}.jpg",
                            f"media/{media.file_id}.jpg"
                        ]
                        
                        for path in paths_to_check:
                            if os.path.exists(os.path.join('static', path)):
                                logger.info(f"Found image at path: {path}")
                                return redirect(url_for('static', filename=path))
                        
                        # اگر هیچ فایلی پیدا نشد، از مسیر اصلی استفاده می‌کنیم
                        return redirect(url_for('static', filename=f"media/educational/{media.file_id}.jpg"))
                        
            else:
                # برای انواع دیگر فایل‌ها (احتمالاً غیرممکن)
                logger.warning(f"Unknown media type: {type(media).__name__}")
            
            # اگر file_id خودش یک مسیر فایل است، آن را سرو می‌کنیم
            if '/' in media.file_id and os.path.exists(os.path.join('static', media.file_id)):
                logger.info(f"Serving media file_id with static route: {media.file_id}")
                return redirect(url_for('static', filename=media.file_id))
            
            # نهایتاً اگر همه روش‌ها شکست خورد، تصویر پیش‌فرض را نمایش می‌دهیم
            logger.warning(f"Could not find a valid path for file_id: {file_id}, using default image")
            
            # ایجاد دایرکتوری static/images اگر وجود ندارد
            default_img_dir = os.path.join('static', 'images')
            os.makedirs(default_img_dir, exist_ok=True)
            
            # کپی کردن تصویر پیش‌فرض از attached_assets به static/images اگر وجود ندارد
            default_img_path = os.path.join(default_img_dir, 'no-image.png')
            if not os.path.exists(default_img_path):
                fallback_img = os.path.join('attached_assets', 'show.jpg')
                if os.path.exists(fallback_img):
                    import shutil
                    shutil.copy(fallback_img, default_img_path)
                    logger.info(f"Created default image at {default_img_path}")
            
            # اگر تصویر پیش‌فرض وجود دارد، آن را نمایش می‌دهیم
            if os.path.exists(default_img_path):
                return redirect(url_for('static', filename='images/no-image.png'))
            else:
                return jsonify({'error': 'فایل در سرور وجود ندارد'}), 404
        except Exception as e:
            logger.error(f"Error processing media record {media.id}: {str(e)}")
            return jsonify({'error': f"Error processing media: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unhandled exception in telegram_file: {str(e)}")
        
        # در صورت خطا، تلاش برای نمایش تصویر پیش‌فرض
        try:
            # ایجاد دایرکتوری static/images اگر وجود ندارد
            default_img_dir = os.path.join('static', 'images')
            os.makedirs(default_img_dir, exist_ok=True)
            
            # کپی کردن تصویر پیش‌فرض از attached_assets به static/images اگر وجود ندارد
            default_img_path = os.path.join(default_img_dir, 'no-image.png')
            if not os.path.exists(default_img_path):
                fallback_img = os.path.join('attached_assets', 'show.jpg')
                if os.path.exists(fallback_img):
                    import shutil
                    shutil.copy(fallback_img, default_img_path)
                    logger.info(f"Created default image at {default_img_path} (error fallback)")
            
            # اگر تصویر پیش‌فرض وجود دارد، آن را نمایش می‌دهیم
            if os.path.exists(default_img_path):
                return redirect(url_for('static', filename='images/no-image.png'))
            else:
                return jsonify({'error': str(e)}), 500
                
        except Exception as e2:
            logger.error(f"Error in fallback image logic: {str(e2)}")
            return jsonify({'error': str(e)}), 500

# ----- Database Management Routes -----
@app.route('/admin/database')
@login_required
def admin_database():
    """صفحه مدیریت پایگاه داده"""
    try:
        # دریافت اطلاعات کلی جداول
        tables = {
            'users': db.session.query(User).count(),
            'products': db.session.query(Product).count(),
            'services': db.session.query(Service).count(),
            'product_media': db.session.query(ProductMedia).count(),
            'service_media': db.session.query(ServiceMedia).count(),
            'product_categories': db.session.query(ProductCategory).count(),
            'service_categories': db.session.query(ServiceCategory).count(),
            'inquiries': db.session.query(Inquiry).count(),
            'educational_content': db.session.query(EducationalContent).count(),
            'educational_categories': db.session.query(EducationalCategory).count(),
            'educational_content_media': db.session.query(EducationalContentMedia).count(),
            'static_content': db.session.query(StaticContent).count(),
        }
        
        return render_template('admin/database.html', tables=tables)
    except Exception as e:
        logger.error(f"Error in admin_database: {e}")
        return render_template('error.html', error=str(e))

@app.route('/admin/database/view/<table>')
@login_required
def admin_view_table(table):
    """نمایش محتوای یک جدول"""
    try:
        model_map = {
            'users': User,
            'products': Product,
            'services': Service,
            'product_media': ProductMedia,
            'service_media': ServiceMedia,
            'product_categories': ProductCategory, 
            'service_categories': ServiceCategory,
            'inquiries': Inquiry,
            'educational_content': EducationalContent,
            'educational_categories': EducationalCategory,
            'educational_content_media': EducationalContentMedia,
            'static_content': StaticContent,
        }
        
        if table not in model_map:
            flash(f'جدول {table} یافت نشد.', 'danger')
            return redirect(url_for('admin_database'))
        
        # دریافت محتوای جدول
        model = model_map[table]
        data = model.query.all()
        
        # دریافت نام ستون‌ها
        columns = [column.name for column in model.__table__.columns]
        
        return render_template('admin/table_view.html', 
                            data=data, 
                            columns=columns, 
                            table_name=table)
    except Exception as e:
        logger.error(f"Error in admin_view_table: {e}")
        return render_template('error.html', error=str(e))

@app.route('/admin/database/fix/<table>', methods=['POST'])
@login_required
def admin_database_fix(table):
    """اصلاح جداول دیتابیس برای اطمینان از صحت اطلاعات"""
    try:
        fixed_count = 0
        
        # بر اساس جدول، عملیات اصلاح مناسب را انجام می‌دهیم
        if table == 'service_media':
            # دریافت همه رکوردهای service_media
            service_media = ServiceMedia.query.all()
            
            for media in service_media:
                # بررسی وجود service_id معتبر
                service = Service.query.get(media.service_id)
                if not service:
                    # حذف رکورد اگر service_id معتبر نیست
                    db.session.delete(media)
                    fixed_count += 1
                    continue
            
            # ذخیره تغییرات
            db.session.commit()
            
            # ایجاد رکوردهای media برای سرویس‌هایی که رسانه ندارند
            services = Service.query.all()
            for service in services:
                count = ServiceMedia.query.filter_by(service_id=service.id).count()
                if count == 0:
                    # ایجاد دو رکورد پیش‌فرض
                    for i in range(1, 3):
                        media = ServiceMedia(
                            service_id=service.id,
                            file_id=f"service_image_{service.id}_{i}",
                            file_type="photo"
                        )
                        db.session.add(media)
                        fixed_count += 1
            
            # ذخیره تغییرات
            db.session.commit()
        
        elif table == 'product_media':
            # دریافت همه رکوردهای product_media
            product_media = ProductMedia.query.all()
            
            for media in product_media:
                # بررسی وجود product_id معتبر
                product = Product.query.get(media.product_id)
                if not product:
                    # حذف رکورد اگر product_id معتبر نیست
                    db.session.delete(media)
                    fixed_count += 1
                    continue
            
            # ذخیره تغییرات
            db.session.commit()
            
            # ایجاد رکوردهای media برای محصولاتی که رسانه ندارند
            products = Product.query.all()
            for product in products:
                count = ProductMedia.query.filter_by(product_id=product.id).count()
                if count == 0:
                    # ایجاد دو رکورد پیش‌فرض
                    for i in range(1, 3):
                        media = ProductMedia(
                            product_id=product.id,
                            file_id=f"product_image_{product.id}_{i}",
                            file_type="photo"
                        )
                        db.session.add(media)
                        fixed_count += 1
            
            # ذخیره تغییرات
            db.session.commit()
        
        elif table == 'services':
            # بررسی و اصلاح خدمات
            services = Service.query.all()
            for service in services:
                modified = False
                
                # اطمینان از وجود دسته‌بندی معتبر
                if service.category_id:
                    category = Category.query.get(service.category_id)
                    if not category:
                        # تنظیم دسته‌بندی پیش‌فرض
                        default_category = Category.query.filter_by(cat_type='service').first()
                        if default_category:
                            service.category_id = default_category.id
                            modified = True
                
                if modified:
                    fixed_count += 1
            
            # ذخیره تغییرات
            db.session.commit()
        
        elif table == 'products':
            # بررسی و اصلاح محصولات
            products = Product.query.all()
            for product in products:
                modified = False
                
                # اطمینان از وجود دسته‌بندی معتبر
                if product.category_id:
                    category = Category.query.get(product.category_id)
                    if not category:
                        # تنظیم دسته‌بندی پیش‌فرض
                        default_category = Category.query.filter_by(cat_type='product').first()
                        if default_category:
                            product.category_id = default_category.id
                            modified = True
                
                if modified:
                    fixed_count += 1
            
            # ذخیره تغییرات
            db.session.commit()
        
        elif table == 'inquiries':
            # بررسی و اصلاح استعلام‌ها
            inquiries = Inquiry.query.all()
            for inquiry in inquiries:
                modified = False
                
                # بررسی product_id و service_id
                if inquiry.product_id:
                    product = Product.query.get(inquiry.product_id)
                    if not product:
                        inquiry.product_id = None
                        modified = True
                
                if inquiry.service_id:
                    service = Service.query.get(inquiry.service_id)
                    if not service:
                        inquiry.service_id = None
                        modified = True
                
                if modified:
                    fixed_count += 1
            
            # ذخیره تغییرات
            db.session.commit()
        
        elif table == 'educational_content':
            # بررسی و اصلاح محتوای آموزشی
            contents = EducationalContent.query.all()
            for content in contents:
                modified = False
                
                # اطمینان از وجود category_id معتبر
                if content.category_id:
                    category = EducationalCategory.query.get(content.category_id)
                    if not category:
                        # تنظیم دسته‌بندی پیش‌فرض یا خالی
                        default_category = EducationalCategory.query.first()
                        if default_category:
                            content.category_id = default_category.id
                        else:
                            content.category_id = None
                        modified = True
                
                # اطمینان از همخوانی فیلد category با category_id
                if content.category_id and content.category:
                    category = EducationalCategory.query.get(content.category_id)
                    if category and category.name != content.category:
                        content.category = category.name
                        modified = True
                
                # حذف کد مربوط به فیلدهای content_type و type، چون دیگر استفاده نمی‌شوند
                
                if modified:
                    fixed_count += 1
            
            # ذخیره تغییرات
            db.session.commit()
            
            # ایجاد رکوردهای media برای محتوای آموزشی که رسانه ندارند
            for content in contents:
                count = EducationalContentMedia.query.filter_by(educational_content_id=content.id).count()
                if count == 0:
                    # ایجاد یک رکورد پیش‌فرض با نوع 'photo'
                    media = EducationalContentMedia(
                        educational_content_id=content.id,
                        file_id=f"educational_content_image_{content.id}_1",
                        file_type='photo',  # استفاده از نوع پیش‌فرض برای همه محتوای آموزشی
                        local_path=None  # Will be set when a real file is uploaded
                    )
                    db.session.add(media)
                    fixed_count += 1
            
            # ذخیره تغییرات
            db.session.commit()
        
        elif table == 'educational_content_media':
            # بررسی و اصلاح رسانه‌های محتوای آموزشی
            media_items = EducationalContentMedia.query.all()
            for media in media_items:
                # بررسی وجود educational_content_id معتبر
                content = EducationalContent.query.get(media.educational_content_id)
                if not content:
                    # حذف رکورد اگر educational_content_id معتبر نیست
                    db.session.delete(media)
                    fixed_count += 1
            
            # ذخیره تغییرات
            db.session.commit()
        
        elif table == 'categories':
            # بررسی و اصلاح دسته‌بندی‌ها
            categories = Category.query.all()
            for category in categories:
                modified = False
                
                # بررسی parent_id
                if category.parent_id:
                    parent = Category.query.get(category.parent_id)
                    if not parent:
                        category.parent_id = None
                        modified = True
                
                # اطمینان از وجود cat_type
                if not category.cat_type:
                    category.cat_type = 'product'  # cat_type پیش‌فرض
                    modified = True
                
                if modified:
                    fixed_count += 1
            
            # ذخیره تغییرات
            db.session.commit()
        
        else:
            # برای سایر جداول، پیام‌رسانی مناسب
            flash(f'اصلاح برای جدول {table} در حال حاضر پشتیبانی نمی‌شود.', 'warning')
            return redirect(url_for('admin_view_table', table=table))
        
        # پیام‌رسانی موفقیت
        if fixed_count > 0:
            flash(f'{fixed_count} رکورد در جدول {table} اصلاح شد.', 'success')
        else:
            flash(f'همه رکوردهای جدول {table} سالم هستند.', 'info')
        
        return redirect(url_for('admin_view_table', table=table))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in admin_database_fix for table {table}: {e}")
        flash(f'خطا در اصلاح جدول {table}: {str(e)}', 'danger')
        return redirect(url_for('admin_database'))

@app.route('/admin/database/service_media_fix', methods=['POST'])
@login_required
def admin_service_media_fix():
    """برای حفظ سازگاری با کد قبلی"""
    return admin_database_fix('service_media')

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
        
        # دریافت دسته‌بندی‌های محصول
        categories = ProductCategory.query.filter_by(parent_id=None).all()
        
        # تبدیل مسیر photo_url برای استفاده در url_for
        for product in products_list:
            product.formatted_photo_url = get_photo_url(product.photo_url)
        
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
        
        # دریافت خدمات از جدول خدمات
        query = Service.query
        if category_id:
            query = query.filter_by(category_id=category_id)
        services_list = query.all()
        
        # دریافت دسته‌بندی‌های خدمات
        categories = ServiceCategory.query.filter_by(parent_id=None).all()
        
        # تبدیل مسیر photo_url برای استفاده در url_for
        for service in services_list:
            service.formatted_photo_url = get_photo_url(service.photo_url)
        
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
        
        # آماده‌سازی لیست‌های media برای هر محتوا
        content_media_map = {}
        for content in contents:
            content_media_map[content.id] = content.media.all()
        
        # دریافت دسته‌بندی‌های منحصر به فرد
        categories = db.session.query(EducationalContent.category).distinct().all()
        categories = [c[0] for c in categories]
        
        return render_template('educational.html', 
                              contents=contents,
                              content_media_map=content_media_map,
                              categories=categories,
                              selected_category=category)
    except Exception as e:
        flash(f'خطا در نمایش صفحه محتوای آموزشی: {str(e)}', 'danger')
        return render_template('educational.html', contents=[], content_media_map={}, categories=[], selected_category=None)

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
        # در مدل جدید، نوع محصول یا خدمت با استفاده از جداول مختلف مشخص می‌شود
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
        
        # در مدل جدید، محصولات و خدمات در جداول مختلف هستند و نیازی به فیلتر product_type نیست
        
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
        categories = ProductCategory.query.all()
        
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

# این route حذف شده و از admin_database استفاده می‌شود

@app.route('/admin/database/table/<table_name>')
@login_required
def view_table_data(table_name):
    """نمایش محتوای جدول"""
    try:
        # مپ کردن نام جدول به کلاس مدل
        model_map = {
            'users': User,
            'product_categories': ProductCategory,
            'service_categories': ServiceCategory,
            'products': Product,
            'services': Service,
            'product_media': ProductMedia,
            'service_media': ServiceMedia,
            'inquiries': Inquiry,
            'educational_content': EducationalContent,
            'educational_media': EducationalContentMedia,
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
        
        return render_template('admin/table_data.html',
                              table_name=table_name,
                              columns=columns,
                              rows=rows,
                              pagination=pagination)
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
        'products': Product.query,
        'services': Service.query,
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
                    category=row.get('category', '')
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
    """تهیه پشتیبان از دیتابیس با استفاده از sqlalchemy"""
    try:
        import os
        import datetime
        import io
        import csv
        import zipfile
        from src.models.models import (
            Product, Service, Inquiry, EducationalContent,
            ProductMedia, ServiceMedia, EducationalContentMedia,
            ProductCategory, ServiceCategory, User, StaticContent
        )
        
        # نام فایل پشتیبان با تاریخ و زمان
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"database_backup_{timestamp}.zip"
        
        # مدل‌های دیتابیس برای پشتیبان‌گیری
        models_map = {
            'products.csv': Product,
            'services.csv': Service,
            'inquiries.csv': Inquiry,
            'educational.csv': EducationalContent,
            'product_media.csv': ProductMedia,
            'service_media.csv': ServiceMedia,
            'educational_media.csv': EducationalContentMedia,
            'product_categories.csv': ProductCategory,
            'service_categories.csv': ServiceCategory,
            'users.csv': User,
            'static_content.csv': StaticContent,
        }
        
        # ایجاد یک فایل ZIP در حافظه
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # پیمایش تمام جداول
            for table_name, model in models_map.items():
                try:
                    # دریافت داده‌ها از جدول
                    items = db.session.query(model).all()
                    
                    # اگر هیچ داده‌ای وجود نداشت، رد کردن این جدول
                    if not items:
                        continue
                    
                    # دریافت نام ستون‌ها
                    columns = [column.name for column in model.__table__.columns]
                    
                    # ایجاد فایل CSV در حافظه
                    csv_output = io.StringIO()
                    writer = csv.writer(csv_output)
                    
                    # نوشتن هدر
                    writer.writerow(columns)
                    
                    # نوشتن داده‌ها
                    for item in items:
                        row = []
                        for column in columns:
                            value = getattr(item, column)
                            # تبدیل None به رشته خالی
                            row.append("" if value is None else str(value))
                        writer.writerow(row)
                    
                    # افزودن فایل CSV به فایل ZIP
                    # از خود نام table_name استفاده می‌کنیم که حاوی پسوند CSV است
                    zf.writestr(f"{table_name}", csv_output.getvalue().encode('utf-8'))
                    
                except Exception as e:
                    logger.error(f"Error backing up table {table_name}: {str(e)}")
                    # ادامه با جدول بعدی
                    continue
                    
            # افزودن فایل README
            readme_content = f"""این پشتیبان در تاریخ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ایجاد شده است.
هر فایل CSV شامل داده‌های یک جدول است.
ستون اول در هر فایل CSV نام ستون‌ها را نشان می‌دهد.

فایل‌های پشتیبان به صورت زیر نام‌گذاری شده‌اند:
- products.csv: جدول محصولات
- services.csv: جدول خدمات 
- product_categories.csv: جدول دسته‌بندی محصولات
- service_categories.csv: جدول دسته‌بندی خدمات
- inquiries.csv: جدول استعلام‌ها
- educational.csv: جدول محتوای آموزشی
- product_media.csv: جدول رسانه‌های محصولات
- service_media.csv: جدول رسانه‌های خدمات
- educational_media.csv: جدول رسانه‌های محتوای آموزشی
- users.csv: جدول کاربران
- static_content.csv: جدول محتوای ثابت
"""
            zf.writestr("README.txt", readme_content.encode('utf-8'))
        
        # آماده‌سازی فایل برای دانلود
        memory_file.seek(0)
        
        # ایجاد پاسخ برای دانلود فایل
        from flask import send_file
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=backup_filename
        )
            
    except Exception as e:
        logger.error(f"Error in backup_database: {str(e)}")
        flash(f"خطا در پشتیبان‌گیری از دیتابیس: {str(e)}", 'danger')
        return redirect(url_for('admin_import_export'))
    
@app.route('/admin/restore', methods=['POST'])
@login_required
def restore_database():
    """بازیابی دیتابیس از فایل پشتیبان"""
    try:
        import os
        import tempfile
        import zipfile
        import csv
        import io
        from werkzeug.utils import secure_filename
        from src.models.models import (
            Product, Service, Inquiry, EducationalContent,
            ProductMedia, ServiceMedia, EducationalContentMedia,
            ProductCategory, ServiceCategory, User, StaticContent
        )
        
        # دریافت فایل آپلود شده
        backup_file = request.files.get('backup_file')
        if not backup_file:
            flash('لطفاً یک فایل پشتیبان انتخاب کنید.', 'warning')
            return redirect(url_for('admin_import_export'))
        
        # بررسی پسوند فایل
        filename = backup_file.filename
        if not filename or not filename.endswith('.zip'):
            flash('فایل پشتیبان باید با فرمت ZIP باشد.', 'warning')
            return redirect(url_for('admin_import_export'))
        
        # ذخیره موقت فایل
        safe_filename = secure_filename(filename)
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, safe_filename)
        backup_file.save(temp_path)
        
        # مدل‌های دیتابیس برای بازیابی - با اولویت‌بندی برای رعایت محدودیت‌های کلید خارجی
        models_map = {
            # ابتدا کاربران بازیابی می‌شوند
            'users.csv': User,
            # سپس دسته‌بندی‌ها
            'product_categories.csv': ProductCategory,
            'service_categories.csv': ServiceCategory,
            # سپس محتوای ثابت
            'static_content.csv': StaticContent,
            # سپس جداول اصلی
            'products.csv': Product,
            'services.csv': Service, 
            'educational.csv': EducationalContent,
            'inquiries.csv': Inquiry,
            # در نهایت رسانه‌ها (که به جداول اصلی وابسته هستند)
            'product_media.csv': ProductMedia,
            'service_media.csv': ServiceMedia,
            'educational_media.csv': EducationalContentMedia,
        }
        
        # برای اطمینان از پشتیبانی از نسخه‌های قدیمی، نام‌های بدون پسوند را هم پشتیبانی می‌کنیم
        old_format_map = {
            # ابتدا کاربران بازیابی می‌شوند
            'users': User,
            # سپس دسته‌بندی‌ها
            'product_categories': ProductCategory,
            'service_categories': ServiceCategory,
            # سپس محتوای ثابت
            'static_content': StaticContent,
            # سپس جداول اصلی - با ترتیب مشخص شده
            'services': Service,
            'products': Product,
            'educational': EducationalContent,
            'inquiries': Inquiry,
            # در نهایت رسانه‌ها (که به جداول اصلی وابسته هستند) - با ترتیب مشخص شده
            'service_media': ServiceMedia,
            'product_media': ProductMedia, 
            'educational_media': EducationalContentMedia,
        }
        
        # ترکیب هر دو مپ
        models_map.update(old_format_map)
        
        # آمار بازیابی
        restored_tables = []
        skipped_tables = []
        error_tables = []
        
        try:
            # باز کردن فایل ZIP
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                # لیست فایل‌های موجود در ZIP
                file_list = zip_ref.namelist()
                
                # حذف README.txt از لیست
                if 'README.txt' in file_list:
                    file_list.remove('README.txt')
                
                # لاگ کردن فایل‌های موجود برای اشکال‌زدایی
                logger.info(f"فایل‌های موجود در بک‌آپ: {', '.join(file_list)}")
                logger.info(f"تعریف شده در models_map: {', '.join(models_map.keys())}")
                
                # بازیابی هر جدول به ترتیب تعریف شده در models_map
                # این برای رعایت محدودیت‌های کلید خارجی ضروری است
                for csv_filename in models_map.keys():
                    # بررسی اینکه آیا این فایل در ZIP وجود دارد
                    if csv_filename not in file_list:
                        logger.info(f"فایل {csv_filename} در بک‌آپ موجود نیست")
                        continue
                    
                    # دریافت مدل مربوطه
                    model = models_map[csv_filename]
                    logger.info(f"بازیابی فایل {csv_filename} با مدل {model.__name__}")
                    
                    try:
                        # استخراج فایل CSV
                        csv_content = zip_ref.read(csv_filename).decode('utf-8')
                        csv_file = io.StringIO(csv_content)
                        reader = csv.reader(csv_file)
                        
                        # خواندن نام ستون‌ها (سطر اول)
                        headers = next(reader, None)
                        if not headers:
                            skipped_tables.append(csv_filename)
                            continue
                        
                        # بررسی اینکه آیا کاربر می‌خواهد جداول پاکسازی شوند یا خیر
                        should_clear_tables = request.form.get('clear_tables') == 'on'
                        # تعریف متغیرها برای شمارش
                        restored_rows = 0
                        error_rows = 0
                        
                        # تشخیص نوع جدول برای مدیریت ویژه
                        is_user_table = (model.__name__ == 'User')
                        is_media_table = (model.__name__ in ['ProductMedia', 'ServiceMedia', 'EducationalContentMedia'])
                        
                        # برای جداول media، ما نیاز به اطمینان از صحت کلید خارجی داریم
                        media_foreign_key = None
                        if is_media_table:
                            if model.__name__ == 'ProductMedia':
                                media_foreign_key = 'product_id'
                            elif model.__name__ == 'ServiceMedia':
                                media_foreign_key = 'service_id'
                            elif model.__name__ == 'EducationalContentMedia':
                                media_foreign_key = 'content_id'
                        
                        if should_clear_tables:
                            try:
                                # تعداد رکوردهای موجود را ذخیره می‌کنیم
                                existing_count = db.session.query(model).count()
                                # حذف تمام رکوردهای جدول
                                db.session.query(model).delete()
                                db.session.commit()
                                logger.info(f"جدول {csv_filename} با {existing_count} رکورد پاکسازی شد.")
                            except Exception as clear_error:
                                db.session.rollback()
                                logger.error(f"خطا در پاکسازی جدول {csv_filename}: {str(clear_error)}")
                                skipped_tables.append(f"{csv_filename} (خطای پاکسازی: {str(clear_error)})")
                                continue
                        
                        # اکنون داده‌های جدید را اضافه می‌کنیم
                        for row in reader:
                            # ساخت دیکشنری ستون-مقدار
                            data = {}
                            for i, column in enumerate(headers):
                                if i < len(row):
                                    # تبدیل رشته خالی به None
                                    value = row[i]
                                    if value == "":
                                        value = None
                                    
                                    # پیش‌پردازش مقادیر بولین
                                    if column in ['is_admin', 'in_stock', 'featured', 'available']:
                                        if isinstance(value, str):
                                            if value.lower() in ('true', '1', 'yes', 'y', 'بله'):
                                                value = True
                                            elif value.lower() in ('false', '0', 'no', 'n', 'خیر'):
                                                value = False
                                            else:
                                                value = False
                                                logger.warning(f"مقدار نامعتبر برای فیلد بولین {column}: {value} - مقدار False استفاده می‌شود")
                                                
                                    data[column] = value
                            
                            try:
                                # ایجاد یک دیکشنری از داده‌های پردازش شده برای ساخت مدل
                                processed_data = {}
                                
                                # پردازش تمام فیلدها قبل از ساخت مدل
                                for column, value in data.items():
                                    # تبدیل کلیدها به عدد صحیح
                                    if column == 'id' or column.endswith('_id'):
                                        try:
                                            processed_data[column] = int(value) if value else None
                                        except:
                                            processed_data[column] = None
                                    # تبدیل مقادیر بولین به True/False واقعی
                                    elif column in ['is_admin', 'in_stock', 'featured', 'available']:
                                        if isinstance(value, str):
                                            processed_data[column] = value.lower() in ('true', '1', 'yes', 'y', 'بله')
                                        elif value is None:
                                            processed_data[column] = False
                                        else:
                                            processed_data[column] = bool(value)
                                        
                                        # ثبت اطلاعات بیشتر برای مقادیر بولین حساس
                                        if column == 'is_admin':
                                            logger.info(f"مقدار فیلد is_admin تنظیم شد: {processed_data[column]}")
                                    # سایر فیلدها را بدون تغییر استفاده کن
                                    else:
                                        processed_data[column] = value
                                
                                # بررسی و اصلاح مقادیر برای جداول رسانه
                                if model.__name__ in ['ProductMedia', 'ServiceMedia', 'EducationalContentMedia']:
                                    # اگر file_id خالی است ولی local_path وجود دارد، از local_path استفاده کنیم
                                    if 'file_id' in processed_data and processed_data['file_id'] is None:
                                        if 'local_path' in processed_data and processed_data['local_path']:
                                            logger.info(f"جایگزینی file_id با local_path: {processed_data['local_path']}")
                                            processed_data['file_id'] = processed_data['local_path']
                                        else:
                                            # اگر فایل محلی هم نداریم، یک مقدار پیش‌فرض قرار دهیم
                                            logger.warning(f"تنظیم file_id پیش‌فرض برای رکورد {processed_data.get('id', '?')}")
                                            processed_data['file_id'] = f"default_media_{processed_data.get('id', 'unknown')}"
                                
                                # ساخت آیتم با مقادیر پردازش شده
                                try:
                                    # ساخت مدل با تمام داده‌های پردازش شده در یک مرحله
                                    item = model(**processed_data)
                                except Exception as model_error:
                                    logger.error(f"خطا در ساخت مدل {model.__name__}: {str(model_error)}")
                                    # روش دوم: ساخت مدل خالی و تنظیم ویژگی‌ها به صورت جداگانه
                                    item = model()
                                    for column, value in processed_data.items():
                                        if hasattr(item, column):
                                            try:
                                                setattr(item, column, value)
                                            except Exception as attr_error:
                                                logger.error(f"خطا در تنظیم ویژگی {column} با مقدار {value}: {str(attr_error)}")
                                                # اگر خطا به فیلد بولین مربوط است
                                                if column in ['is_admin', 'in_stock', 'featured', 'available']:
                                                    logger.warning(f"تلاش مجدد برای تنظیم فیلد بولین {column}")
                                                    # تلاش نهایی با تبدیل صریح
                                                    setattr(item, column, bool(value == 'True' or value == 'true' or value == '1' or value is True))
                                
                                # بررسی ویژه برای جداول رسانه و صحت کلید خارجی
                                if is_media_table and media_foreign_key:
                                    # در صورتی که این یک جدول رسانه است، کلید خارجی را بررسی کنیم
                                    foreign_key_value = getattr(item, media_foreign_key, None)
                                    if foreign_key_value:
                                        # بررسی کنیم که آیا مقدار کلید خارجی در جدول مرجع وجود دارد
                                        try:
                                            # تعیین مدل مرجع بر اساس نوع جدول رسانه
                                            if model.__name__ == 'ProductMedia':
                                                ref_model = Product
                                            elif model.__name__ == 'ServiceMedia':
                                                ref_model = Service
                                            elif model.__name__ == 'EducationalContentMedia':
                                                ref_model = EducationalContent
                                            
                                            # بررسی وجود رکورد مرجع
                                            ref_exists = db.session.query(ref_model).filter_by(id=foreign_key_value).first() is not None
                                            
                                            if not ref_exists:
                                                # اگر رکورد مرجع وجود ندارد، این رکورد را پرش می‌کنیم
                                                logger.warning(f"رد شد: {model.__name__}، {media_foreign_key}={foreign_key_value} وجود ندارد")
                                                error_rows += 1
                                                continue
                                        except Exception as fk_err:
                                            logger.warning(f"خطا در بررسی کلید خارجی: {str(fk_err)}")
                                            # به روال عادی ادامه می‌دهیم و اجازه می‌دهیم خود دیتابیس خطا بدهد اگر لازم باشد
                                
                                # افزودن به دیتابیس
                                db.session.add(item)
                                # افزایش شمارنده ردیف‌های بازیابی شده
                                restored_rows += 1
                                # برای امنیت بیشتر، هر 100 آیتم یک بار کامیت می‌کنیم
                                if restored_rows % 100 == 0:
                                    try:
                                        db.session.commit()
                                        logger.info(f"کامیت موفق {restored_rows} آیتم برای {csv_filename}")
                                    except Exception as commit_error:
                                        db.session.rollback()
                                        logger.error(f"خطا در کامیت {csv_filename}: {str(commit_error)}")
                                        # اگر خطای کلید خارجی رخ داد، آیتم را رد می‌کنیم اما ادامه می‌دهیم
                                        if 'ForeignKeyViolation' in str(commit_error) or 'foreign key constraint' in str(commit_error).lower():
                                            logger.warning(f"آیتم رد شد به دلیل خطای کلید خارجی - ادامه روند بازیابی")
                                            error_rows += 1
                                        else:
                                            # برای سایر خطاها، کار را متوقف می‌کنیم
                                            raise
                            except Exception as item_error:
                                logger.error(f"خطا در افزودن آیتم در {csv_filename}: {str(item_error)}")
                                continue
                        
                        # ذخیره نهایی تغییرات
                        try:
                            db.session.commit()
                            logger.info(f"کامیت نهایی موفق برای {csv_filename}: {restored_rows} آیتم")
                            restored_tables.append(csv_filename)
                        except Exception as final_commit_error:
                            db.session.rollback()
                            logger.error(f"خطا در کامیت نهایی {csv_filename}: {str(final_commit_error)}")
                            
                            # اگر خطای کلید خارجی بود، تلاش می‌کنیم تک تک رکوردها را کامیت کنیم
                            if 'ForeignKeyViolation' in str(final_commit_error) or 'foreign key constraint' in str(final_commit_error).lower():
                                logger.warning(f"تلاش برای کامیت تک تک رکوردها برای {csv_filename}")
                                success_count = 0
                                
                                # بازگرداندن CSV به ابتدا
                                csv_file.seek(0)
                                reader = csv.reader(csv_file)
                                headers = next(reader, None)  # دوباره هدرها را می‌خوانیم
                                
                                for row in reader:
                                    try:
                                        # ساخت دیکشنری
                                        data = {}
                                        for i, column in enumerate(headers):
                                            if i < len(row):
                                                value = row[i]
                                                if value == "":
                                                    value = None
                                                data[column] = value
                                        
                                        # پردازش داده‌ها قبل از ساخت آیتم
                                        processed_data = {}
                                        for column, value in data.items():
                                            # تبدیل کلیدها به عدد صحیح
                                            if column == 'id' or column.endswith('_id'):
                                                try:
                                                    processed_data[column] = int(value) if value else None
                                                except:
                                                    processed_data[column] = None
                                            # تبدیل مقادیر بولین به True/False واقعی
                                            elif column in ['is_admin', 'in_stock', 'featured', 'available']:
                                                if isinstance(value, str):
                                                    processed_data[column] = value.lower() in ('true', '1', 'yes', 'y', 'بله')
                                                elif value is None:
                                                    processed_data[column] = False
                                                else:
                                                    processed_data[column] = bool(value)
                                            # سایر فیلدها را بدون تغییر استفاده کن
                                            else:
                                                processed_data[column] = value

                                        # بررسی و اصلاح مقادیر برای جداول رسانه
                                        if model.__name__ in ['ProductMedia', 'ServiceMedia', 'EducationalContentMedia']:
                                            # اگر file_id خالی است ولی local_path وجود دارد، از local_path استفاده کنیم
                                            if 'file_id' in processed_data and processed_data['file_id'] is None:
                                                if 'local_path' in processed_data and processed_data['local_path']:
                                                    logger.info(f"جایگزینی file_id با local_path در تک رکورد: {processed_data['local_path']}")
                                                    processed_data['file_id'] = processed_data['local_path']
                                                else:
                                                    # اگر فایل محلی هم نداریم، یک مقدار پیش‌فرض قرار دهیم
                                                    logger.warning(f"تنظیم file_id پیش‌فرض برای تک رکورد {processed_data.get('id', '?')}")
                                                    processed_data['file_id'] = f"default_media_{processed_data.get('id', 'unknown')}"
                                        
                                        # تلاش برای ساخت آیتم جدید
                                        try:
                                            # روش اول: ساخت مدل با تمام داده‌ها در یک مرحله
                                            item = model(**processed_data)
                                        except Exception as model_error:
                                            # روش دوم: ساخت مدل خالی و تنظیم ویژگی‌ها به صورت جداگانه
                                            logger.warning(f"خطا در ساخت مدل {model.__name__} با پارامترها: {str(model_error)}")
                                            
                                            item = model()
                                            for column, value in processed_data.items():
                                                if hasattr(item, column):
                                                    try:
                                                        setattr(item, column, value)
                                                    except Exception as attr_error:
                                                        if column in ['is_admin', 'in_stock', 'featured', 'available']:
                                                            # تبدیل صریح به بولین
                                                            setattr(item, column, bool(value == True or (isinstance(value, str) and value.lower() in ('true', '1', 'yes', 'y', 'بله'))))
                                        
                                        # بررسی کلید خارجی قبل از درج - فقط برای جداول مدیا
                                        foreign_key_valid = True
                                        
                                        # برای جدول ProductMedia، مطمئن شویم که product_id وجود دارد
                                        if model.__name__ == 'ProductMedia' and hasattr(item, 'product_id') and item.product_id:
                                            product_exists = db.session.query(db.exists().where(Product.id == item.product_id)).scalar()
                                            if not product_exists:
                                                foreign_key_valid = False
                                                logger.warning(f"رد رکورد ProductMedia به دلیل وجود نداشتن product_id={item.product_id}")
                                            
                                        # برای جدول ServiceMedia، مطمئن شویم که service_id وجود دارد
                                        elif model.__name__ == 'ServiceMedia' and hasattr(item, 'service_id') and item.service_id:
                                            service_exists = db.session.query(db.exists().where(Service.id == item.service_id)).scalar()
                                            if not service_exists:
                                                foreign_key_valid = False
                                                logger.warning(f"رد رکورد ServiceMedia به دلیل وجود نداشتن service_id={item.service_id}")
                                                
                                        # برای جدول EducationalContentMedia، مطمئن شویم که content_id وجود دارد
                                        elif model.__name__ == 'EducationalContentMedia' and hasattr(item, 'content_id') and item.content_id:
                                            content_exists = db.session.query(db.exists().where(EducationalContent.id == item.content_id)).scalar()
                                            if not content_exists:
                                                foreign_key_valid = False
                                                logger.warning(f"رد رکورد EducationalContentMedia به دلیل وجود نداشتن content_id={item.content_id}")
                                                
                                        # فقط اگر رابطه‌ی کلید خارجی معتبر باشد، رکورد را اضافه کنیم
                                        if foreign_key_valid:
                                            # افزودن به دیتابیس و کامیت فوری
                                            db.session.add(item)
                                            try:
                                                db.session.commit()
                                                success_count += 1
                                            except Exception as commit_error:
                                                db.session.rollback()
                                                logger.error(f"خطا در کامیت تک رکوردی: {str(commit_error)}")
                                    except:
                                        continue
                                
                                # گزارش آمار بازیابی تک رکوردی
                                skipped_records = 0
                                total_records = 0
                                
                                # برگرداندن CSV به ابتدا برای شمارش کل رکوردها
                                csv_file.seek(0)
                                reader = csv.reader(csv_file)
                                next(reader, None)  # رد کردن هدر
                                total_records = sum(1 for _ in reader)
                                
                                skipped_records = total_records - success_count
                                
                                if success_count > 0:
                                    # تهیه گزارش مفصل
                                    success_percent = (success_count / total_records) * 100 if total_records > 0 else 0
                                    details = f"{success_count}/{total_records} رکورد ({success_percent:.1f}٪)"
                                    
                                    logger.info(f"بازیابی موفق {details} از {csv_filename} در حالت تک رکوردی")
                                    
                                    if success_count == total_records:
                                        # همه رکوردها با موفقیت بازیابی شدند
                                        restored_tables.append(f"{csv_filename}")
                                    else:
                                        # بازیابی جزئی
                                        restored_tables.append(f"{csv_filename} (بازیابی جزئی: {details})")
                                else:
                                    logger.warning(f"عدم موفقیت در بازیابی {total_records} رکورد از {csv_filename}")
                                    error_tables.append(f"{csv_filename} (خطای کامیت نهایی)")
                            else:
                                error_tables.append(f"{csv_filename} (خطای کامیت نهایی)")
                    
                    except Exception as table_error:
                        db.session.rollback()
                        model_name = model.__name__ if model else "نامشخص"
                        logger.error(f"خطا در بازیابی جدول {csv_filename} (مدل {model_name}): {str(table_error)}")
                        error_tables.append(f"{csv_filename} ({model_name})")
        finally:
            # پاک کردن فایل موقت
            os.unlink(temp_path)
            os.rmdir(temp_dir)
        
        # نمایش نتیجه با فرمت بهتر
        if restored_tables:
            restored_message = f'بازیابی {len(restored_tables)} جدول با موفقیت انجام شد:<br>'
            restored_message += '<ul>'
            for table in restored_tables:
                restored_message += f'<li>{table}</li>'
            restored_message += '</ul>'
            flash(restored_message, 'success')
            
        if skipped_tables:
            skipped_message = f'{len(skipped_tables)} جدول رد شد:<br>'
            skipped_message += '<ul>'
            for table in skipped_tables:
                skipped_message += f'<li>{table}</li>'
            skipped_message += '</ul>'
            flash(skipped_message, 'warning')
            
        if error_tables:
            error_message = f'خطا در بازیابی {len(error_tables)} جدول:<br>'
            error_message += '<ul>'
            for table in error_tables:
                error_message += f'<li>{table}</li>'
            error_message += '</ul>'
            flash(error_message, 'danger')
            
        return redirect(url_for('admin_import_export'))
            
    except Exception as e:
        logger.error(f"Error in restore_database: {str(e)}")
        flash(f"خطا در بازیابی دیتابیس: {str(e)}", 'danger')
        return redirect(url_for('admin_import_export'))

@app.route('/admin/database/export/<table_name>', methods=['POST'])
@login_required
def export_table_csv(table_name):
    """خروجی CSV از جدول"""
    try:
        # مپ کردن نام جدول به کلاس مدل
        model_map = {
            'users': User,
            'product_categories': ProductCategory,
            'service_categories': ServiceCategory,
            'products': Product,
            'services': Service,
            'product_media': ProductMedia,
            'service_media': ServiceMedia,
            'inquiries': Inquiry,
            'educational_content': EducationalContent,
            'educational_media': EducationalContentMedia,
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