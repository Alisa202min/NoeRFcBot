from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, send_file
import json
import os
import threading
import logging
import subprocess
import time
import signal
import math
import asyncio
from functools import wraps
from datetime import datetime
import tempfile
from database import Database
import ssl
from aiohttp import web
from bot import bot, dp, setup_webhook

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Telegram bot webhook settings
WEBHOOK_HOST = os.environ.get("HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.environ.get("PORT", 5000))
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Bot process variable
bot_process = None
bot_status = "stopped"
bot_logs = []
max_logs = 100  # Maximum number of log entries to keep

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

def read_file_content(file_path):
    """Read the content of a file safely"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        return "File not found"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def capture_bot_output(process):
    """Capture and log bot output"""
    global bot_logs
    for line in iter(process.stdout.readline, b''):
        line_str = line.decode('utf-8').strip()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp} - {line_str}"
        logger.info(log_entry)
        bot_logs.append(log_entry)
        # Keep logs at a reasonable size
        if len(bot_logs) > max_logs:
            bot_logs = bot_logs[-max_logs:]

def start_bot():
    """Start the Telegram bot in a separate process"""
    global bot_process, bot_status, bot_logs

    if bot_process is not None:
        logger.info("Bot is already running")
        return False

    # Check if a bot is already running from workflow
    try:
        bot_check = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        if "python bot.py" in bot_check.stdout and "workflow" in bot_check.stdout:
            logger.info("Bot is already running in workflow")
            bot_status = "running"
            bot_logs.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Bot is already running in workflow")
            return True
    except Exception as e:
        logger.info(f"Failed to check for running bot: {str(e)}")

    try:
        # Clear previous logs
        bot_logs = []

        # Start the bot as a subprocess
        bot_process = subprocess.Popen(
            ["python", "bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=False,
            bufsize=1
        )

        # Start a thread to capture output
        output_thread = threading.Thread(
            target=capture_bot_output,
            args=(bot_process,),
            daemon=True
        )
        output_thread.start()

        bot_status = "running"
        logger.info("Bot started successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        bot_status = "error"
        bot_logs.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error starting bot: {str(e)}")
        return False

def stop_bot():
    """Stop the running Telegram bot"""
    global bot_process, bot_status

    # Check if bot is running in workflow
    try:
        bot_check = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        if "python bot.py" in bot_check.stdout and "workflow" in bot_check.stdout:
            logger.info("Bot is running in workflow and cannot be stopped from web interface")
            bot_logs.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Bot is running in workflow and cannot be stopped from web interface")
            flash('ربات در workflow در حال اجرا است و نمی‌تواند از پنل وب متوقف شود', 'warning')
            return False
    except Exception as e:
        logger.error(f"Failed to check for running bot: {str(e)}")

    if bot_process is None:
        logger.info("Bot is not running")
        return False

    try:
        # Terminate the process
        bot_process.terminate()
        # Wait for process to terminate
        try:
            bot_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if doesn't terminate
            bot_process.kill()

        bot_process = None
        bot_status = "stopped"
        logger.info("Bot stopped successfully")
        return True
    except Exception as e:
        logger.error(f"Error stopping bot: {str(e)}")
        return False

def check_bot_status_workflow():
    """Check if the bot is running in workflow"""
    global bot_status
    try:
        bot_check = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        if "python bot.py" in bot_check.stdout and "workflow" in bot_check.stdout:
            bot_status = "running"
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to check for running bot: {str(e)}")
        return False

@app.route('/')
def index():
    """Main dashboard page"""
    # Get README content
    readme_content = read_file_content('README.md')

    # Check if bot is running in workflow
    check_bot_status_workflow()

    # Check environment variables
    env_status = {
        'BOT_TOKEN': 'Set' if os.environ.get('BOT_TOKEN') else 'Not Set',
        'ADMIN_ID': 'Set' if os.environ.get('ADMIN_ID') else 'Not Set',
        'DB_TYPE': os.environ.get('DB_TYPE', 'sqlite')
    }

    # Check database files
    db_path = os.path.join('data', 'database.db')
    db_exists = os.path.exists(db_path)

    return render_template('index.html',
                          readme_content=readme_content,
                          bot_status=bot_status,
                          env_status=env_status,
                          db_exists=db_exists,
                          bot_logs=bot_logs)

@app.route('/control/start', methods=['POST'])
def control_start():
    """Start the bot"""
    success = start_bot()
    if success:
        flash('Bot started successfully', 'success')
    else:
        flash('Failed to start bot', 'danger')
    return redirect(url_for('index'))

@app.route('/control/stop', methods=['POST'])
def control_stop():
    """Stop the bot"""
    success = stop_bot()
    if success:
        flash('Bot stopped successfully', 'success')
    else:
        flash('Failed to stop bot', 'danger')
    return redirect(url_for('index'))

@app.route('/logs')
def logs():
    """Get the latest logs"""
    return jsonify(bot_logs)

@app.route('/configuration')
def loadConfig():
    """Display the configuration page"""
    from configuration import CONFIG_PATH
    with open(CONFIG_PATH, 'r', encoding='utf-8') as configfile:
        current_config = json.load(configfile)
    return render_template('configuration .html', 
                         config=current_config,
                         config_json=json.dumps(current_config, ensure_ascii=False, indent=4))

@app.route('/database')
def database():
    """Display database information"""
    # Check db existence
    db_path = os.path.join('data', 'database.db')
    db_exists = os.path.exists(db_path)

    # Get size if exists
    db_size = os.path.getsize(db_path) if db_exists else 0

    #Removed Replit DB check - always using SQLite now
    return render_template('database.html', 
                          db_exists=db_exists,
                          db_path=db_path,
                          db_size=db_size)

# Initialize database
db = Database()

# Webhook route for Telegram bot
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    """Forward webhook data to the bot's webhook handler"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update_dict = json.loads(json_string)
        logger.info(f"Received webhook update: {json_string[:100]}...")
        
        # Process the update using asyncio
        try:
            asyncio.run(bot.process_update(update=update_dict))
            return '', 200
        except Exception as e:
            logger.error(f"Error processing webhook update: {str(e)}")
            return '', 500
    else:
        logger.warning("Received non-JSON data in webhook")
        return '', 403

# Setup aiohttp app for bot webhook
def setup_bot_webhook():
    """Setup webhook for Telegram bot"""
    if not WEBHOOK_URL:
        logger.warning("WEBHOOK_URL not set in environment variables. Webhook setup skipped.")
        return
    
    # Create aiohttp app
    app = web.Application()
    
    # Setup webhook handler
    asyncio.run(setup_webhook(app, WEBHOOK_PATH))
    
    # Set webhook URL
    asyncio.run(bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH))
    
    logger.info(f"Webhook set to {WEBHOOK_URL + WEBHOOK_PATH}")
    
    return app

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if ADMIN_ID is set
        admin_id = os.environ.get('ADMIN_ID')
        if not admin_id:
            flash('ADMIN_ID is not set in environment variables', 'danger')
            return redirect(url_for('index'))

        # In a real application, we would check session for admin login
        # Here we're just providing access to admin panel for demonstration
        return f(*args, **kwargs)
    return decorated_function

