from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, DeclarativeBase
from logging_config import get_logger
from repositories.product_repository import ProductRepository
from repositories.service_repository import ServiceRepository
from repositories.tutorial_repository import TutorialRepository
from repositories.user_repository import UserRepository
from repositories.inquiry_repository import InquiryRepository
from repositories.static_content_repository import StaticContentRepository

logger = get_logger('app')

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)  # Flask-SQLAlchemy instance

class Database:
    def __init__(self):
        self.engine = None
        self.Session = None
        self.product_repo = None
        self.service_repo = None
        self.tutorial_repo = None
        self.user_repo = None
        self.inquiry_repo = None
        self.static_content_repo = None

    def initialize(self, database_url):
        try:
            if not database_url:
                logger.error("Database URL not provided")
                raise ValueError("Database URL not provided")
            self.engine = create_engine(database_url, echo=False)
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            self.product_repo = ProductRepository(self.Session)
            self.service_repo = ServiceRepository(self.Session)
            self.tutorial_repo = TutorialRepository(self.Session)
            self.user_repo = UserRepository(self.Session)
            self.inquiry_repo = InquiryRepository(self.Session)
            self.static_content_repo = StaticContentRepository(self.Session)
            logger.info("Database and repository Initialized successfully")
        except Exception as e:
            logger.error(f"Error in  initialize Database: {str(e)}", exc_info=True)
            raise

    # توابع محصول
    def get_product(self, product_id: int) -> dict | None:
        """گرفتن محصول با شناسه."""
        return self.product_repo.get_product(product_id)

    def get_product_media(self, product_id: int) -> list[dict]:
        """گرفتن رسانه‌های محصول."""
        return self.product_repo.get_product_media(product_id)

    def update_product_media_file_id(self, media_id: int, new_file_id: str) -> bool:
        """به‌روزرسانی file_id رسانه محصول."""
        return self.product_repo.update_product_media_file_id(media_id, new_file_id)


    def get_product_categories(self, parent_id: int = None) -> list[dict]:
        """گرفتن دسته‌بندی‌های محصول با تعداد زیرمجموعه‌ها و محصولات."""
        return self.product_repo.get_product_categories(parent_id)
        
    def get_product_category(self, category_id: int) -> dict | None:
        """گرفتن دسته‌بندی محصول با شناسه."""
        return self.product_repo.get_product_category(category_id)

    def get_all_product_categories(self) -> list[dict]:
        """گرفتن همه دسته‌بندی‌های محصول."""
        return self.product_repo.get_all_product_categories()
        
    def get_products(self, category_id: int) -> list[dict]:
        """گرفتن محصولات یعک دسته بندی با شناسه دسته بندی ."""
        return self.product_repo.get_products(category_id)

    
    # توابع سرویس
    def get_service(self, service_id: int) -> dict | None:
        """گرفتن سرویس با شناسه."""
        return self.service_repo.get_service(service_id)

    def get_service_media(self, service_id: int) -> list[dict]:
        """گرفتن رسانه‌های سرویس."""
        return self.service_repo.get_service_media(service_id)

    def update_service_media_file_id(self, media_id: int, new_file_id: str) -> bool:
        """به‌روزرسانی file_id رسانه سرویس."""
        return self.service_repo.update_service_media_file_id(media_id, new_file_id)

    def get_service_category(self, category_id: int) -> dict | None:
        """گرفتن دسته‌بندی سرویس با شناسه."""
        return self.service_repo.get_service_category(category_id)

    def get_all_service_categories(self) -> list[dict]:
        """گرفتن همه دسته‌بندی‌های سرویس."""
        return self.service_repo.get_all_service_categories()

    # توابع محتوای آموزشی
    def get_educational_content(self, content_id: int) -> dict | None:
        """گرفتن محتوای آموزشی با شناسه."""
        return self.tutorial_repo.get_educational_content(content_id)

    def get_educational_content_media(self, content_id: int) -> list[dict]:
        """گرفتن رسانه‌های محتوای آموزشی."""
        return self.tutorial_repo.get_educational_content_media(content_id)

    def update_educational_content_media_file_id(self, media_id: int, new_file_id: str) -> bool:
        """به‌روزرسانی file_id رسانه محتوای آموزشی."""
        return self.tutorial_repo.update_educational_content_media_file_id(media_id, new_file_id)

    def get_educational_category(self, category_id: int) -> dict | None:
        """گرفتن دسته‌بندی محتوای آموزشی با شناسه."""
        return self.tutorial_repo.get_educational_category(category_id)

    def get_all_educational_categories(self) -> list[dict]:
        """گرفتن همه دسته‌بندی‌های محتوای آموزشی."""
        return self.tutorial_repo.get_all_educational_categories()

    # توابع کاربر
    def get_user(self, telegram_id: int) -> dict | None:
        """گرفتن کاربر با شناسه تلگرام."""
        return self.user_repo.get_user(telegram_id)

    def register_user(self, telegram_id: int, username: str, first_name: str, last_name: str, phone: str, language_code: str) -> bool:
        """ثبت کاربر جدید."""
        return self.user_repo.register_user(telegram_id, username, first_name, last_name, phone, language_code)

    def update_user(self, telegram_id: int, **kwargs) -> bool:
        """به‌روزرسانی اطلاعات کاربر."""
        return self.user_repo.update_user(telegram_id, **kwargs)

    # توابع درخواست
    def create_inquiry(self, user_id: int, name: str, phone: str, description: str, product_id: int = None, service_id: int = None) -> bool:
        """ایجاد درخواست جدید."""
        return self.inquiry_repo.create_inquiry(user_id, name, phone, description, product_id, service_id)

    def get_inquiries(self, user_id: int = None, status: str = None) -> list[dict]:
        """گرفتن درخواست‌ها با فیلتر اختیاری."""
        return self.inquiry_repo.get_inquiries(user_id, status)

    # توابع محتوای ثابت
    def get_static_content(self, content_type: str) -> dict | None:
        """گرفتن محتوای ثابت با نوع."""
        return self.static_content_repo.get_static_content(content_type)

    


database = Database()