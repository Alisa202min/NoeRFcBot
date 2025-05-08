from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
import os
import logging
import json
import psycopg2
from datetime import datetime
from werkzeug.utils import secure_filename
import subprocess
import threading

from database import Database
from configuration import load_config, save_config, reset_to_default

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "radio_frequency_store_secret_key")

# Ensure templates directory exists
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)

# Initialize database
db = Database()

# Bot process
bot_process = None
bot_status = "stopped"

def get_telegram_bot_status():
    """Check if the Telegram bot is running"""
    global bot_status
    try:
        # Check if bot process is running
        result = subprocess.run(["pgrep", "-f", "python bot.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            bot_status = "running"
        else:
            bot_status = "stopped"
    except Exception as e:
        logging.error(f"Error checking bot status: {e}")
        bot_status = "error"
    
    return bot_status

def start_telegram_bot():
    """Start the Telegram bot as a subprocess"""
    global bot_process, bot_status
    
    try:
        # Kill any existing bot process
        subprocess.run(["pkill", "-f", "python bot.py"])
        
        # Start new bot process
        bot_process = subprocess.Popen(["python", "bot.py"], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
        
        bot_status = "running"
        return True
    except Exception as e:
        logging.error(f"Error starting bot: {e}")
        bot_status = "error"
        return False

def stop_telegram_bot():
    """Stop the Telegram bot subprocess"""
    global bot_process, bot_status
    
    try:
        # Kill the bot process
        subprocess.run(["pkill", "-f", "python bot.py"])
        
        if bot_process:
            bot_process.terminate()
            bot_process = None
        
        bot_status = "stopped"
        return True
    except Exception as e:
        logging.error(f"Error stopping bot: {e}")
        bot_status = "error"
        return False

@app.route('/')
def index():
    """Homepage - displays dashboard with bot status"""
    # Check environment variables
    env_status = {
        "BOT_TOKEN": "Set" if os.environ.get("BOT_TOKEN") else "Not Set",
        "ADMIN_ID": "Set" if os.environ.get("ADMIN_ID") else "Not Set",
        "DB_TYPE": os.environ.get("DB_TYPE", "PostgreSQL")
    }
    
    # Check database existence
    db_exists = True  # PostgreSQL is always available
    
    # Get bot status
    bot_status = get_telegram_bot_status()
    
    # Get bot logs
    bot_logs = []
    try:
        if os.path.exists("bot.log"):
            with open("bot.log", "r") as f:
                bot_logs = f.readlines()[-20:]  # Get last 20 lines
    except Exception as e:
        logging.error(f"Error reading bot logs: {e}")
    
    # Get README content
    readme_content = "Radio Frequency and Telecommunications Equipment Store Bot"
    try:
        if os.path.exists("README.md"):
            with open("README.md", "r") as f:
                readme_content = f.read()
    except Exception as e:
        logging.error(f"Error reading README: {e}")

    return render_template("index.html", 
                         bot_status=bot_status,
                         env_status=env_status,
                         db_exists=db_exists,
                         bot_logs=bot_logs,
                         readme_content=readme_content)

@app.route('/control/start', methods=['POST'])
def control_start():
    """Start the Telegram bot"""
    if start_telegram_bot():
        flash("Bot started successfully", "success")
    else:
        flash("Failed to start bot", "danger")
    
    return redirect(url_for('index'))

@app.route('/control/stop', methods=['POST'])
def control_stop():
    """Stop the Telegram bot"""
    if stop_telegram_bot():
        flash("Bot stopped successfully", "success")
    else:
        flash("Failed to stop bot", "danger")
    
    return redirect(url_for('index'))

@app.route('/configuration')
def configuration():
    """Display and edit bot configuration"""
    config = load_config()
    return render_template("configuration.html", config=config)

@app.route('/update_config', methods=['POST'])
def update_config():
    """Update bot configuration"""
    view_type = request.form.get('view_type', 'form')
    
    if view_type == 'form':
        # Get config from form data
        config = {}
        for key in request.form:
            if key != 'view_type':
                config[key] = request.form[key]
    else:
        # Get config from JSON
        try:
            config = json.loads(request.form.get('config_json', '{}'))
        except json.JSONDecodeError:
            flash("Invalid JSON config", "danger")
            return redirect(url_for('configuration'))
    
    # Save config
    save_config(config)
    flash("Configuration updated successfully", "success")
    
    return redirect(url_for('configuration'))

@app.route('/reset_config', methods=['POST'])
def reset_config():
    """Reset configuration to default"""
    reset_to_default()
    flash("Configuration reset to default", "success")
    
    return redirect(url_for('configuration'))

@app.route('/database')
def database_info():
    """Display database information"""
    # For PostgreSQL, we can just show that it's available
    db_path = "PostgreSQL Database"
    db_exists = True
    db_size = 0  # Not applicable for PostgreSQL
    using_replit_db = False
    
    return render_template("database.html", 
                         db_path=db_path,
                         db_exists=db_exists,
                         db_size=db_size,
                         using_replit_db=using_replit_db)

# Admin routes
@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    # Get stats for dashboard
    try:
        # Count products and services
        cursor = db.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM products")
        products_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM services")
        services_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM inquiries")
        inquiries_count = cursor.fetchone()[0]
        
        # Get recent inquiries
        cursor.execute("""
            SELECT i.id, i.name, i.date, COALESCE(p.name, s.name) as product_name
            FROM inquiries i
            LEFT JOIN products p ON i.product_id = p.id
            LEFT JOIN services s ON i.product_id = s.id
            ORDER BY i.date DESC
            LIMIT 5
        """)
        recent_inquiries = [dict(id=row[0], name=row[1], date=row[2], product_name=row[3])
                          for row in cursor.fetchall()]
        
        stats = {
            "products_count": products_count,
            "services_count": services_count,
            "inquiries_count": inquiries_count
        }
        
        return render_template("admin_index.html", 
                             stats=stats,
                             recent_inquiries=recent_inquiries)
    except Exception as e:
        logging.error(f"Error getting admin stats: {e}")
        flash(f"Error: {e}", "danger")
        stats = {
            "products_count": 0,
            "services_count": 0,
            "inquiries_count": 0
        }
        return render_template("admin_index.html", 
                             stats=stats,
                             recent_inquiries=[])

@app.route('/admin/categories')
def admin_categories():
    """Admin categories management"""
    # Get categories
    product_categories = []
    service_categories = []
    
    try:
        # For product categories, include parent name and count products
        with db.conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.name, c.parent_id, p.name as parent_name,
                       (SELECT COUNT(*) FROM products WHERE category_id = c.id) as product_count
                FROM categories c
                LEFT JOIN categories p ON c.parent_id = p.id
                WHERE c.cat_type = 'product'
                ORDER BY c.name
            """)
            
            product_categories = [dict(
                id=row[0], 
                name=row[1], 
                parent_id=row[2], 
                parent_name=row[3],
                product_count=row[4]
            ) for row in cursor.fetchall()]
            
            # For service categories
            cursor.execute("""
                SELECT c.id, c.name, c.parent_id, p.name as parent_name,
                       (SELECT COUNT(*) FROM services WHERE category_id = c.id) as service_count
                FROM categories c
                LEFT JOIN categories p ON c.parent_id = p.id
                WHERE c.cat_type = 'service'
                ORDER BY c.name
            """)
            
            service_categories = [dict(
                id=row[0], 
                name=row[1], 
                parent_id=row[2], 
                parent_name=row[3],
                product_count=row[4]  # We'll use the same key for UI simplicity
            ) for row in cursor.fetchall()]
        
        return render_template("admin_categories.html", 
                            product_categories=product_categories,
                            service_categories=service_categories)
    except Exception as e:
        logging.error(f"Error getting categories: {e}")
        flash(f"Error: {e}", "danger")
        return render_template("admin_categories.html", 
                            product_categories=[],
                            service_categories=[])

@app.route('/admin/products')
def admin_products():
    """Admin products management"""
    search_query = request.args.get('search', '')
    selected_category_id = request.args.get('category_id', '')
    
    try:
        # Get all categories for the filter dropdown
        with db.conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name FROM categories 
                WHERE cat_type = 'product'
                ORDER BY name
            """)
            categories = [dict(id=row[0], name=row[1]) for row in cursor.fetchall()]
            
            # Build query for products
            query = """
                SELECT p.id, p.name, p.price, p.description, p.photo_url, 
                       p.category_id, c.name as category_name
                FROM products p
                JOIN categories c ON p.category_id = c.id
                WHERE 1=1
            """
            params = []
            
            if search_query:
                query += " AND LOWER(p.name) LIKE LOWER(%s)"
                params.append(f"%{search_query}%")
                
            if selected_category_id:
                query += " AND p.category_id = %s"
                params.append(selected_category_id)
                
            query += " ORDER BY p.name"
            
            cursor.execute(query, params)
            products = [dict(
                id=row[0],
                name=row[1],
                price=row[2],
                description=row[3],
                photo_url=row[4],
                category_id=row[5],
                category_name=row[6]
            ) for row in cursor.fetchall()]
        
        return render_template("admin_products.html", 
                             products=products,
                             categories=categories,
                             search_query=search_query,
                             selected_category_id=selected_category_id,
                             page_type='products')
    except Exception as e:
        logging.error(f"Error getting products: {e}")
        flash(f"Error: {e}", "danger")
        return render_template("admin_products.html", 
                             products=[],
                             categories=[],
                             page_type='products')

@app.route('/admin/services')
def admin_services():
    """Admin services management"""
    search_query = request.args.get('search', '')
    selected_category_id = request.args.get('category_id', '')
    
    try:
        # Get all categories for the filter dropdown
        with db.conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name FROM categories 
                WHERE cat_type = 'service'
                ORDER BY name
            """)
            categories = [dict(id=row[0], name=row[1]) for row in cursor.fetchall()]
            
            # Build query for services
            query = """
                SELECT s.id, s.name, s.price, s.description, s.photo_url, 
                       s.category_id, c.name as category_name
                FROM services s
                JOIN categories c ON s.category_id = c.id
                WHERE 1=1
            """
            params = []
            
            if search_query:
                query += " AND LOWER(s.name) LIKE LOWER(%s)"
                params.append(f"%{search_query}%")
                
            if selected_category_id:
                query += " AND s.category_id = %s"
                params.append(selected_category_id)
                
            query += " ORDER BY s.name"
            
            cursor.execute(query, params)
            services = [dict(
                id=row[0],
                name=row[1],
                price=row[2],
                description=row[3],
                photo_url=row[4],
                category_id=row[5],
                category_name=row[6]
            ) for row in cursor.fetchall()]
        
        return render_template("admin_products.html", 
                             products=services,
                             categories=categories,
                             search_query=search_query,
                             selected_category_id=selected_category_id,
                             page_type='services')
    except Exception as e:
        logging.error(f"Error getting services: {e}")
        flash(f"Error: {e}", "danger")
        return render_template("admin_products.html", 
                             products=[],
                             categories=[],
                             page_type='services')

@app.route('/admin/inquiries')
def admin_inquiries():
    """Admin inquiries management"""
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    product_id = request.args.get('product_id', '')
    
    try:
        # Get all products for the filter dropdown
        with db.conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name FROM products
                UNION
                SELECT id, name FROM services
                ORDER BY name
            """)
            products = [dict(id=row[0], name=row[1]) for row in cursor.fetchall()]
            
            # Build query for inquiries
            query = """
                SELECT i.id, i.user_id, i.name, i.phone, i.description, 
                       i.product_id, i.date, COALESCE(p.name, s.name) as product_name
                FROM inquiries i
                LEFT JOIN products p ON i.product_id = p.id
                LEFT JOIN services s ON i.product_id = s.id
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND i.date >= %s"
                params.append(f"{start_date}T00:00:00")
                
            if end_date:
                query += " AND i.date <= %s"
                params.append(f"{end_date}T23:59:59")
                
            if product_id:
                query += " AND i.product_id = %s"
                params.append(product_id)
                
            query += " ORDER BY i.date DESC"
            
            cursor.execute(query, params)
            inquiries = [dict(
                id=row[0],
                user_id=row[1],
                name=row[2],
                phone=row[3],
                description=row[4],
                product_id=row[5],
                date=row[6],
                product_name=row[7]
            ) for row in cursor.fetchall()]
        
        return render_template("admin_inquiries.html", 
                             inquiries=inquiries,
                             products=products)
    except Exception as e:
        logging.error(f"Error getting inquiries: {e}")
        flash(f"Error: {e}", "danger")
        return render_template("admin_inquiries.html", 
                             inquiries=[],
                             products=[])

@app.route('/admin/import_export')
def admin_import_export():
    """Admin import/export page"""
    message = session.pop('import_export_message', None)
    return render_template("admin_import_export.html", message=message)

# More routes will be added for handling specific operations:
# - Category add/edit/delete
# - Product add/edit/delete
# - Service add/edit/delete
# - Educational content management
# - Content editing
# - Import/Export operations

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)