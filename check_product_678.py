"""
بررسی وضعیت محصول 678
"""

import logging
from src.web.app import app, db
from src.models.models import Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_product_678():
    """بررسی محصول شماره 678"""
    logger.info("بررسی محصول 678...")
    
    try:
        # جستجوی محصول 678
        product = Product.query.filter_by(id=678).first()
        
        if product:
            logger.info(f"محصول 678 یافت شد: {product.name}")
            logger.info(f"وضعیت product_type: {product.product_type}")
            logger.info(f"وضعیت featured: {product.featured}")
            
            # بروزرسانی product_type به 'product'
            if product.product_type != 'product':
                product.product_type = 'product'
                db.session.commit()
                logger.info("محصول 678 به product تغییر یافت")
            else:
                logger.info("محصول 678 از قبل product است")
                
            # بروزرسانی featured به True
            if not product.featured:
                product.featured = True
                db.session.commit()
                logger.info("محصول 678 به featured تغییر یافت")
            else:
                logger.info("محصول 678 از قبل featured است")
        else:
            logger.info("محصول 678 یافت نشد")
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"خطا در بررسی محصول 678: {str(e)}")

if __name__ == "__main__":
    with app.app_context():
        check_product_678()