# Helper function for pagination
def get_pagination(page, per_page, total_count, endpoint, **kwargs):
    """Generate pagination data"""
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    page = max(1, min(page, total_pages))

    pages = range(max(1, page - 2), min(total_pages + 1, page + 3))

    # Create URLs for prev and next
    prev_url = url_for(endpoint, page=page-1, **kwargs) if page > 1 else None
    next_url = url_for(endpoint, page=page+1, **kwargs) if page < total_pages else None

    def url_for_page(p):
        return url_for(endpoint, page=p, **kwargs)

    return {
        'page': page,
        'per_page': per_page,
        'total_count': total_count,
        'total_pages': total_pages,
        'pages': pages,
        'prev_url': prev_url,
        'next_url': next_url,
        'url_for_page': url_for_page
    }

# Admin panel routes
@app.route('/admin')
@admin_required
def admin_index():
    """Admin dashboard"""
    # Get stats for dashboard
    products_count = 0
    services_count = 0
    inquiries_count = 0
    recent_inquiries = []

    # Count products
    product_categories = db.get_categories(cat_type='product')
    for category in product_categories:
        products_count += len(db.get_products_by_category(category['id']))

    # Count services
    service_categories = db.get_categories(cat_type='service')
    for category in service_categories:
        services_count += len(db.get_products_by_category(category['id']))

    # Get inquiries
    all_inquiries = db.get_inquiries()
    inquiries_count = len(all_inquiries)

    # Get most recent inquiries (up to 5)
    if all_inquiries:
        recent_inquiries = sorted(all_inquiries, key=lambda x: x['date'], reverse=True)[:5]

        # Add product name to each inquiry
        for inquiry in recent_inquiries:
            if inquiry['product_id']:
                product = db.get_product(inquiry['product_id'])
                inquiry['product_name'] = product['name'] if product else 'Unknown Product'
            else:
                inquiry['product_name'] = None

    stats = {
        'products_count': products_count,
        'services_count': services_count,
        'inquiries_count': inquiries_count
    }

    return render_template('admin_index.html', 
                          stats=stats,
                          recent_inquiries=recent_inquiries)

