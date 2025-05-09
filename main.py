from app import app, db, media_files
from flask import render_template, request, redirect, url_for, flash, jsonify, abort, send_file
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Category, Product, ProductMedia, Inquiry, EducationalContent, StaticContent
from werkzeug.utils import secure_filename
from database import Database
from sqlalchemy import text

import json
import os
import logging
import subprocess
import threading
import time
import signal
import math
import asyncio
from functools import wraps
from datetime import datetime
import tempfile
import shutil
import io
import uuid
import csv
from configuration import ADMIN_ID

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db_instance = Database()

# Import bot components, which may be None if BOT_TOKEN isn't set
try:
    from bot import bot, dp, setup_webhook
    BOT_AVAILABLE = bot is not None
except Exception as e:
    logging.error(f"Error importing bot module: {e}")
    bot = None
    dp = None
    setup_webhook = None
    BOT_AVAILABLE = False

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


def allowed_file(filename):
    """Check if the file has an allowed extension"""
    if not filename:
        return False
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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


# Webhook route for Telegram bot
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    """Forward webhook data to the bot's webhook handler"""
    if not BOT_AVAILABLE:
        logger.warning("Received webhook data but bot is not available (BOT_TOKEN not set)")
        return 'Bot not available', 503

    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        logger.info(f"Received webhook data: {json_string[:100]}...")
        return '', 200
    else:
        logger.warning("Received non-JSON data in webhook")
        return '', 403


# Setup aiohttp app for bot webhook
def setup_bot_webhook():
    """Setup webhook for Telegram bot"""
    if not WEBHOOK_URL or not BOT_AVAILABLE:
        logger.warning("WEBHOOK_URL not set or bot not available. Webhook setup skipped.")
        return None

    # Create aiohttp app
    from aiohttp import web
    webhook_app = web.Application()

    try:
        if setup_webhook is not None:
            # Setup webhook handler
            asyncio.run(setup_webhook(webhook_app, WEBHOOK_PATH, WEBHOOK_URL))
            
            # Set webhook URL if bot is available
            if bot is not None:
                asyncio.run(bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH))
                logger.info(f"Webhook set to {WEBHOOK_URL + WEBHOOK_PATH}")
    except Exception as e:
        logger.error(f"Error setting up webhook: {e}")
    
    return webhook_app


# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('شما دسترسی مدیریتی ندارید', 'danger')
            return redirect(url_for('index'))
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


# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# Provide datetime in templates
@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

# Main routes
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
        'DB_TYPE': os.environ.get('DB_TYPE', 'postgresql')
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


@app.route('/search', methods=['GET'])
def search():
    """Search page for products and services"""
    # Get search parameters
    query = request.args.get('query', '')
    product_type = request.args.get('type')
    category_id = request.args.get('category_id')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    tags = request.args.get('tags')
    
    # Product-specific parameters
    brand = request.args.get('brand')
    manufacturer = request.args.get('manufacturer')
    model_number = request.args.get('model_number')
    
    # Service-specific parameters
    provider = request.args.get('provider')
    service_code = request.args.get('service_code')
    duration = request.args.get('duration')
    
    # Common parameters
    in_stock = request.args.get('in_stock')
    featured = request.args.get('featured')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Convert string parameters to appropriate types
    if category_id:
        try:
            category_id = int(category_id)
        except ValueError:
            category_id = None
            
    if min_price:
        try:
            min_price = int(min_price)
        except ValueError:
            min_price = None
            
    if max_price:
        try:
            max_price = int(max_price)
        except ValueError:
            max_price = None
            
    if in_stock:
        in_stock = (in_stock.lower() == 'true')
    else:
        in_stock = None
        
    if featured:
        featured = (featured.lower() == 'true')
    else:
        featured = None
        
    # Get categories for the filter sidebar
    product_categories = Category.query.filter_by(cat_type='product').all()
    service_categories = Category.query.filter_by(cat_type='service').all()
    
    # Get all available brands for filtering
    brands = db.session.query(Product.brand).filter(
        Product.brand.isnot(None), Product.brand != '').distinct().all()
    brands = [brand[0] for brand in brands]
    
    # Get all available manufacturers for filtering
    manufacturers = db.session.query(Product.manufacturer).filter(
        Product.manufacturer.isnot(None), Product.manufacturer != '').distinct().all()
    manufacturers = [manufacturer[0] for manufacturer in manufacturers]
    
    # Get all available providers for filtering
    providers = db.session.query(Product.provider).filter(
        Product.provider.isnot(None), Product.provider != '').distinct().all()
    providers = [provider[0] for provider in providers]
    
    # Get all available tags for filtering
    all_tags = []
    products_with_tags = db.session.query(Product.tags).filter(
        Product.tags.isnot(None), Product.tags != '').all()
    for product_tags in products_with_tags:
        if product_tags[0]:
            all_tags.extend([tag.strip() for tag in product_tags[0].split(',')])
    all_tags = sorted(list(set(all_tags)))  # Remove duplicates and sort
    
    # Perform the search
    search_query = Product.search(
        query=query,
        product_type=product_type,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        tags=tags,
        brand=brand,
        manufacturer=manufacturer,
        model_number=model_number,
        provider=provider,
        service_code=service_code,
        duration=duration,
        in_stock=in_stock,
        featured=featured
    )
    
    # Add sorting
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    
    if sort_by == 'price':
        if sort_order == 'asc':
            search_query = search_query.order_by(Product.price.asc())
        else:
            search_query = search_query.order_by(Product.price.desc())
    elif sort_by == 'newest':
        search_query = search_query.order_by(Product.created_at.desc())
    else:  # Default to name
        if sort_order == 'asc':
            search_query = search_query.order_by(Product.name.asc())
        else:
            search_query = search_query.order_by(Product.name.desc())
    
    # Paginate results
    paginated_results = search_query.paginate(page=page, per_page=per_page)
    
    # Prepare search summary
    search_summary = {
        'query': query,
        'type': 'محصولات' if product_type == 'product' else 'خدمات' if product_type == 'service' else 'همه',
        'total_results': paginated_results.total,
        'filters_applied': bool(
            category_id or min_price or max_price or tags or brand or 
            manufacturer or model_number or provider or service_code or 
            duration or in_stock is not None or featured is not None
        )
    }
    
    # If a category filter is applied, get the category name
    if category_id:
        category = Category.query.get(category_id)
        if category:
            search_summary['category'] = category.name
    
    # Generate pagination info
    pagination = {
        'page': paginated_results.page,
        'total_pages': paginated_results.pages,
        'has_prev': paginated_results.has_prev,
        'has_next': paginated_results.has_next,
        'prev_url': url_for('search', page=paginated_results.prev_num, query=query, 
                           type=product_type, category_id=category_id, min_price=min_price, 
                           max_price=max_price, tags=tags, brand=brand, 
                           manufacturer=manufacturer, model_number=model_number,
                           provider=provider, service_code=service_code, duration=duration,
                           in_stock=in_stock, featured=featured, 
                           sort_by=sort_by, sort_order=sort_order) if paginated_results.has_prev else None,
        'next_url': url_for('search', page=paginated_results.next_num, query=query, 
                           type=product_type, category_id=category_id, min_price=min_price, 
                           max_price=max_price, tags=tags, brand=brand,
                           manufacturer=manufacturer, model_number=model_number,
                           provider=provider, service_code=service_code, duration=duration,
                           in_stock=in_stock, featured=featured,
                           sort_by=sort_by, sort_order=sort_order) if paginated_results.has_next else None,
    }
    
    return render_template(
        'search.html',
        search_summary=search_summary,
        results=paginated_results.items,
        pagination=pagination,
        product_categories=product_categories,
        service_categories=service_categories,
        brands=brands,
        manufacturers=manufacturers,
        providers=providers,
        all_tags=all_tags,
        query=query,
        product_type=product_type,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        tags=tags,
        brand=brand,
        manufacturer=manufacturer,
        model_number=model_number,
        provider=provider,
        service_code=service_code,
        duration=duration,
        in_stock=in_stock,
        featured=featured,
        sort_by=sort_by,
        sort_order=sort_order
    )


