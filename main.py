"""
مسیرهای وب فلسک
این فایل شامل تمام مسیرها و نقاط پایانی وب است.
"""

import os
import io
import logging
import datetime
import csv
import zipfile
import tempfile
from sqlalchemy.orm import joinedload
from flask import (render_template, request, redirect, url_for, flash, session,
                   Response, send_file, jsonify, send_from_directory)
import time
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import inspect, text
import shutil
from app import app
from extensions import db
from utils_upload import media_files, handle_media_upload, remove_file, serve_file
from models import (User, Product, ProductMedia, Service, ServiceMedia,
                    Inquiry, EducationalContent, StaticContent,
                    EducationalCategory, EducationalContentMedia,
                    ProductCategory, ServiceCategory)
from flask_wtf.csrf import CSRFProtect
# تنظیم لاگر
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# تنظیم لاگر برای ذخیره لاگ‌ها در فایل
file_handler = logging.FileHandler('logs/rfcbot.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# ایجاد دایرکتوری logs اگر وجود ندارد
os.makedirs('logs', exist_ok=True)

app.config['SECRET_KEY'] = 'your-secret-key'  # یا از متغیر محیطی
csrf = CSRFProtect(app)
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
    """Main page of the application"""
    try:
        # Fetch featured products and services
        products = Product.query.filter_by(featured=True).limit(6).all() or []
        services = Service.query.filter_by(featured=True).limit(6).all() or []

        # Fetch recent educational content
        try:
            educational = EducationalContent.query.order_by(
                EducationalContent.created_at.desc()).limit(3).all() or []
        except Exception as e:
            logger.warning(f"Error loading educational content: {str(e)}")
            educational = []

        # Fetch 'about' static content
        try:
            about_content = StaticContent.query.filter_by(
                content_type='about').first()
            about = about_content.content if about_content else "No about content available"
        except Exception as e:
            logger.warning(f"Error loading about content: {str(e)}")
            about = "Error loading about content"

        # Check bot status from log file
        def check_bot_status():
            """Check bot status by analyzing recent log entries"""
            try:
                if os.path.exists('bot.log'):
                    with open('bot.log', 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        recent_lines = lines[-15:]  # Check last 15 lines
                        for line in reversed(recent_lines):
                            if 'Run polling for bot' in line or 'Start polling' in line:
                                return 'running'
                            if 'ERROR' in line or 'CRITICAL' in line:
                                return 'error'
                return 'stopped'
            except Exception as e:
                logger.warning(f"Error checking bot status: {str(e)}")
                return 'unknown'

        bot_status = check_bot_status()

        # Prepare environment variables status
        env_status = {
            'BOT_TOKEN': 'Set' if os.environ.get('BOT_TOKEN') else 'Not Set',
            'DATABASE_URL':
            'Set' if os.environ.get('DATABASE_URL') else 'Not Set',
            'ADMIN_ID': 'Set' if os.environ.get('ADMIN_ID') else 'Not Set'
        }

        # Fetch recent bot logs
        try:
            log_file = 'bot.log'
            bot_logs = ['Log file not found.']
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    bot_logs = lines[-50:] if len(lines) > 50 else lines
        except Exception as e:
            logger.warning(f"Error reading log file: {str(e)}")
            bot_logs = [f"Error reading log file: {str(e)}"]

        # Render the template with all data
        return render_template(
            'index.html',
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
        logger.error(f"Error in index route: {str(e)}")
        # Fallback values in case of error
        env_status = {
            'BOT_TOKEN': 'Set' if os.environ.get('BOT_TOKEN') else 'Not Set',
            'DATABASE_URL':
            'Set' if os.environ.get('DATABASE_URL') else 'Not Set',
            'ADMIN_ID': 'Set' if os.environ.get('ADMIN_ID') else 'Not Set'
        }
        return render_template(
            'index.html',
            products=[],
            services=[],
            educational=[],
            about_text="Error loading content",
            bot_status='error',
            env_status=env_status,
            bot_logs=['Error loading logs'],
            last_run=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            datetime=datetime)


@app.route('/logs')
@login_required
def logs():
    """دریافت لاگ‌های ربات"""
    import os
    try:
        # تلاش برای خواندن آخرین خطوط فایل لاگ
        log_file = 'bot.log'
        max_lines = 500  # حداکثر تعداد خطوط برای نمایش

        # برای درخواست‌های AJAX، پاسخ JSON برگردان
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        # خواندن آخرین خطوط
                        all_lines = f.readlines()
                        lines = all_lines[-max_lines:] if len(
                            all_lines) > max_lines else all_lines
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
        from configuration import load_config
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
    # بررسی دسترسی ادمین
    if not current_user.is_admin:
        logger.warning(
            f"Non-admin user {current_user.id} attempted to delete media")
        return jsonify({'success': False, 'error': 'دسترسی مجاز نیست'}), 403

    try:
        # دریافت پارامترها
        content_type = request.args.get('type')
        content_id = request.args.get('content_id')
        media_id = request.args.get('media_id')

        # اعتبارسنجی پارامترها
        if not all([content_type, content_id, media_id]):
            logger.error(
                f"Missing parameters in delete_media request: {request.args}")
            return jsonify({'success': False, 'error': 'پارامترهای ناقص'}), 400

        content_id = int(content_id)
        media_id = int(media_id)

        # تعریف مپینگ برای مدل‌ها و مسیرهای ذخیره‌سازی
        media_config = {
            'product': {
                'model': ProductMedia,
                'id_field': 'product_id',
                'upload_dir': os.path.join('static', 'uploads', 'products')
            },
            'service': {
                'model': ServiceMedia,
                'id_field': 'service_id',
                'upload_dir': os.path.join('static', 'uploads', 'services')
            },
            'educational': {
                'model': EducationalContentMedia,
                'id_field': 'educational_id',
                'upload_dir': os.path.join('static', 'uploads', 'educationals')
            }
        }

        # بررسی نوع محتوا
        if content_type not in media_config:
            logger.error(
                f"Invalid content type in delete_media request: {content_type}"
            )
            return jsonify({
                'success': False,
                'error': 'نوع محتوا نامعتبر است'
            }), 400

        # دریافت مدل و اطلاعات مربوطه
        config = media_config[content_type]
        MediaModel = config['model']
        id_field = config['id_field']
        upload_dir = config['upload_dir']

        # یافتن رسانه
        media = MediaModel.query.get(media_id)
        if not media or getattr(media, id_field) != content_id:
            logger.warning(
                f"{content_type.capitalize()} media not found or mismatch: media_id={media_id}, {id_field}={content_id}"
            )
            return jsonify({
                'success': False,
                'error': f'رسانه {content_type} یافت نشد'
            }), 404

        # تعیین مسیر فایل لوکال
        file_path = media.local_path if hasattr(
            media, 'local_path') and media.local_path else None
        if not file_path and media.file_id:
            # اگر local_path وجود ندارد، مسیر را از file_id بسازیم
            file_name = media.file_id.split('_')[
                -1]  # فرض: file_id شامل نام فایل است
            file_path = os.path.join(upload_dir, file_name)

        # حذف فایل لوکال (در صورت وجود)
        delete_result = delete_media_file(file_path) if file_path else False

        # حذف رسانه از دیتابیس
        db.session.delete(media)
        db.session.commit()

        logger.info(
            f"{content_type.capitalize()} media deleted: id={media_id}, {id_field}={content_id}, file_path={file_path}"
        )
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error in delete_media: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ----- Admin Dashboard Routes -----


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
        recent_inquiries = Inquiry.query.order_by(
            Inquiry.created_at.desc()).limit(5).all()

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
        return render_template('error.html',
                               error=str(e),
                               traceback=traceback.format_exc())


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


# ----- Product Management Routes -----


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    media = ProductMedia.query.filter_by(product_id=product_id).all()
    related_products = Product.query.filter(
        Product.id != product_id,
        Product.category_id == product.category_id).limit(4).all()
    return render_template('product_detail.html',
                           product=product,
                           media=media,
                           related_products=related_products)


@app.route('/admin/products', methods=['GET', 'POST'])
@login_required
def admin_products():
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز.', 'danger')
        return redirect(url_for('index'))

    action = request.args.get('action')
    product_id = request.args.get('id')

    # Handle POST requests
    if request.method == 'POST':
        if action == 'delete':
            product_id = request.form.get('product_id')
            if not product_id:
                flash('شناسه محصول الزامی است.', 'danger')
                return redirect(url_for('admin_products'))
            try:
                product = Product.query.get_or_404(int(product_id))
                media_files = ProductMedia.query.filter_by(
                    product_id=product.id).all()
                for media in media_files:
                    if media.local_path:
                        delete_media_file(media.local_path)
                    db.session.delete(media)
                db.session.delete(product)
                db.session.commit()
                flash(f'محصول "{product.name}" با موفقیت حذف شد.', 'success')
                logger.info(f"حذف محصول: ID={product_id}, نام={product.name}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"خطا در حذف محصول: {str(e)}")
                flash(f'خطا در حذف محصول: {str(e)}', 'danger')
            return redirect(url_for('admin_products'))

        elif action == 'upload_media':
            product_id = request.form.get('product_id')
            if not product_id:
                flash('شناسه محصول الزامی است.', 'danger')
                return redirect(url_for('admin_products'))
            product = Product.query.get_or_404(int(product_id))
            files = request.files.getlist('file')
            file_type = request.form.get('file_type', 'photo')
            if not files or all(not f.filename for f in files):
                flash('لطفاً حداقل یک فایل انتخاب کنید.', 'warning')
                return redirect(
                    url_for('admin_products', action='media', id=product_id))
            try:
                upload_dir = os.path.join('static', 'uploads', 'products',
                                          str(product.id))
                for file in files:
                    if file.filename:
                        success, file_path = handle_media_upload(
                            file=file,
                            directory=upload_dir,
                            file_type=file_type)
                        if success and file_path:
                            relative_path = file_path.replace('static/', '', 1)
                            media = ProductMedia(product_id=product.id,
                                                 file_id=relative_path,
                                                 file_type=file_type,
                                                 local_path=file_path)
                            db.session.add(media)
                        else:
                            flash(f'آپلود فایل {file.filename} ناموفق بود.',
                                  'danger')
                db.session.commit()
                flash('رسانه‌ها با موفقیت آپلود شدند.', 'success')
                logger.info(f"رسانه‌ها آپلود شدند برای محصول {product_id}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"خطا در آپلود رسانه: {str(e)}")
                flash(f'خطا در آپلود رسانه: {str(e)}', 'danger')
            return redirect(
                url_for('admin_products', action='media', id=product_id))

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
            errors = []
            if not name:
                errors.append('نام محصول الزامی است.')
            try:
                price = int(price) if price else 0
                if price < 0:
                    errors.append('قیمت نمی‌تواند منفی باشد.')
            except ValueError:
                errors.append('قیمت باید یک عدد معتبر باشد.')
            if errors:
                for error in errors:
                    flash(error, 'danger')
                categories = ProductCategory.query.all()
                return render_template(
                    'admin/product_form.html',
                    title="ویرایش محصول"
                    if product_id else "افزودن محصول جدید",
                    product=Product.query.get(int(product_id))
                    if product_id else None,
                    categories=categories)
            try:
                category_id = int(category_id) if category_id else None
                if not category_id:
                    default_category = ProductCategory.query.first()
                    if default_category:
                        category_id = default_category.id
                    else:
                        new_category = ProductCategory(
                            name="دسته‌بندی پیش‌فرض محصولات")
                        db.session.add(new_category)
                        db.session.flush()
                        category_id = new_category.id
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
                    flash('محصول با موفقیت به‌روزرسانی شد.', 'success')
                else:
                    product = Product(name=name,
                                      price=price,
                                      description=description,
                                      category_id=category_id,
                                      brand=brand,
                                      model=model,
                                      in_stock=in_stock,
                                      tags=tags,
                                      featured=featured,
                                      model_number=model_number,
                                      manufacturer=manufacturer)
                    db.session.add(product)
                    db.session.flush()
                db.session.commit()
                return redirect(url_for('admin_products'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"خطا در ذخیره محصول: {str(e)}")
                flash(f'خطا در ذخیره محصول: {str(e)}', 'danger')
                categories = ProductCategory.query.all()
                return render_template(
                    'admin/product_form.html',
                    title="ویرایش محصول"
                    if product_id else "افزودن محصول جدید",
                    product=Product.query.get(int(product_id))
                    if product_id else None,
                    categories=categories)
        elif action == 'delete_media':
            media_id = request.form.get('media_id')
            product_id = request.form.get('product_id')
            if not media_id or not product_id:
                flash('شناسه رسانه و محصول الزامی است.', 'danger')
                return redirect(url_for('admin_products'))
            try:
                media = ProductMedia.query.get(int(media_id))
                if media and media.product_id == int(product_id):
                    if media.local_path:
                        delete_media_file(media.local_path)
                    db.session.delete(media)
                    db.session.commit()
                    flash('رسانه با موفقیت حذف شد.', 'success')
                else:
                    flash('رسانه یافت نشد.', 'warning')
            except Exception as e:
                db.session.rollback()
                logger.error(f"خطا در حذف رسانه: {str(e)}")
                flash(f'خطا در حذف رسانه: {str(e)}', 'danger')
            return redirect(
                url_for('admin_products', action='media', id=product_id))

    # Handle GET requests
    categories = ProductCategory.query.all()
    if action == 'add':
        return render_template('admin/product_form.html',
                               title="افزودن محصول جدید",
                               categories=categories)
    elif action == 'edit' and product_id:
        product = Product.query.get_or_404(int(product_id))
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

    # Display product list with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_query = request.args.get('search')
    category_filter = request.args.get('category_id')
    query = Product.query.options(joinedload(Product.category))
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))
    if category_filter:
        query = query.filter(Product.category_id == category_filter)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    # Add main photo for each product and log for debugging
    for product in products:
        main_media = product.media.filter_by(file_type='photo').first()
        product.main_photo = main_media.file_id if main_media else None
        logger.info(
            f"Product {product.id}: category_id={product.category_id}, category={product.category}, category_name={product.category.name if product.category else 'None'}"
        )

    return render_template('admin/products.html',
                           products=products,
                           categories=categories,
                           pagination=pagination,
                           search_query=search_query,
                           category_filter=category_filter)


# ----- Category Management Routes -----
def build_category_tree(categories):
    """
    ساخت ساختار درختی از دسته‌بندی‌ها
    
    Args:
        categories: لیست اشیاء دسته‌بندی (مانند ProductCategory، ServiceCategory یا EducationalCategory)
                   که هر کدام دارای ویژگی‌های id، name، parent_id هستند
    
    Returns:
        لیست اشیاء درختی که هر کدام شامل name و children (لیست زیردسته‌ها) هستند
    """
    # دیکشنری برای ذخیره گره‌های درختی
    tree_dict = {}
    # لیست نهایی برای دسته‌بندی‌های ریشه (بدون والد)
    tree = []

    # ایجاد گره‌ها برای هر دسته‌بندی
    for category in categories:
        tree_dict[category.id] = {
            'id': category.id,
            'name': category.name,
            'children': []
        }

    # اتصال فرزندان به والدین
    for category in categories:
        if category.parent_id:
            # اگر دسته‌بندی والد دارد، آن را به لیست فرزندان والد اضافه کن
            if category.parent_id in tree_dict:
                tree_dict[category.parent_id]['children'].append(tree_dict[category.id])
        else:
            # اگر والد ندارد، به لیست ریشه اضافه کن
            tree.append(tree_dict[category.id])

    return tree

def get_all_subcategories(category_model,
                          category_id,
                          subcategories=None,
                          visited=None):
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
        get_all_subcategories(category_model, category.id, subcategories,
                              visited)

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
    category_ids = [category_id] + get_all_subcategories(
        category_model, category_id)
    count = model.query.filter(model.category_id.in_(category_ids)).update(
        {model.category_id: None})
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

        return render_template('admin_categories.html',
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
        return render_template('admin_categories.html',
                               product_categories=[],
                               service_categories=[],
                               educational_categories=[],
                               product_tree=[],
                               service_tree=[],
                               educational_tree=[],
                               active_page='categories')


# Products Category Management
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

        subcategories_count = unlink_subcategories(ProductCategory,
                                                   category_id)
        products_count = unlink_objects(Product, ProductCategory, category_id)
        db.session.delete(category)
        db.session.commit()
        flash(
            f'دسته‌بندی محصول "{name}" با موفقیت حذف شد. '
            f'{subcategories_count} زیردسته و {products_count} محصول بدون دسته‌بندی شدند.',
            'success')
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

        subcategories_count = unlink_subcategories(ServiceCategory,
                                                   category_id)
        services_count = unlink_objects(Service, ServiceCategory, category_id)
        db.session.delete(category)
        db.session.commit()
        flash(
            f'دسته‌بندی خدمات "{name}" با موفقیت حذف شد. '
            f'{subcategories_count} زیردسته و {services_count} خدمت بدون دسته‌بندی شدند.',
            'success')
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

        subcategories_count = unlink_subcategories(EducationalCategory,
                                                   category_id)
        contents_count = unlink_objects(EducationalContent,
                                        EducationalCategory, category_id)
        db.session.delete(category)
        db.session.commit()
        flash(
            f'دسته‌بندی آموزشی "{name}" با موفقیت حذف شد. '
            f'{subcategories_count} زیردسته و {contents_count} محتوای آموزشی بدون دسته شدند.',
            'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting educational category: {str(e)}")
        flash(f'خطا در حذف دسته‌بندی آموزشی: {str(e)}', 'danger')

    return redirect(url_for('admin_categories'))


# ----- Service Routes -----


@app.route('/service/<int:service_id>')
def service_detail(service_id):
    service = Service.query.get_or_404(service_id)
    media = ServiceMedia.query.filter_by(service_id=service_id).all()
    related_services = Service.query.filter(
        Service.id != service_id,
        Service.category_id == service.category_id).limit(4).all()
    return render_template('service_detail.html',
                           service=service,
                           media=media,
                           related_services=related_services)

@app.route('/admin/services', methods=['GET', 'POST'])
@login_required
def admin_services():
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز.', 'danger')
        return redirect(url_for('index'))

    action = request.args.get('action')
    service_id = request.args.get('id')

    # Handle POST requests
    if request.method == 'POST':
        if action == 'delete':
            service_id = request.form.get('service_id')
            if not service_id:
                flash('شناسه خدمت الزامی است.', 'danger')
                return redirect(url_for('admin_services'))
            try:
                service = Service.query.get_or_404(int(service_id))
                media_files = ServiceMedia.query.filter_by(
                    service_id=service.id).all()
                for media in media_files:
                    if media.local_path:
                        delete_media_file(media.local_path)
                    db.session.delete(media)
                db.session.delete(service)
                db.session.commit()
                flash(f'خدمت "{service.name}" با موفقیت حذف شد.', 'success')
                logger.info(f"حذف خدمت: ID={service_id}, نام={service.name}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"خطا در حذف خدمت: {str(e)}")
                flash(f'خطا در حذف خدمت: {str(e)}', 'danger')
            return redirect(url_for('admin_services'))

        elif action == 'upload_media':
            service_id = request.form.get('service_id')
            if not service_id:
                flash('شناسه خدمت الزامی است.', 'danger')
                return redirect(url_for('admin_services'))
            service = Service.query.get_or_404(int(service_id))
            files = request.files.getlist('file')
            file_type = request.form.get('file_type', 'photo')
            if not files or all(not f.filename for f in files):
                flash('لطفاً حداقل یک فایل انتخاب کنید.', 'warning')
                return redirect(
                    url_for('admin_services', action='media', id=service_id))
            try:
                upload_dir = os.path.join('static', 'uploads', 'services',
                                          str(service.id))
                for file in files:
                    if file.filename:
                        success, file_path = handle_media_upload(
                            file=file,
                            directory=upload_dir,
                            file_type=file_type)
                        if success and file_path:
                            relative_path = file_path.replace('static/', '', 1)
                            media = ServiceMedia(service_id=service.id,
                                                 file_id=relative_path,
                                                 file_type=file_type,
                                                 local_path=file_path)
                            db.session.add(media)
                        else:
                            flash(f'آپلود فایل {file.filename} ناموفق بود.',
                                  'danger')
                db.session.commit()
                flash('رسانه‌ها با موفقیت آپلود شدند.', 'success')
                logger.info(f"رسانه‌ها آپلود شدند برای خدمت {service_id}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"خطا در آپلود رسانه: {str(e)}")
                flash(f'خطا در آپلود رسانه: {str(e)}', 'danger')
            return redirect(
                url_for('admin_services', action='media', id=service_id))

        elif action == 'save':
            service_id = request.form.get('id')
            name = request.form.get('name')
            price = request.form.get('price', '0')
            description = request.form.get('description', '')
            category_id = request.form.get('category_id')
            available = 'available' in request.form
            tags = request.form.get('tags', '')
            featured = 'featured' in request.form
            errors = []
            if not name:
                errors.append('نام خدمت الزامی است.')
            try:
                price = int(price) if price else 0
                if price < 0:
                    errors.append('قیمت نمی‌تواند منفی باشد.')
            except ValueError:
                errors.append('قیمت باید یک عدد معتبر باشد.')
            if errors:
                for error in errors:
                    flash(error, 'danger')
                categories = ServiceCategory.query.all()
                return render_template(
                    'admin/service_form.html',
                    title="ویرایش خدمت"
                    if service_id else "افزودن خدمت جدید",
                    service=Service.query.get(int(service_id))
                    if service_id else None,
                    categories=categories)
            try:
                category_id = int(category_id) if category_id else None
                if not category_id:
                    default_category = ServiceCategory.query.first()
                    if default_category:
                        category_id = default_category.id
                    else:
                        new_category = ServiceCategory(
                            name="دسته‌بندی پیش‌فرض خدمات")
                        db.session.add(new_category)
                        db.session.flush()
                        category_id = new_category.id
                if service_id:
                    service = Service.query.get_or_404(int(service_id))
                    service.name = name
                    service.price = price
                    service.description = description
                    service.category_id = category_id
                    service.available = available
                    service.tags = tags
                    service.featured = featured
                    flash('خدمت با موفقیت به‌روزرسانی شد.', 'success')
                else:
                    service = Service(name=name,
                                      price=price,
                                      description=description,
                                      category_id=category_id,
                                      available=available,
                                      tags=tags,
                                      featured=featured)
                    db.session.add(service)
                    db.session.flush()
                db.session.commit()
                return redirect(url_for('admin_services'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"خطا در ذخیره خدمت: {str(e)}")
                flash(f'خطا در ذخیره خدمت: {str(e)}', 'danger')
                categories = ServiceCategory.query.all()
                return render_template(
                    'admin/service_form.html',
                    title="ویرایش خدمت"
                    if service_id else "افزودن خدمت جدید",
                    service=Service.query.get(int(service_id))
                    if service_id else None,
                    categories=categories)
        elif action == 'delete_media':
            media_id = request.form.get('media_id')
            service_id = request.form.get('service_id')
            if not media_id or not service_id:
                flash('شناسه رسانه و خدمت الزامی است.', 'danger')
                return redirect(url_for('admin_services'))
            try:
                media = ServiceMedia.query.get(int(media_id))
                if media and media.service_id == int(service_id):
                    if media.local_path:
                        delete_media_file(media.local_path)
                    db.session.delete(media)
                    db.session.commit()
                    flash('رسانه با موفقیت حذف شد.', 'success')
                else:
                    flash('رسانه یافت نشد.', 'warning')
            except Exception as e:
                db.session.rollback()
                logger.error(f"خطا در حذف رسانه: {str(e)}")
                flash(f'خطا در حذف رسانه: {str(e)}', 'danger')
            return redirect(
                url_for('admin_services', action='media', id=service_id))

    # Handle GET requests
    categories = ServiceCategory.query.all()
    if action == 'add':
        return render_template('admin/service_form.html',
                               title="افزودن خدمت جدید",
                               categories=categories)
    elif action == 'edit' and service_id:
        service = Service.query.get_or_404(int(service_id))
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

    # Display service list with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_query = request.args.get('search')
    category_filter = request.args.get('category_id')
    query = Service.query.options(joinedload(Service.category))
    if search_query:
        query = query.filter(Service.name.ilike(f'%{search_query}%'))
    if category_filter:
        query = query.filter(Service.category_id == category_filter)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    services = pagination.items

    # Add main photo for each service and log for debugging
    for service in services:
        main_media = service.media.filter_by(file_type='photo').first()
        service.main_photo = main_media.file_id if main_media else None
        logger.info(
            f"Service {service.id}: category_id={service.category_id}, category={service.category}, category_name={service.category.name if service.category else 'None'}"
        )

    return render_template('admin/services.html',
                           services=services,
                           categories=categories,
                           pagination=pagination,
                           search_query=search_query,
                           category_filter=category_filter)

# ----- Educational Content Routes -----


@app.route('/educational/<int:content_id>')
def educational_detail(content_id):
    """صفحه جزئیات محتوای آموزشی"""
    content = EducationalContent.query.get_or_404(content_id)
    media = EducationalContentMedia.query.filter_by(
        content_id=content.id).all()
    related_content = EducationalContent.query.filter_by(
        category_id=content.category_id).filter(
            EducationalContent.id != content_id).limit(4).all()

    # دریافت تصویر اصلی از EducationalContentMedia
    main_photo = EducationalContentMedia.query.filter_by(
        content_id=content.id, file_type='photo').first()
    photo_url = get_photo_url(main_photo.file_id) if main_photo else None

    for related in related_content:
        media = EducationalContentMedia.query.filter_by(
            content_id=related.id, file_type='photo').first()
        related.formatted_photo_url = get_photo_url(
            media.file_id) if media else None

    return render_template('educational_detail.html',
                           content=content,
                           photo_url=photo_url,
                           media=media,
                           related_content=related_content)


@app.route('/admin/education', methods=['GET', 'POST'])
@login_required
def admin_education():
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
                return redirect(url_for('admin_education'))

            content = EducationalContent.query.get_or_404(int(content_id))
            media_files = EducationalContentMedia.query.filter_by(
                content_id=content.id).all()
            for media in media_files:
                if media.file_id and not media.file_id.startswith('http'):
                    file_path = os.path.join('static', media.file_id)
                    delete_media_file(file_path)

            db.session.delete(content)
            db.session.commit()
            flash(f'محتوای آموزشی "{content.title}" با موفقیت حذف شد.',
                  'success')
            return redirect(
                url_for('admin_education'))  # اصلاح به admin_education

        elif action == 'save':
            content_id = request.form.get('id')
            title = request.form.get('title')
            content_text = request.form.get('content')
            category_id = request.form.get('category_id')
            new_category = request.form.get(
                'new_category')  # دریافت نام دسته‌بندی جدید
            tags = request.form.get('tags', '')
            featured = 'featured' in request.form

            try:
                # بررسی اینکه آیا دسته‌بندی جدید انتخاب شده است
                if category_id == 'new_category':
                    if not new_category:
                        flash('لطفاً نام دسته‌بندی جدید را وارد کنید.',
                              'danger')
                        categories = EducationalCategory.query.all()
                        content = EducationalContent.query.get(
                            int(content_id)) if content_id else None
                        return render_template(
                            'admin/education_form.html',
                            title="ویرایش محتوای آموزشی"
                            if content_id else "افزودن محتوای آموزشی جدید",
                            educational_content=content,
                            categories=categories)
                    # ایجاد دسته‌بندی جدید
                    new_category_obj = EducationalCategory(name=new_category)
                    db.session.add(new_category_obj)
                    db.session.flush()  # برای دریافت ID دسته‌بندی جدید
                    category_id = new_category_obj.id
                    logger.info(
                        f"Created new category: {new_category} with ID: {category_id}"
                    )
                else:
                    category_id = int(category_id) if category_id else None

                # اگر category_id همچنان None باشد، دسته‌بندی پیش‌فرض را ایجاد یا انتخاب کنید
                if category_id is None:
                    default_category = EducationalCategory.query.first()
                    if default_category:
                        category_id = default_category.id
                    else:
                        new_category = EducationalCategory(
                            name="دسته آموزشی پیش‌فرض")
                        db.session.add(new_category)
                        db.session.flush()
                        category_id = new_category.id
                        logger.info(
                            f"Created default educational category ID: {category_id}"
                        )

                # ادامه فرآیند ذخیره محتوا
                if content_id:
                    content = EducationalContent.query.get_or_404(
                        int(content_id))
                    content.title = title
                    content.content = content_text
                    content.category_id = category_id
                    content.tags = tags
                    content.featured = featured
                    flash('محتوای آموزشی به‌روزرسانی شد.', 'success')
                else:
                    content = EducationalContent(title=title,
                                                 content=content_text,
                                                 category_id=category_id,
                                                 tags=tags,
                                                 featured=featured)
                    db.session.add(content)
                    db.session.commit()  # Commit برای دریافت content.id
                    logger.info(
                        f"New content created with ID: {content.id}, Title: {content.title}"
                    )

                # آپلود رسانه جدید
                file = request.files.get('file')
                file_type = request.form.get('file_type', 'photo')
                if file and file.filename:
                    try:
                        upload_dir = os.path.join('static',
                                                  'uploads', 'educational',
                                                  str(content.id))
                        success, file_path = handle_media_upload(
                            file=file,
                            directory=upload_dir,
                            file_type=file_type,
                            custom_filename=None)
                        if success:
                            relative_path = file_path.replace(
                                'static/', '', 1) if file_path.startswith(
                                    'static/') else file_path
                            media = EducationalContentMedia(
                                content_id=content.id,
                                file_id=relative_path,
                                file_type=file_type,
                                local_path=file_path)
                            db.session.add(media)
                            db.session.commit()
                            flash('رسانه با موفقیت آپلود شد.', 'success')
                            logger.info(
                                f"Media uploaded for content: {file_path}")
                        else:
                            flash('خطا در آپلود فایل.', 'danger')
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Error uploading media: {str(e)}")
                        flash(f'خطا در آپلود رسانه: {str(e)}', 'danger')

                db.session.commit()

            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving educational content: {str(e)}")
                flash(f'خطا در ذخیره محتوای آموزشی: {str(e)}', 'danger')
                categories = EducationalCategory.query.all()
                content = EducationalContent.query.get(
                    int(content_id)) if content_id else None
                return render_template(
                    'admin/education_form.html',
                    title="ویرایش محتوای آموزشی"
                    if content_id else "افزودن محتوای آموزشی جدید",
                    educational_content=content,
                    categories=categories)

            return redirect(url_for('admin_education'))
        elif action == 'upload_media':
            content_id = request.form.get('content_id')
            if not content_id:
                flash('شناسه محتوا الزامی است.', 'danger')
                return redirect(url_for('admin_education'))

            content = EducationalContent.query.get_or_404(int(content_id))
            file = request.files.get('file')
            file_type = request.form.get('file_type', 'photo')

            if file and file.filename:
                try:
                    upload_dir = os.path.join('static', 'uploads',
                                              'educational', str(content.id))
                    success, file_path = handle_media_upload(
                        file=file,
                        directory=upload_dir,
                        file_type=file_type,
                        custom_filename=None)
                    if success:
                        relative_path = file_path.replace(
                            'static/', '', 1) if file_path.startswith(
                                'static/') else file_path
                        media = EducationalContentMedia(content_id=content.id,
                                                        file_id=relative_path,
                                                        file_type=file_type,
                                                        local_path=file_path)
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

            return redirect(
                url_for('admin_education', action='media', id=content_id))

        elif action == 'delete_media':
            media_id = request.form.get('media_id')
            content_id = request.form.get('content_id')

            if not media_id or not content_id:
                flash('شناسه رسانه و محتوا الزامی است.', 'danger')
                return redirect(url_for('admin_education'))

            try:
                media = EducationalContentMedia.query.get(int(media_id))
                if media and media.content_id == int(content_id):
                    delete_media_file(media.local_path)
                    db.session.delete(media)
                    db.session.commit()
                    flash('رسانه با موفقیت حذف شد.', 'success')
                    logger.info(
                        f"Media deleted: id={media_id}, content_id={content_id}"
                    )
                else:
                    flash('رسانه یافت نشد.', 'warning')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error deleting media: {str(e)}")
                flash(f'خطا در حذف رسانه: {str(e)}', 'danger')

            return redirect(
                url_for('admin_education', action='media', id=content_id))

    if action == 'add':
        categories = EducationalCategory.query.all()
        return render_template('admin/education_form.html',
                               title="افزودن محتوای آموزشی جدید",
                               categories=categories)
    elif action == 'edit' and content_id:
        content = EducationalContent.query.get_or_404(int(content_id))
        categories = EducationalCategory.query.all()
        return render_template('admin/education_form.html',
                               title="ویرایش محتوای آموزشی",
                               educational_content=content,
                               categories=categories)
    elif action == 'media' and content_id:
        content = EducationalContent.query.get_or_404(int(content_id))
        media = EducationalContentMedia.query.filter_by(
            content_id=content.id).all()
        return render_template('admin/education_form.html',
                               educational_content=content,
                               media=media,
                               active_page='educational')

    # اطمینان از وجود دسته‌بندی پیش‌فرض
    if not EducationalCategory.query.first():
        new_category = EducationalCategory(name="دسته آموزشی پیش‌فرض")
        db.session.add(new_category)
        db.session.commit()
        logger.info("Created default educational category")

    # صفحه‌بندی
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = EducationalContent.query.paginate(page=page,
                                                   per_page=per_page,
                                                   error_out=False)
    contents = pagination.items
    categories = EducationalCategory.query.all()

    for content in contents:
        media = EducationalContentMedia.query.filter_by(
            content_id=content.id, file_type='photo').first()
        content.formatted_photo_url = get_photo_url(
            media.file_id) if media else None

    logger.info(f"Number of educational contents: {len(contents)}")

    return render_template('admin/education.html',
                           educational_content=contents,
                           categories=categories,
                           pagination=pagination,
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
                status='pending')
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


# ----- Database Management Routes -----


@app.route('/admin/database', methods=['GET'])
@login_required
def admin_database():
    """Display database management page for admins."""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز است.', 'danger')
        return redirect(url_for('index'))

    try:
        table_model_map = {
            'users': User,
            'products': Product,
            'services': Service,
            'inquiries': Inquiry,
            'educational_content': EducationalContent,
            'static_content': StaticContent,
            'product_categories': ProductCategory,
            'service_categories': ServiceCategory,
            'educational_categories': EducationalCategory,
            'product_media': ProductMedia,
            'educational_content_media': EducationalContentMedia
        }

        table_counts = {}
        for table_name, model in table_model_map.items():
            try:
                count = model.query.count()
                table_counts[table_name] = count
            except Exception as e:
                logger.warning(
                    f"Error counting records for table {table_name}: {str(e)}")
                table_counts[table_name] = 'Error'

        with db.engine.connect() as connection:
            pg_version = connection.execute(
                text("SELECT version();")).fetchone()[0]

        pg_host = os.environ.get('DATABASE_HOST', 'localhost')
        pg_database = os.environ.get('DATABASE_NAME', 'unknown')
        pg_user = os.environ.get('DATABASE_USER', 'unknown')

        inspector = inspect(db.engine)
        table_structures = {}
        for table_name in table_model_map.keys():
            try:
                columns = inspector.get_columns(table_name)
                table_structures[table_name] = columns
            except Exception as e:
                logger.warning(
                    f"Error fetching structure for table {table_name}: {str(e)}"
                )
                table_structures[table_name] = []

        return render_template('admin/database.html',
                               title='مدیریت دیتابیس',
                               table_counts=table_counts,
                               table_structures=table_structures,
                               pg_version=pg_version,
                               pg_host=pg_host,
                               pg_database=pg_database,
                               pg_user=pg_user,
                               active_page='database')
    except Exception as e:
        logger.error(f"Error loading admin_database: {str(e)}", exc_info=True)
        flash(f'خطا در بارگذاری صفحه مدیریت دیتابیس: {str(e)}', 'danger')
        return redirect(url_for('admin_index'))


@app.route('/admin/database/execute_sql', methods=['POST'])
@login_required
def execute_sql():
    """Execute a custom SQL query."""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز است.', 'danger')
        return redirect(url_for('index'))

    try:
        sql_query = request.form.get('sql_query')
        if not sql_query:
            flash('کوئری SQL خالی است.', 'danger')
            return redirect(url_for('admin_database'))

        sql_query = sql_query.strip().lower()
        if sql_query.startswith(
            ('drop ', 'alter ', 'truncate ', 'delete ', 'insert ', 'update ')):
            flash('کوئری‌های تغییر ساختار یا داده مجاز نیستند.', 'danger')
            return redirect(url_for('admin_database'))

        with db.engine.connect() as connection:
            result = connection.execute(text(sql_query))
            rows = result.fetchall()
            columns = result.keys() if rows else []

        results = [dict(zip(columns, row)) for row in rows] if rows else []
        flash(f'کوئری با موفقیت اجرا شد. تعداد ردیف‌ها: {len(results)}',
              'success')

        table_model_map = {
            'users': User,
            'products': Product,
            'services': Service,
            'inquiries': Inquiry,
            'educational_content': EducationalContent,
            'static_content': StaticContent,
            'product_categories': ProductCategory,
            'service_categories': ServiceCategory,
            'educational_categories': EducationalCategory,
            'product_media': ProductMedia,
            'educational_content_media': EducationalContentMedia
        }

        table_counts = {}
        for table_name, model in table_model_map.items():
            try:
                count = model.query.count()
                table_counts[table_name] = count
            except Exception as e:
                logger.warning(
                    f"Error counting records for table {table_name}: {str(e)}")
                table_counts[table_name] = 'Error'

        with db.engine.connect() as connection:
            pg_version = connection.execute(
                text("SELECT version();")).fetchone()[0]

        pg_host = os.environ.get('DATABASE_HOST', 'localhost')
        pg_database = os.environ.get('DATABASE_NAME', 'unknown')
        pg_user = os.environ.get('DATABASE_USER', 'unknown')

        inspector = inspect(db.engine)
        table_structures = {}
        for table_name in table_model_map.keys():
            try:
                columns = inspector.get_columns(table_name)
                table_structures[table_name] = columns
            except Exception as e:
                logger.warning(
                    f"Error fetching structure for table {table_name}: {str(e)}"
                )
                table_structures[table_name] = []

        return render_template('admin/database.html',
                               title='مدیریت دیتابیس',
                               table_counts=table_counts,
                               table_structures=table_structures,
                               pg_version=pg_version,
                               pg_host=pg_host,
                               pg_database=pg_database,
                               pg_user=pg_user,
                               sql_results=results,
                               sql_columns=columns,
                               active_page='database')
    except Exception as e:
        logger.error(f"Error executing SQL query: {str(e)}", exc_info=True)
        flash(f'خطا در اجرای کوئری: {str(e)}', 'danger')
        return redirect(url_for('admin_database'))


@app.route('/admin/database/fix/<string:table>', methods=['POST'])
@login_required
def admin_database_fix(table):
    """Fix issues in the specified table."""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز است.', 'danger')
        return redirect(url_for('index'))

    try:
        table_model_map = {
            'users': User,
            'products': Product,
            'services': Service,
            'inquiries': Inquiry,
            'educational_content': EducationalContent,
            'static_content': StaticContent,
            'product_categories': ProductCategory,
            'service_categories': ServiceCategory,
            'educational_categories': EducationalCategory,
            'product_media': ProductMedia,
            'educational_content_media': EducationalContentMedia
        }

        if table not in table_model_map:
            flash(f'جدول "{table}" نامعتبر است.', 'danger')
            return redirect(url_for('admin_database'))

        model = table_model_map[table]

        if table == 'inquiries':
            invalid_inquiries = model.query.filter(
                (model.product_id != None) &
                (model.product_id.notin_(db.session.query(Product.id)))).all()
            for inquiry in invalid_inquiries:
                inquiry.product_id = None
            db.session.commit()
            flash(f'جدول {table} اصلاح شد: ارجاعات نامعتبر اصلاح شدند.',
                  'success')
        else:
            flash(f'اصلاح برای جدول {table} پیاده‌سازی نشده است.', 'warning')

        return redirect(url_for('admin_database'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error fixing table {table}: {str(e)}", exc_info=True)
        flash(f'خطا در اصلاح جدول: {str(e)}', 'danger')
        return redirect(url_for('admin_database'))


@app.route('/admin/database/view/<string:table>', methods=['GET'])
@login_required
def admin_view_table(table):
    """View table data in the database."""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز است.', 'danger')
        return redirect(url_for('index'))

    try:
        table_model_map = {
            'users': User,
            'products': Product,
            'services': Service,
            'inquiries': Inquiry,
            'educational_content': EducationalContent,
            'static_content': StaticContent,
            'product_categories': ProductCategory,
            'service_categories': ServiceCategory,
            'educational_categories': EducationalCategory,
            'product_media': ProductMedia,
            'educational_content_media': EducationalContentMedia
        }

        if table not in table_model_map:
            flash(f'جدول "{table}" یافت نشد.', 'danger')
            return redirect(url_for('admin_database'))

        model = table_model_map[table]

        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table)]

        per_page = int(request.args.get('per_page', 10))
        page = int(request.args.get('page', 1))
        if per_page not in [10, 20, 50, 100]:
            per_page = 10

        total_records = model.query.count()
        total_pages = max(1, (total_records + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))

        query = model.query.offset((page - 1) * per_page).limit(per_page)
        data = query.all()

        rows = []
        for row in data:
            row_data = []
            for column in columns:
                value = getattr(row, column, None)
                row_data.append(value)
            rows.append(row_data)

        def url_for_page(p):
            return url_for('admin_view_table',
                           table=table,
                           page=p,
                           per_page=per_page)

        return render_template('view_table.html',
                               title=f'مشاهده جدول {table}',
                               table_name=table,
                               columns=columns,
                               rows=rows,
                               total_records=total_records,
                               total_pages=total_pages,
                               page=page,
                               url_for_page=url_for_page,
                               active_page='database')
    except Exception as e:
        logger.error(f"Error loading table {table}: {str(e)}", exc_info=True)
        flash(f'خطا در بارگذاری داده‌های جدول: {str(e)}', 'danger')
        return redirect(url_for('admin_database'))


@app.route('/telegram/file/<string:file_id>')
@login_required
def telegram_file(file_id):
    """Serve or redirect to a Telegram file."""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز است.', 'danger')
        return redirect(url_for('index'))

    try:
        flash(
            f'فایل با شناسه {file_id} یافت نشد. لطفاً منطق بازیابی را پیاده‌سازی کنید.',
            'warning')
        return redirect(url_for('admin_database'))
    except Exception as e:
        logger.error(f"Error serving telegram file {file_id}: {str(e)}",
                     exc_info=True)
        flash(f'خطا در بارگذاری فایل: {str(e)}', 'danger')
        return redirect(url_for('admin_database'))


# ----- Static Content Routes -----
@app.route('/admin/content', methods=['GET', 'POST'])
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
            return redirect(url_for('admin_static_content'))

        try:
            static_content = StaticContent.query.filter_by(
                content_type=content_type).first()
            if static_content:
                static_content.content = content
                flash(f'محتوای "{content_type}" به‌روزرسانی شد.', 'success')
            else:
                static_content = StaticContent(content_type=content_type,
                                               content=content)
                db.session.add(static_content)
                flash(f'محتوای "{content_type}" ایجاد شد.', 'success')

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving static content: {str(e)}")
            flash(f'خطا در ذخیره محتوا: {str(e)}', 'danger')
            return redirect(url_for('admin_static_content'))

    # Fetch specific content for the template
    contact_content = StaticContent.query.filter_by(
        content_type='contact').first()
    about_content = StaticContent.query.filter_by(content_type='about').first()

    return render_template('admin_content.html',
                           contact_content=contact_content,
                           about_content=about_content,
                           active_page='content')


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


# ----- Control Bot Handlers -----
@app.route('/control/start', methods=['POST'])
@login_required
def control_start():
    """Start the Telegram bot"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز.', 'danger')
        return redirect(url_for('index'))

    try:
        # Placeholder for bot start logic
        # Example: Write to bot.log or trigger a bot process
        with open('bot.log', 'a', encoding='utf-8') as f:
            f.write(
                f"{datetime.datetime.now()}: Bot started by admin {current_user.username}\n"
            )
        logger.info(f"Bot started by admin {current_user.username}")
        flash('ربات با موفقیت راه‌اندازی شد.', 'success')
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        flash(f'خطا در راه‌اندازی ربات: {str(e)}', 'danger')

    return redirect(url_for('index'))


@app.route('/control/stop', methods=['POST'])
@login_required
def control_stop():
    """Stop the Telegram bot"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز.', 'danger')
        return redirect(url_for('index'))

    try:
        # Placeholder for bot stop logic
        # Example: Write to bot.log or terminate a bot process
        with open('bot.log', 'a', encoding='utf-8') as f:
            f.write(
                f"{datetime.datetime.now()}: Bot stopped by admin {current_user.username}\n"
            )
        logger.info(f"Bot stopped by admin {current_user.username}")
        flash('ربات با موفقیت متوقف شد.', 'success')
    except Exception as e:
        logger.error(f"Error stopping bot: {str(e)}")
        flash(f'خطا در توقف ربات: {str(e)}', 'danger')

    return redirect(url_for('index'))


# ----- Import Export Routes -----


@app.route('/admin/import_export')
@login_required
def admin_import_export():
    """Admin panel - Data import/export"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز.', 'danger')
        return redirect(url_for('index'))

    message = session.pop('import_export_message', None)
    return render_template('admin_import_export.html',
                           message=message,
                           active_page='import_export')


@app.route('/admin/export/<entity_type>')
@login_required
def export_entity(entity_type):
    """Export data to CSV format"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز.', 'danger')
        return redirect(url_for('index'))

    try:
        # Map entity types to models
        entity_map = {
            'products': Product,
            'services': Service,
            'inquiries': Inquiry,
            'educational': EducationalContent,
            'categories': {
                'product_categories': ProductCategory,
                'service_categories': ServiceCategory,
                'educational_categories': EducationalCategory
            }
        }

        # Handle category export separately
        if entity_type == 'categories':
            output = io.StringIO()
            writer = csv.writer(output)

            # Write headers for all category types
            headers = ['id', 'name', 'parent_id', 'category_type']
            writer.writerow(headers)

            # Export product categories
            for category in ProductCategory.query.all():
                writer.writerow([
                    category.id, category.name,
                    category.parent_id if category.parent_id else '', 'product'
                ])

            # Export service categories
            for category in ServiceCategory.query.all():
                writer.writerow([
                    category.id, category.name,
                    category.parent_id if category.parent_id else '', 'service'
                ])

            # Export educational categories
            for category in EducationalCategory.query.all():
                writer.writerow([
                    category.id, category.name,
                    category.parent_id if category.parent_id else '',
                    'educational'
                ])

        else:
            if entity_type not in entity_map:
                flash(f'نوع داده {entity_type} معتبر نیست.', 'danger')
                return redirect(url_for('admin_import_export'))

            model = entity_map[entity_type]
            items = model.query.all()

            if not items:
                flash(f'داده‌ای برای {entity_type} یافت نشد.', 'warning')
                return redirect(url_for('admin_import_export'))

            output = io.StringIO()
            writer = csv.writer(output)
            columns = [c.name for c in model.__table__.columns]
            writer.writerow(columns)

            for item in items:
                row = []
                for column in columns:
                    value = getattr(item, column)
                    row.append(str(value) if value is not None else '')
                writer.writerow(row)

        output.seek(0)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition':
                f'attachment; filename={entity_type}_{timestamp}.csv'
            })

    except Exception as e:
        logger.error(f"Error exporting {entity_type}: {str(e)}")
        flash(f'خطا در خروجی‌گیری: {str(e)}', 'danger')
        return redirect(url_for('admin_import_export'))


@app.route('/admin/import', methods=['POST'])
@login_required
def import_entity():
    """Import data from CSV file"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز.', 'danger')
        return redirect(url_for('index'))

    try:
        entity_type = request.form.get('entity_type')
        if not entity_type:
            flash('لطفاً نوع داده را انتخاب کنید.', 'danger')
            return redirect(url_for('admin_import_export'))

        if 'csv_file' not in request.files:
            flash('لطفاً یک فایل CSV انتخاب کنید.', 'danger')
            return redirect(url_for('admin_import_export'))

        file = request.files['csv_file']
        if not file.filename.endswith('.csv'):
            flash('فایل باید فرمت CSV داشته باشد.', 'danger')
            return redirect(url_for('admin_import_export'))

        content = file.read().decode('utf-8')
        csv_data = io.StringIO(content)
        reader = csv.DictReader(csv_data)
        imported_count = 0

        if entity_type == 'products':
            for row in reader:
                product = Product(
                    name=row.get('name', ''),
                    price=int(row.get('price', 0)) if row.get('price') else 0,
                    description=row.get('description', ''),
                    category_id=int(row.get('category_id'))
                    if row.get('category_id') else None,
                    brand=row.get('brand', None),
                    model=row.get('model', None),
                    in_stock=row.get('in_stock', 'True').lower() == 'true',
                    tags=row.get('tags', None),
                    featured=row.get('featured', 'False').lower() == 'true')
                db.session.add(product)
                imported_count += 1
        elif entity_type == 'services':
            for row in reader:
                service = Service(
                    name=row.get('name', ''),
                    price=int(row.get('price', 0)) if row.get('price') else 0,
                    description=row.get('description', ''),
                    category_id=int(row.get('category_id'))
                    if row.get('category_id') else None,
                    featured=row.get('featured', 'False').lower() == 'true',
                    available=row.get('available', 'True').lower() == 'true',
                    tags=row.get('tags', None))
                db.session.add(service)
                imported_count += 1

        elif entity_type == 'categories':
            for row in reader:
                category_type = row.get('category_type', 'product')
                name = row.get('name', '')
                parent_id = int(
                    row.get('parent_id')) if row.get('parent_id') else None

                if category_type == 'product':
                    category = ProductCategory(name=name, parent_id=parent_id)
                elif category_type == 'service':
                    category = ServiceCategory(name=name, parent_id=parent_id)
                elif category_type == 'educational':
                    category = EducationalCategory(name=name,
                                                   parent_id=parent_id)
                else:
                    continue

                db.session.add(category)
                imported_count += 1

        elif entity_type == 'inquiries':
            for row in reader:
                inquiry = Inquiry(
                    user_id=int(row.get('user_id', 0)),
                    product_id=int(row.get('product_id'))
                    if row.get('product_id') else None,
                    service_id=int(row.get('service_id'))
                    if row.get('service_id') else None,
                    name=row.get('name', ''),
                    phone=row.get('phone', ''),
                    description=row.get('description', None),
                    status=row.get('status', 'new'),
                    date=datetime.datetime.strptime(row.get('date'),
                                                    '%Y-%m-%d %H:%M:%S')
                    if row.get('date') else datetime.datetime.utcnow())
                db.session.add(inquiry)
                imported_count += 1

        elif entity_type == 'educational':
            for row in reader:
                content = EducationalContent(
                    title=row.get('title', ''),
                    content=row.get('content', ''),
                    category_id=int(row.get('category_id'))
                    if row.get('category_id') else None,
                    tags=row.get('tags', None),
                    featured=row.get('featured', 'False').lower() == 'true')
                db.session.add(content)
                imported_count += 1

        db.session.commit()
        flash(f'{imported_count} مورد با موفقیت وارد شد.', 'success')
        return redirect(url_for('admin_import_export'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error importing {entity_type}: {str(e)}")
        flash(f'خطا در وارد کردن داده‌ها: {str(e)}', 'danger')
        return redirect(url_for('admin_import_export'))


@app.route('/admin/backup')
@login_required
def backup_database():
    """Create database backup as ZIP file"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز.', 'danger')
        return redirect(url_for('index'))

    try:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"database_backup_{timestamp}.zip"

        models_map = {
            'users.csv': User,
            'product_categories.csv': ProductCategory,
            'service_categories.csv': ServiceCategory,
            'educational_categories.csv': EducationalCategory,
            'products.csv': Product,
            'services.csv': Service,
            'inquiries.csv': Inquiry,
            'educational_content.csv': EducationalContent,
            'product_media.csv': ProductMedia,
            'service_media.csv': ServiceMedia,
            'educational_content_media.csv': EducationalContentMedia,
            'static_content.csv': StaticContent
        }

        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for table_name, model in models_map.items():
                items = model.query.all()
                if not items:
                    continue

                columns = [c.name for c in model.__table__.columns]
                csv_output = io.StringIO()
                writer = csv.writer(csv_output)
                writer.writerow(columns)

                for item in items:
                    row = [
                        str(getattr(item, col))
                        if getattr(item, col) is not None else ''
                        for col in columns
                    ]
                    writer.writerow(row)

                zf.writestr(table_name, csv_output.getvalue().encode('utf-8'))

            readme_content = f"""این پشتیبان در تاریخ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ایجاد شده است.
هر فایل CSV شامل داده‌های یک جدول است.
ستون اول در هر فایل CSV نام ستون‌ها را نشان می‌دهد.

فایل‌های پشتیبان شامل:
{', '.join(models_map.keys())}
"""
            zf.writestr("README.txt", readme_content.encode('utf-8'))

        memory_file.seek(0)
        return send_file(memory_file,
                         mimetype='application/zip',
                         as_attachment=True,
                         download_name=backup_filename)

    except Exception as e:
        logger.error(f"Error in backup_database: {str(e)}")
        flash(f"خطا در پشتیبان‌گیری از دیتابیس: {str(e)}", 'danger')
        return redirect(url_for('admin_import_export'))


@app.route('/admin/restore', methods=['POST'])
@login_required
def restore_database():
    """Restore database from backup file"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز.', 'danger')
        return redirect(url_for('index'))

    try:
        backup_file = request.files.get('backup_file')
        if not backup_file or not backup_file.filename.endswith('.zip'):
            flash('فایل پشتیبان باید با فرمت ZIP باشد.', 'warning')
            return redirect(url_for('admin_import_export'))

        safe_filename = secure_filename(backup_file.filename)
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, safe_filename)
        backup_file.save(temp_path)

        models_map = {
            'users.csv': User,
            'product_categories.csv': ProductCategory,
            'service_categories.csv': ServiceCategory,
            'educational_categories.csv': EducationalCategory,
            'static_content.csv': StaticContent,
            'products.csv': Product,
            'services.csv': Service,
            'educational_content.csv': EducationalContent,
            'inquiries.csv': Inquiry,
            'product_media.csv': ProductMedia,
            'service_media.csv': ServiceMedia,
            'educational_content_media.csv': EducationalContentMedia
        }

        restored_tables = []
        skipped_tables = []
        error_tables = []

        with zipfile.ZipFile(temp_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            if 'README.txt' in file_list:
                file_list.remove('README.txt')

            should_clear_tables = request.form.get('clear_tables') == 'on'

            for csv_filename in models_map.keys():
                if csv_filename not in file_list:
                    logger.info(f"File {csv_filename} not in backup")
                    continue

                model = models_map[csv_filename]
                csv_content = zip_ref.read(csv_filename).decode('utf-8')
                csv_file = io.StringIO(csv_content)
                reader = csv.DictReader(csv_file)

                if should_clear_tables:
                    try:
                        db.session.query(model).delete()
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        logger.error(
                            f"Error clearing table {csv_filename}: {str(e)}")
                        skipped_tables.append(csv_filename)
                        continue

                restored_rows = 0
                for row in reader:
                    try:
                        data = {}
                        for field in reader.fieldnames:
                            value = row[field]
                            if value == '':
                                value = None
                            elif field in [
                                    'id', 'parent_id', 'category_id',
                                    'product_id', 'service_id', 'content_id',
                                    'user_id'
                            ]:
                                value = int(value) if value else None
                            elif field in [
                                    'is_admin', 'in_stock', 'featured',
                                    'available'
                            ]:
                                value = value.lower() in ('true', '1', 'yes')
                            elif field in ['created_at', 'updated_at', 'date']:
                                value = datetime.datetime.strptime(
                                    value,
                                    '%Y-%m-%d %H:%M:%S') if value else None
                            data[field] = value

                        # Validate foreign keys for media tables
                        if model == ProductMedia and data.get('product_id'):
                            if not Product.query.get(data['product_id']):
                                continue
                        elif model == ServiceMedia and data.get('service_id'):
                            if not Service.query.get(data['service_id']):
                                continue
                        elif model == EducationalContentMedia and data.get(
                                'content_id'):
                            if not EducationalContent.query.get(
                                    data['content_id']):
                                continue

                        item = model(**data)
                        db.session.add(item)
                        restored_rows += 1
                    except Exception as e:
                        logger.warning(
                            f"Error adding row to {csv_filename}: {str(e)}")
                        continue

                try:
                    db.session.commit()
                    restored_tables.append(
                        f"{csv_filename} ({restored_rows} rows)")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error committing {csv_filename}: {str(e)}")
                    error_tables.append(csv_filename)

        os.unlink(temp_path)
        os.rmdir(temp_dir)

        if restored_tables:
            flash(f'بازیابی جداول: {", ".join(restored_tables)}', 'success')
        if skipped_tables:
            flash(f'جداول رد شده: {", ".join(skipped_tables)}', 'warning')
        if error_tables:
            flash(f'خطا در جداول: {", ".join(error_tables)}', 'danger')

        return redirect(url_for('admin_import_export'))

    except Exception as e:
        logger.error(f"Error in restore_database: {str(e)}")
        flash(f"خطا در بازیابی دیتابیس: {str(e)}", 'danger')
        return redirect(url_for('admin_import_export'))


@app.route('/admin/database/export/<table_name>', methods=['POST'])
@login_required
def export_table_csv(table_name):
    """Export table data as CSV"""
    if not current_user.is_admin:
        flash('دسترسی غیرمجاز.', 'danger')
        return redirect(url_for('admin_database'))

    try:
        model_map = {
            'users': User,
            'product_categories': ProductCategory,
            'service_categories': ServiceCategory,
            'educational_categories': EducationalCategory,
            'products': Product,
            'services': Service,
            'inquiries': Inquiry,
            'educational_content': EducationalContent,
            'product_media': ProductMedia,
            'service_media': ServiceMedia,
            'educational_content_media': EducationalContentMedia,
            'static_content': StaticContent
        }

        if table_name not in model_map:
            flash(f'جدول {table_name} یافت نشد.', 'danger')
            return redirect(url_for('admin_database'))

        model = model_map[table_name]
        export_type = request.form.get('export_type', 'all')
        include_headers = request.form.get('include_headers') == 'on'

        query = model.query
        if export_type == 'current':
            page = request.form.get('page', 1, type=int)
            per_page = request.form.get('per_page', 20, type=int)
            query = query.offset((page - 1) * per_page).limit(per_page)
        elif export_type == 'custom':
            start_row = request.form.get('start_row', 1, type=int)
            end_row = request.form.get('end_row', type=int)
            query = query.offset(start_row - 1)
            if end_row:
                query = query.limit(end_row - start_row + 1)

        items = query.all()
        columns = [c.name for c in model.__table__.columns]

        output = io.StringIO()
        writer = csv.writer(output)
        if include_headers:
            writer.writerow(columns)

        for item in items:
            row = [
                str(getattr(item, col))
                if getattr(item, col) is not None else '' for col in columns
            ]
            writer.writerow(row)

        output.seek(0)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return Response(output.getvalue(),
                        mimetype='text/csv',
                        headers={
                            'Content-Disposition':
                            f'attachment;filename={table_name}_{timestamp}.csv'
                        })

    except Exception as e:
        logger.error(f"Error exporting table {table_name}: {str(e)}")
        flash(f'خطا در خروجی‌گیری از جدول: {str(e)}', 'danger')
        return redirect(url_for('admin_database'))
