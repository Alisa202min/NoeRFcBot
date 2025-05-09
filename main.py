from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, send_file
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
from database import Database
import ssl
from aiohttp import web
from werkzeug.utils import secure_filename
import io
import uuid
import csv
from configuration import ADMIN_ID

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "رمز موقت برای ربات RFCBot")

# Configure uploads directory
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db = Database()

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
    webhook_app = web.Application()

    try:
        if setup_webhook is not None:
            # Setup webhook handler
            asyncio.run(setup_webhook(webhook_app, WEBHOOK_PATH))

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

@app.route('/control/start', methods=['POST'])
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
def logs():
    """Get the latest logs"""
    return jsonify(bot_logs)

@app.route('/configuration', methods=['GET'])
def loadConfig():
    """Display the configuration page"""
    from configuration import CONFIG_PATH
    with open(CONFIG_PATH, 'r', encoding='utf-8') as configfile:
        current_config = json.load(configfile)
    return render_template('configuration.html', 
                         config=current_config,
                         config_json=json.dumps(current_config, ensure_ascii=False, indent=4))

@app.route('/update_config', methods=['POST'])
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
                    flash('پیکربندی با موفقیت به‌روزرسانی شد.', 'success')
                except json.JSONDecodeError:
                    flash('خطا در ساختار JSON. لطفاً ساختار را بررسی کنید.', 'danger')
                    return redirect(url_for('loadConfig'))
            else:
                flash('فایل پیکربندی خالی است.', 'danger')
                return redirect(url_for('loadConfig'))
        else:
            # Handle form-based editing
            with open(CONFIG_PATH, 'r', encoding='utf-8') as configfile:
                current_config = json.load(configfile)
            
            # Update config from form data
            for key in current_config:
                if key in request.form:
                    form_value = request.form.get(key, '')
                    # Convert ADMIN_ID to int if it's a number
                    if key == 'ADMIN_ID' and form_value and form_value.isdigit():
                        current_config[key] = int(form_value)
                    else:
                        current_config[key] = form_value
            
            # Save updated config
            save_config(current_config)
            flash('پیکربندی با موفقیت به‌روزرسانی شد.', 'success')
    
    except Exception as e:
        flash(f'خطا در به‌روزرسانی پیکربندی: {str(e)}', 'danger')
    
    return redirect(url_for('loadConfig'))

@app.route('/config/reset', methods=['POST'])
def reset_config():
    """Reset configuration to default"""
    try:
        from configuration import reset_to_default
        reset_to_default()
        flash('پیکربندی با موفقیت به مقادیر پیش‌فرض بازنشانی شد.', 'success')
    except Exception as e:
        flash(f'خطا در بازنشانی پیکربندی: {str(e)}', 'danger')
        return '', 500
    
    return '', 200

@app.route('/database')
def database():
    """Display database information"""
    # Get PostgreSQL database information
    pg_info = {}
    table_counts = {}
    table_structures = {}
    
    try:
        # Get PostgreSQL version
        with db.conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            pg_version = cursor.fetchone()[0].split()[1]
            
            # Get connection info
            pg_info = {
                'pg_version': pg_version,
                'pg_host': os.environ.get('PGHOST', 'localhost'),
                'pg_port': os.environ.get('PGPORT', '5432'),
                'pg_database': os.environ.get('PGDATABASE', 'postgres'),
                'pg_user': os.environ.get('PGUSER', 'postgres')
            }
            
            # Get table counts
            cursor.execute("""
                SELECT tablename FROM pg_catalog.pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                table_counts[table] = count
                
                # Get table structure
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position;
                """, (table,))
                columns = [dict(row) for row in cursor.fetchall()]
                table_structures[table] = columns
    except Exception as e:
        flash(f"Error getting database information: {str(e)}", "danger")
        logger.error(f"Database error: {str(e)}")
    
    return render_template('database.html',
                          pg_version=pg_info.get('pg_version', 'Unknown'),
                          pg_host=pg_info.get('pg_host', 'Unknown'),
                          pg_database=pg_info.get('pg_database', 'Unknown'),
                          pg_user=pg_info.get('pg_user', 'Unknown'),
                          table_counts=table_counts,
                          table_structures=table_structures)

