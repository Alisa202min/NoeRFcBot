#!/usr/bin/env python
"""
Fresh Flask application for RFCBot
This is a clean, simple implementation without the complexity of the original app
"""

import os
import logging
from flask import Flask, render_template, jsonify, redirect, url_for
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "رمز موقت برای ربات RFCBot")

# Simple routes
@app.route('/')
def index():
    """Home page."""
    return render_template('index.html', title="RFCBot Admin Dashboard")

@app.route('/admin')
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

@app.route('/api/bot/status')
def bot_status():
    """Check bot status."""
    try:
        # Make a request to the Telegram Bot API to check if the bot is active
        bot_token = os.environ.get("BOT_TOKEN")
        if not bot_token:
            return {"status": "error", "message": "BOT_TOKEN environment variable not set"}
        
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe")
        if response.status_code == 200:
            bot_info = response.json()["result"]
            return {
                "status": "ok",
                "message": "Bot is active",
                "bot_info": {
                    "id": bot_info["id"],
                    "username": bot_info["username"],
                    "name": bot_info.get("first_name", "")
                }
            }
        else:
            return {"status": "error", "message": f"Bot API returned error: {response.json()}"}
    except Exception as e:
        logger.error(f"Error checking bot status: {e}")
        return {"status": "error", "message": f"Error checking bot status: {str(e)}"}

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

# Only run the app directly when script is executed directly
if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Starting Flask app on port {port}...")
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        import sys
        sys.exit(1)