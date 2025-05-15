"""
به‌روزرسانی سرویس‌ها برای نمایش در صفحه اصلی
"""

import logging
from src.web.app import app, db
from src.models.models import Service
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_services():
    """تنظیم مقدار featured برای همه سرویس‌ها به true"""
    logger.info("شروع به‌روزرسانی سرویس‌ها...")
    
    try:
        # تعداد سرویس‌ها قبل از به‌روزرسانی
        services_count = Service.query.count()
        logger.info(f"تعداد سرویس‌ها قبل از به‌روزرسانی: {services_count}")
        
        # به‌روزرسانی همه سرویس‌ها
        update_query = text("""
            UPDATE services SET featured = TRUE, available = TRUE
        """)
        db.session.execute(update_query)
        db.session.commit()
        
        # تعداد سرویس‌های به‌روزرسانی شده
        featured_count = Service.query.filter_by(featured=True).count()
        available_count = Service.query.filter_by(available=True).count()
        
        logger.info(f"تعداد سرویس‌های featured شده: {featured_count}")
        logger.info(f"تعداد سرویس‌های available شده: {available_count}")
        logger.info("به‌روزرسانی سرویس‌ها با موفقیت انجام شد")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"خطا در به‌روزرسانی سرویس‌ها: {str(e)}")
        raise

if __name__ == "__main__":
    with app.app_context():
        update_services()
