from typing import Dict, Optional
from sqlalchemy.orm import scoped_session
from models import StaticContent
from logging_config import get_logger

logger = get_logger('app')

class StaticContentRepository:
    """
    مدیریت عملیات دیتابیس برای محتوای ثابت.
    """
    def __init__(self, session: scoped_session):
        """
        مقداردهی اولیه با session دیتابیس.
        
        آرگومان‌ها:
            session: نمونه scoped_session برای تعامل با دیتابیس
        """
        self.session = session

    def get_static_content(self, content_type: str) -> Optional[Dict]:
        """
        گرفتن محتوای ثابت با نوع.
        
        آرگومان‌ها:
            content_type: نوع محتوای ثابت
        
        خروجی:
            دیکشنری محتوای ثابت یا None اگه پیدا نشه
        """
        try:
            content = self.session.query(StaticContent).filter_by(content_type=content_type).first()
            if content:
                return {
                    'id': content.id,
                    'content_type': content.content_type,
                    'content': content.content,
                    'updated_at': content.updated_at
                }
            logger.debug(f"محتوای ثابت با نوع {content_type} پیدا نشد")
            return None
        except Exception as e:
            logger.error(f"خطا در گرفتن محتوای ثابت {content_type}: {str(e)}")
            return None
        finally:
            self.session.close()