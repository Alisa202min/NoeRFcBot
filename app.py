# app.py
import os
from flask import Flask
from extensions import db  # Import db from extensions.py
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from dotenv import load_dotenv
from configuration import load_config  # Import load_config to get DATABASE_URL

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

# Initialize SQLAlchemy with the app
db.init_app(app)

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
    from models import User
    return User.query.get(int(user_id))

# Create database tables and initialize admin user
with app.app_context():
    # Import models here to ensure they're registered with SQLAlchemy
    import models
    
    # Create tables
    db.create_all()
    
    # Create admin user if not exists
    from models import User
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin')  # Set a default password - should be changed immediately
        db.session.add(admin)
        db.session.commit()