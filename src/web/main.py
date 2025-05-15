"""
Routes and views for the Flask application.
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from .app import app, db
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Import any database models you need
from models import User

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html', title='RFCBot Admin Dashboard')

# Create other routes as needed below
@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    return render_template('admin/dashboard.html', title='Admin Dashboard')

# Ensure the admin user exists
try:
    from .app import create_admin_user
    create_admin_user()
except Exception as e:
    logging.error(f"Error creating admin user: {e}")