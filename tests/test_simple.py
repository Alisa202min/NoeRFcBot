import pytest
from database import Database

def test_database_connection():
    """Test that we can connect to the database"""
    db = Database()
    assert db is not None
    print("Database connection successful")

def test_simple_category_creation():
    """Test that we can create a category"""
    db = Database()
    # Create a test category
    category_name = "Test Simple Category"
    category_id = db.add_category(category_name, parent_id=None, cat_type="product")
    assert category_id > 0
    
    # Get the category
    category = db.get_category(category_id)
    assert category is not None
    assert category["name"] == category_name
    
    # Clean up
    db.delete_category(category_id)
    print("Category creation test successful")