@app.route('/control/start', methods=['POST'])
@admin_required
def control_start():
    """Start the bot"""
    if not os.environ.get('BOT_TOKEN'):
        flash('BOT_TOKEN is not set in environment variables', 'danger')
        return redirect(url_for('index'))
    
    success = start_bot()
    if success:
        flash('Bot started successfully', 'success')
    else:
        flash('Failed to start bot', 'danger')
    return redirect(url_for('index'))


@app.route('/control/stop', methods=['POST'])
@admin_required
def control_stop():
    """Stop the bot"""
    if not os.environ.get('BOT_TOKEN'):
        flash('BOT_TOKEN is not set in environment variables', 'danger')
        return redirect(url_for('index'))
    
    success = stop_bot()
    if success:
        flash('Bot stopped successfully', 'success')
    else:
        flash('Failed to stop bot', 'danger')
    return redirect(url_for('index'))


@app.route('/logs')
@admin_required
def logs():
    """Get the latest logs"""
    return jsonify(bot_logs)


@app.route('/configuration', methods=['GET'])
@admin_required
def loadConfig():
    """Display the configuration page"""
    from configuration import CONFIG_PATH
    with open(CONFIG_PATH, 'r', encoding='utf-8') as configfile:
        current_config = json.load(configfile)
    return render_template('configuration.html', 
                         config=current_config,
                         config_json=json.dumps(current_config, ensure_ascii=False, indent=4))


@app.route('/update_config', methods=['POST'])
@admin_required
def update_config():
    """Update configuration"""
    from configuration import CONFIG_PATH, save_config
    
    try:
        view_type = request.form.get('view_type', '')
        
        if view_type == 'raw':
            # Handle raw JSON editing
            raw_config = request.form.get('raw_config', '')
            if raw_config:
                try:
                    new_config = json.loads(raw_config)
                    save_config(new_config)
                    flash('تنظیمات با موفقیت به‌روزرسانی شد', 'success')
                except json.JSONDecodeError:
                    flash('خطا در فرمت JSON. لطفاً بررسی کنید و دوباره تلاش کنید', 'danger')
        else:
            # Handle form-based editing
            with open(CONFIG_PATH, 'r', encoding='utf-8') as configfile:
                current_config = json.load(configfile)
            
            # Update form values
            for key in current_config:
                new_value = request.form.get(key)
                if new_value is not None:
                    current_config[key] = new_value

            # Save updated config
            save_config(current_config)
            flash('تنظیمات با موفقیت به‌روزرسانی شد', 'success')
        
        # Optional: restart bot to apply new configuration
        # stop_bot()
        # start_bot()
        
    except Exception as e:
        flash(f'خطا در به‌روزرسانی تنظیمات: {str(e)}', 'danger')
    
    return redirect(url_for('loadConfig'))


@app.route('/reset_config', methods=['POST'])
@admin_required
def reset_config():
    """Reset configuration to default"""
    from configuration import reset_to_default
    try:
        reset_to_default()
        flash('تنظیمات به حالت پیش‌فرض بازنشانی شد', 'success')
    except Exception as e:
        flash(f'خطا در بازنشانی تنظیمات: {str(e)}', 'danger')
    
    return redirect(url_for('loadConfig'))


