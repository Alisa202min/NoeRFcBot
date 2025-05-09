"""
Test the User model specifically
"""

import os
import sys
import uuid
import time
from app import app, db
from models import User
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

def test_user_model():
    """Test User model operations"""
    print("Testing User model...")
    
    try:
        with app.app_context():
            # Check if the users table exists by querying it
            print("Checking users table...")
            existing_users = User.query.all()
            print(f"Found {len(existing_users)} existing users in database")
            
            # Create a test user with unique username
            unique_id = str(uuid.uuid4())[:8]
            test_username = f"testuser_{unique_id}_{int(time.time())}"
            test_email = f"test_{unique_id}@example.com"
            
            print(f"Creating test user with unique username: {test_username}")
            test_user = User(
                username=test_username, 
                email=test_email,
                is_admin=False
            )
            test_user.set_password('password123')
            
            # Test password hashing
            if test_user.check_password('password123'):
                print("✅ Password hashing works correctly")
            else:
                print("❌ Password hashing failed")
                return False
            
            # Save user to database temporarily to test retrieval
            try:
                print("Saving test user to database...")
                db.session.add(test_user)
                db.session.commit()
                
                # Test user retrieval
                print(f"Retrieving test user {test_username}...")
                retrieved_user = User.query.filter_by(username=test_username).first()
                
                if retrieved_user:
                    print("✅ User retrieval successful")
                    if retrieved_user.email == test_email:
                        print("✅ User data matches")
                    else:
                        print(f"❌ User data does not match. Expected: {test_email}, Got: {retrieved_user.email}")
                        return False
                else:
                    print("❌ User retrieval failed")
                    return False
                
                return True
                
            except Exception as e:
                print(f"❌ Error saving/retrieving user: {str(e)}")
                db.session.rollback()
                return False
            
            finally:
                # Clean up test data
                print("Cleaning up test data...")
                User.query.filter_by(username='testuser').delete()
                db.session.commit()
                
    except Exception as e:
        print(f"❌ Error in user model test: {str(e)}")
        return False

if __name__ == '__main__':
    print("===== User Model Test =====")
    
    # Test the User model
    result = test_user_model()
    
    # Print overall result
    print("\n===== Test Results =====")
    print(f"User model test: {'✅ PASSED' if result else '❌ FAILED'}")
    
    # Exit with appropriate status code
    sys.exit(0 if result else 1)