import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging():
    """Configure logging for the application with separate loggers for bot and webpanel."""
    
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Define log format
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # General application logger (for critical errors and shared logs)
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.INFO)
    
    # File handler for app logger with rotation
    app_file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB per file
        backupCount=5  # Keep 5 backup files
    )
    app_file_handler.setFormatter(log_format)
    app_logger.addHandler(app_file_handler)
    
    # Console handler for app logger
    app_console_handler = logging.StreamHandler()
    app_console_handler.setFormatter(log_format)
    app_logger.addHandler(app_console_handler)

    # Bot logger
    bot_logger = logging.getLogger('bot')
    bot_logger.setLevel(logging.INFO)
    
    # File handler for bot logger with rotation
    bot_file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'bot.log'),
        maxBytes=10*1024*1024,  # 10MB per file
        backupCount=5
    )
    bot_file_handler.setFormatter(log_format)
    bot_logger.addHandler(bot_file_handler)
    
    # Console handler for bot logger (optional, only in debug mode)
    if os.environ.get('DEBUG_MODE', 'False').lower() == 'true':
        bot_console_handler = logging.StreamHandler()
        bot_console_handler.setFormatter(log_format)
        bot_logger.addHandler(bot_console_handler)

    # Webpanel logger
    webpanel_logger = logging.getLogger('webpanel')
    webpanel_logger.setLevel(logging.INFO)
    
    # File handler for webpanel logger with rotation
    webpanel_file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'webpanel.log'),
        maxBytes=10*1024*1024,  # 10MB per file
        backupCount=5
    )
    webpanel_file_handler.setFormatter(log_format)
    webpanel_logger.addHandler(webpanel_file_handler)
    
    # Console handler for webpanel logger (optional, only in debug mode)
    if os.environ.get('DEBUG_MODE', 'False').lower() == 'true':
        webpanel_console_handler = logging.StreamHandler()
        webpanel_console_handler.setFormatter(log_format)
        webpanel_logger.addHandler(webpanel_console_handler)

    return {
        'app': app_logger,
        'bot': bot_logger,
        'webpanel': webpanel_logger
    }

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger by name."""
    loggers = setup_logging()
    return loggers.get(name, loggers['app'])