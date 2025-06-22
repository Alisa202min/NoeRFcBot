from typing import Dict, List, Optional
from sqlalchemy.orm import scoped_session
from models import EducationalContent, EducationalContentMedia, EducationalCategory
from logging_config import get_logger

logger = get_logger('app')

class TutorialRepository:
    """
    مدیریت عملیات دیتابیس برای محتوای آموزشی، رسانه‌ها، و دسته‌بندی‌های آموزشی.
    """
    def __init__(self, session: scoped_session):
        """
        مقداردهی اولیه با session دیتابیس.
        
        آرگومان‌ها:
            session: نمونه scoped_session برای تعامل با دیتابیس
        """
        self.session = session

    def get_educational_content(self, content_id: int) -> Optional[Dict]:
        """
        گرفتن اطلاعات محتوای آموزشی با شناسه.
        
        آرگومان‌ها:
            content_id: شناسه محتوای آموزشی
        
        خروجی:
            دیکشنری اطلاعات محتوا یا None اگه پیدا نشه
        """
        try:
            content = self.session.query(EducationalContent).filter_by(id=content_id).first()
            if content:
                return {
                    'id': content.id,
                    'title': content.title,
                    'content': content.content,
                    'category_id': content.category_id,
                    'tags': content.tags,
                    'featured': content.featured,
                    'created_at': content.created_at
                }
            logger.debug(f"محتوای آموزشی با id {content_id} پیدا نشد")
            return None
        except Exception as e:
            logger.error(f"خطا در گرفتن محتوای آموزشی {content_id}: {str(e)}")
            return None
        finally:
            self.session.close()

    def get_educational_content_media(self, content_id: int) -> List[Dict]:
        """
        گرفتن رسانه‌های مرتبط با محتوای آموزشی.
        
        آرگومان‌ها:
            content_id: شناسه محتوای آموزشی
        
        خروجی:
            لیست دیکشنری‌های رسانه‌ها
        """
        try:
            media_list = self.session.query(EducationalContentMedia).filter_by(content_id=content_id).all()
            return [
                {
                    'id': media.id,
                    'content_id': media.content_id,
                    'file_id': media.file_id,
                    'file_type': media.file_type,
                    'local_path': media.local_path,
                    'created_at': media.created_at
                }
                for media in media_list
            ]
        except Exception as e:
            logger.error(f"خطا در گرفتن رسانه‌های محتوای آموزشی {content_id}: {str(e)}")
            return []
        finally:
            self.session.close()

    def update_educational_content_media_file_id(self, media_id: int, new_file_id: str) -> bool:
        """
        به‌روزرسانی file_id رسانه محتوای آموزشی.
        
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
            media = self.session.query(EducationalContentMedia).filter_by(id=media_id).first()
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

    def get_educational_category(self, category_id: int) -> Optional[Dict]:
        """
        گرفتن اطلاعات دسته‌بندی آموزشی با شناسه.
        
        آرگومان‌ها:
            category_id: شناسه دسته‌بندی
        
        خروجی:
            دیکشنری اطلاعات دسته‌بندی یا None اگه پیدا نشه
        """
        try:
            category = self.session.query(EducationalCategory).filter_by(id=category_id).first()
            if category:
                return {
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id
                }
            logger.debug(f"دسته‌بندی آموزشی با id {category_id} پیدا نشد")
            return None
        except Exception as e:
            logger.error(f"خطا در گرفتن دسته‌بندی آموزشی {category_id}: {str(e)}")
            return None
        finally:
            self.session.close()

    def get_all_educational_categories(self) -> List[Dict]:
        """
        گرفتن همه دسته‌بندی‌های آموزشی.
        
        خروجی:
            لیست دیکشنری‌های دسته‌بندی‌ها
        """
        try:
            categories = self.session.query(EducationalCategory).all()
            return [
                {
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id
                }
                for category in categories
            ]
        except Exception as e:
            logger.error(f"خطا در گرفتن همه دسته‌بندی‌های آموزشی: {str(e)}")
            return []
        finally:
            self.session.close()