@app.route('/view_table_data/<table_name>')
def view_table_data(table_name):
    """View data in a specific table"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get total records
        with db.conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            total_count = cursor.fetchone()[0]
            
            # Get column names
            cursor.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            columns = [row[0] for row in cursor.fetchall()]
            
            # Get data with pagination
            offset = (page - 1) * per_page
            cursor.execute(f"""
                SELECT * FROM {table_name}
                ORDER BY (SELECT c.column_name
                          FROM information_schema.key_column_usage k
                          JOIN information_schema.table_constraints c ON k.constraint_name = c.constraint_name
                          WHERE k.table_name = %s AND c.constraint_type = 'PRIMARY KEY'
                          LIMIT 1) NULLS LAST,
                         id NULLS LAST
                LIMIT %s OFFSET %s;
            """, (table_name, per_page, offset))
            data = cursor.fetchall()
            
            # Convert to list of dicts
            rows = []
            for row in data:
                row_dict = {}
                for i, col in enumerate(columns):
                    row_dict[col] = row[i]
                rows.append(row_dict)
        
        # Get pagination
        pagination = get_pagination(page, per_page, total_count, 'view_table_data', table_name=table_name)
        
        return render_template('table_data.html',
                              table_name=table_name,
                              columns=columns,
                              rows=rows,
                              pagination=pagination)
    except Exception as e:
        flash(f"Error viewing table data: {str(e)}", "danger")
        logger.error(f"Database error: {str(e)}")
        return redirect(url_for('database'))

@app.route('/execute_sql', methods=['POST'])
def execute_sql():
    """Execute a SQL query and return results as JSON"""
    try:
        # Get SQL query from POST data
        if request.is_json:
            data = request.get_json()
            if data and 'sql_query' in data:
                sql_query = data.get('sql_query', '')
            else:
                sql_query = ''
        else:
            sql_query = request.form.get('sql_query', '')
        
        if not sql_query:
            return jsonify({'error': 'No SQL query provided'})
        
        # Check if query is SELECT or other type
        sql_query = sql_query.strip()
        is_select = sql_query.lower().startswith('select')
        
        with db.conn.cursor() as cursor:
            cursor.execute(sql_query)
            
            if is_select and cursor.description:  # Make sure description is not None
                # For SELECT queries, return the results
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i]
                    results.append(row_dict)
                
                return jsonify({
                    'results': results,
                    'count': len(results)
                })
            else:
                # For non-SELECT queries, return affected rows
                return jsonify({
                    'message': 'Query executed successfully',
                    'affected_rows': cursor.rowcount
                })
    except Exception as e:
        logger.error(f"SQL execution error: {str(e)}")
        return jsonify({'error': str(e)})
        
@app.route('/export_table_csv/<table_name>', methods=['POST'])
def export_table_csv(table_name):
    """Export table data as CSV"""
    try:
        # Get export options
        export_type = request.form.get('export_type', 'all')
        include_headers = request.form.get('include_headers') == 'on'
        
        # Prepare SQL query based on export type
        if export_type == 'all':
            sql_query = f"SELECT * FROM {table_name}"
        elif export_type == 'current':
            page = request.form.get('page', 1, type=int)
            per_page = request.form.get('per_page', 20, type=int)
            offset = (page - 1) * per_page
            sql_query = f"SELECT * FROM {table_name} LIMIT {per_page} OFFSET {offset}"
        elif export_type == 'custom':
            start_row = max(1, request.form.get('start_row', 1, type=int))
            end_row = request.form.get('end_row', 1, type=int)
            count = end_row - start_row + 1
            offset = start_row - 1
            sql_query = f"SELECT * FROM {table_name} LIMIT {count} OFFSET {offset}"
        else:
            return "Invalid export type", 400
        
        # Get column names
        with db.conn.cursor() as cursor:
            cursor.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            columns = [row[0] for row in cursor.fetchall()]
            
            # Execute query to get data
            cursor.execute(sql_query)
            rows = cursor.fetchall()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers if requested
        if include_headers:
            writer.writerow(columns)
        
        # Write data rows
        for row in rows:
            # Convert None values to empty strings
            processed_row = ['' if val is None else val for val in row]
            writer.writerow(processed_row)
        
        # Prepare response
        output.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"{table_name}_{timestamp}.csv"
        )
    except Exception as e:
        logger.error(f"CSV export error: {str(e)}")
        flash(f"خطا در خروجی CSV: {str(e)}", "danger")
        return redirect(url_for('view_table_data', table_name=table_name))
                          
# Admin product and service routes
@app.route('/admin/products')
@admin_required
def admin_products():
    """List all products for admin"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '')
    
    if search:
        products = db.search_products(search)
        total_count = len(products)
    else:
        products = db.get_products_by_category(category_id)
        total_count = len(products)
    
    # Apply pagination
    start = (page - 1) * per_page
    end = start + per_page
    products_page = products[start:end]
    
    # Get categories for the filter dropdown
    categories = db.get_categories(cat_type='product')
    
    # Get pagination data
    pagination = get_pagination(
        page, per_page, total_count, 'admin_products',
        category_id=category_id, search=search
    )
    
    return render_template('admin_products.html',
                           products=products_page,
                           categories=categories,
                           category_id=category_id,
                           search=search,
                           pagination=pagination,
                           page_type='products')

