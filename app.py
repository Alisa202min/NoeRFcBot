"""
Main Flask application for RFCBot Admin Panel
This version uses a centralized database configuration to avoid circular imports
"""

import os
import logging
from flask import Flask, render_template, jsonify, redirect, url_for, flash, request
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "رمز موقت برای ربات RFCBot")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Import database components
from database import db
from database.config import configure_database

# Configure the database
configure_database(app)

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(user_id)

# Basic routes
@app.route('/')
def index():
    """Home page."""
    # Check environment variables
    import os
    env_status = {
        'BOT_TOKEN': 'Set' if os.environ.get('BOT_TOKEN') else 'Not Set',
        'ADMIN_ID': 'Set' if os.environ.get('ADMIN_ID') else 'Not Set',
        'DB_TYPE': 'PostgreSQL'
    }
    
    # Check bot status by looking at the running processes (simplified)
    bot_status = 'running'  # Simplified status indicator
    
    # Sample logs for display
    bot_logs = [
        "[INFO] Bot started successfully",
        "[INFO] Connected to Telegram servers",
        "[INFO] Using aiogram version 3.7.0+",
        "[INFO] Webhook mode: Not active",
        "[INFO] Polling mode: Active",
        "[INFO] Bot is ready to receive messages",
        "[INFO] Database connection successful"
    ]
    
    # Sample readme content
    readme_content = "<p>RFCBot یک ربات تلگرام برای مدیریت محصولات، خدمات و محتوای آموزشی در حوزه محصولات و خدمات صنعت ارتباطات رادیویی است.</p>"
    
    # Include datetime for template use
    from datetime import datetime

    return render_template('index.html', title="RFCBot Admin Panel", 
                          env_status=env_status, bot_status=bot_status,
                          bot_logs=bot_logs, readme_content=readme_content,
                          datetime=datetime)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        from models import User
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('admin'))
        
        flash('Invalid username or password')
    
    return render_template('login.html', title="Login")

@app.route('/logout')
@login_required
def logout():
    """Logout the user."""
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    """Admin dashboard."""
    from datetime import datetime
    return render_template(
        'admin/index.html', 
        title="Admin Dashboard", 
        now=datetime.now(),
        product_count=0,
        service_count=0,
        category_count=0,
        inquiry_count=0,
        inquiries=[]
    )

@app.route('/api/health')
def health():
    """Health check endpoint."""
    return {
        "status": "ok", 
        "message": "The RFCBot admin panel is running",
        "database": os.environ.get("DATABASE_URL", "").split("@")[1] if "@" in os.environ.get("DATABASE_URL", "") else None
    }

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

# Create admin user for testing
def create_admin():
    try:
        from models import User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin_user = User(
                username='admin',
                password_hash=generate_password_hash('admin'),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            logger.info("Admin user created")
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")

# Run application directly (development only)
if __name__ == '__main__':
    with app.app_context():
        create_admin()
    app.run(host='0.0.0.0', port=5000, debug=True)