import os
import csv
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime

def format_price(price: int) -> str:
    """
    Format price with thousand separator
    
    Args:
        price: Price as integer
        
    Returns:
        Formatted price string
    """
    return f"{price:,} تومان"

def format_product_details(product: Dict) -> str:
    """
    Format product details for display
    
    Args:
        product: Product dictionary
        
    Returns:
        Formatted product details
    """
    name = product['name']
    price = format_price(product['price'])
    description = product['description'] or "توضیحات موجود نیست"
    
    return f"📦 *{name}*\n\n💰 قیمت: {price}\n\n📝 توضیحات:\n{description}"

def format_inquiry_details(inquiry: Dict) -> str:
    """
    Format inquiry details for display
    
    Args:
        inquiry: Inquiry dictionary
        
    Returns:
        Formatted inquiry details
    """
    # Format date
    date_str = inquiry['date']
    try:
        date_obj = datetime.fromisoformat(date_str)
        formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
    except:
        formatted_date = date_str
    
    # Get product name if available
    product_info = f"\n🛍 محصول: {inquiry['product_name']}" if inquiry.get('product_name') else ""
    
    return (
        f"📝 *استعلام قیمت*\n\n"
        f"👤 نام: {inquiry['name']}\n"
        f"📞 شماره تماس: {inquiry['phone']}\n"
        f"📅 تاریخ: {formatted_date}{product_info}\n\n"
        f"توضیحات: {inquiry['description'] or 'بدون توضیحات'}"
    )

def format_educational_content(content: Dict) -> str:
    """
    Format educational content for display
    
    Args:
        content: Content dictionary
        
    Returns:
        Formatted content
    """
    title = content['title']
    content_text = content['content']
    category = content['category']
    content_type = content['type']
    
    # Format based on content type
    if content_type == 'link':
        return f"📚 *{title}*\n\n🔗 لینک: {content_text}\n\n📂 دسته‌بندی: {category}"
    else:
        return f"📚 *{title}*\n\n{content_text}\n\n📂 دسته‌بندی: {category}"

def is_valid_phone_number(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Simple validation: should be at least 10 digits
    digits = ''.join(filter(str.isdigit, phone))
    return len(digits) >= 10

def get_category_path(db, category_id: int) -> str:
    """
    Get full category path
    
    Args:
        db: Database instance
        category_id: Category ID
        
    Returns:
        Full category path (e.g., "Electronics > Sensors > Temperature")
    """
    path = []
    current_id = category_id
    
    while current_id is not None:
        category = db.get_category(current_id)
        if category:
            path.append(category['name'])
            current_id = category['parent_id']
        else:
            break
    
    # Reverse to get top-down order
    path.reverse()
    return " > ".join(path)

def create_sample_data(db) -> None:
    """
    Create sample data for initial setup
    
    Args:
        db: Database instance
    """
    # Create product categories
    electronics_id = db.add_category("تجهیزات الکترونیکی", None, 'product')
    sensors_id = db.add_category("سنسورها", electronics_id, 'product')
    temp_sensors_id = db.add_category("سنسور دما", sensors_id, 'product')
    
    # Create products
    db.add_product(
        name="سنسور دما حرفه‌ای",
        price=500000,
        description="سنسور دمای دقیق با قابلیت اندازه‌گیری دما از -50 تا 150 درجه سانتیگراد",
        category_id=temp_sensors_id,
        photo_url="https://example.com/temp_sensor.jpg"
    )
    
    db.add_product(
        name="سنسور رطوبت",
        price=350000,
        description="سنسور رطوبت با دقت بالا",
        category_id=sensors_id,
        photo_url="https://example.com/humidity_sensor.jpg"
    )
    
    # Create service categories
    services_id = db.add_category("خدمات فنی", None, 'service')
    repair_id = db.add_category("تعمیرات", services_id, 'service')
    
    # Create services
    db.add_product(
        name="تعمیر سنسور",
        price=200000,
        description="تعمیر انواع سنسورهای الکترونیکی",
        category_id=repair_id
    )
    
    # Create educational content
    db.add_educational_content(
        title="اصول کار با سنسورها",
        content="در این مطلب با اصول کار با سنسورهای الکترونیکی آشنا می‌شوید.",
        category="آموزش سنسورها",
        content_type="text"
    )
    
    db.add_educational_content(
        title="ویدیوی آموزشی نصب سنسور",
        content="https://example.com/sensor_installation_video",
        category="آموزش سنسورها",
        content_type="link"
    )

def import_initial_data(db, csv_path: str = None) -> Tuple[int, int]:
    """
    Import initial data from CSV file
    
    Args:
        db: Database instance
        csv_path: Path to CSV file, or None to use default
        
    Returns:
        Tuple of (success_count, error_count)
    """
    from configuration import CSV_PATH
    
    if csv_path is None:
        csv_path = CSV_PATH
    
    if not os.path.exists(csv_path):
        logging.warning(f"CSV file not found: {csv_path}")
        return (0, 0)
    
    try:
        # Try to determine entity type from CSV
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames
            
            if 'price' in headers:
                entity_type = 'products'
            elif 'parent_id' in headers:
                entity_type = 'categories'
            elif 'content' in headers:
                entity_type = 'educational'
            else:
                logging.error("Unknown CSV format")
                return (0, 0)
        
        # Import data
        return db.import_from_csv(entity_type, csv_path)
    except Exception as e:
        logging.error(f"Error importing data from CSV: {e}")
        return (0, 0)

def generate_csv_template(output_path: str, entity_type: str) -> bool:
    """
    Generate a CSV template file
    
    Args:
        output_path: Path to save CSV file
        entity_type: Type of entity (products/categories/educational)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            if entity_type == 'products':
                fieldnames = ['name', 'price', 'description', 'photo_url', 'category_name']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                # Add sample row
                writer.writerow({
                    'name': 'سنسور دما',
                    'price': '500000',
                    'description': 'سنسور دقیق برای دما',
                    'photo_url': 'https://example.com/photo1.jpg',
                    'category_name': 'سنسورها'
                })
            
            elif entity_type == 'categories':
                fieldnames = ['name', 'parent_name', 'type']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                # Add sample rows
                writer.writerow({
                    'name': 'تجهیزات الکترونیکی',
                    'parent_name': '',
                    'type': 'product'
                })
                writer.writerow({
                    'name': 'سنسورها',
                    'parent_name': 'تجهیزات الکترونیکی',
                    'type': 'product'
                })
            
            elif entity_type == 'educational':
                fieldnames = ['title', 'content', 'category', 'type']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                # Add sample row
                writer.writerow({
                    'title': 'اصول کار با سنسورها',
                    'content': 'در این مطلب با اصول کار با سنسورهای الکترونیکی آشنا می‌شوید.',
                    'category': 'آموزش سنسورها',
                    'type': 'text'
                })
        
        return True
    except Exception as e:
        logging.error(f"Error generating CSV template: {e}")
        return False
