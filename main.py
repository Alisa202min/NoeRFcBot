"""
نقطه ورود اصلی برنامه RFCBot
این فایل برنامه Flask و بات تلگرام را راه‌اندازی می‌کند.
"""

# Import the Flask application directly from the reorganized structure
from src.web import app
# Import main routes to ensure they are registered
from src.web import main

# Export the app object for Gunicorn
app = app

if __name__ == "__main__":
    # Run the Flask application
    app.run(host="0.0.0.0", port=5000, debug=True)