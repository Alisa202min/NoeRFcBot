import pytest
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import User, Chat, Message, CallbackQuery, Update
from database import Database

# Setup the testing environment
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db():
    """Initialize test database with sample data"""
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        pytest.fail("DATABASE_URL environment variable not set")
    
    # Create a database instance for testing
    db = Database()
    
    # Create test data and clean up after tests
    try:
        setup_test_db(db)
        yield db
    finally:
        cleanup_test_db(db)

def setup_test_db(db):
    """Set up the test database with sample data"""
    # Create the test categories hierarchy (4 levels)
    # Level 1 - Main categories
    radio_cat_id = db.add_category("تجهیزات رادیویی", cat_type='product')
    network_cat_id = db.add_category("تجهیزات شبکه", cat_type='product')
    services_cat_id = db.add_category("خدمات فنی", cat_type='service')
    
    # Level 2 - Subcategories
    radio_receivers_id = db.add_category("گیرنده‌های رادیویی", parent_id=radio_cat_id, cat_type='product')
    radio_transmitters_id = db.add_category("فرستنده‌های رادیویی", parent_id=radio_cat_id, cat_type='product')
    network_switches_id = db.add_category("سوئیچ‌های شبکه", parent_id=network_cat_id, cat_type='product')
    network_routers_id = db.add_category("روترها", parent_id=network_cat_id, cat_type='product')
    service_installation_id = db.add_category("نصب و راه‌اندازی", parent_id=services_cat_id, cat_type='service')
    
    # Level 3 - Specific types
    uhf_receivers_id = db.add_category("گیرنده‌های UHF", parent_id=radio_receivers_id, cat_type='product')
    vhf_receivers_id = db.add_category("گیرنده‌های VHF", parent_id=radio_receivers_id, cat_type='product')
    enterprise_switches_id = db.add_category("سوئیچ‌های سازمانی", parent_id=network_switches_id, cat_type='product')
    radio_installation_id = db.add_category("نصب تجهیزات رادیویی", parent_id=service_installation_id, cat_type='service')
    
    # Level 4 - Specific models/brands
    motorola_uhf_id = db.add_category("گیرنده‌های موتورولا UHF", parent_id=uhf_receivers_id, cat_type='product')
    cisco_switches_id = db.add_category("سوئیچ‌های سیسکو", parent_id=enterprise_switches_id, cat_type='product')
    antenna_installation_id = db.add_category("نصب آنتن", parent_id=radio_installation_id, cat_type='service')
    
    # Add products to level 4 categories
    db.add_product(
        name="گیرنده موتورولا XPR 5550",
        price=850000,
        description="گیرنده دیجیتال UHF موتورولا با محدوده فرکانسی 403-470 MHz",
        category_id=motorola_uhf_id,
        photo_url=None,
        brand="Motorola",
        model="XPR 5550",
        in_stock=True,
        tags="UHF,Radio,Digital",
        featured=True
    )
    
    db.add_product(
        name="گیرنده موتورولا XPR 7550",
        price=1250000,
        description="گیرنده دیجیتال UHF موتورولا با محدوده فرکانسی وسیع و قابلیت اتصال به شبکه",
        category_id=motorola_uhf_id,
        photo_url=None,
        brand="Motorola",
        model="XPR 7550",
        in_stock=True,
        tags="UHF,Radio,Digital,Network",
        featured=True
    )
    
    db.add_product(
        name="سوئیچ سیسکو Catalyst 2960",
        price=1800000,
        description="سوئیچ لایه 2 سیسکو با 24 پورت گیگابیت اترنت",
        category_id=cisco_switches_id,
        photo_url=None,
        brand="Cisco",
        model="Catalyst 2960",
        in_stock=True,
        tags="Switch,Ethernet,Gigabit,Managed",
        featured=True
    )
    
    # Add service to level 4 category
    db.add_service(
        name="نصب آنتن رادیویی",
        price=350000,
        description="نصب و تنظیم آنتن‌های رادیویی با تضمین کیفیت سیگنال",
        category_id=antenna_installation_id,
        photo_url=None,
        featured=True,
        tags="Antenna,Installation,Radio"
    )
    
    # Add educational content
    db.add_educational_content(
        title="راهنمای انتخاب فرکانس مناسب",
        content="در این مقاله به بررسی نحوه انتخاب فرکانس مناسب برای تجهیزات رادیویی می‌پردازیم...",
        category="آموزش رادیو",
        content_type="article"
    )
    
    db.add_educational_content(
        title="نحوه عیب‌یابی اختلالات سیگنال",
        content="در این ویدیو آموزشی، روش‌های تشخیص و رفع اختلالات سیگنال را مشاهده می‌کنید...",
        category="عیب‌یابی",
        content_type="video"
    )
    
    # Add static content
    db.update_static_content("contact", "برای تماس با ما از طریق زیر اقدام کنید:\n\nتلفن: 021-12345678\nایمیل: info@rfcatalog.com")
    db.update_static_content("about", "فروشگاه تخصصی تجهیزات رادیویی و فرکانسی با بیش از 15 سال سابقه ارائه خدمات...")
    
    # Add inquiries
    db.add_inquiry(
        user_id=123456789,
        name="علی محمدی",
        phone="09123456789",
        description="درخواست قیمت برای خرید 5 دستگاه گیرنده موتورولا",
        product_id=1
    )
    
    db.add_inquiry(
        user_id=987654321,
        name="سارا احمدی",
        phone="09187654321",
        description="استعلام هزینه نصب آنتن رادیویی برای 3 سایت",
        service_id=1
    )

