from typing import Dict, List, Optional
from sqlalchemy.orm import scoped_session
from models import Inquiry
from logging_config import get_logger
from datetime import datetime

logger = get_logger('app')

class InquiryRepository:
    """
    مدیریت عملیات دیتابیس برای درخواست‌ها.
    """
    def __init__(self, session: scoped_session):
        """
        مقداردهی اولیه با session دیتابیس.
        
        آرگومان‌ها:
            session: نمونه scoped_session برای تعامل با دیتابیس
        """
        self.session = session

    def create_inquiry(self, user_id: int, name: str, phone: str, description: str, product_id: int = None, service_id: int = None) -> bool:
        """
        ایجاد درخواست جدید.
        
        آرگومان‌ها:
            user_id: شناسه تلگرام کاربر
            name: نام کاربر
            phone: شماره تلفن
            description: توضیحات درخواست
            product_id: شناسه محصول (اختیاری)
            service_id: شناسه سرویس (اختیاری)
        
        خروجی:
            True اگه موفق باشه، False در غیر این صورت
        """
        try:
            if (product_id and service_id) or (not product_id and not service_id and not description):
                logger.error(f"ورودی نامعتبر برای درخواست: product_id={product_id}, service_id={service_id}")
                return False
            inquiry = Inquiry(
                user_id=user_id,
                name=name,
                phone=phone,
                description=description,
                product_id=product_id,
                service_id=service_id,
                status='new',
                date=datetime.utcnow()
            )
            self.session.add(inquiry)
            self.session.commit()
            logger.info(f"درخواست با id {inquiry.id} برای کاربر {user_id} ایجاد شد")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"خطا در ایجاد درخواست برای کاربر {user_id}: {str(e)}")
            return False
        finally:
            self.session.close()

    def get_inquiries(self, user_id: int = None, status: str = None) -> List[Dict]:
        """
        گرفتن درخواست‌ها با فیلتر اختیاری.
        
        آرگومان‌ها:
            user_id: شناسه تلگرام کاربر (اختیاری)
            status: وضعیت درخواست (اختیاری)
        
        خروجی:
            لیست دیکشنری‌های درخواست‌ها
        """
        try:
            query = self.session.query(Inquiry)
            if user_id:
                query = query.filter_by(user_id=user_id)
            if status:
                query = query.filter_by(status=status)
            inquiries = query.all()
            return [
                {
                    'id': inquiry.id,
                    'user_id': inquiry.user_id,
                    'product_id': inquiry.product_id,
                    'service_id': inquiry.service_id,
                    'name': inquiry.name,
                    'phone': inquiry.phone,
                    'description': inquiry.description,
                    'status': inquiry.status,
                    'date': inquiry.date,
                    'created_at': inquiry.created_at,
                    'updated_at': inquiry.updated_at
                }
                for inquiry in inquiries
            ]
        except Exception as e:
            logger.error(f"خطا در گرفتن درخواست‌ها: {str(e)}")
            return []
        finally:
            self.session.close()