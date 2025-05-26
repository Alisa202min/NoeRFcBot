import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

class Base(DeclarativeBase):
    pass

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy with Base class
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "رمز موقت برای ربات RFCBot")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI") or os.environ.get("DATABASE_URL")
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

# بقیه کدها بدون تغییر...
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
login_manager.login_view = 'login'

# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Create database tables
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

# Import routes to register them with the app
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'web'))
    import main
    logging.info("Routes imported successfully")
except ImportError as e:
    logging.error(f"Failed to import routes: {e}")
    # Add basic routes to make the admin panel functional
    from flask import render_template, redirect, url_for
    
    @app.route('/')
    def index():
        return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin')
    def admin_dashboard():
        return render_template('admin/index.html')
