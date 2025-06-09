from typing import Dict, Optional
from sqlalchemy.orm import scoped_session
from models import User
from logging_config import get_logger
from datetime import datetime

logger = get_logger('app')

class UserRepository:
    """
    مدیریت عملیات دیتابیس برای کاربران.
    """
    def __init__(self, session: scoped_session):
        """
        مقداردهی اولیه با session دیتابیس.
        
        آرگومان‌ها:
            session: نمونه scoped_session برای تعامل با دیتابیس
        """
        self.session = session

    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """
        گرفتن اطلاعات کاربر با شناسه تلگرام.
        
        آرگومان‌ها:
            telegram_id: شناسه تلگرام کاربر
        
        خروجی:
            دیکشنری اطلاعات کاربر یا None اگه پیدا نشه
        """
        try:
            user = self.session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_admin': user.is_admin,
                    'telegram_id': user.telegram_id,
                    'telegram_username': user.telegram_username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone,
                    'language_code': user.language_code,
                    'created_at': user.created_at,
                    'updated_at': user.updated_at
                }
            logger.debug(f"کاربر با telegram_id {telegram_id} پیدا نشد")
            return None
        except Exception as e:
            logger.error(f"خطا در گرفتن کاربر {telegram_id}: {str(e)}")
            return None
        finally:
            self.session.close()

    def register_user(self, telegram_id: int, username: str, first_name: str, last_name: str, phone: str, language_code: str) -> bool:
        """
        ثبت کاربر جدید در دیتابیس.
        
        آرگومان‌ها:
            telegram_id: شناسه تلگرام کاربر
            username: نام کاربری تلگرام
            first_name: نام
            last_name: نام خانوادگی
            phone: شماره تلفن
            language_code: کد زبان
        
        خروجی:
            True اگه موفق باشه، False در غیر این صورت
        """
        try:
            if self.session.query(User).filter_by(telegram_id=telegram_id).first():
                logger.debug(f"کاربر با telegram_id {telegram_id} قبلاً ثبت شده")
                return False
            user = User(
                telegram_id=telegram_id,
                telegram_username=username,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                language_code=language_code,
                username=f"tg_{telegram_id}"  # برای جلوگیری از null
            )
            self.session.add(user)
            self.session.commit()
            logger.info(f"کاربر با telegram_id {telegram_id} ثبت شد")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"خطا در ثبت کاربر {telegram_id}: {str(e)}")
            return False
        finally:
            self.session.close()

    def update_user(self, telegram_id: int, **kwargs) -> bool:
        """
        به‌روزرسانی اطلاعات کاربر.
        
        آرگومان‌ها:
            telegram_id: شناسه تلگرام کاربر
            kwargs: فیلدهای به‌روزرسانی (مثل first_name, phone)
        
        خروجی:
            True اگه موفق باشه، False در غیر این صورت
        """
        try:
            user = self.session.query(User).filter_by(telegram_id=telegram_id).first()
            if not user:
                logger.warning(f"کاربر با telegram_id {telegram_id} پیدا نشد")
                return False
            allowed_fields = {'username', 'email', 'first_name', 'last_name', 'phone', 'language_code', 'telegram_username'}
            for key, value in kwargs.items():
                if key in allowed_fields and value is not None:
                    setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            self.session.commit()
            logger.debug(f"کاربر با telegram_id {telegram_id} به‌روزرسانی شد")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"خطا در به‌روزرسانی کاربر {telegram_id}: {str(e)}")
            return False
        finally:
            self.session.close()