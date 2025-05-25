"""
نقطه ورود اصلی برنامه RFCBot
این فایل برنامه Flask و بات تلگرام را راه‌اندازی می‌کند.
"""

# Import the unified Flask application and routes
from app import app

# Import all the routes from src/web/main.py
from src.web.main import *

if __name__ == "__main__":
    # Run the Flask application
    app.run(host="0.0.0.0", port=5000, debug=True)