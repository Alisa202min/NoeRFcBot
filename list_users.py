"""
Utility to list users in the database
"""

import os
import sys
from app import app, db
from models import User

def list_all_users():
    """List all users in the database"""
    with app.app_context():
        users = User.query.all()
        
        print(f"Found {len(users)} users in the database:")
        for user in users:
            print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Admin: {user.is_admin}")

if __name__ == '__main__':
    list_all_users()