def cleanup_test_db(db):
    """Clean up the test database after tests"""
    try:
        # In a real implementation, you might want to drop the test tables
        # or delete the test data created during setup
        pass
    except Exception as e:
        print(f"Error during test database cleanup: {e}")

@pytest.fixture
def mock_bot():
    """Create a mock bot instance for testing."""
    bot = AsyncMock(spec=Bot)
    bot.send_message = AsyncMock(return_value=MagicMock(message_id=42))
    bot.send_photo = AsyncMock(return_value=MagicMock(message_id=43))
    bot.edit_message_text = AsyncMock(return_value=MagicMock())
    bot.edit_message_reply_markup = AsyncMock(return_value=MagicMock())
    bot.delete_message = AsyncMock(return_value=True)
    return bot

@pytest.fixture
def mock_dp():
    """Create a mock dispatcher instance for testing."""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    return dp

@pytest.fixture
def test_user():
    """Create a test user for testing."""
    return User(id=12345, is_bot=False, first_name="Test", last_name="User", username="testuser", language_code="fa")

@pytest.fixture
def test_admin_user():
    """Create a test admin user for testing."""
    admin_id = int(os.environ.get('ADMIN_ID', 67890))
    return User(id=admin_id, is_bot=False, first_name="Admin", last_name="User", username="adminuser", language_code="fa")

@pytest.fixture
def test_chat():
    """Create a test chat for testing."""
    return Chat(id=12345, type="private", title=None, username="testuser", first_name="Test", last_name="User")

@pytest.fixture
def test_admin_chat():
    """Create a test admin chat for testing."""
    admin_id = int(os.environ.get('ADMIN_ID', 67890))
    return Chat(id=admin_id, type="private", title=None, username="adminuser", first_name="Admin", last_name="User")

@pytest.fixture
def test_message(test_user, test_chat):
    """Create a test message for testing."""
    message = AsyncMock(spec=Message)
    message.from_user = test_user
    message.chat = test_chat
    message.message_id = 1
    message.text = "/start"
    message.reply = AsyncMock(return_value=MagicMock(message_id=2))
    message.answer = AsyncMock(return_value=MagicMock(message_id=3))
    message.reply_photo = AsyncMock(return_value=MagicMock(message_id=4))
    return message

@pytest.fixture
def test_admin_message(test_admin_user, test_admin_chat):
    """Create a test message from admin for testing."""
    message = AsyncMock(spec=Message)
    message.from_user = test_admin_user
    message.chat = test_admin_chat
    message.message_id = 1
    message.text = "/admin"
    message.reply = AsyncMock(return_value=MagicMock(message_id=2))
    message.answer = AsyncMock(return_value=MagicMock(message_id=3))
    message.reply_photo = AsyncMock(return_value=MagicMock(message_id=4))
    return message

@pytest.fixture
def test_callback_query(test_user, test_chat):
    """Create a test callback query for testing."""
    callback_query = AsyncMock(spec=CallbackQuery)
    callback_query.from_user = test_user
    callback_query.message = AsyncMock(spec=Message)
    callback_query.message.chat = test_chat
    callback_query.message.message_id = 5
    callback_query.message.reply = AsyncMock(return_value=MagicMock(message_id=6))
    callback_query.message.answer = AsyncMock(return_value=MagicMock(message_id=7))
    callback_query.message.edit_text = AsyncMock()
    callback_query.message.edit_reply_markup = AsyncMock()
    callback_query.data = "category_1"  # Default callback data
    callback_query.answer = AsyncMock()
    return callback_query

@pytest.fixture
def test_update(test_message):
    """Create a test update for testing."""
    update = AsyncMock(spec=Update)
    update.message = test_message
    update.callback_query = None
    return update