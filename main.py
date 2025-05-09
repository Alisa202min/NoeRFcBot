from app import app
from flask import render_template, request, redirect, url_for, flash, jsonify, abort, send_file
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

@app.route('/configuration')
def loadConfig():
    """Display the configuration page"""
    from configuration import CONFIG_PATH
    with open(CONFIG_PATH, 'r', encoding='utf-8') as configfile:
        current_config = json.load(configfile)
    return render_template('configuration.html', 
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

    # Now using PostgreSQL
    return render_template('database.html', 
                          db_exists=db_exists,
                          db_path=db_path,
                          db_size=db_size)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)