@app.route('/database')
@admin_required
def database():
    """Display database information"""
    db_info = {
        'type': os.environ.get('DB_TYPE', 'postgresql'),
        'tables': []
    }
    
    # Initialize required variables
    table_counts = {}
    table_structures = {}
    pg_version = "Unknown"
    pg_host = os.environ.get('PGHOST', 'Unknown')
    pg_database = os.environ.get('PGDATABASE', 'Unknown')
    pg_user = os.environ.get('PGUSER', 'Unknown')
    
    # Get list of tables
    if db_info['type'] == 'postgresql':
        try:
            # Get list of all tables
            tables = db.session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).fetchall()
            db_info['tables'] = [table[0] for table in tables]
            
            # Get count for each table
            for table in db_info['tables']:
                try:
                    count_query = text(f"SELECT COUNT(*) FROM {table}")
                    count = db.session.execute(count_query).scalar()
                    table_counts[table] = count
                except Exception as e:
                    logger.error(f"Error counting records in {table}: {e}")
                    table_counts[table] = 0
            
            # Get structure for each table
            for table in db_info['tables']:
                try:
                    structure_query = text(f"""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_schema='public' AND table_name='{table}'
                        ORDER BY ordinal_position
                    """)
                    columns = db.session.execute(structure_query).fetchall()
                    table_structures[table] = columns
                except Exception as e:
                    logger.error(f"Error fetching structure for {table}: {e}")
                    table_structures[table] = []
            
            # Get PostgreSQL version
            try:
                version_query = text("SELECT version()")
                version_info = db.session.execute(version_query).scalar()
                if version_info:
                    pg_version = version_info.split()[1]
            except Exception as e:
                logger.error(f"Error fetching PostgreSQL version: {e}")
                
        except Exception as e:
            flash(f'Error fetching database tables: {str(e)}', 'danger')
            db_info['tables'] = []
    
    return render_template('database.html', 
                          db_info=db_info,
                          table_counts=table_counts,
                          table_structures=table_structures,
                          pg_version=pg_version,
                          pg_host=pg_host,
                          pg_database=pg_database,
                          pg_user=pg_user)


@app.route('/view_table/<table_name>')
@admin_required
def view_table_data(table_name):
    """View data in a specific table"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    try:
        # Get total count
        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
        total_count = db.session.execute(count_query).scalar()
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get data with pagination
        data_query = text(f"SELECT * FROM {table_name} LIMIT {per_page} OFFSET {offset}")
        rows = db.session.execute(data_query).fetchall()
        
        # Get column names
        columns_query = text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        columns = [col[0] for col in db.session.execute(columns_query).fetchall()]
        
        # Format data as list of dicts
        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # Format datetime objects for display
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                row_dict[col] = value
            data.append(row_dict)
        
        # Generate pagination data
        pagination = get_pagination(page, per_page, total_count, 'view_table_data', table_name=table_name)
        
        return render_template('table_data.html', 
                              table_name=table_name, 
                              columns=columns, 
                              data=data, 
                              pagination=pagination)
    
    except Exception as e:
        import traceback
        app.logger.error(f"View table error: {str(e)}")
        app.logger.error(traceback.format_exc())
        flash(f'خطا در بازیابی داده‌ها: {str(e)}', 'danger')
        return redirect(url_for('database'))


@app.route('/execute_sql', methods=['POST'])
@admin_required
def execute_sql():
    """Execute a SQL query and return results as JSON"""
    # Handle both form data and JSON requests
    if request.is_json:
        data = request.get_json()
        sql_query = data.get('sql_query', '')
    else:
        sql_query = request.form.get('sql_query', '')
    
    if not sql_query:
        return jsonify({
            'success': False,
            'message': 'No SQL query provided'
        })
    
    try:
        # Execute the query
        result = db.session.execute(text(sql_query))
        
        # Check if query returns columns (has results)
        if hasattr(result, 'keys'):
            # Get column names
            columns = result.keys()
            
            # Format data as list of dicts
            data = []
            for row in result:
                row_dict = {}
                for i, col in enumerate(columns):
                    # Handle datetime objects
                    if isinstance(row[i], datetime):
                        row_dict[col] = row[i].isoformat()
                    else:
                        row_dict[col] = row[i]
                data.append(row_dict)
            
            db.session.commit()
            return jsonify({
                'success': True,
                'results': data,
                'columns': [str(col) for col in columns],
                'rowCount': len(data)
            })
        else:
            # For queries that don't return rows (INSERT, UPDATE, etc.)
            db.session.commit()
            affected_rows = 0
            if hasattr(result, 'rowcount'):
                affected_rows = result.rowcount
            return jsonify({
                'success': True,
                'message': 'Query executed successfully',
                'affected_rows': affected_rows
            })
    
    except Exception as e:
        import traceback
        app.logger.error(f"SQL execution error: {str(e)}")
        app.logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/export_table_csv/<table_name>')
@admin_required
def export_table_csv(table_name):
    """Export table data as CSV"""
    try:
        # Get all data
        data_query = text(f"SELECT * FROM {table_name}")
        rows = db.session.execute(data_query).fetchall()
        
        # Get column names
        columns_query = text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        columns = [col[0] for col in db.session.execute(columns_query).fetchall()]
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(columns)
        
        # Write data
        for row in rows:
            row_values = []
            for value in row:
                # Handle datetime objects
                if isinstance(value, datetime):
                    row_values.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    row_values.append(value)
            writer.writerow(row_values)
        
        # Create response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{table_name}-{datetime.now().strftime("%Y%m%d")}.csv'
        )
    
    except Exception as e:
        import traceback
        app.logger.error(f"CSV Export error: {str(e)}")
        app.logger.error(traceback.format_exc())
        flash(f'خطا در صدور CSV: {str(e)}', 'danger')
        return redirect(url_for('view_table_data', table_name=table_name))


# Product management routes
@app.route('/admin/products')
@admin_required
def admin_products():
    """List all products for admin"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Query products of type 'product'
    products = Product.query.filter_by(product_type='product').order_by(Product.id.desc()).paginate(page=page, per_page=per_page)
    
    # Get categories for dropdown
    categories = Category.query.filter_by(cat_type='product').all()
    
    return render_template('admin/products.html', 
                          products=products,
                          categories=categories)