@app.route('/admin/categories')
@admin_required
def admin_categories():
    """Admin categories management"""
    # Get product categories (top level)
    product_categories = db.get_categories(cat_type='product')

    # Get service categories (top level)
    service_categories = db.get_categories(cat_type='service')

    # For each category, get parent name and count of products
    for category in product_categories + service_categories:
        # Get parent name if has parent
        if category['parent_id']:
            parent = db.get_category(category['parent_id'])
            category['parent_name'] = parent['name'] if parent else 'Unknown'
        else:
            category['parent_name'] = None

        # Count products
        category['product_count'] = len(db.get_products_by_category(category['id']))

    return render_template('admin_categories.html',
                          product_categories=product_categories,
                          service_categories=service_categories)

@app.route('/admin/categories/add', methods=['GET', 'POST'])
@admin_required
def admin_add_category():
    """Admin add category"""
    if request.method == 'POST':
        name = request.form.get('name')
        parent_id = request.form.get('parent_id')
        cat_type = request.form.get("cat_type")

        # Validate
        if not name:
            flash('نام دسته‌بندی الزامی است', 'danger')
            return redirect(url_for('admin_add_category'))

        # Convert empty parent_id to None
        if not parent_id:
            parent_id = None
        else:
            parent_id = int(parent_id)

        # Add to database
        category_id = db.add_category(name, parent_id, cat_type)

        if category_id:
            flash(f'دسته‌بندی {name} با موفقیت ایجاد شد', 'success')
            return redirect(url_for('admin_categories'))
        else:
            flash('خطا در ایجاد دسته‌بندی', 'danger')
            return redirect(url_for('admin_add_category'))

    # GET request
    # Get all categories for parent selection
    all_categories = db.get_categories()

    return render_template('admin_category_form.html',
                          all_categories=all_categories)

