
from typing import Dict, List, Optional
from sqlalchemy.orm import scoped_session
from models import EducationalContent, EducationalContentMedia, EducationalCategory
from logging_config import get_logger

logger = get_logger('app')

class EducationalContentRepository:
    """
    مدیریت عملیات دیتابیس برای محتواهای آموزشی، رسانه‌ها، و دسته‌بندی‌های محتوای آموزشی.
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
            دیکشنری اطلاعات محتوای آموزشی یا None اگه پیدا نشه
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
        گرفتن اطلاعات دسته‌بندی محتوای آموزشی با شناسه.

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
            logger.debug(f"دسته‌بندی محتوای آموزشی با id {category_id} پیدا نشد")
            return None
        except Exception as e:
            logger.error(f"خطا در گرفتن دسته‌بندی محتوای آموزشی {category_id}: {str(e)}")
            return None
        finally:
            self.session.close()

    def get_all_educational_categories(self) -> List[Dict]:
        """
        گرفتن همه دسته‌بندی‌های محتوای آموزشی.

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
            logger.error(f"خطا در گرفتن همه دسته‌بندی‌های محتوای آموزشی: {str(e)}")
            return []
        finally:
            self.session.close()

    def get_educational_categories(self, parent_id: Optional[int] = None) -> List[Dict]:
        """
        گرفتن دسته‌بندی‌های محتوای آموزشی با تعداد زیرمجموعه‌ها و محتواها.

        آرگومان‌ها:
            parent_id: شناسه دسته‌بندی والد (اختیاری)

        خروجی:
            لیست دیکشنری‌های دسته‌بندی‌ها با اطلاعات اضافی
        """
        session = self.session()
        try:
            query = session.query(EducationalCategory)
            if parent_id is None:
                query = query.filter(EducationalCategory.parent_id.is_(None))
            else:
                query = query.filter_by(parent_id=parent_id)
            categories = query.order_by(EducationalCategory.name).all()
            result = []
            for category in categories:
                subcategory_count = session.query(EducationalCategory).filter_by(parent_id=category.id).count()
                content_count = session.query(EducationalContent).filter_by(category_id=category.id).count()
                result.append({
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id,
                    'subcategory_count': subcategory_count,
                    'content_count': content_count,
                    'total_items': subcategory_count + content_count
                })
            return result
        except Exception as e:
            logger.error(f"خطا در گرفتن دسته‌بندی‌های محتوای آموزشی: {str(e)}")
            return []
        finally:
            session.close()

    def get_educational_contents(self, category_id: int) -> List[Dict]:
        """
        گرفتن همه محتواهای آموزشی یک دسته‌بندی.

        آرگومان‌ها:
            category_id: شناسه دسته‌بندی

        خروجی:
            لیست دیکشنری‌های محتواهای آموزشی
        """
        try:
            contents = self.session.query(EducationalContent).filter_by(category_id=category_id).order_by(EducationalContent.title).all()
            return [{
                'id': c.id,
                'title': c.title,
                'content': c.content,
                'category_id': c.category_id
            } for c in contents]
        except Exception as e:
            logger.error(f"خطا در گرفتن محتواهای آموزشی: {str(e)}")
            return []
        finally:
            self.session.close()