@app.route('/admin/services')
@admin_required
def admin_services():
    """List all services for admin"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '')
    
    if search:
        services = db.search_products(search, 'service')
        total_count = len(services)
    else:
        services = db.get_products_by_category(category_id, 'service')
        total_count = len(services)
    
    # Apply pagination
    start = (page - 1) * per_page
    end = start + per_page
    services_page = services[start:end]
    
    # Get categories for the filter dropdown
    categories = db.get_categories(cat_type='service')
    
    # Get pagination data
    pagination = get_pagination(
        page, per_page, total_count, 'admin_services',
        category_id=category_id, search=search
    )
    
    return render_template('admin_products.html',
                           products=services_page,
                           categories=categories,
                           category_id=category_id,
                           search=search,
                           pagination=pagination,
                           page_type='services')

# Product and service media management routes
@app.route('/admin/products/media/<int:product_id>', methods=['GET'])
@admin_required
def product_media(product_id):
    """Product media management page"""
    product = db.get_product(product_id)
    
    if not product:
        flash('محصول مورد نظر یافت نشد', 'danger')
        return redirect(url_for('admin_products'))
    
    media_files = db.get_product_media(product_id)
    
    return render_template('admin_product_media.html',
                           product=product,
                           media_files=media_files)

@app.route('/admin/services/media/<int:service_id>', methods=['GET'])
@admin_required
def service_media(service_id):
    """Service media management page"""
    service = db.get_service(service_id)
    
    if not service:
        flash('خدمت مورد نظر یافت نشد', 'danger')
        return redirect(url_for('admin_services'))
    
    media_files = db.get_service_media(service_id)
    
    return render_template('admin_service_media.html',
                           service=service,
                           media_files=media_files)

@app.route('/admin/products/media/<int:product_id>/add', methods=['GET', 'POST'])
@admin_required
def add_product_media(product_id):
    """Add media to a product"""
    product = db.get_product(product_id)
    
    if not product:
        flash('محصول مورد نظر یافت نشد', 'danger')
        return redirect(url_for('admin_products'))
    
    if request.method == 'POST':
        # Check if files were uploaded
        if 'media_files' not in request.files:
            flash('No files uploaded', 'danger')
            return redirect(request.url)
            
        files = request.files.getlist('media_files')
        
        # Track success/failure
        upload_results = []
        
        for file in files:
            if file and allowed_file(file.filename):
                # Generate a secure filename with UUID to avoid duplicates
                filename = secure_filename(file.filename)
                filename = f"{uuid.uuid4()}_{filename}"
                
                # Save the file
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Determine file type
                file_type = 'photo'
                if filename.lower().endswith('.mp4'):
                    file_type = 'video'
                
                # Add to database - in a real app this would store Telegram file_id
                # but for this admin panel we'll store the local path
                try:
                    # Get the relative path for storage in database
                    relative_path = os.path.join('uploads', filename)
                    db.add_product_media(product_id, relative_path, file_type)
                    upload_results.append({'filename': filename, 'success': True})
                except Exception as e:
                    upload_results.append({
                        'filename': filename, 
                        'success': False,
                        'error': str(e)
                    })
                    logger.error(f"Error adding product media: {e}")
            else:
                upload_results.append({
                    'filename': file.filename if file else 'Unknown',
                    'success': False,
                    'error': 'Invalid file type'
                })
        
        # Check and display results
        success_count = sum(1 for r in upload_results if r['success'])
        if success_count == len(upload_results) and success_count > 0:
            flash(f'تمام {success_count} فایل با موفقیت آپلود شد', 'success')
        elif success_count > 0:
            flash(f'{success_count} از {len(upload_results)} فایل با موفقیت آپلود شد', 'warning')
        else:
            flash('خطا در آپلود فایل‌ها', 'danger')
        
        return redirect(url_for('product_media', product_id=product_id))
    
    return render_template('admin_product_media_add.html', product=product)

@app.route('/admin/services/media/<int:service_id>/add', methods=['GET', 'POST'])
@admin_required
def add_service_media(service_id):
    """Add media to a service"""
    service = db.get_service(service_id)
    
    if not service:
        flash('خدمت مورد نظر یافت نشد', 'danger')
        return redirect(url_for('admin_services'))
    
    if request.method == 'POST':
        # Check if files were uploaded
        if 'media_files' not in request.files:
            flash('No files uploaded', 'danger')
            return redirect(request.url)
            
        files = request.files.getlist('media_files')
        
        # Track success/failure
        upload_results = []
        
        for file in files:
            if file and allowed_file(file.filename):
                # Generate a secure filename with UUID to avoid duplicates
                filename = secure_filename(file.filename)
                filename = f"{uuid.uuid4()}_{filename}"
                
                # Save the file
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Determine file type
                file_type = 'photo'
                if filename.lower().endswith('.mp4'):
                    file_type = 'video'
                
                # Add to database - in a real app this would store Telegram file_id
                # but for this admin panel we'll store the local path
                try:
                    # Get the relative path for storage in database
                    relative_path = os.path.join('uploads', filename)
                    db.add_service_media(service_id, relative_path, file_type)
                    upload_results.append({'filename': filename, 'success': True})
                except Exception as e:
                    upload_results.append({
                        'filename': filename, 
                        'success': False,
                        'error': str(e)
                    })
                    logger.error(f"Error adding service media: {e}")
            else:
                upload_results.append({
                    'filename': file.filename if file else 'Unknown',
                    'success': False,
                    'error': 'Invalid file type'
                })
        
        # Check and display results
        success_count = sum(1 for r in upload_results if r['success'])
        if success_count == len(upload_results) and success_count > 0:
            flash(f'تمام {success_count} فایل با موفقیت آپلود شد', 'success')
        elif success_count > 0:
            flash(f'{success_count} از {len(upload_results)} فایل با موفقیت آپلود شد', 'warning')
        else:
            flash('خطا در آپلود فایل‌ها', 'danger')
        
        return redirect(url_for('service_media', service_id=service_id))
    
    return render_template('admin_service_media_add.html', service=service)

@app.route('/admin/products/media/<int:product_id>/delete/<int:media_id>', methods=['POST'])
@admin_required
def delete_product_media(product_id, media_id):
    """Delete media from a product"""
    # Get the media record first to check if it exists
    media = db.get_media_by_id(media_id)
    
    if not media:
        flash('فایل مورد نظر یافت نشد', 'danger')
        return redirect(url_for('product_media', product_id=product_id))
    
    # Delete from database
    success = db.delete_product_media(media_id)
    
    if success:
        flash('فایل با موفقیت حذف شد', 'success')
    else:
        flash('خطا در حذف فایل', 'danger')
    
    return redirect(url_for('product_media', product_id=product_id))

@app.route('/admin/services/media/<int:service_id>/delete/<int:media_id>', methods=['POST'])
@admin_required
def delete_service_media(service_id, media_id):
    """Delete media from a service"""
    # Get the media record first to check if it exists
    media = db.get_service_media_by_id(media_id)
    
    if not media:
        flash('فایل مورد نظر یافت نشد', 'danger')
        return redirect(url_for('service_media', service_id=service_id))
    
    # Delete from database
    success = db.delete_service_media(media_id)
    
    if success:
        flash('فایل با موفقیت حذف شد', 'success')
    else:
        flash('خطا در حذف فایل', 'danger')
    
    return redirect(url_for('service_media', service_id=service_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)