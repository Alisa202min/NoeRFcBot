from typing import Dict, List, Optional
from sqlalchemy.orm import scoped_session
from models import Product, ProductMedia, ProductCategory
from logging_config import get_logger

logger = get_logger('app')

class ProductRepository:
    """
    مدیریت عملیات دیتابیس برای محصولات، رسانه‌ها، و دسته‌بندی‌های محصول.
    """
    def __init__(self, session: scoped_session):
        """
        مقداردهی اولیه با session دیتابیس.

        آرگومان‌ها:
            session: نمونه scoped_session برای تعامل با دیتابیس
        """
        self.session = session

    def get_product(self, product_id: int) -> Optional[Dict]:
        """
        گرفتن اطلاعات محصول با شناسه.

        آرگومان‌ها:
            product_id: شناسه محصول

        خروجی:
            دیکشنری اطلاعات محصول یا None اگه پیدا نشه
        """
        try:
            product = self.session.query(Product).filter_by(id=product_id).first()
            if product:
                return {
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'price': product.price,
                    'category_id': product.category_id,
                    'brand': product.brand,
                    'model': product.model,
                    'in_stock': product.in_stock,
                    'tags': product.tags,
                    'featured': product.featured,
                    'model_number': product.model_number,
                    'manufacturer': product.manufacturer,
                    'provider': product.provider,
                    'service_code': product.service_code,
                    'duration': product.duration,
                    'created_at': product.created_at,
                    'updated_at': product.updated_at
                }
            logger.debug(f"محصول با id {product_id} پیدا نشد")
            return None
        except Exception as e:
            logger.error(f"خطا در گرفتن محصول {product_id}: {str(e)}")
            return None
        finally:
            self.session.close()

    def get_product_media(self, product_id: int) -> List[Dict]:
        """
        گرفتن رسانه‌های مرتبط با محصول.

        آرگومان‌ها:
            product_id: شناسه محصول

        خروجی:
            لیست دیکشنری‌های رسانه‌ها
        """
        try:
            media_list = self.session.query(ProductMedia).filter_by(product_id=product_id).all()
            return [
                {
                    'id': media.id,
                    'product_id': media.product_id,
                    'file_id': media.file_id,
                    'file_type': media.file_type,
                    'local_path': media.local_path,
                    'created_at': media.created_at
                }
                for media in media_list
            ]
        except Exception as e:
            logger.error(f"خطا در گرفتن رسانه‌های محصول {product_id}: {str(e)}")
            return []
        finally:
            self.session.close()

    def update_product_media_file_id(self, media_id: int, new_file_id: str) -> bool:
        """
        به‌روزرسانی file_id رسانه محصول.

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
            media = self.session.query(ProductMedia).filter_by(id=media_id).first()
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

    def get_product_category(self, category_id: int) -> Optional[Dict]:
        """
        گرفتن اطلاعات دسته‌بندی محصول با شناسه.

        آرگومان‌ها:
            category_id: شناسه دسته‌بندی

        خروجی:
            دیکشنری اطلاعات دسته‌بندی یا None اگه پیدا نشه
        """
        try:
            category = self.session.query(ProductCategory).filter_by(id=category_id).first()
            if category:
                return {
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id
                }
            logger.debug(f"دسته‌بندی محصول با id {category_id} پیدا نشد")
            return None
        except Exception as e:
            logger.error(f"خطا در گرفتن دسته‌بندی محصول {category_id}: {str(e)}")
            return None
        finally:
            self.session.close()

    def get_all_product_categories(self) -> List[Dict]:
        """
        گرفتن همه دسته‌بندی‌های محصول.

        خروجی:
            لیست دیکشنری‌های دسته‌بندی‌ها
        """
        try:
            categories = self.session.query(ProductCategory).all()
            return [
                {
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id
                }
                for category in categories
            ]
        except Exception as e:
            logger.error(f"خطا در گرفتن همه دسته‌بندی‌های محصول: {str(e)}")
            return []
        finally:
            self.session.close()

    def get_product_categories(self, parent_id: Optional[int] = None) -> List[Dict]:
        """
        گرفتن دسته‌بندی‌های محصول با تعداد زیرمجموعه‌ها و محصولات.

        آرگومان‌ها:
            parent_id: شناسه دسته‌بندی والد (اختیاری)

        خروجی:
            لیست دیکشنری‌های دسته‌بندی‌ها با اطلاعات اضافی
        """
        session = self.session()
        try:
            query = session.query(ProductCategory)
            if parent_id is None:
                query = query.filter(ProductCategory.parent_id.is_(None))
            else:
                query = query.filter_by(parent_id=parent_id)
            categories = query.order_by(ProductCategory.name).all()
            result = []
            for category in categories:
                subcategory_count = session.query(ProductCategory).filter_by(parent_id=category.id).count()
                product_count = session.query(Product).filter_by(category_id=category.id).count()
                result.append({
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id,
                    'subcategory_count': subcategory_count,
                    'product_count': product_count,
                    'total_items': subcategory_count + product_count
                })
            return result
        except Exception as e:
            logger.error(f"Error in get_product_categories: {str(e)}")
            return []
        finally:
            session.close()

    def get_products(self, category_id: int) -> List[Dict]:
        """Get all products in a category"""
       
        try:
            products = self.session.query(Product).filter_by(category_id=category_id).order_by(Product.name).all()
            return [{
                'id': p.id,
                'name': p.name,
                'price': p.price,
                'description': p.description,
                'category_id': p.category_id
            } for p in products]
        except Exception as e:
            logger.error(f"Error getting products: {str(e)}")
            return []
        finally:
            self.session.close()