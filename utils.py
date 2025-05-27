import os
import csv
import logging
import aiohttp
import json
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

def format_product_details(product: Dict, media_files: List[Dict] = None) -> str:
    """
    Format product details for display
    
    Args:
        product: Product dictionary
        media_files: List of media files (optional)
        
    Returns:
        Formatted product details
    """
    name = product['name']
    price = format_price(product['price'])
    description = product['description'] or "توضیحات موجود نیست"
    
    result = f"📦 *{name}*\n\n💰 قیمت: {price}\n\n📝 توضیحات:\n{description}"
    
    # Add media info if available
    if media_files and len(media_files) > 0:
        photo_count = sum(1 for m in media_files if m['file_type'] == 'photo')
        video_count = sum(1 for m in media_files if m['file_type'] == 'video')
        
        media_info = []
        if photo_count > 0:
            media_info.append(f"🖼 {photo_count} تصویر")
        if video_count > 0:
            media_info.append(f"🎬 {video_count} ویدیو")
            
        if media_info:
            result += "\n\n" + " | ".join(media_info)
    
    return result
    
def format_service_details(service: Dict, media_files: List[Dict] = None) -> str:
    """
    Format service details for display
    
    Args:
        service: Service dictionary
        media_files: List of media files (optional)
        
    Returns:
        Formatted service details
    """
    name = service['name']
    price = format_price(service['price']) if service['price'] is not None else "تماس بگیرید"
    description = service['description'] or "توضیحات موجود نیست"
    
    result = f"🔧 *{name}*\n\n💰 قیمت: {price}\n\n📝 توضیحات:\n{description}"
    
    # Add media info if available
    if media_files and len(media_files) > 0:
        photo_count = sum(1 for m in media_files if m['file_type'] == 'photo')
        video_count = sum(1 for m in media_files if m['file_type'] == 'video')
        
        media_info = []
        if photo_count > 0:
            media_info.append(f"🖼 {photo_count} تصویر")
        if video_count > 0:
            media_info.append(f"🎬 {video_count} ویدیو")
            
        if media_info:
            result += "\n\n" + " | ".join(media_info)
    
    return result

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
    
    # Get product/service name if available
    is_service = inquiry.get('product_type') == 'service'
    item_prefix = "🔧 خدمت" if is_service else "🛍 محصول"
    item_info = f"\n{item_prefix}: {inquiry['product_name']}" if inquiry.get('product_name') else ""
    
    return (
        f"📝 *استعلام قیمت*\n\n"
        f"👤 نام: {inquiry['name']}\n"
        f"📞 شماره تماس: {inquiry['phone']}\n"
        f"📅 تاریخ: {formatted_date}{item_info}\n\n"
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
    
    # Simplified format - all content is now text-based
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
    from config import CSV_PATH
    
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

async def create_telegraph_page(title: str, content: str, author: str = "RFCatalogbot") -> Optional[str]:
    """
    Create a Telegraph page for longer educational content
    
    Args:
        title: Title of the page
        content: Content of the page (can include simple HTML)
        author: Author name (default: "RFCatalogbot")
        
    Returns:
        URL of the created page, or None if failed
    """
    try:
        # Format content for Telegraph (convert to HTML nodes)
        # Simple conversion for basic formatting - paragraphs
        html_content = []
        for paragraph in content.split('\n\n'):
            if paragraph.strip():
                # Skip empty paragraphs
                html_content.append({
                    'tag': 'p',
                    'children': [paragraph.strip()]
                })
        
        # First create a Telegraph account to get an access token
        create_account_url = 'https://api.telegra.ph/createAccount'
        account_data = {
            'short_name': author,
            'author_name': author
        }
        
        async with aiohttp.ClientSession() as session:
            # Step 1: Create an account and get access token
            async with session.post(create_account_url, data=account_data) as response:
                if response.status == 200:
                    account_result = await response.json()
                    if not account_result.get('ok'):
                        logging.error(f"Telegraph API error creating account: {account_result}")
                        return None
                    
                    access_token = account_result.get('result', {}).get('access_token')
                    if not access_token:
                        logging.error("No access token received from Telegraph API")
                        return None
                    
                    # Step 2: Create the page using the access token
                    create_page_url = 'https://api.telegra.ph/createPage'
                    
                    # Generate a path from title (simple slugify)
                    import re
                    path = re.sub(r'[^\w\s-]', '', title.lower())
                    path = re.sub(r'[\s_-]+', '-', path)
                    
                    # Prepare page creation data
                    page_data = {
                        'access_token': access_token,
                        'title': title,
                        'author_name': author,
                        'content': json.dumps(html_content),
                        'return_content': False
                    }
                    
                    # Create the page
                    async with session.post(create_page_url, data=page_data) as page_response:
                        if page_response.status == 200:
                            page_result = await page_response.json()
                            if page_result.get('ok'):
                                page_url = page_result.get('result', {}).get('url')
                                if page_url:
                                    logging.info(f"Created Telegraph page: {page_url}")
                                    return page_url
                            
                            logging.error(f"Telegraph API error creating page: {page_result}")
                        else:
                            logging.error(f"Telegraph API HTTP error: {page_response.status}")
                else:
                    logging.error(f"Telegraph API HTTP error creating account: {response.status}")
        
        return None
    except Exception as e:
        logging.error(f"Error creating Telegraph page: {str(e)}")
        return None
