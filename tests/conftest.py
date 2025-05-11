"""
Pytest fixtures for RFCBot tests
"""

import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from database import Database


@pytest.fixture
def test_db():
    """Fixture for providing a database instance"""
    db = Database()
    return db


@pytest.fixture
def test_user():
    """Fixture for providing a mock user"""
    user = MagicMock()
    user.id = 123456789
    user.first_name = "Test"
    user.last_name = "User"
    user.username = "testuser"
    user.language_code = "fa"
    return user


@pytest.fixture
def test_message(test_user):
    """Fixture for providing a mock message"""
    message = AsyncMock()
    message.from_user = test_user
    message.chat.id = test_user.id
    message.message_id = 1
    message.text = "/start"
    return message


@pytest.fixture
def test_admin_message(test_user):
    """Fixture for providing a mock admin message"""
    admin_user = MagicMock()
    admin_user.id = int(os.environ.get('ADMIN_ID', '987654321'))
    admin_user.first_name = "Admin"
    admin_user.last_name = "User"
    admin_user.username = "adminuser"
    admin_user.language_code = "fa"
    
    message = AsyncMock()
    message.from_user = admin_user
    message.chat.id = admin_user.id
    message.message_id = 1
    message.text = "/admin"
    return message


@pytest.fixture
def test_callback_query(test_user):
    """Fixture for providing a mock callback query"""
    callback_query = AsyncMock()
    callback_query.from_user = test_user
    callback_query.message = AsyncMock()
    callback_query.message.chat.id = test_user.id
    callback_query.message.message_id = 1
    callback_query.data = "test_data"
    return callback_query


@pytest.fixture
def test_photo():
    """Fixture for providing a mock photo"""
    photo = MagicMock()
    photo.file_id = "test_file_id"
    photo.file_unique_id = "test_file_unique_id"
    return [photo]


@pytest.fixture
def test_video():
    """Fixture for providing a mock video"""
    video = MagicMock()
    video.file_id = "test_video_file_id"
    video.file_unique_id = "test_video_file_unique_id"
    return video


@pytest.fixture
def test_document():
    """Fixture for providing a mock document"""
    document = MagicMock()
    document.file_id = "test_document_file_id"
    document.file_unique_id = "test_document_file_unique_id"
    document.file_name = "test_document.pdf"
    return document


@pytest.fixture
def test_voice():
    """Fixture for providing a mock voice message"""
    voice = MagicMock()
    voice.file_id = "test_voice_file_id"
    voice.file_unique_id = "test_voice_file_unique_id"
    voice.duration = 10
    return voice


@pytest.fixture
def test_category(test_db):
    """Fixture for providing a test category"""
    category_id = test_db.add_category("Test Category", cat_type="product")
    yield category_id
    # Clean up after the test
    test_db.delete_category(category_id)


@pytest.fixture
def test_product(test_db, test_category):
    """Fixture for providing a test product"""
    product_id = test_db.add_product(
        name="Test Product",
        price=1000000,
        description="Test product description",
        category_id=test_category,
        brand="Test Brand",
        model="Test Model",
        in_stock=True,
        tags="test, product",
        featured=False
    )
    yield product_id
    # Clean up after the test
    test_db.delete_product(product_id)


@pytest.fixture
def test_service(test_db, test_category):
    """Fixture for providing a test service"""
    service_id = test_db.add_service(
        name="Test Service",
        price=2000000,
        description="Test service description",
        category_id=test_category,
        tags="test, service",
        featured=False
    )
    yield service_id
    # Clean up after the test
    test_db.delete_product(service_id)  # Services are stored in the products table


@pytest.fixture
def test_product_media(test_db, test_product):
    """Fixture for providing test product media"""
    media_id = test_db.add_product_media(
        product_id=test_product,
        file_id="test_file_id",
        file_type="photo"
    )
    yield media_id
    # Clean up after the test
    test_db.delete_product_media(media_id)


@pytest.fixture
def test_educational_content(test_db):
    """Fixture for providing test educational content"""
    content_id = test_db.add_educational_content(
        title="Test Educational Content",
        content="This is test educational content.",
        category="Test Category",
        content_type="article"
    )
    yield content_id
    # Clean up after the test
    test_db.delete_educational_content(content_id)


@pytest.fixture
def test_inquiry(test_db, test_product):
    """Fixture for providing a test inquiry"""
    inquiry_id = test_db.add_inquiry(
        user_id=123456789,
        name="Test Customer",
        phone="09123456789",
        description="Test inquiry description",
        product_id=test_product
    )
    yield inquiry_id
    # Clean up after the test
    test_db.delete_inquiry(inquiry_id)