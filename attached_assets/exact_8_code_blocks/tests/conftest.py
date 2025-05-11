import pytest
import psycopg2
from telegram.ext import Application
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import Database
from flask import Flask

@pytest.fixture(scope="session")
def db():
    """Fixture for test PostgreSQL database."""
    conn = psycopg2.connect(
        dbname="rfcbot_test",
        user="test_user",
        password="test_password",
        host="localhost",
        port="5432"
    )
    db = Database(conn=conn)
    db.create_tables()
    yield db
    with conn.cursor() as cur:
        cur.execute("""
            DROP TABLE IF EXISTS inquiries, products, services, educational_content,
            product_categories, service_categories, educational_categories CASCADE
        """)
        conn.commit()
    conn.close()

@pytest.fixture
async def app():
    """Fixture for Telegram bot application."""
    app = Application.builder().token("TEST_BOT_TOKEN").build()
    from bot import start, products, services, education, inquiries, callback_query_handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("products", products))
    app.add_handler(CommandHandler("services", services))
    app.add_handler(CommandHandler("education", education))
    app.add_handler(CommandHandler("inquiries", inquiries))
    app.add_handler(CallbackQueryHandler(callback_query_handler))
    yield app
    await app.shutdown()

@pytest.fixture
def flask_client():
    """Fixture for Flask test client."""
    from app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client