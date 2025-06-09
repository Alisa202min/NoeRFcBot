# app.py
import os
from logging_config import get_logger
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from dotenv import load_dotenv
from configuration import load_config
from utils_upload import UploadSet, IMAGES, VIDEO, configure_uploads
from extensions import db, database
from models import (  # Import all models explicitly
    User, ProductCategory, ServiceCategory, EducationalCategory,
    Product, Service, ProductMedia, ServiceMedia, Inquiry,
    EducationalContent, EducationalContentMedia, StaticContent, Base
)

logger = get_logger('app')

# Load environment variables
load_dotenv()

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "رمز موقت برای ربات RFCBot")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config['WTF_CSRF_ENABLED'] = False

# Load configuration
config = load_config()
app.config["SQLALCHEMY_DATABASE_URI"] = config.get("DATABASE_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "connect_args": {
        "sslmode": "prefer",
        "application_name": "RFCBot",
        "connect_timeout": 10
    }
}

# Initialize SQLAlchemy with the app and bind to Base from models
db.init_app(app)
with app.app_context():
    db.Model = Base  # Bind the Base class from models.py to db
    database.initialize(app.config["SQLALCHEMY_DATABASE_URI"])  # Initialize custom Database

# Configure file uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
app.config['UPLOADED_MEDIA_DEST'] = 'static/uploads'
app.config['UPLOADS_DEFAULT_DEST'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Create a custom media upload set that includes images and mp4 videos
media_files = UploadSet('media', IMAGES + VIDEO)

# Initialize extensions for file uploads
configure_uploads(app, media_files)

# Ensure upload directory exists
os.makedirs(app.config['UPLOADED_MEDIA_DEST'], exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables and initialize admin user
with app.app_context():
    db.create_all()  # Create all tables for models
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        logger.info("Admin user created successfully")
    else:
        logger.info("Admin user already exists")

if __name__ == "__main__":
    app.run(debug=True)