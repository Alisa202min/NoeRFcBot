import os

# Bot token from BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Admin user ID (Telegram user ID for admin access)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Directory for storing data (images, CSV files, etc.)
DATA_DIR = os.getenv("DATA_DIR", "data")

# Database file path
DATABASE_PATH = os.path.join(DATA_DIR, "rfcbot.db")

# Logging level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)
