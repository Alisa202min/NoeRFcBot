import os
import pytest
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from unittest.mock import AsyncMock

# Import for web app testing
from src.web.app import app as flask_app
from src.web.app import db as flask_db
import models

# Load environment variables
load_dotenv()

# Test database constants
TEST_DB_NAME = "rfcbot_test"
TEST_DB_USER = os.environ.get("PGUSER", "postgres")
TEST_DB_PASSWORD = os.environ.get("PGPASSWORD", "postgres")
TEST_DB_HOST = os.environ.get("PGHOST", "localhost")
TEST_DB_PORT = os.environ.get("PGPORT", "5432")
TEST_DB_URL = f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"

# Test bot token - prefer a special test bot token for testing
TEST_BOT_TOKEN = os.environ.get("TEST_BOT_TOKEN", os.environ.get("BOT_TOKEN"))


@pytest.fixture(scope="session")
def test_db_url():
    """Return the test database URL"""
    return TEST_DB_URL


@pytest.fixture(scope="session")
def db_setup():
    """Set up a test database for the test session"""
    # Connection to default postgres database to create test database
    conn = psycopg2.connect(
        dbname="postgres",
        user=TEST_DB_USER,
        password=TEST_DB_PASSWORD,
        host=TEST_DB_HOST,
        port=TEST_DB_PORT
    )
    conn.autocommit = True
    
    try:
        with conn.cursor() as cursor:
            # Check if test database exists and drop it if it does
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB_NAME,))
            if cursor.fetchone():
                cursor.execute(f"DROP DATABASE {TEST_DB_NAME}")
            
            # Create test database
            cursor.execute(f"CREATE DATABASE {TEST_DB_NAME}")
    except Exception as e:
        print(f"Error setting up test database: {e}")
        raise
    finally:
        conn.close()
    
    # Connect to the new test database and set up schema
    test_conn = psycopg2.connect(TEST_DB_URL)
    test_conn.autocommit = True
    
    try:
        with test_conn.cursor() as cursor:
            # Create necessary tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    parent_id INTEGER NULL,
                    cat_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    description TEXT,
                    photo_url TEXT,
                    category_id INTEGER NOT NULL,
                    product_type TEXT NOT NULL DEFAULT 'product',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags TEXT,
                    brand TEXT,
                    model_number TEXT,
                    manufacturer TEXT,
                    provider TEXT,
                    service_code TEXT,
                    duration TEXT,
                    in_stock BOOLEAN DEFAULT TRUE,
                    featured BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS product_media (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    local_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inquiries (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    description TEXT NOT NULL,
                    product_id INTEGER,
                    product_type TEXT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS educational_content (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    content_type TEXT DEFAULT 'text',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS static_content (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    content_type TEXT NOT NULL UNIQUE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT,
                    password_hash TEXT,
                    is_admin BOOLEAN DEFAULT FALSE,
                    telegram_id BIGINT UNIQUE,
                    telegram_username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    last_seen TIMESTAMP,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert sample data for testing
            # Set up a 4-level category hierarchy for testing
            # Level 1 Categories (Root)
            cursor.execute(
                "INSERT INTO categories (name, parent_id, cat_type) VALUES (%s, NULL, %s) RETURNING id",
                ("محصولات فرکانس پایین", None, "product")
            )
            cat_level1_1_id = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO categories (name, parent_id, cat_type) VALUES (%s, NULL, %s) RETURNING id",
                ("محصولات فرکانس بالا", None, "product")
            )
            cat_level1_2_id = cursor.fetchone()[0]
            
            # Level 2 Categories
            cursor.execute(
                "INSERT INTO categories (name, parent_id, cat_type) VALUES (%s, %s, %s) RETURNING id",
                ("آنتن‌ها", cat_level1_1_id, "product")
            )
            cat_level2_1_id = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO categories (name, parent_id, cat_type) VALUES (%s, %s, %s) RETURNING id",
                ("ماژول‌ها", cat_level1_1_id, "product")
            )
            cat_level2_2_id = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO categories (name, parent_id, cat_type) VALUES (%s, %s, %s) RETURNING id",
                ("تجهیزات تست", cat_level1_2_id, "product")
            )
            cat_level2_3_id = cursor.fetchone()[0]
            
            # Level 3 Categories
            cursor.execute(
                "INSERT INTO categories (name, parent_id, cat_type) VALUES (%s, %s, %s) RETURNING id",
                ("آنتن‌های یکطرفه", cat_level2_1_id, "product")
            )
            cat_level3_1_id = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO categories (name, parent_id, cat_type) VALUES (%s, %s, %s) RETURNING id",
                ("آنتن‌های دوطرفه", cat_level2_1_id, "product")
            )
            cat_level3_2_id = cursor.fetchone()[0]
            
            # Level 4 Categories (Leaf nodes)
            cursor.execute(
                "INSERT INTO categories (name, parent_id, cat_type) VALUES (%s, %s, %s) RETURNING id",
                ("آنتن‌های یکطرفه موج کوتاه", cat_level3_1_id, "product")
            )
            cat_level4_1_id = cursor.fetchone()[0]
            
            # Add sample service categories with 4-level hierarchy
            cursor.execute(
                "INSERT INTO categories (name, parent_id, cat_type) VALUES (%s, NULL, %s) RETURNING id",
                ("خدمات نصب", None, "service")
            )
            service_cat_level1_id = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO categories (name, parent_id, cat_type) VALUES (%s, %s, %s) RETURNING id",
                ("نصب آنتن", service_cat_level1_id, "service")
            )
            service_cat_level2_id = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO categories (name, parent_id, cat_type) VALUES (%s, %s, %s) RETURNING id",
                ("نصب آنتن‌های خارجی", service_cat_level2_id, "service")
            )
            service_cat_level3_id = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO categories (name, parent_id, cat_type) VALUES (%s, %s, %s) RETURNING id",
                ("نصب آنتن‌های خارجی فرکانس پایین", service_cat_level3_id, "service")
            )
            service_cat_level4_id = cursor.fetchone()[0]
            
            # Add sample products
            cursor.execute(
                """
                INSERT INTO products 
                (name, price, description, category_id, product_type, brand, tags, in_stock, featured) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """,
                (
                    "آنتن یکطرفه XYZ",
                    1500000,
                    "آنتن یکطرفه با فرکانس پایین",
                    cat_level3_1_id,
                    "product",
                    "XYZ",
                    "آنتن,فرکانس پایین,یکطرفه",
                    True,
                    True
                )
            )
            product_id = cursor.fetchone()[0]
            
            # Add sample service
            cursor.execute(
                """
                INSERT INTO products 
                (name, price, description, category_id, product_type, provider, tags, in_stock, featured) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """,
                (
                    "نصب آنتن خارجی",
                    500000,
                    "خدمات نصب آنتن خارجی به همراه تنظیمات",
                    service_cat_level3_id,
                    "service",
                    "شرکت خدمات RF",
                    "نصب,آنتن,خارجی",
                    True,
                    False
                )
            )
            service_id = cursor.fetchone()[0]
            
            # Add sample educational content
            cursor.execute(
                """
                INSERT INTO educational_content 
                (title, content, category, content_type) 
                VALUES (%s, %s, %s, %s)
                """,
                (
                    "راهنمای نصب آنتن",
                    "این راهنما به شما کمک می‌کند تا آنتن را به درستی نصب کنید...",
                    "آموزش نصب",
                    "text"
                )
            )
            
            # Add sample static content
            cursor.execute(
                """
                INSERT INTO static_content 
                (content, content_type) 
                VALUES (%s, %s)
                """,
                (
                    "اطلاعات تماس با ما: تلفن: 021-12345678",
                    "contact"
                )
            )
            
            cursor.execute(
                """
                INSERT INTO static_content 
                (content, content_type) 
                VALUES (%s, %s)
                """,
                (
                    "درباره ما: شرکت ما در زمینه فناوری RF فعالیت می‌کند...",
                    "about"
                )
            )
            
            # Add test admin user
            cursor.execute(
                """
                INSERT INTO users 
                (username, email, password_hash, is_admin) 
                VALUES (%s, %s, %s, %s)
                """,
                (
                    "admin_test",
                    "admin_test@example.com",
                    "pbkdf2:sha256:150000$wvf7VfY9$7d36aca90e08cdc1fe1cb8f7f3aae59c9ccf23048f72d0cc4d0f04f72494db53",  # password: test123
                    True
                )
            )
            
    except Exception as e:
        print(f"Error initializing test database: {e}")
        raise
    finally:
        test_conn.close()
    
    # Return the test database URL for use in tests
    return TEST_DB_URL


