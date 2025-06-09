from typing import Dict, List, Optional
from sqlalchemy.orm import scoped_session
from models import Service, ServiceMedia, ServiceCategory
from logging_config import get_logger

logger = get_logger('app')

class ServiceRepository:
    """
    مدیریت عملیات دیتابیس برای سرویس‌ها، رسانه‌ها، و دسته‌بندی‌های سرویس.
    """
    def __init__(self, session: scoped_session):
        """
        مقداردهی اولیه با session دیتابیس.
        
        آرگومان‌ها:
            session: نمونه scoped_session برای تعامل با دیتابیس
        """
        self.session = session

    def get_service(self, service_id: int) -> Optional[Dict]:
        """
        گرفتن اطلاعات سرویس با شناسه.
        
        آرگومان‌ها:
            service_id: شناسه سرویس
        
        خروجی:
            دیکشنری اطلاعات سرویس یا None اگه پیدا نشه
        """
        try:
            service = self.session.query(Service).filter_by(id=service_id).first()
            if service:
                return {
                    'id': service.id,
                    'name': service.name,
                    'description': service.description,
                    'price': service.price,
                    'category_id': service.category_id,
                    'featured': service.featured,
                    'available': service.available,
                    'tags': service.tags,
                    'created_at': service.created_at,
                    'updated_at': service.updated_at
                }
            logger.debug(f"سرویس با id {service_id} پیدا نشد")
            return None
        except Exception as e:
            logger.error(f"خطا در گرفتن سرویس {service_id}: {str(e)}")
            return None
        finally:
            self.session.close()

    def get_service_media(self, service_id: int) -> List[Dict]:
        """
        گرفتن رسانه‌های مرتبط با سرویس.
        
        آرگومان‌ها:
            service_id: شناسه سرویس
        
        خروجی:
            لیست دیکشنری‌های رسانه‌ها
        """
        try:
            media_list = self.session.query(ServiceMedia).filter_by(service_id=service_id).all()
            return [
                {
                    'id': media.id,
                    'service_id': media.service_id,
                    'file_id': media.file_id,
                    'file_type': media.file_type,
                    'local_path': media.local_path,
                    'created_at': media.created_at
                }
                for media in media_list
            ]
        except Exception as e:
            logger.error(f"خطا در گرفتن رسانه‌های سرویس {service_id}: {str(e)}")
            return []
        finally:
            self.session.close()

    def update_service_media_file_id(self, media_id: int, new_file_id: str) -> bool:
        """
        به‌روزرسانی file_id رسانه سرویس.
        
        آرگومان‌ها:
            media_id: شناسه رسانه
            new_file_id: file_id جدید تلگرام
        
        خروجی:
            True اگه موفق باشه، False در غیر این صورت
        """
        try:
            if not new_file_id:
                logger.error(f"file_id جدید برای رسانه {media_id} خالی است")
                return False
            media = self.session.query(ServiceMedia).filter_by(id=media_id).first()
            if not media:
                logger.warning(f"رسانه با id {media_id} پیدا نشد")
                return False
            media.file_id = new_file_id
            self.session.commit()
            logger.debug(f"file_id رسانه {media_id} به {new_file_id} به‌روزرسانی شد")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"خطا در به‌روزرسانی file_id رسانه {media_id}: {str(e)}")
            return False
        finally:
            self.session.close()

    def get_service_category(self, category_id: int) -> Optional[Dict]:
        """
        گرفتن اطلاعات دسته‌بندی سرویس با شناسه.
        
        آرگومان‌ها:
            category_id: شناسه دسته‌بندی
        
        خروجی:
            دیکشنری اطلاعات دسته‌بندی یا None اگه پیدا نشه
        """
        try:
            category = self.session.query(ServiceCategory).filter_by(id=category_id).first()
            if category:
                return {
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id
                }
            logger.debug(f"دسته‌بندی سرویس با id {category_id} پیدا نشد")
            return None
        except Exception as e:
            logger.error(f"خطا در گرفتن دسته‌بندی سرویس {category_id}: {str(e)}")
            return None
        finally:
            self.session.close()

    def get_all_service_categories(self) -> List[Dict]:
        """
        گرفتن همه دسته‌بندی‌های سرویس.
        
        خروجی:
            لیست دیکشنری‌های دسته‌بندی‌ها
        """
        try:
            categories = self.session.query(ServiceCategory).all()
            return [
                {
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id
                }
                for category in categories
            ]
        except Exception as e:
            logger.error(f"خطا در گرفتن همه دسته‌بندی‌های سرویس: {str(e)}")
            return []
        finally:
            self.session.close()