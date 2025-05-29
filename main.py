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
import shutil
from app import app
from extensions import db
from utils_upload import media_files, handle_media_upload, remove_file, serve_file
from models import (
    User, Product, ProductMedia, Service, ServiceMedia, Inquiry,
    EducationalContent, StaticContent, EducationalCategory, EducationalContentMedia,
    ProductCategory, ServiceCategory
)
from utils import allowed_file, save_uploaded_file, create_directory
from configuration import load_config, save_config

# تنظیم لاگر
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# تنظیم لاگر برای ذخیره لاگ‌ها در فایل
file_handler = logging.FileHandler('logs/rfcbot.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# ایجاد دایرکتوری logs اگر وجود ندارد
os.makedirs('logs', exist_ok=True)

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
        if file_path and os.path.exists(file_path):
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
        products = Product.query.filter_by(featured=True).limit(6).all()
        services = Service.query.filter_by(featured=True).limit(6).all()
        
        if not products:
            products = []
        if not services:
            services = []
            
        try:
            educational = EducationalContent.query.order_by(
                EducationalContent.created_at.desc()).limit(3).all()
        except Exception as e:
            logger.warning(f"Error loading educational content: {e}")
            educational = []
            
        try:
            about_content = StaticContent.query.filter_by(content_type='about').first()
            about = about_content.content if about_content else "محتوای درباره ما وجود ندارد"
        except Exception as e:
            logger.warning(f"Error loading about content: {e}")
            about = "خطا در بارگذاری محتوای درباره ما"
        
        def check_bot_status():
            try:
                if os.path.exists('bot.log'):
                    with open('bot.log', 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if lines:
                            recent_lines = lines[-10:]
                            for line in reversed(recent_lines):
                                if 'Run polling for bot' in line or 'Start polling' in line:
                                    return 'running'
                                elif 'ERROR' in line or 'CRITICAL' in line:
                                    return 'error'
                return 'stopped'
            except Exception:
                return 'unknown'
        
        bot_status = check_bot_status()
        
        env_status = {
            'BOT_TOKEN': 'Set' if os.environ.get('BOT_TOKEN') else 'Not Set',
            'DATABASE_URL': 'Set' if os.environ.get('DATABASE_URL') else 'Not Set',
            'ADMIN_ID': 'Set' if os.environ.get('ADMIN_ID') else 'Not Set'
        }
        
        try:
            log_file = 'bot.log'
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
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
                              about_text=about,
                              bot_status=bot_status,
                              env_status=env_status,
                              last_run=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                              datetime=datetime,
                              bot_logs=bot_logs)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        env_status = {
            'BOT_TOKEN': 'Set' if os.environ.get('BOT_TOKEN') else 'Not Set',
            'DATABASE_URL': 'Set' if os.environ.get('DATABASE_URL') else 'Not Set',
            'ADMIN_ID': 'Set' if os.environ.get('ADMIN_ID') else 'Not Set'
        }
        return render_template('index.html', 
                              products=[], 
                              services=[], 
                              educational=[], 
                              about_text="خطا در بارگذاری محتوا", 
                              env_status=env_status,
                              bot_status='error',
                              bot_logs=['خطا در بارگذاری لاگ‌ها'],
                              last_run=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                              datetime=datetime)
            
@app.route('/api/logs')
def get_logs_json():
    """دریافت لاگ‌های ربات برای درخواست‌های AJAX"""
    try:
        log_file = 'bot.log'
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                bot_logs = lines[-50:] if len(lines) > 50 else lines
                logs_text = ''.join(bot_logs)
        else:
            logs_text = 'فایل لاگ موجود نیست.'
        
        return jsonify({'logs': logs_text})
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/configuration')
@login_required
def loadConfig():
    """صفحه پیکربندی"""
    try:
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

@app.route('/admin/delete_media', methods=['POST'])
@login_required
def delete_media():
    """
    حذف فایل رسانه‌ای از سیستم
    """
    if not current_user.is_admin:
        logger.warning(f"Non-admin user {current_user.id} attempted to delete media")
        return jsonify({'success': False, 'error': 'دسترسی مجاز نیست'}), 403
    
    try:
        content_type = request.args.get('type')
        content_id = request.args.get('content_id')
        media_id = request.args.get('media_id')
        
        if not all([content_type, content_id, media_id]):
            logger.error(f"Missing parameters in delete_media request: {request.args}")
            return jsonify({'success': False, 'error': 'پارامترهای ناقص'}), 400
        
        content_id = int(content_id)
        media_id = int(media_id)
        
        if content_type == 'product':
            media = ProductMedia.query.get(media_id)
            if not media or media.product_id != content_id:
                logger.warning(f"Product media not found or mismatch: media_id={media_id}, product_id={content_id}")
                return jsonify({'success': False, 'error': 'رسانه محصول یافت نشد'}), 404
            
            file_path = media.local_path if hasattr(media, 'local_path') and media.local_path else None
            if not file_path and media.file_id:
                file_path = os.path.join('static', 'uploads', 'products', f"{media.file_id.split('_')[-1]}")
            
            delete_result = delete_media_file(file_path) if file_path else False
            db.session.delete(media)
            db.session.commit()
            logger.info(f"Product media deleted: id={media_id}, product_id={content_id}, file_path={file_path}")
            return jsonify({'success': True})
            
        elif content_type == 'service':
            media = ServiceMedia.query.get(media_id)
            if not media or media.service_id != content_id:
                logger.warning(f"Service media not found or mismatch: media_id={media_id}, service_id={content_id}")
                return jsonify({'success': False, 'error': 'رسانه خدمت یافت نشد'}), 404
            
            file_path = media.local_path if hasattr(media, 'local_path') and media.local_path else None
            if not file_path and media.file_id:
                file_path = os.path.join('static', 'uploads', 'services', f"{media.file_id.split('_')[-1]}")
            
            delete_result = delete_media_file(file_path) if file_path else False
            db.session.delete(media)
            db.session.commit()
            logger.info(f"Service media deleted: id={media_id}, service_id={content_id}, file_path={file_path}")
            return jsonify({'success': True})
            
        elif content_type == 'educational':
            media = EducationalContentMedia.query.get(media_id)
            if not media or media.content_id != content_id:
                logger.warning(f"Educational content media not found or mismatch: media_id={media_id}, content_id={content_id}")
                return jsonify({'success': False, 'error': 'رسانه محتوای آموزشی یافت نشد'}), 404
            
            file_path = media.local_path if hasattr(media, 'local_path') and media.local_path else None
            if not file_path and media.file_id:
                file_path = os.path.join('static', 'uploads', 'educational', f"{media.file_id.split('_')[-1]}")
            
            delete_result = delete_media_file(file_path) if file_path else False
            db.session.delete(media)
            db.session.commit()
            logger.info(f"Educational content media deleted: id={media_id}, content_id={content_id}, file_path={file_path}")
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
        product_count = Product.query.count()
        service_count = Service.query.count()
        product_category_count = ProductCategory.query.count()
        service_category_count = ServiceCategory.query.count()
        educational_category_count = EducationalCategory.query.count()
        category_count = product_category_count + service_category_count + educational_category_count
        inquiry_count = Inquiry.query.count()
        pending_count = Inquiry.query.filter_by(status='pending').count()
        
        recent_inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(5).all()
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
        return render_template('error.html', 
                            error=str(e),
                            traceback=traceback.format_exc())

# تابع کمکی برای تبدیل مسیر فایل تصویر
def get_photo_url(photo_url):
    """
    تبدیل مسیر photo_url به مسیر قابل استفاده در url_for
    """
    if not photo_url:
        return None
    if photo_url.startswith('static/'):
        return photo_url[7:]
    return photo_url

# روت‌های مربوط به محصولات
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """صفحه جزئیات محصول"""
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter_by(category_id=product.category_id).filter(Product.id != product.id).limit(4).all()
    media = ProductMedia.query.filter_by(product_id=product.id).all()
    
    photo_url = get_photo_url(product.photo_url)
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
    
    if request.method == 'POST':
        if action == 'delete':
            product_id = request.form.get('product_id')
            if not product_id:
                flash('شناسه محصول الزامی است.', 'danger')
                return redirect(url_for('admin_products'))
                
            try:
                product = Product.query.get_or_404(int(product_id))
                media_files = ProductMedia.query.filter_by(product_id=product.id).all()
                for media in media_files:
                    if media.file_id and not media.file_id.startswith('http'):
                        file_path = os.path.join('static', media.file_id)
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                logger.info(f"Removed file from disk: {file_path}")
                            except Exception as e:
                                logger.warning(f"Could not remove file {file_path}: {e}")
                
                db.session.delete(product)
                db.session.commit()
                flash(f'محصول "{product.name}" با موفقیت حذف شد.', 'success')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error deleting product: {e}")
                flash(f'خطا در حذف محصول: {str(e)}', 'danger')
                
            return redirect(url_for('admin_products'))
            
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
                    upload_dir = os.path.join('static', 'uploads', 'products', str(product.id))
                    success, file_path = handle_media_upload(
                        file=file,
                        directory=upload_dir,
                        file_type=file_type,
                        custom_filename=None
                    )
                    
                    if success and file_path:
                        relative_path = file_path.replace('static/', '', 1) if file_path.startswith('static/') else file_path
                        logger.info(f"Product media relative path: {relative_path}")
                        media = ProductMedia(
                            product_id=product.id,
                            file_id=relative_path,
                            file_type=file_type,
                            local_path=file_path
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
                    flash(f'خطا در آپلود رسانه: {str(e)}', 'danger')
            else:
                flash('لطفاً یک فایل انتخاب کنید.', 'warning')
                
            return redirect(url_for('admin_products', action='media', id=product_id))
            
        elif action == 'save':
            product_id = request.form.get('id')
            name = request.form.get('name')
            price = request.form.get('price', '0')
            description = request.form.get('description', '')
            category_id = request.form.get('category_id')
            brand = request.form.get('brand', '')
            model = request.form.get('model', '')
            in_stock = 'in_stock' in request.form
            tags = request.form.get('tags', '')
            featured = 'featured' in request.form
            model_number = request.form.get('model_number', '')
            manufacturer = request.form.get('manufacturer', '')
            
            try:
                price = float(price) if price else 0
            except ValueError:
                price = 0
                
            try:
                category_id = int(category_id) if category_id else None
            except ValueError:
                category_id = None
                
            try:
                if category_id is None:
                    default_category = ProductCategory.query.first()
                    if default_category:
                        category_id = default_category.id
                        logger.info(f"Using default product category ID: {category_id}")
                    else:
                        new_category = ProductCategory(name="دسته‌بندی پیش‌فرض محصولات")
                        db.session.add(new_category)
                        db.session.flush()
                        category_id = new_category.id
                        logger.info(f"Created new default product category ID: {category_id}")
                
                if product_id:
                    product = Product.query.get_or_404(int(product_id))
                    product.name = name
                    product.price = price
                    product.description = description
                    product.category_id = category_id
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
                    product = Product(
                        name=name,
                        price=price,
                        description=description,
                        category_id=category_id,
                        brand=brand,
                        model=model,
                        in_stock=in_stock,
                        tags=tags,
                        featured=featured,
                        model_number=model_number,
                        manufacturer=manufacturer
                    )
                    db.session.add(product)
                    logger.info(f"Creating new product: Name: {name}")
                    flash('محصول جدید با موفقیت ثبت شد.', 'success')
                
                photo = request.files.get('photo')
                if photo and photo.filename:
                    upload_dir = os.path.join('static', 'uploads', 'products', 'main')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    success, file_path = handle_media_upload(
                        file=photo,
                        directory=upload_dir,
                        file_type='photo',
                        custom_filename=None
                    )
                    
                    if success and file_path:
                        relative_path = file_path.replace('static/', '', 1) if file_path.startswith('static/') else file_path
                        product.photo_url = relative_path
                        logger.info(f"Uploaded main photo for product: {file_path}")
                
                db.session.commit()
                
                if not product_id and photo and photo.filename and success:
                    product_upload_dir = os.path.join('static', 'uploads', 'products', str(product.id))
                    os.makedirs(product_upload_dir, exist_ok=True)
                    new_file_path = os.path.join(product_upload_dir, os.path.basename(file_path))
                    shutil.move(file_path, new_file_path)
                    new_relative_path = new_file_path.replace('static/', '', 1) if new_file_path.startswith('static/') else new_file_path
                    product.photo_url = new_relative_path
                    db.session.commit()
                    logger.info(f"Moved product photo to dedicated directory: {new_file_path}")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving product: {str(e)}")
                flash(f'خطا در ذخیره محصول: {str(e)}', 'danger')
                categories = ProductCategory.query.all()
                if product_id:
                    product = Product.query.get_or_404(int(product_id))
                    return render_template('admin/product_form.html',
                                          title="ویرایش محصول",
                                          product=product,
                                          categories=categories)
                return render_template('admin/product_form.html',
                                      title="افزودن محصول جدید",
                                      categories=categories)
                
            return redirect(url_for('admin_products'))
            
        elif action == 'delete_media':
            media_id = request.form.get('media_id')
            product_id = request.form.get('product_id')
            
            if not media_id or not product_id:
                flash('شناسه رسانه و محصول الزامی است.', 'danger')
                return redirect(url_for('admin_products'))
                
            try:
                media = ProductMedia.query.get(int(media_id))
                if media and media.product_id == int(product_id):
                    if not media.file_id.startswith('http'):
                        file_path = os.path.join('static', 'uploads', media.file_id)
                        delete_media_file(file_path)
                    db.session.delete(media)
                    db.session.commit()
                    flash('رسانه با موفقیت حذف شد.', 'success')
                    logger.info(f"Media deleted: id={media_id}, product_id={product_id}")
                else:
                    flash('رسانه یافت نشد.', 'warning')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error deleting media: {str(e)}")
                flash(f'خطا در حذف رسانه: {str(e)}', 'danger')
                
            return redirect(url_for('admin_products', action='media', id=product_id))
    
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
    elif action == 'media' and product_id:
        product = Product.query.get_or_404(int(product_id))
        media = ProductMedia.query.filter_by(product_id=product.id).all()
        return render_template('admin/product_media.html',
                              product=product,
                              media=media,
                              active_page='products')
    
    products = Product.query.all()
    categories = ProductCategory.query.all()
    for product in products:
        product.formatted_photo_url = get_photo_url(product.photo_url)
    
    return render_template('admin/products.html', 
                          products=products, 
                          categories=categories)

# ----- Category Management Routes -----

def build_category_tree(categories, parent_id=None):
    """ساخت ساختار درختی از دسته‌بندی‌ها"""
    tree = []
    for category in categories:
        if category.parent_id == parent_id:
            children = build_category_tree(categories, category.id)
            tree.append({
                'id': category.id,
                'name': category.name,
                'children': children
            })
    return tree

def get_all_subcategories(category_model, category_id, subcategories=None, visited=None):
    """دریافت تمام زیردسته‌ها به صورت بازگشتی"""
    if subcategories is None:
        subcategories = []
    if visited is None:
        visited = set()
    
    if category_id in visited:
        logger.warning(f"Circular reference detected: {category_id}")
        return subcategories
    
    visited.add(category_id)
    categories = category_model.query.filter_by(parent_id=category_id).all()
    for category in categories:
        subcategories.append(category.id)
        get_all_subcategories(category_model, category.id, subcategories, visited)
    
    return subcategories

def unlink_subcategories(category_model, category_id):
    """تنظیم parent_id به None برای زیردسته‌ها"""
    subcategories = get_all_subcategories(category_model, category_id)
    count = 0
    for subcategory_id in subcategories:
        subcategory = category_model.query.get(subcategory_id)
        if subcategory:
            subcategory.parent_id = None
            count += 1
    return count

def unlink_objects(model, category_model, category_id):
    """تنظیم category_id به None برای اشیا"""
    category_ids = [category_id] + get_all_subcategories(category_model, category_id)
    count = model.query.filter(model.category_id.in_(category_ids)).update({model.category_id: None})
    return count

@app.route('/admin/categories')
@login_required
def admin_categories():
    """نمایش صفحه مدیریت دسته‌بندی‌ها"""
    try:
        if not current_user.is_admin:
            flash('دسترسی غیرمجاز.', 'danger')
            return redirect(url_for('index'))
            
        product_categories = ProductCategory.query.all()
        service_categories = ServiceCategory.query.all()
        educational_categories = EducationalCategory.query.all()
        
        product_tree = build_category_tree(product_categories)
        service_tree = build_category_tree(service_categories)
        educational_tree = build_category_tree(educational_categories)
        
        return render_template('admin/categories.html',
                              product_categories=product_categories,
                              service_categories=service_categories,
                              educational_categories=educational_categories,
                              product_tree=product_tree,
                              service_tree=service_tree,
                              educational_tree=educational_tree,
                              active_page='categories')
    except Exception as e:
        logger.error(f"Error in admin_categories: {str(e)}")
        flash(f'خطا در بارگذاری دسته‌بندی‌ها: {str(e)}', 'danger')
        return render_template('admin/categories.html',
                              product_categories=[],
                              service_categories=[],
                              educational_categories=[],
                              product_tree=[],
                              service_tree=[],
                              educational_tree=[],
                              active_page='categories')

@app.route('/admin/categories/add_product', methods=['POST'])
@login_required
def add_product_category():
    """اضافه کردن دسته‌بندی محصولات"""
    try:
        if not current_user.is_admin:
            flash('دسترسی غیرمجاز.', 'danger')
            return redirect(url_for('admin_categories'))
            
        name = request.form.get('name')
        parent_id = request.form.get('parent_id')
        
        if not name:
            flash('نام دسته‌بندی الزامی است.', 'danger')
            return redirect(url_for('admin_categories'))
        
        parent_id = int(parent_id) if parent_id else None
        
        category = ProductCategory(name=name, parent_id=parent_id)
        db.session.add(category)
        db.session.commit()
        flash(f'دسته‌بندی محصول "{name}" با موفقیت اضافه شد.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding product category: {str(e)}")
        flash(f'خطا در افزودن دسته‌بندی محصول: {str(e)}', 'danger')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/update_product', methods=['POST'])
@login_required
def update_product_category():
    """ویرایش دسته‌بندی محصولات"""
    try:
        if not current_user.is_admin:
            flash('دسترسی غیرمجاز.', 'danger')
            return redirect(url_for('admin_categories'))
            
        category_id = request.form.get('id')
        name = request.form.get('name')
        parent_id = request.form.get('parent_id')
        
        if not category_id or not name:
            flash('شناسه و نام دسته‌بندی الزامی هستند.', 'danger')
            return redirect(url_for('admin_categories'))
        
        category = ProductCategory.query.get_or_404(int(category_id))
        parent_id = int(parent_id) if parent_id else None
        
        if parent_id == category.id:
            flash('دسته‌بندی نمی‌تواند والد خودش باشد.', 'danger')
            return redirect(url_for('admin_categories'))
        
        category.name = name
        category.parent_id = parent_id
        db.session.commit()
        flash(f'دسته‌بندی محصول "{name}" با موفقیت ویرایش شد.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating product category: {str(e)}")
        flash(f'خطا در ویرایش دسته‌بندی محصول: {str(e)}', 'danger')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/delete_product', methods=['POST'])
@login_required
def delete_product_category():
    """حذف دسته‌بندی محصولات"""
    try:
        if not current_user.is_admin:
            flash('دسترسی غیرمجاز.', 'danger')
            return redirect(url_for('admin_categories'))
            
        category_id = request.form.get('id')
        if not category_id:
            flash('شناسه دسته‌بندی نامعتبر است.', 'danger')
            return redirect(url_for('admin_categories'))
        
        category = ProductCategory.query.get_or_404(int(category_id))
        name = category.name
        
        subcategories_count = unlink_subcategories(ProductCategory, category_id)
        products_count = unlink_objects(Product, ProductCategory, category_id)
        db.session.delete(category)
        db.session.commit()
        flash(f'دسته‌بندی محصول "{name}" با موفقیت حذف شد. '
              f'{subcategories_count} زیردسته و {products_count} محصول بدون دسته‌بندی شدند.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting product category: {str(e)}")
        flash(f'خطا در حذف دسته‌بندی محصول: {str(e)}', 'danger')
    
    return redirect(url_for('admin_categories'))

# Service Category Management
@app.route('/admin/categories/add_service', methods=['POST'])
@login_required
def add_service_category():
    """اضافه کردن دسته‌بندی خدمات"""
    try:
        if not current_user.is_admin:
            flash('دسترسی غیرمجاز.', 'danger')
            return redirect(url_for('admin_categories'))
            
        name = request.form.get('name')
        parent_id = request.form.get('parent_id')
        
        if not name:
            flash('نام دسته‌بندی الزامی است.', 'danger')
            return redirect(url_for('admin_categories'))
        
        parent_id = int(parent_id) if parent_id else None
        
        category = ServiceCategory(name=name, parent_id=parent_id)
        db.session.add(category)
        db.session.commit()
        flash(f'دسته‌بندی خدمات "{name}" با موفقیت اضافه شد.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding service category: {str(e)}")
        flash(f'خطا در افزودن دسته‌بندی خدمات: {str(e)}', 'danger')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/update_service', methods=['POST'])
@login_required
def update_service_category():
    """ویرایش دسته‌بندی خدمات"""
    try:
        if not current_user.is_admin:
            flash('دسترسی غیرمجاز.', 'danger')
            return redirect(url_for('admin_categories'))
            
        category_id = request.form.get('id')
        name = request.form.get('name')
        parent_id = request.form.get('parent_id')
        
        if not category_id or not name:
            flash('شناسه و نام دسته‌بندی الزامی هستند.', 'danger')
            return redirect(url_for('admin_categories'))
        
        category = ServiceCategory.query.get_or_404(int(category_id))
        parent_id = int(parent_id) if parent_id else None
        
        if parent_id == category.id:
            flash('دسته‌بندی نمی‌تواند والد خودش باشد.', 'danger')
            return redirect(url_for('admin_categories'))
        
        category.name = name
        category.parent_id = parent_id
        db.session.commit()
        flash(f'دسته‌بندی خدمات "{name}" با موفقیت ویرایش شد.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating service category: {str(e)}")
        flash(f'خطا در ویرایش دسته‌بندی خدمات: {str(e)}', 'danger')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/delete_service', methods=['POST'])
@login_required
def delete_service_category():
    """حذف دسته‌بندی خدمات"""
    try:
        if not current_user.is_admin:
            flash('دسترسی غیرمجاز.', 'danger')
            return redirect(url_for('admin_categories'))
            
        category_id = request.form.get('id')
        if not category_id:
            flash('شناسه دسته‌بندی نامعتبر است.', 'danger')
            return redirect(url_for('admin_categories'))
        
        category = ServiceCategory.query.get_or_404(int(category_id))
        name = category.name
        
        subcategories_count = unlink_subcategories(ServiceCategory, category_id)
        services_count = unlink_objects(Service, ServiceCategory, category_id)
        db.session.delete(category)
        db.session.commit()
        flash(f'دسته‌بندی خدمات "{name}" با موفقیت حذف شد. '
              f'{subcategories_count} زیردسته و {services_count} خدمت بدون دسته‌بندی شدند.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting service category: {str(e)}")
        flash(f'خطا در حذف دسته‌بندی خدمات: {str(e)}', 'danger')
    
    return redirect(url_for('admin_categories'))

# Educational Category Management
@app.route('/admin/categories/add_educational', methods=['POST'])
@login_required
def add_educational_category():
    """اضافه کردن دسته‌بندی آموزشی"""
    try:
        if not current_user.is_admin:
            flash('دسترسی غیرمجاز.', 'danger')
            return redirect(url_for('admin_categories'))
            
        name = request.form.get('name')
        parent_id = request.form.get('parent_id')
        
        if not name:
            flash('نام دسته‌بندی الزامی است.', 'danger')
            return redirect(url_for('admin_categories'))
        
        parent_id = int(parent_id) if parent_id else None
        
        category = EducationalCategory(name=name, parent_id=parent_id)
        db.session.add(category)
        db.session.commit()
        flash(f'دسته‌بندی آموزشی "{name}" با موفقیت اضافه شد.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding educational category: {str(e)}")
        flash(f'خطا در افزودن دسته‌بندی آموزشی: {str(e)}', 'danger')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/update_educational', methods=['POST'])
@login_required
def update_educational_category():
    """ویرایش دسته‌بندی آموزشی"""
    try:
        if not current_user.is_admin:
            flash('دسترسی غیرمجاز.', 'danger')
            return redirect(url_for('admin_categories'))
            
        category_id = request.form.get('id')
        name = request.form.get('name')
        parent_id = request.form.get('parent_id')
        
        if not category_id or not name:
            flash('شناسه و نام دسته‌بندی الزامی هستند.', 'danger')
            return redirect(url_for('admin_categories'))
        
        category = EducationalCategory.query.get_or_404(int(category_id))
        parent_id = int(parent_id) if parent_id else None
        
        if parent_id == category.id:
            flash('دسته‌بندی نمی‌تواند والد خودش باشد.', 'danger')
            return redirect(url_for('admin_categories'))
        
        category.name = name
        category.parent_id = parent_id
        db.session.commit()
        flash(f'دسته‌بندی آموزشی "{name}" با موفقیت ویرایش شد.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating educational category: {str(e)}")
        flash(f'خطا در ویرایش دسته‌بندی آموزشی: {str(e)}', 'danger')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/delete_educational', methods=['POST'])
@login_required
def delete_educational_category():
    """حذف دسته‌بندی آموزشی"""
    try:
        if not current_user.is_admin:
            flash('دسترسی غیرمجاز.', 'danger')
            return redirect(url_for('admin_categories'))
            
        category_id = request.form.get('id')
        if not category_id:
            flash('شناسه دسته‌بندی نامعتبر است.', 'danger')
            return redirect(url_for('admin_categories'))
        
        category = EducationalCategory.query.get_or_404(int(category_id))
        name = category.name
        
        subcategories_count = unlink_subcategories(EducationalCategory, category_id)
        contents_count = unlink_objects(EducationalContent, EducationalCategory, category_id)
        db.session.delete(category)
        db.session.commit()
        flash(f'دسته‌بندی آموزشی "{name}" با موفقیت حذف شد. '
              f'{subcategories_count} زیردسته و {contents_count} محتوای آموزشی بدون دسته شدند.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting educational category: {str(e)}")
        flash(f'خطا در حذف دسته‌بندی آموزشی: {str(e)}', 'danger')
    
    return redirect(url_for('admin_categories'))

# ----- Service Routes -----

@app.route('/service/<int:service_id>')
def service_detail(service_id):
    """صفحه جزئیات خدمت"""
    service = Service.query.get_or_404(service_id)
    related_services = Service.query.filter_by(category_id=service.category_id).filter(Service.id != service.id).limit(4).all()
    media = ServiceMedia.query.filter_by(service_id=service.id).all()
    
    photo_url = get_photo_url(service.photo_url)
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
    
    if request.method == 'POST':
        if action == 'delete':
            service_id = request.form.get('service_id')
            if not service_id:
                flash('شناسه خدمت الزامی است.', 'danger')
                return redirect(url_for('admin_services'))
                
            try:
                service = Service.query.get_or_404(int(service_id))
                media_files = ServiceMedia.query.filter_by(service_id=service.id).all()
                for media in media_files:
                    if media.file_id and not media.file_id.startswith('http'):
                        file_path = os.path.join('static', media.file_id)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            logger.info(f"Removed file from disk: {file_path}")
                
                db.session.delete(service)
                db.session.commit()
                flash(f'خدمت "{service.name}" با موفقیت حذف شد.', 'success')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error deleting service: {str(e)}")
                flash(f'خطا در حذف خدمت: {str(e)}', 'danger')
                
            return redirect(url_for('admin_services'))
            
        elif action == 'save':
            service_id = request.form.get('id')
            name = request.form.get('name')
            price = request.form.get('price', '0')
            description = request.form.get('description', '')
            category_id = request.form.get('category_id')
            tags = request.form.get('tags', '')
            featured = 'featured' in request.form
            
            try:
                price = float(price) if price else 0
                category_id = int(category_id) if category_id else None
                
                if category_id is None:
                    default_category = ServiceCategory.query.first()
                    if default_category:
                        category_id = default_category.id
                    else:
                        new_category = ServiceCategory(name="دسته‌بندی پیش‌فرض خدمات")
                        db.session.add(new_category)
                        db.session.flush()
                        category_id = new_category.id
                        logger.info(f"Created default category ID: {category_id}")
                
                if service_id:
                    service = Service.query.get_or_404(int(service_id))
                    service.name = name
                    service.price = price
                    service.description = description
                    service.category_id = category_id
                    service.tags = tags
                    service.featured = featured
                    logger.info(f"Updating service ID: {service_id}, Name: {name}")
                    flash('خدمت با موفقیت به‌روزرسانی شد.', 'success')
                else:
                    service = Service(
                        name=name,
                        price=price,
                        description=description,
                        category_id=category_id,
                        tags=tags,
                        featured=featured
                    )
                    db.session.add(service)
                    logger.info(f"Creating new service: Name: {name}")
                    flash('خدمت جدید ثبت شد.', 'success')
                
                photo = request.files.get('photo')
                if photo and photo.filename:
                    upload_dir = os.path.join('static', 'uploads', 'services', 'main')
                    os.makedirs(upload_dir, exist_ok=True)
                    success, file_path = handle_media_upload(
                        file=photo,
                        directory=upload_dir,
                        file_type='photo',
                        custom_filename=None
                    )
                    if success and file_path:
                        relative_path = file_path.replace('static/', '', 1) if file_path.startswith('static/') else file_path
                        service.photo_url = relative_path
                        logger.info(f"Uploaded main photo for service: {file_path}")
                
                db.session.commit()
                
                if not service_id and photo and success and photo.filename:
                    service_upload_dir = os.path.join('static', 'uploads', 'services', str(service.id))
                    os.makedirs(service_upload_dir, exist_ok=True)
                    new_file_path = os.path.join(service_upload_dir, os.path.basename(file_path))
                    shutil.move(file_path, new_file_path)
                    new_relative_path = new_file_path.replace('static/', '', 1) if new_file_path.startswith('static/') else new_file_path
                    service.photo_url = new_relative_path
                    db.session.commit()
                    logger.info(f"Moved service photo to: {new_file_path}")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving service: {str(e)}")
                flash(f"خطا در ذخیره خدمت: {str(e)}", 'danger')
                categories = ServiceCategory.query.all()
                if service_id:
                    service = Service.query.get_or_404(int(service_id))
                    return render_template('admin/service_form.html',
                                          title="ویرایش خدمت",
                                          service=service,
                                          categories=categories)
                return render_template('admin/service_form.html',
                                      title="افزودن خدمت جدید",
                                      categories=categories)
                
            return redirect(url_for('admin_services'))
            
        elif action == 'upload_media':
            service_id = request.form.get('service_id')
            if not service_id:
                flash('شناسه خدمت الزامی است.', 'danger')
                return redirect(url_for('admin_services'))
            
            service = Service.query.get_or_404(int(service_id))
            file = request.files.get('file')
            file_type = request.form.get('file_type', 'photo')
            
            if file and file.filename:
                try:
                    upload_dir = os.path.join('static', 'uploads', 'services', str(service.id))
                    success, file_path = handle_media_upload(
                        file=file,
                        directory=upload_dir,
                        file_type=file_type,
                        custom_filename=None
                    )
                    
                    if success and file_path:
                        relative_path = file_path.replace('static/', '', 1) if file_path.startswith('static/') else file_path
                        media = ServiceMedia(
                            service_id=service.id,
                            file_id=relative_path,
                            file_type=file_type,
                            local_path=file_path
                        )
                        db.session.add(media)
                        db.session.commit()
                        logger.info(f"Media uploaded successfully: {file_path}")
                        flash('رسانه با موفقیت آپلود شد.', 'success')
                    else:
                        flash('خطا در آپلود فایل.', 'danger')
                        logger.error(f"File upload failed")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error uploading media: {str(e)}")
                    flash(f'خطا در آپلود رسانه: {str(e)}', 'danger')
                else:
                    flash('لطفاً یک فایل انتخاب کنید.', 'warning')
                
            return redirect(url_for('admin_services', action='media', id=service_id))
            
        elif action == 'delete_media':
            media_id = request.form.get('media_id')
            service_id = request.form.get('service_id')
            
            if not media_id or not service_id:
                flash('شناسه رسانه و خدمت الزامی است.', 'danger')
                return redirect(url_for('admin_services'))
            
            try:
                media = ServiceMedia.query.get_or_404(int(media_id))
                if media.service_id == int(service_id):
                    if not media.file_id.startswith('http'):
                        file_path = os.path.join('static', 'Uploads', media.file_id)
                        delete_media_file(file_path)
                    db.session.delete(media)
                    db.session.commit()
                    flash('رسانه با موفقیت حذف شد.', 'success')
                    logger.info(f"Media deleted: id={media_id}, service_id={service_id}")
                else:
                    flash('رسانه یافت نشد.', 'warning')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error deleting media: {str(e)}")
                flash(f'خطا در حذف رسانه: {str(e)}', 'danger')
                
            return redirect(url_for('admin_services', action='media', id=service_id))
    
    if action == 'add':
        categories = ServiceCategory.query.all()
        return render_template('admin/service_form.html',
                              title="افزودن خدمت جدید",
                              categories=categories)
    elif action == 'edit' and service_id:
        service = Service.query.get_or_404(int(service_id))
        categories = ServiceCategory.query.all()
        return render_template('admin/service_form.html',
                              title="ویرایش خدمت",
                              service=service,
                              categories=categories)
    elif action == 'media' and service_id:
        service = Service.query.get_or_404(int(service_id))
        media = ServiceMedia.query.filter_by(service_id=service.id).all()
        return render_template('admin/service_media.html',
                              service=service,
                              media=media,
                              active_page='services')

    services = Service.query.all()
    categories = ServiceCategory.query.all()
    for service in services:
        service.formatted_photo_url = get_photo_url(service.photo_url)
    
    return render_template('admin/services.html', 
                          services=services, 
                          categories=categories)

# ----- Educational Content Routes -----

@app.route('/educational/<int:content_id>')
def educational_detail(content_id):
    """صفحه جزئیات محتوای آموزشی"""
    content = EducationalContent.query.get_or_404(content_id)
    media = EducationalContentMedia.query.filter_by(content_id=content.id).all()
    related_content = EducationalContent.query.filter_by(category_id=content.category_id).filter(EducationalContent.id != content_id).limit(4).all()
    
    photo_url = get_photo_url(content.photo_url)
    for related in related_content:
        related.formatted_photo_url = get_photo_url(related.photo_url)
    
    return render_template('educational_detail.html',
                          content=content,
                          photo_url=photo_url,
                          media=media,
                          related_content=related_content)

@app.route('/admin/educational', methods=['GET', 'POST'])
@login_required
def admin_educational():
    """پنل مدیریت - محتوای آموزشی"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز.', 'danger')
        return redirect(url_for('index'))
        
    action = request.args.get('action')
    content_id = request.args.get('id')
    
    if request.method == 'POST':
        if action == 'delete':
            content_id = request.form.get('content_id')
            if not content_id:
                flash('شناسه محتوا الزامی است.', 'danger')
                return redirect(url_for('admin_educational'))
                
            content = EducationalContent.query.get_or_404(int(content_id))
            media_files = EducationalContentMedia.query.filter_by(content_id=content.id).all()
            for media in media_files:
                if media.file_id and not media.file_id.startswith('http'):
                    file_path = os.path.join('static', media.file_id)
                    delete_media_file(file_path)
            
            db.session.delete(content)
            db.session.commit()
            flash(f'محتوای آموزشی "{content.title}" با موفقیت حذف شد.', 'success')
            return redirect(url_for('admin_educational'))
            
        elif action == 'save':
            content_id = request.form.get('id')
            title = request.form.get('title')
            content_text = request.form.get('content')
            category_id = request.form.get('category_id')
            tags = request.form.get('tags', '')
            featured = 'featured' in request.form
            
            try:
                category_id = int(category_id) if category_id else None
                if category_id is None:
                    default_category = EducationalCategory.query.first()
                    if default_category:
                        category_id = default_category.id
                    else:
                        new_category = EducationalCategory(name="دسته آموزشی پیش‌فرض")
                        db.session.add(new_category)
                        db.session.flush()
                        category_id = new_category.id
                        logger.info(f"Created default educational category ID: {category_id}")
                
                if content_id:
                    content = EducationalContent.query.get_or_404(int(content_id))
                    content.title = title
                    content.content = content_text
                    content.category_id = category_id
                    content.tags = tags
                    content.featured = featured
                    flash('محتوای آموزشی به‌روزرسانی شد.', 'success')
                else:
                    content = EducationalContent(
                        title=title,
                        content=content_text,
                        category_id=category_id,
                        tags=tags,
                        featured=featured
                    )
                    db.session.add(content)
                    flash('محتوای آموزشی جدید ثبت شد.', 'success')
                
                photo = request.files.get('photo')
                if photo and photo.filename:
                    upload_dir = os.path.join('static', 'uploads', 'educational', 'main')
                    os.makedirs(upload_dir, exist_ok=True)
                    success, file_path = handle_media_upload(
                        file=photo,
                        directory=upload_dir,
                        file_type='photo',
                        custom_filename=None
                    )
                    if success:
                        relative_path = file_path.replace('static/', '', 1) if file_path.startswith('static/') else file_path
                        content.photo_url = relative_path
                        logger.info(f"Uploaded main photo for educational content: {file_path}")
                
                db.session.commit()
                
                if not content_id and photo and success:
                    content_upload_dir = os.path.join('static', 'uploads', 'educational', str(content.id))
                    os.makedirs(content_upload_dir, exist_ok=True)
                    new_file_path = os.path.join(content_upload_dir, os.path.basename(file_path))
                    shutil.move(file_path, new_file_path)
                    new_relative_path = new_file_path.replace('static/', '', 1) if new_file_path.startswith('static/') else new_file_path
                    content.photo_url = new_relative_path
                    db.session.commit()
                    logger.info(f"Moved content photo to: {new_file_path}")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving educational content: {str(e)}")
                flash(f'خطا در ذخیره محتوای آموزشی: {str(e)}', 'danger')
                categories = EducationalCategory.query.all()
                if content_id:
                    content = EducationalContent.query.get_or_404(int(content_id))
                    return render_template('admin/educational_form.html',
                                          title="ویرایش محتوای آموزشی",
                                          content=content,
                                          categories=categories)
                return render_template('admin/educational_form.html',
                                      title="افزودن محتوای آموزشی جدید",
                                      categories=categories)
                
            return redirect(url_for('admin_educational'))
            
        elif action == 'upload_media':
            content_id = request.form.get('content_id')
            if not content_id:
                flash('شناسه محتوا الزامی است.', 'danger')
                return redirect(url_for('admin_educational'))
                
            content = EducationalContent.query.get_or_404(int(content_id))
            file = request.files.get('file')
            file_type = request.form.get('file_type', 'photo')
            
            if file and file.filename:
                try:
                    upload_dir = os.path.join('static', 'uploads', 'educational', str(content.id))
                    success, file_path = handle_media_upload(
                        file=file,
                        directory=upload_dir,
                        file_type=file_type,
                        custom_filename=None
                    )
                    if success:
                        relative_path = file_path.replace('static/', '', 1) if file_path.startswith('static/') else file_path
                        media = EducationalContentMedia(
                            content_id=content.id,
                            file_id=relative_path,
                            file_type=file_type,
                            local_path=file_path
                        )
                        db.session.add(media)
                        db.session.commit()
                        flash('رسانه با موفقیت آپلود شد.', 'success')
                        logger.info(f"Media uploaded for content: {file_path}")
                    else:
                        flash('خطا در آپلود فایل.', 'danger')
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error uploading media: {str(e)}")
                    flash(f'خطا در آپلود رسانه: {str(e)}', 'danger')
            else:
                flash('لطفاً یک فایل انتخاب کنید.', 'warning')
                
            return redirect(url_for('admin_educational', action='media', id=content_id))
            
        elif action == 'delete_media':
            media_id = request.form.get('media_id')
            content_id = request.form.get('content_id')
            
            if not media_id or not content_id:
                flash('شناسه رسانه و محتوا الزامی است.', 'danger')
                return redirect(url_for('admin_educational'))
                
            try:
                media = EducationalContentMedia.query.get(int(media_id))
                if media and media.content_id == int(content_id):
                    delete_media_file(media.local_path)
                    db.session.delete(media)
                    db.session.commit()
                    flash('رسانه با موفقیت حذف شد.', 'success')
                    logger.info(f"Media deleted: id={media_id}, content_id={content_id}")
                else:
                    flash('رسانه یافت نشد.', 'warning')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error deleting media: {str(e)}")
                flash(f'خطا در حذف رسانه: {str(e)}', 'danger')
                
            return redirect(url_for('admin_educational', action='media', id=content_id))
    
    if action == 'add':
        categories = EducationalCategory.query.all()
        return render_template('admin/educational_form.html',
                              title="افزودن محتوای آموزشی جدید",
                              categories=categories)
    elif action == 'edit' and content_id:
        content = EducationalContent.query.get_or_404(int(content_id))
        categories = EducationalCategory.query.all()
        return render_template('admin/educational_form.html',
                              title="ویرایش محتوای آموزشی",
                              content=content,
                              categories=categories)
    elif action == 'media' and content_id:
        content = EducationalContent.query.get_or_404(int(content_id))
        media = EducationalContentMedia.query.filter_by(content_id=content.id).all()
        return render_template('admin/educational_media.html',
                              content=content,
                              media=media,
                              active_page='educational')
    
    contents = EducationalContent.query.all()
    categories = EducationalCategory.query.all()
    for content in contents:
        content.formatted_photo_url = get_photo_url(content.photo_url)
    return render_template('admin/educational.html',
                          contents=contents,
                          categories=categories,
                          active_page='educational')

# ----- Inquiry Routes -----

@app.route('/inquiry', methods=['GET', 'POST'])
def inquiry():
    """فرم ارسال استعلام"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        product_id = request.form.get('product_id')
        service_id = request.form.get('service_id')
        
        try:
            inquiry = Inquiry(
                name=name,
                email=email,
                phone=phone,
                message=message,
                product_id=int(product_id) if product_id else None,
                service_id=int(service_id) if service_id else None,
                status='pending'
            )
            db.session.add(inquiry)
            db.session.commit()
            flash('استعلام با موفقیت ثبت شد.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving inquiry: {str(e)}")
            flash(f'خطا در ثبت استعلام: {str(e)}', 'danger')
    
    return render_template('inquiry.html')

@app.route('/admin/inquiries', methods=['GET', 'POST'])
@login_required
def admin_inquiries():
    """پنل مدیریت - استعلام‌ها"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز.', 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        action = request.form.get('action')
        inquiry_id = request.form.get('inquiry_id')
        
        if not inquiry_id:
            flash('شناسه استعلام الزامی است.', 'danger')
            return redirect(url_for('admin_inquiries'))
            
        inquiry = Inquiry.query.get_or_404(int(inquiry_id))
        
        if action == 'update_status':
            status = request.form.get('status')
            if status in ['pending', 'in_progress', 'completed', 'rejected']:
                inquiry.status = status
                db.session.commit()
                flash(f'وضعیت استعلام به "{status}" تغییر کرد.', 'success')
            else:
                flash('وضعیت نامعتبر.', 'danger')
                
        elif action == 'delete':
            db.session.delete(inquiry)
            db.session.commit()
            flash('استعلام حذف شد.', 'success')
            
        return redirect(url_for('admin_inquiries'))
    
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    return render_template('admin/inquiries.html',
                          inquiries=inquiries,
                          active_page='inquiries')

# ----- Static Content Routes -----

@app.route('/admin/static_content', methods=['GET', 'POST'])
@login_required
def admin_static_content():
    """مدیریت محتوای ثابت"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز.', 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        content_type = request.form.get('content_type')
        content = request.form.get('content')
        
        if not content_type or not content:
            flash('نوع محتوا و متن الزامی هستند.', 'danger')
            return redirect(url_for('admin/static_content'))
        
        static_content = StaticContent.query.filter_by(content_type=content_type).first()
        if static_content:
            static_content.content = content
            flash(f'محتوای "{content_type}" به‌روزرسانی شد.', 'success')
        else:
            static_content = StaticContent(content_type=content_type, content=content)
            db.session.add(static_content)
            flash(f'محتوای "{content_type}" ایجاد شد.', 'success')
        
        db.session.commit()
        return redirect(url_for('admin/static_content'))
    
    contents = StaticContent.query.all()
    return render_template('admin/static_content.html',
                          contents=contents,
                          active_page='static_content')

# ----- File Serving Routes -----

@app.route('/media/<path:filename>')
def serve_media(filename):
    """ارائه فایل‌های رسانه‌ای"""
    try:
        return send_from_directory('static/uploads', filename)
    except Exception as e:
        logger.error(f"Error serving media file {filename}: {str(e)}")
        return jsonify({'error': 'File not found'}), 404

# ----- Error Handlers -----

@app.errorhandler(404)
def page_not_found(e):
    """مدیریت خطای 404"""
    logger.warning(f"404 error: {request.url}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """مدیریت خطای 500"""
    logger.error(f"500 error: {str(e)}")
    return render_template('500.html'), 500