@app.route('/admin/services')
@admin_required
def admin_services():
    """List all services for admin"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Query products of type 'service'
    services = Product.query.filter_by(product_type='service').order_by(Product.id.desc()).paginate(page=page, per_page=per_page)
    
    # Get categories for dropdown
    categories = Category.query.filter_by(cat_type='service').all()
    
    return render_template('admin/services.html', 
                          services=services,
                          categories=categories)


@app.route('/admin/product/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    """Add a new product"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            price = request.form.get('price')
            description = request.form.get('description')
            category_id = request.form.get('category_id')
            
            # Validate required fields
            if not name or not price or not category_id:
                flash('لطفاً تمام فیلدهای الزامی را پر کنید', 'danger')
                return redirect(url_for('add_product'))
            
            # Create new product
            product = Product(
                name=name,
                price=int(price),
                description=description,
                category_id=int(category_id),
                product_type='product'
            )
            
            # Process single photo upload
            photo = request.files.get('photo')
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                
                # Save file locally
                photo_path = os.path.join(app.config['UPLOADED_MEDIA_DEST'], filename)
                photo.save(photo_path)
                
                # Set photo URL
                photo_url = os.path.join('uploads', filename)
                product.photo_url = photo_url
            
            # Save product to database
            db.session.add(product)
            db.session.commit()
            
            # Process multiple media uploads
            media_files = request.files.getlist('media')
            for file in media_files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    ext = filename.rsplit('.', 1)[1].lower()
                    
                    # Determine file type
                    file_type = 'video' if ext == 'mp4' else 'photo'
                    
                    # Save file locally
                    file_path = os.path.join(app.config['UPLOADED_MEDIA_DEST'], filename)
                    file.save(file_path)
                    
                    # Upload to Telegram and get file_id
                    file_id = None
                    if BOT_AVAILABLE and bot is not None:
                        try:
                            # Use bot to upload file and get file_id
                            with open(file_path, 'rb') as f:
                                if file_type == 'photo':
                                    # Send photo to Telegram
                                    message = asyncio.run(bot.send_photo(chat_id=ADMIN_ID, photo=f))
                                    # Extract file_id
                                    file_id = message.photo[-1].file_id
                                else:  # video
                                    # Send video to Telegram
                                    message = asyncio.run(bot.send_video(chat_id=ADMIN_ID, video=f))
                                    # Extract file_id
                                    file_id = message.video.file_id
                        except Exception as e:
                            logger.error(f"Error uploading to Telegram: {e}")
                    
                    # If couldn't get file_id from Telegram, use local path as fallback
                    if not file_id:
                        file_id = os.path.join('uploads', filename)
                    
                    # Create product media record
                    media = ProductMedia(
                        product_id=product.id,
                        file_id=file_id,
                        file_type=file_type,
                        local_path=os.path.join('uploads', filename)
                    )
                    db.session.add(media)
            
            db.session.commit()
            flash('محصول با موفقیت اضافه شد', 'success')
            return redirect(url_for('admin_products'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در افزودن محصول: {str(e)}', 'danger')
    
    # Get categories for dropdown
    categories = Category.query.filter_by(cat_type='product').all()
    
    return render_template('admin/product_form.html',
                         product=None,
                         categories=categories,
                         action='add')


@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """Edit an existing product"""
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            # Update product data
            product.name = request.form.get('name')
            product.price = int(request.form.get('price'))
            product.description = request.form.get('description')
            product.category_id = int(request.form.get('category_id'))
            
            # Process single photo upload
            photo = request.files.get('photo')
            if photo and photo.filename and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                
                # Save file locally
                photo_path = os.path.join(app.config['UPLOADED_MEDIA_DEST'], filename)
                photo.save(photo_path)
                
                # Set photo URL
                photo_url = os.path.join('uploads', filename)
                product.photo_url = photo_url
            
            # Save changes
            db.session.commit()
            flash('محصول با موفقیت به‌روزرسانی شد', 'success')
            return redirect(url_for('admin_products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در به‌روزرسانی محصول: {str(e)}', 'danger')
    
    # Get categories for dropdown
    categories = Category.query.filter_by(cat_type='product').all()
    
    return render_template('admin/product_form.html',
                         product=product,
                         categories=categories,
                         action='edit')


@app.route('/admin/product/<int:product_id>/media', methods=['GET'])
@admin_required
def product_media(product_id):
    """Product media management page"""
    product = Product.query.get_or_404(product_id)
    media = ProductMedia.query.filter_by(product_id=product_id).all()
    
    return render_template('admin/product_media.html',
                         product=product,
                         media=media)


@app.route('/admin/service/add', methods=['GET', 'POST'])
@admin_required
def add_service():
    """Add a new service"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            price = request.form.get('price')
            description = request.form.get('description')
            category_id = request.form.get('category_id')
            
            # Validate required fields
            if not name or not price or not category_id:
                flash('لطفاً تمام فیلدهای الزامی را پر کنید', 'danger')
                return redirect(url_for('add_service'))
            
            # Create new service (using Product model with type='service')
            service = Product(
                name=name,
                price=int(price),
                description=description,
                category_id=int(category_id),
                product_type='service'
            )
            
            # Process single photo upload
            photo = request.files.get('photo')
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                
                # Save file locally
                photo_path = os.path.join(app.config['UPLOADED_MEDIA_DEST'], filename)
                photo.save(photo_path)
                
                # Set photo URL
                photo_url = os.path.join('uploads', filename)
                service.photo_url = photo_url
            
            # Save service to database
            db.session.add(service)
            db.session.commit()
            
            # Process multiple media uploads
            media_files = request.files.getlist('media')
            for file in media_files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    ext = filename.rsplit('.', 1)[1].lower()
                    
                    # Determine file type
                    file_type = 'video' if ext == 'mp4' else 'photo'
                    
                    # Save file locally
                    file_path = os.path.join(app.config['UPLOADED_MEDIA_DEST'], filename)
                    file.save(file_path)
                    
                    # Upload to Telegram and get file_id
                    file_id = None
                    if BOT_AVAILABLE and bot is not None:
                        try:
                            # Use bot to upload file and get file_id
                            with open(file_path, 'rb') as f:
                                if file_type == 'photo':
                                    # Send photo to Telegram
                                    message = asyncio.run(bot.send_photo(chat_id=ADMIN_ID, photo=f))
                                    # Extract file_id
                                    file_id = message.photo[-1].file_id
                                else:  # video
                                    # Send video to Telegram
                                    message = asyncio.run(bot.send_video(chat_id=ADMIN_ID, video=f))
                                    # Extract file_id
                                    file_id = message.video.file_id
                        except Exception as e:
                            logger.error(f"Error uploading to Telegram: {e}")
                    
                    # If couldn't get file_id from Telegram, use local path as fallback
                    if not file_id:
                        file_id = os.path.join('uploads', filename)
                    
                    # Create service media record
                    media = ProductMedia(
                        product_id=service.id,
                        file_id=file_id,
                        file_type=file_type,
                        local_path=os.path.join('uploads', filename)
                    )
                    db.session.add(media)
            
            db.session.commit()
            flash('خدمت با موفقیت اضافه شد', 'success')
            return redirect(url_for('admin_services'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در افزودن خدمت: {str(e)}', 'danger')
    
    # Get categories for dropdown
    categories = Category.query.filter_by(cat_type='service').all()
    
    return render_template('admin/service_form.html',
                         service=None,
                         categories=categories,
                         action='add')


@app.route('/admin/service/edit/<int:service_id>', methods=['GET', 'POST'])
@admin_required
def edit_service(service_id):
    """Edit an existing service"""
    service = Product.query.get_or_404(service_id)
    
    if request.method == 'POST':
        try:
            # Update service data
            service.name = request.form.get('name')
            service.price = int(request.form.get('price'))
            service.description = request.form.get('description')
            service.category_id = int(request.form.get('category_id'))
            
            # Process single photo upload
            photo = request.files.get('photo')
            if photo and photo.filename and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                
                # Save file locally
                photo_path = os.path.join(app.config['UPLOADED_MEDIA_DEST'], filename)
                photo.save(photo_path)
                
                # Set photo URL
                photo_url = os.path.join('uploads', filename)
                service.photo_url = photo_url
            
            # Save changes
            db.session.commit()
            flash('خدمت با موفقیت به‌روزرسانی شد', 'success')
            return redirect(url_for('admin_services'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در به‌روزرسانی خدمت: {str(e)}', 'danger')
    
    # Get categories for dropdown
    categories = Category.query.filter_by(cat_type='service').all()
    
    return render_template('admin/service_form.html',
                         service=service,
                         categories=categories,
                         action='edit')


@app.route('/admin/service/<int:service_id>/media', methods=['GET'])
@admin_required
def service_media(service_id):
    """Service media management page"""
    service = Product.query.get_or_404(service_id)
    media = ProductMedia.query.filter_by(product_id=service_id).all()
    
    return render_template('admin/service_media.html',
                         service=service,
                         media=media)


# Media management routes
@app.route('/admin/product/<int:product_id>/add_media', methods=['GET', 'POST'])
@admin_required
def add_product_media(product_id):
    """Add media to a product"""
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            # Process multiple media uploads
            media_files = request.files.getlist('media')
            media_added = 0
            
            for file in media_files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    ext = filename.rsplit('.', 1)[1].lower()
                    
                    # Determine file type
                    file_type = 'video' if ext == 'mp4' else 'photo'
                    
                    # Generate unique filename
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    
                    # Save file locally
                    file_path = os.path.join(app.config['UPLOADED_MEDIA_DEST'], unique_filename)
                    file.save(file_path)
                    
                    # Upload to Telegram and get file_id
                    file_id = None
                    if BOT_AVAILABLE and bot is not None:
                        try:
                            # Use bot to upload file and get file_id
                            with open(file_path, 'rb') as f:
                                if file_type == 'photo':
                                    # Send photo to Telegram
                                    message = asyncio.run(bot.send_photo(chat_id=ADMIN_ID, photo=f))
                                    # Extract file_id
                                    file_id = message.photo[-1].file_id
                                else:  # video
                                    # Send video to Telegram
                                    message = asyncio.run(bot.send_video(chat_id=ADMIN_ID, video=f))
                                    # Extract file_id
                                    file_id = message.video.file_id
                        except Exception as e:
                            logger.error(f"Error uploading to Telegram: {e}")
                    
                    # If couldn't get file_id from Telegram, use local path as fallback
                    if not file_id:
                        file_id = os.path.join('uploads', unique_filename)
                    
                    # Create product media record
                    media = ProductMedia(
                        product_id=product.id,
                        file_id=file_id,
                        file_type=file_type,
                        local_path=os.path.join('uploads', unique_filename)
                    )
                    db.session.add(media)
                    media_added += 1
            
            if media_added > 0:
                db.session.commit()
                flash(f'{media_added} فایل رسانه با موفقیت اضافه شد', 'success')
            else:
                flash('هیچ فایل معتبری آپلود نشد', 'warning')
                
            return redirect(url_for('product_media', product_id=product_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در افزودن رسانه: {str(e)}', 'danger')
    
    return render_template('admin/add_media.html',
                         item=product,
                         item_type='product')


@app.route('/admin/service/<int:service_id>/add_media', methods=['GET', 'POST'])
@admin_required
def add_service_media(service_id):
    """Add media to a service"""
    service = Product.query.get_or_404(service_id)
    
    if request.method == 'POST':
        try:
            # Process multiple media uploads
            media_files = request.files.getlist('media')
            media_added = 0
            
            for file in media_files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    ext = filename.rsplit('.', 1)[1].lower()
                    
                    # Determine file type
                    file_type = 'video' if ext == 'mp4' else 'photo'
                    
                    # Generate unique filename
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    
                    # Save file locally
                    file_path = os.path.join(app.config['UPLOADED_MEDIA_DEST'], unique_filename)
                    file.save(file_path)
                    
                    # Upload to Telegram and get file_id
                    file_id = None
                    if BOT_AVAILABLE and bot is not None:
                        try:
                            # Use bot to upload file and get file_id
                            with open(file_path, 'rb') as f:
                                if file_type == 'photo':
                                    # Send photo to Telegram
                                    message = asyncio.run(bot.send_photo(chat_id=ADMIN_ID, photo=f))
                                    # Extract file_id
                                    file_id = message.photo[-1].file_id
                                else:  # video
                                    # Send video to Telegram
                                    message = asyncio.run(bot.send_video(chat_id=ADMIN_ID, video=f))
                                    # Extract file_id
                                    file_id = message.video.file_id
                        except Exception as e:
                            logger.error(f"Error uploading to Telegram: {e}")
                    
                    # If couldn't get file_id from Telegram, use local path as fallback
                    if not file_id:
                        file_id = os.path.join('uploads', unique_filename)
                    
                    # Create service media record
                    media = ProductMedia(
                        product_id=service.id,
                        file_id=file_id,
                        file_type=file_type,
                        local_path=os.path.join('uploads', unique_filename)
                    )
                    db.session.add(media)
                    media_added += 1
            
            if media_added > 0:
                db.session.commit()
                flash(f'{media_added} فایل رسانه با موفقیت اضافه شد', 'success')
            else:
                flash('هیچ فایل معتبری آپلود نشد', 'warning')
                
            return redirect(url_for('service_media', service_id=service_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در افزودن رسانه: {str(e)}', 'danger')
    
    return render_template('admin/add_media.html',
                         item=service,
                         item_type='service')


@app.route('/admin/product/<int:product_id>/delete_media/<int:media_id>', methods=['POST'])
@admin_required
def delete_product_media(product_id, media_id):
    """Delete media from a product"""
    media = ProductMedia.query.get_or_404(media_id)
    
    # Verify media belongs to product
    if media.product_id != product_id:
        flash('خطای دسترسی: این فایل رسانه متعلق به این محصول نیست', 'danger')
        return redirect(url_for('product_media', product_id=product_id))
    
    try:
        # Delete local file if it exists
        if media.local_path:
            file_path = os.path.join(app.static_folder, media.local_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Delete database record
        db.session.delete(media)
        db.session.commit()
        
        flash('فایل رسانه با موفقیت حذف شد', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطا در حذف فایل رسانه: {str(e)}', 'danger')
    
    return redirect(url_for('product_media', product_id=product_id))


@app.route('/admin/service/<int:service_id>/delete_media/<int:media_id>', methods=['POST'])
@admin_required
def delete_service_media(service_id, media_id):
    """Delete media from a service"""
    media = ProductMedia.query.get_or_404(media_id)
    
    # Verify media belongs to service
    if media.product_id != service_id:
        flash('خطای دسترسی: این فایل رسانه متعلق به این خدمت نیست', 'danger')
        return redirect(url_for('service_media', service_id=service_id))
    
    try:
        # Delete local file if it exists
        if media.local_path:
            file_path = os.path.join(app.static_folder, media.local_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Delete database record
        db.session.delete(media)
        db.session.commit()
        
        flash('فایل رسانه با موفقیت حذف شد', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'خطا در حذف فایل رسانه: {str(e)}', 'danger')
    
    return redirect(url_for('service_media', service_id=service_id))


# Admin Dashboard
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Dashboard for admin panel with key statistics and quick actions"""
    # Get stats for dashboard
    products_count = Product.query.filter_by(product_type='product').count()
    services_count = Product.query.filter_by(product_type='service').count()
    inquiries_count = Inquiry.query.count()
    
    # Get recent inquiries for dashboard
    recent_inquiries = []
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(5).all()
    
    for inquiry in inquiries:
        product_name = None
        if inquiry.product_id:
            product = Product.query.get(inquiry.product_id)
            if product:
                product_name = product.name
        
        recent_inquiries.append({
            'id': inquiry.id,
            'name': inquiry.name,
            'phone': inquiry.phone,
            'product_name': product_name,
            'date': inquiry.created_at.strftime('%Y-%m-%dT%H:%M:%S')
        })
    
    stats = {
        'products_count': products_count,
        'services_count': services_count,
        'inquiries_count': inquiries_count
    }
    
    return render_template('admin_index.html', stats=stats, recent_inquiries=recent_inquiries)

# Admin Inquiries
@app.route('/admin/inquiries')
@login_required
@admin_required
def admin_inquiries():
    """Display and manage price inquiries"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    product_id = request.args.get('product_id')
    
    # Build query
    query = Inquiry.query
    
    if start_date:
        query = query.filter(Inquiry.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
    
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        end_date_obj = datetime.combine(end_date_obj.date(), datetime.max.time())
        query = query.filter(Inquiry.created_at <= end_date_obj)
    
    if product_id and product_id.isdigit():
        query = query.filter(Inquiry.product_id == int(product_id))
    
    # Paginate results
    pagination = query.order_by(Inquiry.created_at.desc()).paginate(page=page, per_page=per_page)
    inquiries = pagination.items
    
    # Format inquiry data
    formatted_inquiries = []
    for inquiry in inquiries:
        product_name = None
        if inquiry.product_id:
            product = Product.query.get(inquiry.product_id)
            if product:
                product_name = product.name
        
        formatted_inquiries.append({
            'id': inquiry.id,
            'name': inquiry.name,
            'phone': inquiry.phone,
            'description': inquiry.description,
            'product_name': product_name,
            'date': inquiry.created_at.strftime('%Y-%m-%dT%H:%M:%S')
        })
    
    # Get products for filter dropdown
    products = Product.query.all()
    
    return render_template('admin_inquiries.html', inquiries=formatted_inquiries, products=products, pagination=pagination)

# Admin Delete Inquiry
@app.route('/admin/inquiry/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_inquiry():
    """Delete a price inquiry"""
    inquiry_id = request.form.get('inquiry_id', type=int)
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    
    db.session.delete(inquiry)
    db.session.commit()
    
    flash('استعلام با موفقیت حذف شد.', 'success')
    return redirect(url_for('admin_inquiries'))

# Admin Export Inquiries to Excel
@app.route('/admin/inquiries/export')
@login_required
@admin_required
def admin_export_inquiries():
    """Export price inquiries to CSV/Excel file"""
    # Get all inquiries
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    
    # Create CSV file in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['نام', 'شماره تماس', 'محصول', 'توضیحات', 'تاریخ'])
    
    # Write data rows
    for inquiry in inquiries:
        product_name = 'عمومی'
        if inquiry.product_id:
            product = Product.query.get(inquiry.product_id)
            if product:
                product_name = product.name
        
        writer.writerow([
            inquiry.name,
            inquiry.phone,
            product_name,
            inquiry.description,
            inquiry.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Prepare response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'inquiries_export_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
    )

# Admin Categories
@app.route('/admin/categories')
@login_required
@admin_required
def admin_categories():
    """List and manage all categories"""
    categories = Category.query.all()
    return render_template('admin_categories.html', categories=categories)

# Admin Add Category
@app.route('/admin/categories/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_category():
    """Add a new category"""
    if request.method == 'POST':
        name = request.form.get('name')
        parent_id = request.form.get('parent_id')
        cat_type = request.form.get('cat_type', 'product')
        
        if not name:
            flash('نام دسته‌بندی الزامی است.', 'danger')
            return redirect(url_for('admin_add_category'))
        
        # Convert parent_id to int or None
        if parent_id and parent_id.isdigit():
            parent_id = int(parent_id)
        else:
            parent_id = None
        
        category = Category(name=name, parent_id=parent_id, cat_type=cat_type)
        db.session.add(category)
        db.session.commit()
        
        flash('دسته‌بندی جدید با موفقیت ایجاد شد.', 'success')
        return redirect(url_for('admin_categories'))
    
    # Get all categories for parent dropdown
    categories = Category.query.all()
    return render_template('admin_category_form.html', categories=categories, category=None)

# Admin Edit Category
@app.route('/admin/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_category(category_id):
    """Edit an existing category"""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        parent_id = request.form.get('parent_id')
        cat_type = request.form.get('cat_type', 'product')
        
        if not name:
            flash('نام دسته‌بندی الزامی است.', 'danger')
            return redirect(url_for('admin_edit_category', category_id=category_id))
        
        # Convert parent_id to int or None
        if parent_id and parent_id.isdigit() and int(parent_id) != category_id:
            parent_id = int(parent_id)
        else:
            parent_id = None
        
        category.name = name
        category.parent_id = parent_id
        category.cat_type = cat_type
        
        db.session.commit()
        
        flash('دسته‌بندی با موفقیت ویرایش شد.', 'success')
        return redirect(url_for('admin_categories'))
    
    # Get all categories for parent dropdown
    categories = Category.query.all()
    return render_template('admin_category_form.html', categories=categories, category=category)

# Admin Delete Category
@app.route('/admin/categories/delete/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_category(category_id):
    """Delete a category"""
    category = Category.query.get_or_404(category_id)
    
    # Check if category has products
    products_count = Product.query.filter_by(category_id=category_id).count()
    if products_count > 0:
        flash(f'این دسته‌بندی دارای {products_count} محصول/خدمت است و نمی‌تواند حذف شود.', 'danger')
        return redirect(url_for('admin_categories'))
    
    # Check if category has subcategories
    subcategories_count = Category.query.filter_by(parent_id=category_id).count()
    if subcategories_count > 0:
        flash(f'این دسته‌بندی دارای {subcategories_count} زیردسته است و نمی‌تواند حذف شود.', 'danger')
        return redirect(url_for('admin_categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('دسته‌بندی با موفقیت حذف شد.', 'success')
    return redirect(url_for('admin_categories'))

# Educational Content
@app.route('/admin/education')
@login_required
@admin_required
def admin_education():
    """List and manage educational content"""
    contents = EducationalContent.query.all()
    return render_template('admin_education.html', contents=contents)

# Add Educational Content
@app.route('/admin/education/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_education():
    """Add a new educational content item"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        content_type = request.form.get('content_type', 'text')
        
        if not title or not content or not category:
            flash('همه فیلدهای الزامی باید تکمیل شوند.', 'danger')
            return redirect(url_for('admin_add_education'))
        
        educational_content = EducationalContent(
            title=title,
            content=content,
            category=category,
            content_type=content_type
        )
        
        db.session.add(educational_content)
        db.session.commit()
        
        flash('محتوای آموزشی با موفقیت ایجاد شد.', 'success')
        return redirect(url_for('admin_education'))
    
    return render_template('admin_education_form.html', content=None)

# Edit Educational Content
@app.route('/admin/education/edit/<int:content_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_education(content_id):
    """Edit an existing educational content item"""
    content = EducationalContent.query.get_or_404(content_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        content_text = request.form.get('content')
        category = request.form.get('category')
        content_type = request.form.get('content_type', 'text')
        
        if not title or not content_text or not category:
            flash('همه فیلدهای الزامی باید تکمیل شوند.', 'danger')
            return redirect(url_for('admin_edit_education', content_id=content_id))
        
        content.title = title
        content.content = content_text
        content.category = category
        content.content_type = content_type
        
        db.session.commit()
        
        flash('محتوای آموزشی با موفقیت ویرایش شد.', 'success')
        return redirect(url_for('admin_education'))
    
    return render_template('admin_education_form.html', content=content)

# Delete Educational Content
@app.route('/admin/education/delete/<int:content_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_education(content_id):
    """Delete an educational content item"""
    content = EducationalContent.query.get_or_404(content_id)
    
    db.session.delete(content)
    db.session.commit()
    
    flash('محتوای آموزشی با موفقیت حذف شد.', 'success')
    return redirect(url_for('admin_education'))

# Static Content
@app.route('/admin/content')
@login_required
@admin_required
def admin_static_content():
    """Manage static content (contact/about)"""
    contact_content = StaticContent.query.filter_by(content_type='contact').first()
    about_content = StaticContent.query.filter_by(content_type='about').first()
    
    if not contact_content:
        contact_content = StaticContent(content_type='contact', content='')
        db.session.add(contact_content)
    
    if not about_content:
        about_content = StaticContent(content_type='about', content='')
        db.session.add(about_content)
    
    db.session.commit()
    
    return render_template('admin_content.html', contact_content=contact_content, about_content=about_content)

# Update Static Content
@app.route('/admin/content/update', methods=['POST'])
@login_required
@admin_required
def admin_update_static_content():
    """Update static content (contact/about)"""
    content_type = request.form.get('content_type')
    content = request.form.get('content', '')
    
    if content_type not in ['contact', 'about']:
        flash('نوع محتوا نامعتبر است.', 'danger')
        return redirect(url_for('admin_static_content'))
    
    static_content = StaticContent.query.filter_by(content_type=content_type).first()
    
    if not static_content:
        static_content = StaticContent(content_type=content_type, content=content)
        db.session.add(static_content)
    else:
        static_content.content = content
    
    db.session.commit()
    
    flash('محتوا با موفقیت به‌روزرسانی شد.', 'success')
    return redirect(url_for('admin_static_content'))

# Import/Export Data
@app.route('/admin/import_export')
@login_required
@admin_required
def admin_import_export():
    """Import/Export data functionality"""
    return render_template('admin_import_export.html')

# Export Data
@app.route('/admin/export/<entity_type>')
@login_required
@admin_required
def admin_export_data(entity_type):
    """Export data to CSV file"""
    if entity_type not in ['products', 'services', 'categories']:
        flash('نوع داده نامعتبر است.', 'danger')
        return redirect(url_for('admin_import_export'))
    
    temp_dir = tempfile.mkdtemp()
    filename = f"{entity_type}_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    filepath = os.path.join(temp_dir, filename)
    
    success = db_instance.export_to_csv(entity_type, filepath)
    
    if not success:
        flash('خطا در خروجی گرفتن داده‌ها.', 'danger')
        shutil.rmtree(temp_dir)
        return redirect(url_for('admin_import_export'))
    
    response = send_file(
        filepath,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )
    
    # Clean up temp directory after response is sent
    @response.call_on_close
    def cleanup():
        shutil.rmtree(temp_dir)
    
    return response

# Import Data
@app.route('/admin/import/<entity_type>', methods=['POST'])
@login_required
@admin_required
def admin_import_data(entity_type):
    """Import data from CSV file"""
    if entity_type not in ['products', 'services', 'categories']:
        flash('نوع داده نامعتبر است.', 'danger')
        return redirect(url_for('admin_import_export'))
    
    if 'file' not in request.files:
        flash('فایلی انتخاب نشده است.', 'danger')
        return redirect(url_for('admin_import_export'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('فایلی انتخاب نشده است.', 'danger')
        return redirect(url_for('admin_import_export'))
    
    if not file.filename.endswith('.csv'):
        flash('فرمت فایل باید CSV باشد.', 'danger')
        return redirect(url_for('admin_import_export'))
    
    temp_dir = tempfile.mkdtemp()
    filepath = os.path.join(temp_dir, secure_filename(file.filename))
    file.save(filepath)
    
    try:
        success_count, error_count = db_instance.import_from_csv(entity_type, filepath)
        
        if success_count > 0:
            flash(f'{success_count} مورد با موفقیت وارد شد. {error_count} خطا رخ داد.', 'success')
        else:
            flash(f'خطا در وارد کردن داده‌ها. {error_count} خطا رخ داد.', 'danger')
    
    except Exception as e:
        flash(f'خطا در وارد کردن داده‌ها: {str(e)}', 'danger')
    
    finally:
        shutil.rmtree(temp_dir)
    
    return redirect(url_for('admin_import_export'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)