"""

### توضیحات فایل و توابع
1. **کلاس `EducationalContentRepository`**:
   - مشابه `ProductRepository`، این کلاس عملیات پایگاه داده را برای محتوای آموزشی مدیریت می‌کند.
   - با یک نمونه `scoped_session` مقداردهی اولیه می‌شود.

2. **توابع تعریف‌شده**:
   - **`get_educational_content`**:
     - اطلاعات یک محتوای آموزشی را با شناسه (`content_id`) دریافت می‌کند.
     - خروجی شامل فیلدهای `id`, `title`, `content`, `category_id`, `tags`, `featured`, و `created_at` است.
     - مشابه `get_product`، در صورت عدم وجود محتوا `None` و در صورت خطا `None` با لاگ خطا برمی‌گرداند.
   - **`get_educational_content_media`**:
     - رسانه‌های یک محتوای آموزشی را با `content_id` دریافت می‌کند.
     - خروجی لیست دیکشنری‌هایی با فیلدهای `id`, `content_id`, `file_id`, `file_type`, `local_path`, و `created_at` است.
     - مشابه `get_product_media`، در صورت خطا لیست خالی برمی‌گرداند.
   - **`update_educational_content_media_file_id`**:
     - `file_id` یک رسانه را با `media_id` به‌روزرسانی می‌کند.
     - بررسی می‌کند که `new_file_id` خالی نباشد و رسانه وجود داشته باشد.
     - مشابه `update_product_media_file_id`، تراکنش را در صورت خطا رول‌بک می‌کند.
   - **`get_educational_category`**:
     - اطلاعات یک دسته‌بندی را با `category_id` دریافت می‌کند.
     - خروجی شامل `id`, `name`, و `parent_id` است.
     - مشابه `get_product_category`، در صورت عدم وجود دسته‌بندی `None` برمی‌گرداند.
   - **`get_all_educational_categories`**:
     - همه دسته‌بندی‌های محتوای آموزشی را دریافت می‌کند.
     - خروجی لیست دیکشنری‌هایی با `id`, `name`, و `parent_id` است.
     - مشابه `get_all_product_categories`، در صورت خطا لیست خالی برمی‌گرداند.
   - **`get_educational_categories`**:
     - دسته‌بندی‌ها را با تعداد زیرمجموعه‌ها و محتواها دریافت می‌کند.
     - بر اساس `parent_id` فیلتر می‌کند (ریشه یا زیرمجموعه).
     - خروجی شامل `id`, `name`, `parent_id`, `subcategory_count`, `content_count`, و `total_items` است.
     - مشابه `get_product_categories`، تعداد زیرمجموعه‌ها و محتواها را محاسبه می‌کند.
   - **`get_educational_contents`**:
     - همه محتواهای یک دسته‌بندی را با `category_id` دریافت می‌کند.
     - محتواها بر اساس عنوان (`title`) مرتب‌سازی می‌شوند.
     - خروجی شامل `id`, `title`, `content`, و `category_id` است.
     - مشابه `get_products`، در صورت خطا لیست خالی برمی‌گرداند.

3. **مدیریت خطاها و لاگ‌گیری**:
   - هر تابع خطاها را با جزئیات لاگ می‌کند (با استفاده از `logger.error`).
   - پیام‌های دیباگ برای موارد یافت‌نشده (مانند عدم وجود محتوا یا دسته‌بندی) ثبت می‌شود.
   - جلسه پایگاه داده در بلاک `finally` بسته می‌شود.
   - مقادیر پیش‌فرض (`None` یا `[]`) در صورت خطا برگردانده می‌شوند.

4. **مستندات**:
   - مستندات به زبان فارسی روان و مشابه `product_repository.py` نوشته شده‌اند.
   - توضیحات شامل آرگومان‌ها، خروجی، و هدف هر تابع است.
   - از فرمت یکسان برای تمام توابع استفاده شده است.

### سازگاری با `models.py`
- مدل‌های مورد استفاده:
  - `EducationalContent`: شامل فیلدهای لازم برای توابع (`id`, `title`, `content`, `category_id`, `tags`, `featured`, `created_at`).
  - `EducationalContentMedia`: شامل فیلدهای `id`, `content_id`, `file_id`, `file_type`, `local_path`, `created_at`.
  - `EducationalCategory`: شامل فیلدهای `id`, `name`, `parent_id`.
- روابط:
  - رابطه `educational_contents` در `EducationalCategory` (با `backref='educational_contents'`) امکان شمارش محتواها در `get_educational_categories` را فراهم می‌کند.
  - رابطه `media` در `EducationalContent` امکان دسترسی به رسانه‌ها را در توابع فراهم می‌کند.
- مدل‌ها با توابع سازگار هستند و نیازی به تغییر ندارند.

### هماهنگی با پروژه
- **با `product_repository.py`**:
  - ساختار و منطق توابع دقیقاً مشابه است، با تفاوت در مدل‌های استفاده‌شده (`EducationalContent` به جای `Product`, `EducationalCategory` به جای `ProductCategory`, `EducationalContentMedia` به جای `ProductMedia`).
- **با `service_handlers.py`**:
  - مشابه `service_handlers.py` (نسخه اصلاح‌شده در پاسخ قبلی)، که توابع `get_service_categories` و `get_services` به آن اضافه شد.
- **با فایل‌های دیگر**:
  - **upload_utils.py**:
    - تابع `store_educational_content_media` از مدل `EducationalContentMedia` استفاده می‌کند و با `update_educational_content_media_file_id` هماهنگ است.
  - **utils.py**:
    - تابع `format_educational_content` از خروجی `get_educational_content` و `get_educational_content_media` برای قالب‌بندی اطلاعات استفاده می‌کند.
  - **education_handlers.py** (فرض‌شده):
    - می‌تواند از توابع این فایل برای نمایش محتوا و دسته‌بندی‌ها استفاده کند. مثال:
      ```python
      async def callback_educational_content(callback: CallbackQuery, db: EducationalContentRepository):
          content_id = int(callback.data.split(':')[1])
          content = db.get_educational_content(content_id)
          media = db.get_educational_content_media(content_id)
          # نمایش محتوا و رسانه‌ها
      ```

### نکات
- **وابستگی‌ها**:
  - فایل به `typing`, `sqlalchemy.orm`, `models`, و `logging_config` وابسته است.
- **مدیریت جلسه**:
  - مشابه `product_repository.py`, جلسه در `get_educational_categories` به صورت دستی ایجاد می‌شود (`session = self.session()`), زیرا نیاز به چندین پرس‌وجو دارد.
- **به‌روزرسانی‌های احتمالی**:
  - اگر نیاز به افزودنابع اضافی به خروجی‌ها (مانند `updated_at` یا فیلدهای جدید) دارید, مشخص کنید.
  - اگر نیاز به افزودن توابع جدید (مانند جستجو بر اساس برچسب یا فیلترهای پیشرفته) دارید, اطلاع دهید.
- **استفاده در هندلرها**:
  - پیشنهاد می‌شود در فایل `education_handlers.py` از توابع `get_educational_categories` و `get_educational_contents` برای نمایش دسته‌بندی‌ها و محتواها در رابط کاربری تلگرام استفاده شود.

این فایل باید تمام نیازهای شما را برای مدیریت محتوای آموزشی مشابه محصولات برآورده کند. اگر تغییر یا افزودنی دیگری لازم است (مانند افزودن توابع جدید یا هماهنگی با بخش‌های دیگر پروژه), لطفاً اطلاع دهید!
"""