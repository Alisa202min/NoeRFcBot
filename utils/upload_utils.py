from typing import Optional
from aiogram.types import Update
from extensions import database
from models import ProductMedia, ServiceMedia, EducationalContentMedia
from logging_config import get_logger

logger = get_logger('media')

class UploadManager:
    """
    ابزارهای آپلود و ذخیره رسانه‌ها در دیتابیس.
    """
    def __init__(self):
        """
        مقداردهی اولیه با نمونه پایگاه داده.
        """
        self.db = database

    async def store_product_media(self, product_id: int, file_id: str, file_type: str = 'photo', local_path: str = None) -> bool:
        """
        ذخیره رسانه جدید برای محصول در دیتابیس.

        Args:
            product_id: شناسه محصول
            file_id: file_id تلگرام
            file_type: نوع رسانه (پیش‌فرض: 'photo')
            local_path: مسیر محلی فایل (اختیاری)

        Returns:
            True اگه موفق، False در غیر این صورت
        """
        try:
            if not file_id:
                logger.error(f"file_id برای رسانه محصول {product_id} خالی است")
                return False

            # استفاده از database برای ایجاد رکورد
            media = ProductMedia(
                product_id=product_id,
                file_id=file_id,
                file_type=file_type,
                local_path=local_path
            )
            self.db.session.add(media)
            self.db.session.commit()
            logger.info(f"رسانه با file_id {file_id} برای محصول {product_id} ذخیره شد")
            return True
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"خطا در ذخیره رسانه برای محصول {product_id}: {str(e)}")
            return False
        finally:
            self.db.session.close()

    async def store_service_media(self, service_id: int, file_id: str, file_type: str = 'photo', local_path: str = None) -> bool:
        """
        ذخیره رسانه جدید برای سرویس در دیتابیس.

        Args:
            service_id: شناسه سرویس
            file_id: file_id تلگرام
            file_type: نوع رسانه (پیش‌فرض: 'photo')
            local_path: مسیر محلی فایل (اختیاری)

        Returns:
            True اگه موفق، False در غیر این صورت
        """
        try:
            if not file_id:
                logger.error(f"file_id برای رسانه سرویس {service_id} خالی است")
                return False

            media = ServiceMedia(
                service_id=service_id,
                file_id=file_id,
                file_type=file_type,
                local_path=local_path
            )
            self.db.session.add(media)
            self.db.session.commit()
            logger.info(f"رسانه با file_id {file_id} برای سرویس {service_id} ذخیره شد")
            return True
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"خطا در ذخیره رسانه برای سرویس {service_id}: {str(e)}")
            return False
        finally:
            self.db.session.close()

    async def store_educational_content_media(self, content_id: int, file_id: str, file_type: str = 'photo', local_path: str = None) -> bool:
        """
        ذخیره رسانه جدید برای محتوای آموزشی در دیتابیس.

        Args:
            content_id: شناسه محتوای آموزشی
            file_id: file_id تلگرام
            file_type: نوع رسانه (پیش‌فرض: 'photo')
            local_path: مسیر محلی فایل (اختیاری)

        Returns:
            True اگه موفق، False در غیر این صورت
        """
        try:
            if not file_id:
                logger.error(f"file_id برای رسانه محتوای آموزشی {content_id} خالی است")
                return False

            media = EducationalContentMedia(
                content_id=content_id,
                file_id=file_id,
                file_type=file_type,
                local_path=local_path
            )
            self.db.session.add(media)
            self.db.session.commit()
            logger.info(f"رسانه با file_id {file_id} برای محتوای آموزشی {content_id} ذخیره شد")
            return True
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"خطا در ذخیره رسانه برای محتوای آموزشی {content_id}: {str(e)}")
            return False
        finally:
            self.db.session.close()

    async def process_uploaded_media(self, update: Update, entity_type: str, entity_id: int) -> bool:
        """
        پردازش رسانه آپلود شده از آپدیت تلگرام و ذخیره در دیتابیس.

        Args:
            update: آپدیت تلگرام حاوی رسانه
            entity_type: نوع موجودیت ('product', 'service', 'educational_content')
            entity_id: شناسه موجودیت

        Returns:
            True اگه موفق، False در غیر این صورت
        """
        try:
            message = update.message
            file_id = None
            file_type = None

            # بررسی نوع رسانه
            if message.photo:
                file_id = message.photo[-1].file_id
                file_type = 'photo'
            elif message.video:
                file_id = message.video.file_id
                file_type = 'video'
            elif message.animation:
                file_id = message.animation.file_id
                file_type = 'animation'
            elif message.document:
                file_id = message.document.file_id
                file_type = 'document'
            else:
                logger.warning(f"نوع رسانه ناشناخته برای آپدیت {update.update_id}")
                return False

            # ذخیره رسانه بر اساس نوع موجودیت
            if entity_type == 'product':
                return await self.store_product_media(entity_id, file_id, file_type)
            elif entity_type == 'service':
                return await self.store_service_media(entity_id, file_id, file_type)
            elif entity_type == 'educational_content':
                return await self.store_educational_content_media(entity_id, file_id, file_type)
            else:
                logger.error(f"نوع موجودیت {entity_type} پشتیبانی نمی‌شود")
                return False
        except Exception as e:
            logger.error(f"خطا در پردازش رسانه آپلود شده برای {entity_type} {entity_id}: {str(e)}")
            return False