@pytest.fixture(scope="session")
def test_db_connection(db_setup):
    """Create a connection to the test database that can be used by tests"""
    conn = psycopg2.connect(db_setup)
    conn.autocommit = True
    
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture(scope="function")
def test_db_cursor(test_db_connection):
    """Create a cursor for the test database"""
    with test_db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
        yield cursor


@pytest.fixture
def mock_bot():
    """Create a mock Bot instance for testing"""
    bot = AsyncMock(spec=Bot)
    bot.send_message = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.set_webhook = AsyncMock()
    bot.delete_webhook = AsyncMock()
    bot.get_webhook_info = AsyncMock()
    
    bot.get_webhook_info.return_value = AsyncMock(url="")
    
    return bot


@pytest.fixture
def bot_dispatcher():
    """Create a real Dispatcher with memory storage for testing"""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    try:
        yield dp
    finally:
        # Cleanup if needed
        pass


@pytest.fixture
def flask_test_client():
    """Create a Flask test client"""
    # Configure Flask for testing
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DB_URL
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    # Create all tables
    with flask_app.app_context():
        flask_db.create_all()
    
    # Return a test client
    with flask_app.test_client() as client:
        yield client
    
    # Clean up after tests
    with flask_app.app_context():
        flask_db.session.remove()
        flask_db.drop_all()


@pytest.fixture
def auth_flask_test_client(flask_test_client):
    """Create an authenticated Flask test client"""
    # Log in the test admin user
    flask_test_client.post('/login', data={
        'username': 'admin_test',
        'password': 'test123'
    }, follow_redirects=True)
    
    return flask_test_client