@app.route('/admin/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_category(category_id):
    """Admin edit category"""
    # Get category
    category = db.get_category(category_id)
    if not category:
        flash('دسته‌بندی مورد نظر یافت نشد', 'danger')
        return redirect(url_for('admin_categories'))

    if request.method == 'POST':
        name = request.form.get('name')
        parent_id = request.form.get('parent_id')
        cat_type = request.form.get('cat_type')

        # Validate
        if not name:
            flash('نام دسته‌بندی الزامی است', 'danger')
            return redirect(url_for('admin_edit_category', category_id=category_id))

        # Convert empty parent_id to None
        if not parent_id:
            parent_id = None
        else:
            parent_id = int(parent_id)

        # Check that category is not its own parent
        if parent_id == category_id:
            flash('دسته‌بندی نمی‌تواند والد خودش باشد', 'danger')
            return redirect(url_for('admin_edit_category', category_id=category_id))

        # Update database
        success = db.update_category(category_id, name, parent_id, cat_type)

        if success:
            flash(f'دسته‌بندی {name} با موفقیت به‌روزرسانی شد', 'success')
            return redirect(url_for('admin_categories'))
        else:
            flash('خطا در به‌روزرسانی دسته‌بندی', 'danger')
            return redirect(url_for('admin_edit_category', category_id=category_id))

    # GET request
    # Get all categories for parent selection
    all_categories = db.get_categories()

    return render_template('admin_category_form.html',
                          category=category,
                          all_categories=all_categories)

@app.route('/admin/categories/delete', methods=['POST'])
@admin_required
def admin_delete_category():
    """Admin delete category"""
    category_id = request.form.get('category_id')

    if not category_id:
        flash('شناسه دسته‌بندی الزامی است', 'danger')
        return redirect(url_for('admin_categories'))

    # Get category name for success message
    category = db.get_category(int(category_id))
    if not category:
        flash('دسته‌بندی مورد نظر یافت نشد', 'danger')
        return redirect(url_for('admin_categories'))

    # Delete from database
    success = db.delete_category(int(category_id))

    if success:
        flash(f'دسته‌بندی {category["name"]} با موفقیت حذف شد', 'success')
    else:
        flash('خطا در حذف دسته‌بندی', 'danger')

    return redirect(url_for('admin_categories'))

@app.route('/admin/services/add', methods=['GET', 'POST'])
@admin_required
def admin_add_service():
    """Admin add service"""
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description')
        photo_url = request.form.get('photo_url')
        category_id = request.form.get('category_id')

        # Validate
        if not all([name, price, category_id]):
            flash('نام، قیمت و دسته‌بندی الزامی هستند', 'danger')
            return redirect(url_for('admin_add_service'))

        # Add to database
        service_id = db.add_product(
            name=name,
            price=int(price),
            description=description,
            photo_url=photo_url if photo_url else None,
            category_id=int(category_id)
        )

        if service_id:
            flash(f'خدمت {name} با موفقیت ایجاد شد', 'success')
            return redirect(url_for('admin_services'))
        else:
            flash('خطا در ایجاد خدمت', 'danger')
            return redirect(url_for('admin_add_service'))

    # GET request
    # Get all service categories
    categories = db.get_categories(cat_type='service')
    return render_template('admin_service_form.html',
                         categories=categories)

@app.route('/admin/services')
@admin_required
def admin_services():
    """Admin services management"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_query = request.args.get('search')
    selected_category_id = request.args.get('category_id')

    # Get all services from service categories
    all_services = []
    if search_query:
        # Search by name
        all_services = db.search_products(search_query, cat_type='service')
    elif selected_category_id:
        # Filter by category
        all_services = db.get_products_by_category(int(selected_category_id))
    else:
        # Get all services from service categories
        categories = db.get_categories(cat_type='service')
        for category in categories:
            all_services.extend(db.get_products_by_category(category['id']))

    # Total count for pagination
    total_count = len(all_services)

    # Apply pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    services = all_services[start_idx:end_idx] if all_services else []

    # Generate pagination data
    pagination = get_pagination(
        page, per_page, total_count, 'admin_services',
        search=search_query, category_id=selected_category_id
    ) if services else None

    # For each service, get category name
    for service in services:
        category = db.get_category(service['category_id'])
        service['category_name'] = category['name'] if category else 'Unknown'

    # Get all categories for filter dropdown
    categories = db.get_categories(cat_type='service')

    return render_template('admin_products.html',
                          products=services,
                          categories=categories,
                          selected_category_id=int(selected_category_id) if selected_category_id else None,
                          search_query=search_query,
                          pagination=pagination,
                          page_type='services')

@app.route('/admin/products')
@admin_required
def admin_products():
    """Admin products management"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_query = request.args.get('search')
    selected_category_id = request.args.get('category_id')

    # Get all products
    all_products = []

    if search_query:
        # Search by name
        all_products = db.search_products(search_query)
    elif selected_category_id:
        # Filter by category
        all_products = db.get_products_by_category(int(selected_category_id))
    else:
        # Get all products from all categories
        categories = db.get_categories()
        for category in categories:
            all_products.extend(db.get_products_by_category(category['id']))

    # Total count for pagination
    total_count = len(all_products)

    # Apply pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    products = all_products[start_idx:end_idx] if all_products else []

    # Generate pagination data
    pagination = get_pagination(
        page, per_page, total_count, 'admin_products',
        search=search_query, category_id=selected_category_id
    ) if products else None

    # For each product, get category name
    for product in products:
        category = db.get_category(product['category_id'])
        product['category_name'] = category['name'] if category else 'Unknown'

    # Get all categories for filter dropdown
    categories = db.get_categories()

    return render_template('admin_products.html',
                          products=products,
                          categories=categories,
                          selected_category_id=int(selected_category_id) if selected_category_id else None,
                          search_query=search_query,
                          pagination=pagination)

@app.route('/configuration/update', methods=['POST'])
@admin_required
def update_config():
    """Update bot configuration"""
    try:
        if request.form.get('view_type') == 'raw':
            # Handle raw JSON update
            try:
                new_config = json.loads(request.form.get('raw_config'))
                config.save_config(new_config)
            except json.JSONDecodeError:
                flash('خطا در فرمت JSON', 'danger')
                return redirect(url_for('config'))
        else:
            # Handle form update
            current_config = config.load_config()
            for key in request.form:
                if key not in ['view_type']:
                    current_config[key] = request.form[key]
            config.save_config(current_config)

        flash('تنظیمات با موفقیت به‌روزرسانی شد', 'success')
    except Exception as e:
        flash(f'خطا در به‌روزرسانی تنظیمات: {str(e)}', 'danger')

    return redirect(url_for('config'))

@app.route('/configuration/reset', methods=['POST'])
@admin_required
def reset_config():
    """Reset config to default values"""
    try:
        configuration.reset_to_default()
        flash('تنظیمات با موفقیت به حالت پیش‌فرض برگردانده شد', 'success')
    except Exception as e:
        flash(f'خطا در بازگشت به تنظیمات پیش‌فرض: {str(e)}', 'danger')

    return redirect(url_for('config'))

@app.route('/control/restart', methods=['POST'])
@admin_required
def restart_bot():
    """Restart the bot"""
    try:
        stop_bot()
        time.sleep(1)  # Wait for bot to stop
        success = start_bot()

        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to restart bot'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    """Admin add product"""
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description')
        photo_url = request.form.get('photo_url')
        category_id = request.form.get('category_id')

        # Validate
        if not all([name, price, category_id]):
            flash('نام، قیمت و دسته‌بندی الزامی هستند', 'danger')
            return redirect(url_for('admin_add_product'))

        # Add to database
        product_id = db.add_product(
            name=name,
            price=int(price),
            description=description,
            photo_url=photo_url if photo_url else None,
            category_id=int(category_id)
        )

        if product_id:
            flash(f'محصول {name} با موفقیت ایجاد شد', 'success')
            return redirect(url_for('admin_products'))
        else:
            flash('خطا در ایجاد محصول', 'danger')
            return redirect(url_for('admin_add_product'))

    # GET request
    # Get all categories for category selection
    categories = db.get_categories()

    return render_template('admin_product_form.html',
                          categories=categories)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    """Admin edit product"""
    # Get product
    product = db.get_product(product_id)
    if not product:
        flash('محصول مورد نظر یافت نشد', 'danger')
        return redirect(url_for('admin_products'))

    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        description = request.form.get('description')
        photo_url = request.form.get('photo_url')
        category_id = request.form.get('category_id')

        # Validate
        if not all([name, price, category_id]):
            flash('نام، قیمت و دسته‌بندی الزامی هستند', 'danger')
            return redirect(url_for('admin_edit_product', product_id=product_id))

        # Update database
        success = db.update_product(
            product_id=product_id,
            name=name,
            price=int(price),
            description=description,
            photo_url=photo_url if photo_url else None,
            category_id=int(category_id)
        )

        if success:
            flash(f'محصول {name} با موفقیت به‌روزرسانی شد', 'success')
            return redirect(url_for('admin_products'))
        else:
            flash('خطا در به‌روزرسانی محصول', 'danger')
            return redirect(url_for('admin_edit_product', product_id=product_id))

    # GET request
    # Get all categories for category selection
    categories = db.get_categories()

    # Get category name
    category = db.get_category(product['category_id'])
    product['category_name'] = category['name'] if category else 'Unknown'

    return render_template('admin_product_form.html',
                          product=product,
                          categories=categories)

@app.route('/admin/products/delete', methods=['POST'])
@admin_required
def admin_delete_product():
    """Admin delete product"""
    product_id = request.form.get('product_id')

    if not product_id:
        flash('شناسه محصول الزامی است', 'danger')
        return redirect(url_for('admin_products'))

    # Get product name for success message
    product = db.get_product(int(product_id))
    if not product:
        flash('محصول مورد نظر یافت نشد', 'danger')
        return redirect(url_for('admin_products'))

    # Delete from database
    success = db.delete_product(int(product_id))

    if success:
        flash(f'محصول {product["name"]} با موفقیت حذف شد', 'success')
    else:
        flash('خطا در حذف محصول', 'danger')

    return redirect(url_for('admin_products'))

@app.route('/admin/education')
@admin_required
def admin_education():
    """Admin educational content management"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_query = request.args.get('search')
    selected_category = request.args.get('category')

    # Get all educational content
    all_content = db.get_all_educational_content(category=selected_category)

    # If search query, filter content
    if search_query:
        search_query = search_query.lower()
        all_content = [c for c in all_content if search_query in c['title'].lower()]

    # Total count for pagination
    total_count = len(all_content)

    # Apply pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    educational_content = all_content[start_idx:end_idx] if all_content else []

    # Generate pagination data
    pagination = get_pagination(
        page, per_page, total_count, 'admin_education',
        search=search_query, category=selected_category
    ) if educational_content else None

    # Get all categories for filter dropdown
    categories = db.get_educational_categories()

    return render_template('admin_education.html',
                          educational_content=educational_content,
                          categories=categories,
                          selected_category=selected_category,
                          search_query=search_query,
                          pagination=pagination)

@app.route('/admin/education/add', methods=['GET', 'POST'])
@admin_required
def admin_add_education():
    """Admin add educational content"""
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category') or request.form.get('new_category')
        content_type = request.form.get('content_type')

        # Get content based on type
        if content_type == 'text':
            content = request.form.get('content_text')
        elif content_type == 'link':
            content = request.form.get('content_link')
        elif content_type == 'file':
            content = request.form.get('content_file')
        else:
            content = ''

        # Validate
        if not all([title, category, content_type, content]):
            flash('تمامی فیلدها الزامی هستند', 'danger')
            return redirect(url_for('admin_add_education'))

        # Add to database
        content_id = db.add_educational_content(
            title=title,
            content=content,
            category=category,
            content_type=content_type
        )

        if content_id:
            flash(f'مطلب آموزشی {title} با موفقیت ایجاد شد', 'success')
            return redirect(url_for('admin_education'))
        else:
            flash('خطا در ایجاد مطلب آموزشی', 'danger')
            return redirect(url_for('admin_add_education'))

    # GET request
    # Get all categories
    categories = db.get_educational_categories()

    return render_template('admin_education_form.html',
                          categories=categories)

@app.route('/admin/education/edit/<int:content_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_education(content_id):
    """Admin edit educational content"""
    # Get content
    content = db.get_educational_content(content_id)
    if not content:
        flash('مطلب آموزشی مورد نظر یافت نشد', 'danger')
        return redirect(url_for('admin_education'))

    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category') or request.form.get('new_category')
        content_type = request.form.get('content_type')

        # Get content based on type
        if content_type == 'text':
            content_text = request.form.get('content_text')
        elif content_type == 'link':
            content_text = request.form.get('content_link')
        elif content_type == 'file':
            content_text = request.form.get('content_file')
        else:
            content_text = ''

        # Validate
        if not all([title, category, content_type, content_text]):
            flash('تمامی فیلدها الزامی هستند', 'danger')
            return redirect(url_for('admin_edit_education', content_id=content_id))

        # Update database
        success = db.update_educational_content(
            content_id=content_id,
            title=title,
            content=content_text,
            category=category,
            content_type=content_type
        )

        if success:
            flash(f'مطلب آموزشی {title} با موفقیت به‌روزرسانی شد', 'success')
            return redirect(url_for('admin_education'))
        else:
            flash('خطا در به‌روزرسانی مطلب آموزشی', 'danger')
            return redirect(url_for('admin_edit_education', content_id=content_id))

    # GET request
    # Get all categories
    categories = db.get_educational_categories()

    return render_template('admin_education_form.html',
                          content=content,
                          categories=categories)

@app.route('/admin/content')
@admin_required
def admin_content():
    """Admin static content management"""
    contact_content = db.get_static_content('contact')
    about_content = db.get_static_content('about')

    return render_template('admin_content.html',
                          contact_content=contact_content,
                          about_content=about_content)

@app.route('/admin/import_export')
@admin_required
def admin_import_export():
    """Import/Export data management"""
    message = request.args.get('message')
    message_type = request.args.get('type', 'info')

    return render_template('admin_import_export.html',
                          message={'text': message, 'type': message_type} if message else None)

@app.route('/admin/backup')
@admin_required
def backup_database():
    """Create database backup"""
    import shutil
    from datetime import datetime

    try:
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'database_backup_{timestamp}.db'
        backup_path = os.path.join('data', 'backups', backup_filename)

        # Create backups directory if it doesn't exist
        os.makedirs(os.path.join('data', 'backups'), exist_ok=True)

        # Copy database file
        shutil.copy2(os.path.join('data', 'database.db'), backup_path)

        return send_file(
            backup_path,
            as_attachment=True,
            download_name=backup_filename,
            mimetype='application/x-sqlite3'
        )
    except Exception as e:
        flash(f'خطا در تهیه پشتیبان: {str(e)}', 'danger')
        return redirect(url_for('admin_import_export'))

@app.route('/admin/restore', methods=['POST'])
@admin_required
def restore_database():
    """Restore database from backup"""
    if 'backup_file' not in request.files:
        flash('فایل پشتیبان انتخاب نشده است', 'danger')
        return redirect(url_for('admin_import_export'))

    file = request.files['backup_file']
    if not file.filename.endswith('.db'):
        flash('فایل باید با پسوند .db باشد', 'danger')
        return redirect(url_for('admin_import_export'))

    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            file.save(tmp_file.name)

            # Verify it's a valid SQLite database
            try:
                test_conn = sqlite3.connect(tmp_file.name)
                test_conn.close()
            except:
                os.unlink(tmp_file.name)
                flash('فایل پشتیبان معتبر نیست', 'danger')
                return redirect(url_for('admin_import_export'))

            # Replace current database
            shutil.move(tmp_file.name, os.path.join('data', 'database.db'))

        flash('بازیابی پشتیبان با موفقیت انجام شد', 'success')
    except Exception as e:
        flash(f'خطا در بازیابی پشتیبان: {str(e)}', 'danger')

    return redirect(url_for('admin_import_export'))

@app.route('/admin/export/<entity_type>')
@admin_required
def admin_export(entity_type):
    """Export data to CSV"""
    if entity_type not in ['products', 'services', 'categories', 'inquiries', 'educational']:
        flash('نوع داده نامعتبر است', 'danger')
        return redirect(url_for('admin_import_export'))

    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
        temp_path = temp_file.name
        temp_file.close()

        success = db.export_to_csv(entity_type, temp_path)

        if success:
            # Send file and then delete it
            response = send_file(
                temp_path,
                as_attachment=True,
                download_name=f'{entity_type}.csv',
                mimetype='text/csv'
            )

            # Delete temp file after sending
            try:
                os.unlink(temp_path)
            except:
                pass

            return response
        else:
            try:
                os.unlink(temp_path)
            except:
                pass
            flash('خطا در ایجاد خروجی CSV', 'danger')
            return redirect(url_for('admin_import_export'))

    except Exception as e:
        flash(f'خطا در ایجاد فایل خروجی: {str(e)}', 'danger')
        return redirect(url_for('admin_import_export'))

@app.route('/admin/import', methods=['POST'])
@admin_required
def admin_import():
    """Import data from CSV"""
    if 'csv_file' not in request.files:
        flash('فایل انتخاب نشده است', 'danger')
        return redirect(url_for('admin_import_export'))

    file = request.files['csv_file']
    entity_type = request.form.get('entity_type')

    if not file or not file.filename.endswith('.csv'):
        flash('فایل باید با فرمت CSV باشد', 'danger')
        return redirect(url_for('admin_import_export'))

    if entity_type not in ['products', 'services', 'categories', 'inquiries', 'educational']:
        flash('نوع داده نامعتبر است', 'danger')
        return redirect(url_for('admin_import_export'))

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
        file.save(temp_file.name)
        success_count, error_count = db.import_from_csv(entity_type, temp_file.name)
        os.unlink(temp_file.name)

    if success_count > 0:
        message = f'{success_count} مورد با موفقیت وارد شد'
        if error_count > 0:
            message += f' و {error_count} مورد با خطا مواجه شد'
        flash(message, 'success' if error_count == 0 else 'warning')
    else:
        flash('خطا در ورود داده‌ها', 'danger')

    return redirect(url_for('admin_import_export'))

@app.route('/admin/content/update', methods=['POST'])
@admin_required
def admin_update_content():
    """Update static content"""
    contact = request.form.get('contact')
    about = request.form.get('about')

    if contact:
        db.update_static_content('contact', contact)
    if about:
        db.update_static_content('about', about)

    flash('محتوای ثابت با موفقیت به‌روزرسانی شد', 'success')
    return redirect(url_for('admin_content'))

@app.route('/admin/education/delete', methods=['POST'])
@admin_required
def admin_delete_education():
    """Admin delete educational content"""
    content_id = request.form.get('content_id')

    if not content_id:
        flash('شناسه مطلب آموزشی الزامی است', 'danger')
        return redirect(url_for('admin_education'))

    # Get content title for success message
    content = db.get_educational_content(int(content_id))
    if not content:
        flash('مطلب آموزشی مورد نظر یافت نشد', 'danger')
        return redirect(url_for('admin_education'))

    # Delete from database
    success = db.delete_educational_content(int(content_id))

    if success:
        flash(f'مطلب آموزشی {content["title"]} با موفقیت حذف شد', 'success')
    else:
        flash('خطا در حذف مطلب آموزشی', 'danger')

    return redirect(url_for('admin_education'))

@app.route('/admin/inquiries')
@admin_required
def admin_inquiries():
    """Admin inquiries management"""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    product_id = request.args.get('product_id')

    # Get all inquiries with filters
    inquiries = db.get_inquiries(start_date=start_date, end_date=end_date, product_id=product_id)

    # Total count for pagination
    total_count = len(inquiries)

    # Apply pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    inquiries = inquiries[start_idx:end_idx] if inquiries else []

    # Generate pagination data
    pagination = get_pagination(
        page, per_page, total_count, 'admin_inquiries',
        start_date=start_date, end_date=end_date, product_id=product_id
    ) if inquiries else None

    # Get all products for filter dropdown
    products = []
    categories = db.get_categories()
    for category in categories:
        products.extend(db.get_products_by_category(category['id']))

    return render_template('admin_inquiries.html',
                          inquiries=inquiries,
                          products=products,
                          pagination=pagination)

@app.route('/admin/inquiries/export')
@admin_required
def admin_export_inquiries():
    """Export inquiries to Excel"""
    import tempfile

    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    product_id = request.args.get('product_id')

    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
        temp_path = temp_file.name

    # Export to CSV
    success = db.export_to_csv('inquiries', temp_path)

    if success:
        return send_file(
            temp_path,
            as_attachment=True,
            download_name='inquiries.csv',
            mimetype='text/csv'
        )
    else:
        flash('خطا در ایجاد فایل خروجی', 'danger')
        return redirect(url_for('admin_inquiries'))

@app.route('/admin/inquiries/delete', methods=['POST'])
@admin_required
def admin_delete_inquiry():
    """Delete an inquiry"""
    inquiry_id = request.form.get('inquiry_id')

    if not inquiry_id:
        flash('شناسه استعلام الزامی است', 'danger')
        return redirect(url_for('admin_inquiries'))

    # Delete inquiry
    success = db.delete_inquiry(int(inquiry_id))

    if success:
        flash('استعلام با موفقیت حذف شد', 'success')
    else:
        flash('خطا در حذف استعلام', 'danger')

    return redirect(url_for('admin_inquiries'))

if __name__ == '__main__':
    # Initialize the webhook setup
    if WEBHOOK_URL:
        # Setup webhook 
        try:
            logger.info(f"Setting up webhook at {WEBHOOK_URL + WEBHOOK_PATH}")
            setup_bot_webhook()
            logger.info("Webhook setup successful")
        except Exception as e:
            logger.error(f"Error setting up webhook: {str(e)}")
    else:
        logger.warning("WEBHOOK_URL not set, bot will not receive updates via webhook")
    
    # Start Flask app
    app.run(host=WEBHOOK_HOST, port=WEBHOOK_PORT)