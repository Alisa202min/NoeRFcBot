"""
نقطه ورود اصلی برنامه RFCBot
این فایل برنامه Flask و بات تلگرام را راه‌اندازی می‌کند.
"""

# Import the Flask application directly from app.py
from app import app

if __name__ == "__main__":
    # Run the Flask application
    app.run(host="0.0.0.0", port=5000, debug=True)