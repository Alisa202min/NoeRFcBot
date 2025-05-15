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
    return render_template('index.html', title="RFCBot Admin Panel")

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
    return render_template('admin/index.html', title="Admin Dashboard")

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
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

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