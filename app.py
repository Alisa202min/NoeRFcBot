import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager


class Base(DeclarativeBase):
    pass


# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy with Base class
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')
app.secret_key = os.environ.get("SESSION_SECRET", "رمز موقت برای ربات RFCBot")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # For proper URL generation with https

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "connect_args": {
        "sslmode": "prefer",
        "application_name": "RFCBot",
        "connect_timeout": 10
    }
}

# Configure Flask-Uploads
from utils_upload import UploadSet, IMAGES, VIDEO, configure_uploads

# Add mp4 to allowed formats
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'} 
app.config['UPLOADED_MEDIA_DEST'] = 'static/uploads'
app.config['UPLOADS_DEFAULT_DEST'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Create a custom media upload set that includes images and mp4 videos
media_files = UploadSet('media', IMAGES + VIDEO)

# Initialize extensions
db.init_app(app)
configure_uploads(app, media_files)

# Ensure upload directory exists
os.makedirs(app.config['UPLOADED_MEDIA_DEST'], exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    # Temporarily disable user loading to fix DB transaction issue
    return None

# Import main routes to register them
from src.web.main import *

# Create database tables
with app.app_context():
    # Import models here to ensure they're registered with SQLAlchemy
    import models
    
    # Create tables
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    
    # Skip admin user creation for now to avoid circular import
    logger.info("Application setup completed")
