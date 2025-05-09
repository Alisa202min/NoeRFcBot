import os
import logging
from database import Database
from dotenv import load_dotenv
import random

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def seed_database():
    """Seed the database with test data for products, services, categories and inquiries"""
    logger.info("Starting database seeding...")
    
    # Initialize database
    db = Database()
    
    # Clear existing data
    logger.info("Clearing existing data...")
    clear_tables(db)
    
    # Create categories
    logger.info("Creating categories...")
    product_categories = create_product_categories(db)
    service_categories = create_service_categories(db)
    
    # Create products
    logger.info("Creating products...")
    products = create_products(db, product_categories)
    
    # Create services
    logger.info("Creating services...")
    services = create_services(db, service_categories)
    
    # Create inquiries
    logger.info("Creating inquiries...")
    create_inquiries(db, products, services)
    
    # Create educational content
    logger.info("Creating educational content...")
    create_educational_content(db)
    
    # Create static content
    logger.info("Creating static content...")
    create_static_content(db)
    
    logger.info("Database seeding completed successfully!")

def clear_tables(db):
    """Clear existing data from tables"""
    with db.conn.cursor() as cur:
        # Disable foreign key constraints temporarily
        cur.execute("SET CONSTRAINTS ALL DEFERRED")
        
        # Clear tables in reverse order of dependencies
        cur.execute("DELETE FROM inquiries")
        cur.execute("DELETE FROM product_media")
        cur.execute("DELETE FROM products")
        cur.execute("DELETE FROM categories")
        cur.execute("DELETE FROM educational_content")
        cur.execute("DELETE FROM static_content")
        
        # Re-enable constraints
        cur.execute("SET CONSTRAINTS ALL IMMEDIATE")
        
    db.conn.commit()

def create_product_categories(db):
    """Create product categories with a hierarchical structure"""
    # Main product categories
    main_categories = [
        "تجهیزات اکسس پوینت",   # Access Point Equipment
        "تجهیزات شبکه",         # Network Equipment
        "آنتن‌ها",               # Antennas
        "کابل‌ها و اتصالات"      # Cables and Connectors
    ]
    
    main_category_ids = []
    for name in main_categories:
        cat_id = db.add_category(name=name, cat_type='product')
        main_category_ids.append(cat_id)
        logger.info(f"Created main category: {name} (ID: {cat_id})")
    
    # Subcategories for each main category
    subcategories = {
        0: ["اکسس پوینت داخلی", "اکسس پوینت خارجی", "کنترلر اکسس پوینت"],  # Indoor AP, Outdoor AP, AP Controllers
        1: ["روتر", "سوئیچ", "فایروال", "مودم"],                          # Router, Switch, Firewall, Modem
        2: ["آنتن سکتوری", "آنتن امنی", "آنتن دیش", "آنتن یاگی"],         # Sector, Omni, Dish, Yagi antennas
        3: ["کابل کواکسیال", "فیبر نوری", "کانکتور‌ها", "مبدل‌ها"]        # Coaxial, Fiber, Connectors, Adapters
    }
    
    subcategory_ids = []
    for main_idx, subcat_list in subcategories.items():
        for name in subcat_list:
            cat_id = db.add_category(name=name, parent_id=main_category_ids[main_idx], cat_type='product')
            subcategory_ids.append((cat_id, main_idx))
            logger.info(f"Created subcategory: {name} (ID: {cat_id}, Parent: {main_category_ids[main_idx]})")
    
    # Some 3rd level categories
    third_level_categories = [
        ("اکسس پوینت میکروتیک", 0, 0),  # MikroTik AP (under Indoor AP)
        ("اکسس پوینت یوبیکوییتی", 0, 0), # Ubiquiti AP (under Indoor AP)
        ("اکسس پوینت سیسکو", 0, 0),       # Cisco AP (under Indoor AP)
        ("روتر میکروتیک", 1, 1),         # MikroTik Router (under Router)
        ("روتر سیسکو", 1, 1),              # Cisco Router (under Router)
        ("آنتن سکتوری میکروتیک", 2, 2),   # MikroTik Sector (under Sector antennas)
        ("کابل LMR", 3, 3)                  # LMR Cable (under Coaxial)
    ]
    
    third_level_ids = []
    for name, main_idx, sub_idx in third_level_categories:
        # Find the right subcategory ID
        for sub_id, parent_idx in subcategory_ids:
            if parent_idx == main_idx:
                # This is a subcategory of the right main category
                parent_subcat = db.get_category(sub_id)
                if sub_idx == subcategories[main_idx].index(parent_subcat['name']):
                    # This is the right subcategory
                    cat_id = db.add_category(name=name, parent_id=sub_id, cat_type='product')
                    third_level_ids.append(cat_id)
                    logger.info(f"Created L3 category: {name} (ID: {cat_id}, Parent: {sub_id})")
                    break
    
    return main_category_ids + [id for id, _ in subcategory_ids] + third_level_ids

def create_service_categories(db):
    """Create service categories"""
    main_categories = [
        "نصب و راه‌اندازی",     # Installation and Setup
        "تعمیر و نگهداری",      # Repair and Maintenance
        "طراحی و مشاوره",       # Design and Consultation
        "آموزش"                 # Training
    ]
    
    main_category_ids = []
    for name in main_categories:
        cat_id = db.add_category(name=name, cat_type='service')
        main_category_ids.append(cat_id)
        logger.info(f"Created service category: {name} (ID: {cat_id})")
    
    # Subcategories for services
    subcategories = {
        0: ["نصب شبکه وایرلس", "نصب شبکه کابلی", "راه‌اندازی روتر و فایروال"],  # Wireless, Wired, Router setup
        1: ["سرویس دوره‌ای", "عیب‌یابی و تعمیر", "ارتقای تجهیزات"],               # Periodic, Troubleshooting, Upgrade
        2: ["طراحی شبکه", "مشاوره امنیت", "بهینه‌سازی"],                          # Network design, Security, Optimization
        3: ["دوره میکروتیک", "دوره سیسکو", "آموزش مدیریت شبکه"]                   # MikroTik, Cisco, Management training
    }
    
    subcategory_ids = []
    for main_idx, subcat_list in subcategories.items():
        for name in subcat_list:
            cat_id = db.add_category(name=name, parent_id=main_category_ids[main_idx], cat_type='service')
            subcategory_ids.append(cat_id)
            logger.info(f"Created service subcategory: {name} (ID: {cat_id}, Parent: {main_category_ids[main_idx]})")
    
    return main_category_ids + subcategory_ids

def create_products(db, category_ids):
    """Create sample products in different categories"""
    products = [
        {
            "name": "اکسس پوینت میکروتیک LHG 5",
            "price": 2500000,
            "description": "اکسس پوینت قدرتمند با قابلیت اتصال تا فاصله 20 کیلومتر. دارای آنتن داخلی با گین 24dBi و پشتیبانی از فرکانس 5GHz.",
            "category_id": random.choice(category_ids),
            "brand": "میکروتیک",
            "model": "LHG 5",
            "in_stock": True,
            "tags": "اکسس پوینت,خارجی,میکروتیک,5GHz"
        },
        {
            "name": "روتر میکروتیک RB4011",
            "price": 4800000,
            "description": "روتر قدرتمند و حرفه‌ای با 10 پورت گیگابیت و پردازنده چهار هسته‌ای 1.4GHz. مناسب برای شبکه‌های متوسط و بزرگ.",
            "category_id": random.choice(category_ids),
            "brand": "میکروتیک",
            "model": "RB4011",
            "in_stock": True,
            "tags": "روتر,گیگابیت,میکروتیک,RB"
        },
        {
            "name": "آنتن سکتوری میکروتیک mANT 15s",
            "price": 1800000,
            "description": "آنتن سکتوری با زاویه 120 درجه و گین 15dBi. مناسب برای استفاده در شبکه‌های وایرلس نقطه به چندنقطه.",
            "category_id": random.choice(category_ids),
            "brand": "میکروتیک",
            "model": "mANT 15s",
            "in_stock": True,
            "tags": "آنتن,سکتوری,میکروتیک,5GHz"
        },
        {
            "name": "کابل LMR-400",
            "price": 120000,
            "description": "کابل کواکسیال با کیفیت بالا و افت سیگنال پایین. قیمت برای هر متر.",
            "category_id": random.choice(category_ids),
            "brand": "Times Microwave",
            "model": "LMR-400",
            "in_stock": True,
            "tags": "کابل,کواکسیال,LMR,RF"
        },
        {
            "name": "اکسس پوینت یوبیکوییتی NanoStation loco M5",
            "price": 1900000,
            "description": "اکسس پوینت کامپکت با آنتن داخلی 13dBi و برد موثر تا 5 کیلومتر.",
            "category_id": random.choice(category_ids),
            "brand": "یوبیکوییتی",
            "model": "NanoStation loco M5",
            "in_stock": False,
            "tags": "اکسس پوینت,یوبیکوییتی,5GHz,MIMO"
        },
        {
            "name": "روتر RB750Gr3",
            "price": 1600000,
            "description": "روتر 5 پورت گیگابیت با پردازنده قدرتمند 880MHz. مناسب برای شبکه‌های کوچک و متوسط.",
            "category_id": random.choice(category_ids),
            "brand": "میکروتیک",
            "model": "hEX RB750Gr3",
            "in_stock": True,
            "tags": "روتر,گیگابیت,میکروتیک,hEX"
        },
        {
            "name": "سوئیچ سیسکو WS-C2960L-24PS-LL",
            "price": 7500000,
            "description": "سوئیچ 24 پورت POE با قابلیت‌های لایه 2 پیشرفته. مناسب برای شبکه‌های سازمانی.",
            "category_id": random.choice(category_ids),
            "brand": "سیسکو",
            "model": "WS-C2960L-24PS-LL",
            "in_stock": False,
            "tags": "سوئیچ,POE,سیسکو,لایه2"
        },
        {
            "name": "فایروال سوفوس XG 135",
            "price": 12000000,
            "description": "فایروال نسل جدید با قابلیت‌های حفاظتی پیشرفته و توان پردازشی بالا.",
            "category_id": random.choice(category_ids),
            "brand": "سوفوس",
            "model": "XG 135",
            "in_stock": True,
            "tags": "فایروال,UTM,سوفوس,امنیت"
        },
        {
            "name": "اکسس پوینت سیسکو AIR-CAP1702I",
            "price": 5200000,
            "description": "اکسس پوینت مناسب محیط‌های داخلی با پشتیبانی از استاندارد 802.11ac و قابلیت‌های هوشمند سیسکو.",
            "category_id": random.choice(category_ids),
            "brand": "سیسکو",
            "model": "AIR-CAP1702I",
            "in_stock": True,
            "tags": "اکسس پوینت,داخلی,سیسکو,802.11ac"
        },
        {
            "name": "مودم-روتر TP-Link Archer C6",
            "price": 980000,
            "description": "مودم-روتر دو باند با پشتیبانی از استاندارد 802.11ac و 4 پورت گیگابیت. مناسب برای مصارف خانگی.",
            "category_id": random.choice(category_ids),
            "brand": "TP-Link",
            "model": "Archer C6",
            "in_stock": True,
            "tags": "مودم,روتر,TP-Link,وای‌فای"
        }
    ]
    
    product_ids = []
    for product in products:
        product_id = db.add_product(
            name=product["name"],
            price=product["price"],
            description=product["description"],
            category_id=product["category_id"],
            brand=product.get("brand", ""),
            model=product.get("model", ""),
            in_stock=product.get("in_stock", True),
            tags=product.get("tags", "")
        )
        product_ids.append(product_id)
        logger.info(f"Created product: {product['name']} (ID: {product_id})")
    
    return product_ids

def create_services(db, category_ids):
    """Create sample services in different categories"""
    services = [
        {
            "name": "نصب و راه‌اندازی اکسس پوینت",
            "price": 2000000,
            "description": "نصب و راه‌اندازی اکسس پوینت‌های میکروتیک، یوبیکوییتی و سیسکو با تنظیمات سفارشی. شامل تست سیگنال و بهینه‌سازی اولیه.",
            "category_id": random.choice(category_ids),
            "featured": True,
            "tags": "نصب,اکسس پوینت,راه‌اندازی,وایرلس"
        },
        {
            "name": "طراحی شبکه بی‌سیم",
            "price": 5000000,
            "description": "طراحی شبکه بی‌سیم با ظرفیت بالا و پوشش مناسب. شامل نقشه‌برداری RF، شبیه‌سازی انتشار و تعیین نقاط نصب تجهیزات.",
            "category_id": random.choice(category_ids),
            "featured": True,
            "tags": "طراحی,بی‌سیم,نقشه‌برداری,RF"
        },
        {
            "name": "راه‌اندازی روتر میکروتیک",
            "price": 1500000,
            "description": "نصب و پیکربندی روترهای میکروتیک شامل تنظیمات امنیتی، روتینگ، فایروال و مدیریت پهنای باند.",
            "category_id": random.choice(category_ids),
            "featured": False,
            "tags": "میکروتیک,روتر,پیکربندی,فایروال"
        },
        {
            "name": "نصب و راه‌اندازی WAN لینک",
            "price": 4000000,
            "description": "نصب و راه‌اندازی لینک‌های ارتباطی نقطه به نقطه با برد بالا. شامل تنظیم آنتن، فرکانس و پارامترهای ارتباطی.",
            "category_id": random.choice(category_ids),
            "featured": False,
            "tags": "WAN,لینک,نقطه به نقطه,وایرلس"
        },
        {
            "name": "دوره آموزشی MTCNA",
            "price": 8000000,
            "description": "دوره آموزشی رسمی MTCNA (MikroTik Certified Network Associate) به مدت 5 روز. شامل مباحث پایه روتینگ، سوئیچینگ و وایرلس.",
            "category_id": random.choice(category_ids),
            "featured": True,
            "tags": "آموزش,میکروتیک,MTCNA,دوره"
        },
        {
            "name": "عیب‌یابی و رفع مشکلات شبکه",
            "price": 2500000,
            "description": "عیب‌یابی و رفع مشکلات شبکه‌های کامپیوتری شامل مشکلات سخت‌افزاری و نرم‌افزاری. هزینه برای هر روز کاری.",
            "category_id": random.choice(category_ids),
            "featured": False,
            "tags": "عیب‌یابی,رفع مشکل,سخت‌افزار,نرم‌افزار"
        },
        {
            "name": "پیاده‌سازی VLAN و روتینگ لایه 3",
            "price": 3500000,
            "description": "طراحی و پیاده‌سازی شبکه‌های مبتنی بر VLAN و روتینگ لایه 3 برای محیط‌های سازمانی. شامل پیکربندی سوئیچ‌ها و روترها.",
            "category_id": random.choice(category_ids),
            "featured": False,
            "tags": "VLAN,لایه 3,روتینگ,سوئیچ"
        },
        {
            "name": "مشاوره امنیت شبکه",
            "price": 4000000,
            "description": "ارائه مشاوره تخصصی در زمینه امنیت شبکه‌های کامپیوتری. شامل تست نفوذ، شناسایی آسیب‌پذیری‌ها و ارائه راهکارهای امنیتی.",
            "category_id": random.choice(category_ids),
            "featured": True,
            "tags": "امنیت,مشاوره,تست نفوذ,آسیب‌پذیری"
        },
        {
            "name": "طراحی و پیاده‌سازی شبکه MPLS",
            "price": 12000000,
            "description": "طراحی و پیاده‌سازی شبکه‌های مبتنی بر MPLS برای سازمان‌های بزرگ. شامل پیکربندی BGP، OSPF و پروتکل‌های مرتبط.",
            "category_id": random.choice(category_ids),
            "featured": False,
            "tags": "MPLS,BGP,OSPF,شبکه گسترده"
        },
        {
            "name": "نصب و راه‌اندازی فیبر نوری",
            "price": 6000000,
            "description": "نصب، فیوژن و راه‌اندازی مسیرهای ارتباطی فیبر نوری. شامل تست و عیب‌یابی OTDR و تجهیزات اکتیو.",
            "category_id": random.choice(category_ids),
            "featured": False,
            "tags": "فیبر نوری,فیوژن,OTDR,نصب"
        }
    ]
    
    service_ids = []
    for service in services:
        service_id = db.add_service(
            name=service["name"],
            price=service["price"],
            description=service["description"],
            category_id=service["category_id"],
            featured=service.get("featured", False),
            tags=service.get("tags", "")
        )
        service_ids.append(service_id)
        logger.info(f"Created service: {service['name']} (ID: {service_id})")
    
    return service_ids

def create_inquiries(db, product_ids, service_ids):
    """Create sample inquiries for products and services"""
    names = ["محمد علیزاده", "سارا محمدی", "علی رضایی", "پریسا کریمی", "حسین فتحی"]
    phone_numbers = ["+989123456789", "+989121234567", "+989351112233", "+989361234567", "+989372225566"]
    descriptions = [
        "لطفا در مورد قیمت و موجودی تماس بگیرید",
        "آیا امکان ارسال به شهرستان وجود دارد؟",
        "لطفا در مورد گارانتی و خدمات پس از فروش اطلاع رسانی کنید",
        "آیا امکان خرید اقساطی وجود دارد؟",
        "لطفا درباره نحوه نصب و راه‌اندازی توضیح دهید"
    ]
    
    # Product inquiries
    for _ in range(5):
        if not product_ids:
            continue  # Skip if no products are available
        
        product_id = random.choice(product_ids)
        name = random.choice(names)
        phone = random.choice(phone_numbers)
        description = random.choice(descriptions)
        
        inquiry_id = db.add_inquiry(
            user_id=random.randint(100000, 999999),
            name=name,
            phone=phone,
            description=description,
            product_id=product_id
        )
        logger.info(f"Created product inquiry: ID {inquiry_id} for product {product_id}")
    
    # Service inquiries
    for _ in range(5):
        if not service_ids:
            continue  # Skip if no services are available
        
        service_id = random.choice(service_ids)
        name = random.choice(names)
        phone = random.choice(phone_numbers)
        description = random.choice(descriptions)
        
        inquiry_id = db.add_inquiry(
            user_id=random.randint(100000, 999999),
            name=name,
            phone=phone,
            description=description,
            service_id=service_id
        )
        logger.info(f"Created service inquiry: ID {inquiry_id} for service {service_id}")

def create_educational_content(db):
    """Create sample educational content"""
    articles = [
        {
            "title": "راهنمای انتخاب آنتن مناسب برای لینک‌های وایرلس",
            "content": """
            # راهنمای انتخاب آنتن مناسب برای لینک‌های وایرلس

            در این مقاله به بررسی انواع آنتن‌های مناسب برای لینک‌های وایرلس و کاربردهای هر یک می‌پردازیم.

            ## آنتن‌های جهت‌دار (Directional)
            
            آنتن‌های جهت‌دار، سیگنال را در یک جهت خاص متمرکز می‌کنند و برای ایجاد لینک‌های نقطه به نقطه ایده‌آل هستند.
            
            ### آنتن‌های دیش (Dish)
            
            - گین بالا (معمولاً 22dBi تا 30dBi)
            - مناسب برای لینک‌های با فاصله زیاد (10 تا 50 کیلومتر)
            - حساس به تنظیمات دقیق
            
            ### آنتن‌های یاگی (Yagi)
            
            - گین متوسط (12dBi تا 18dBi)
            - مناسب برای فواصل متوسط
            - نصب و تنظیم آسان‌تر نسبت به آنتن‌های دیش
            
            ## آنتن‌های همه‌جهته (Omnidirectional)
            
            آنتن‌های همه‌جهته، سیگنال را در تمام جهات منتشر می‌کنند و برای پوشش 360 درجه مناسب هستند.
            
            - گین پایین تا متوسط (5dBi تا 12dBi)
            - مناسب برای پوشش نقطه به چندنقطه
            - نصب آسان
            
            ## آنتن‌های سکتوری (Sector)
            
            آنتن‌های سکتوری، سیگنال را در یک بخش مشخص از فضا (معمولاً 60، 90 یا 120 درجه) منتشر می‌کنند.
            
            - گین متوسط تا بالا (14dBi تا 20dBi)
            - مناسب برای پوشش بخشی از فضا
            - کاربرد در ایستگاه‌های پایه
            
            ## فاکتورهای مهم در انتخاب آنتن
            
            1. **فرکانس کاری**: آنتن باید با فرکانس کاری تجهیزات شما (2.4GHz یا 5GHz) سازگار باشد.
            2. **فاصله ارتباطی**: برای فواصل بیشتر، آنتن با گین بالاتر نیاز است.
            3. **الگوی پوشش**: بسته به نیاز شما به پوشش نقطه به نقطه یا چندنقطه، نوع آنتن متفاوت است.
            4. **شرایط محیطی**: برای محیط‌های بیرونی، آنتن باید مقاوم در برابر شرایط جوی باشد.
            5. **محدودیت‌های نصب**: فضای موجود و امکانات نصب در انتخاب نوع و سایز آنتن تأثیرگذار است.
            
            با توجه به این موارد می‌توانید آنتن مناسب برای لینک وایرلس خود را انتخاب کنید.
            """,
            "category": "آموزش وایرلس",
            "content_type": "article"
        },
        {
            "title": "اصول اولیه پیکربندی روترهای میکروتیک",
            "content": """
            # اصول اولیه پیکربندی روترهای میکروتیک

            ## مقدمه
            
            میکروتیک یکی از تولیدکنندگان مطرح تجهیزات شبکه است که روترهای قدرتمندی با قابلیت‌های پیشرفته و قیمت مناسب ارائه می‌کند. در این مقاله، با اصول اولیه پیکربندی روترهای میکروتیک آشنا می‌شویم.
            
            ## روش‌های دسترسی به روتر میکروتیک
            
            برای پیکربندی روترهای میکروتیک می‌توانید از روش‌های زیر استفاده کنید:
            
            1. **WinBox**: ابزار گرافیکی ویندوزی برای مدیریت روتر
            2. **WebFig**: رابط کاربری تحت وب
            3. **SSH**: دسترسی خط فرمان از راه دور
            4. **Console**: اتصال مستقیم از طریق پورت کنسول
            
            ## تنظیمات اولیه روتر
            
            ### 1. تنظیم نام دستگاه
            
            ```
            /system identity set name=MikroTik-Office
            ```
            
            ### 2. تنظیم آدرس IP برای اینترفیس
            
            ```
            /ip address add address=192.168.1.1/24 interface=ether1
            ```
            
            ### 3. تنظیم DNS
            
            ```
            /ip dns set servers=8.8.8.8,8.8.4.4
            ```
            
            ### 4. تنظیم Default Gateway
            
            ```
            /ip route add dst-address=0.0.0.0/0 gateway=192.168.1.254
            ```
            
            ### 5. تنظیم DHCP Server
            
            ```
            /ip pool add name=dhcp-pool ranges=192.168.1.100-192.168.1.200
            /ip dhcp-server network add address=192.168.1.0/24 gateway=192.168.1.1 dns-server=192.168.1.1
            /ip dhcp-server add name=dhcp1 interface=ether2 address-pool=dhcp-pool disabled=no
            ```
            
            ### 6. تنظیم NAT
            
            ```
            /ip firewall nat add chain=srcnat out-interface=ether1 action=masquerade
            ```
            
            ## تنظیمات امنیتی پایه
            
            ### 1. تغییر رمز عبور پیش‌فرض
            
            ```
            /user set admin password=NewStrongPassword
            ```
            
            ### 2. محدود کردن دسترسی‌های مدیریتی
            
            ```
            /ip service set www disabled=yes
            /ip service set telnet disabled=yes
            /ip service set ftp disabled=yes
            /ip service set ssh address=192.168.1.0/24
            /ip service set winbox address=192.168.1.0/24
            ```
            
            ### 3. فایروال پایه
            
            ```
            # مجوز ترافیک شبکه‌های داخلی
            /ip firewall filter add chain=forward action=accept connection-state=established,related
            /ip firewall filter add chain=forward action=drop connection-state=invalid
            
            # مسدود کردن ترافیک ناشناس از اینترنت
            /ip firewall filter add chain=forward action=drop connection-state=new connection-nat-state=!dstnat in-interface=ether1
            ```
            
            ## نتیجه‌گیری
            
            با رعایت اصول اولیه پیکربندی روترهای میکروتیک، می‌توانید یک شبکه امن و کارآمد ایجاد کنید. با افزایش آشنایی با قابلیت‌های RouterOS، می‌توانید تنظیمات پیشرفته‌تری مانند QoS، VPN، و روتینگ پیشرفته را نیز پیاده‌سازی کنید.
            """,
            "category": "آموزش میکروتیک",
            "content_type": "article"
        },
        {
            "title": "مقایسه پروتکل‌های روتینگ در شبکه‌های سازمانی",
            "content": """
            # مقایسه پروتکل‌های روتینگ در شبکه‌های سازمانی

            ## مقدمه
            
            پروتکل‌های روتینگ، ابزارهایی هستند که روترها برای تبادل اطلاعات مسیریابی و انتخاب بهترین مسیر برای ارسال بسته‌های داده استفاده می‌کنند. در این مقاله، پروتکل‌های روتینگ رایج در شبکه‌های سازمانی را مقایسه می‌کنیم.
            
            ## انواع پروتکل‌های روتینگ
            
            پروتکل‌های روتینگ به دو دسته کلی تقسیم می‌شوند:
            
            1. **پروتکل‌های درون‌سازمانی (IGP)**: برای روتینگ درون یک سیستم خودمختار (AS) استفاده می‌شوند.
               - OSPF
               - EIGRP
               - RIP
               - IS-IS
            
            2. **پروتکل‌های بیرون‌سازمانی (EGP)**: برای روتینگ بین سیستم‌های خودمختار استفاده می‌شوند.
               - BGP
            
            ## مقایسه پروتکل‌های IGP
            
            ### RIP (Routing Information Protocol)
            
            **مزایا:**
            - پیاده‌سازی ساده
            - سازگاری با اکثر روترها
            
            **معایب:**
            - محدودیت حداکثر 15 هاپ
            - همگرایی کند
            - ترافیک بالای شبکه به دلیل آپدیت‌های دوره‌ای
            
            **مناسب برای:**
            - شبکه‌های کوچک با توپولوژی ساده
            
            ### OSPF (Open Shortest Path First)
            
            **مزایا:**
            - الگوریتم مسیریابی Link-State
            - همگرایی سریع
            - پشتیبانی از VLSM و CIDR
            - استاندارد باز و پشتیبانی از اکثر تجهیزات
            
            **معایب:**
            - پیچیدگی بیشتر در پیکربندی و عیب‌یابی
            - مصرف منابع CPU و حافظه بیشتر
            
            **مناسب برای:**
            - شبکه‌های متوسط و بزرگ
            - محیط‌های چند‌فروشنده
            
            ### EIGRP (Enhanced Interior Gateway Routing Protocol)
            
            **مزایا:**
            - ترکیبی از مزایای پروتکل‌های Distance Vector و Link State
            - همگرایی سریع
            - مصرف پهنای باند کمتر
            - پشتیبانی از توزیع بار نامتقارن
            
            **معایب:**
            - انحصاری سیسکو (تا قبل از 2013)
            - محدودیت در محیط‌های چند‌فروشنده
            
            **مناسب برای:**
            - شبکه‌های با تجهیزات سیسکو
            - توپولوژی‌های پیچیده با نیاز به همگرایی سریع
            
            ### IS-IS (Intermediate System to Intermediate System)
            
            **مزایا:**
            - مقیاس‌پذیری بالا
            - مناسب برای شبکه‌های بسیار بزرگ
            - مصرف منابع کمتر نسبت به OSPF
            
            **معایب:**
            - پیچیدگی بیشتر در پیکربندی
            - آشنایی کمتر مدیران شبکه با آن
            
            **مناسب برای:**
            - شبکه‌های مخابراتی و ISP‌ها
            - شبکه‌های بسیار بزرگ
            
            ## BGP (Border Gateway Protocol)
            
            **مزایا:**
            - تنها پروتکل روتینگ اینترنت
            - قابلیت‌های کنترل مسیر پیشرفته
            - مقیاس‌پذیری بی‌نظیر
            
            **معایب:**
            - پیچیدگی بالا در پیکربندی و عیب‌یابی
            - همگرایی کندتر
            
            **مناسب برای:**
            - اتصال به چندین ISP
            - شبکه‌های با نیاز به کنترل دقیق ترافیک ورودی/خروجی
            
            ## معیارهای انتخاب پروتکل روتینگ
            
            1. **اندازه شبکه**: شبکه‌های کوچک می‌توانند از RIP یا OSPF ساده استفاده کنند، در حالی که شبکه‌های بزرگ‌تر به OSPF، EIGRP یا IS-IS نیاز دارند.
            
            2. **زمان همگرایی**: اگر در شبکه شما قطعی مسیر اهمیت بالایی دارد، پروتکل‌هایی با همگرایی سریع مانند OSPF یا EIGRP مناسب‌تر هستند.
            
            3. **منابع روتر**: روترهای با منابع محدود ممکن است با پروتکل‌های سبک‌تر مانند RIP بهتر کار کنند.
            
            4. **تخصص تیم فنی**: میزان آشنایی تیم فنی با پروتکل‌های مختلف در انتخاب پروتکل مناسب تأثیرگذار است.
            
            5. **یکپارچگی تجهیزات**: اگر شبکه شما از تجهیزات چندین فروشنده تشکیل شده، استفاده از پروتکل‌های استاندارد مانند OSPF یا BGP مناسب‌تر است.
            
            ## نتیجه‌گیری
            
            انتخاب پروتکل روتینگ مناسب، تأثیر زیادی بر عملکرد، قابلیت اطمینان و مدیریت شبکه شما دارد. با بررسی دقیق نیازها و محدودیت‌های شبکه‌تان، می‌توانید بهترین پروتکل یا ترکیبی از پروتکل‌ها را انتخاب کنید.
            """,
            "category": "مفاهیم شبکه",
            "content_type": "article"
        },
        {
            "title": "نحوه انتخاب تجهیزات شبکه مناسب برای سازمان‌های کوچک و متوسط",
            "content": """
            # نحوه انتخاب تجهیزات شبکه مناسب برای سازمان‌های کوچک و متوسط
            
            ## مقدمه
            
            انتخاب تجهیزات شبکه مناسب برای سازمان‌های کوچک و متوسط (SMB) یک چالش مهم است. از یک طرف باید از اتلاف هزینه با خرید تجهیزات پیشرفته‌تر از نیاز جلوگیری کرد و از طرف دیگر، باید تجهیزاتی انتخاب شوند که قابلیت توسعه در آینده را داشته باشند. در این راهنما، به بررسی نکات کلیدی در انتخاب تجهیزات شبکه برای SMBها می‌پردازیم.
            
            ## روترها
            
            ### نکات کلیدی در انتخاب روتر
            
            1. **ظرفیت پهنای باند**: روتر باید توانایی مدیریت پهنای باند اینترنت فعلی و آینده شما را داشته باشد.
            
            2. **تعداد کاربران همزمان**: برای سازمان‌های کوچک با کمتر از 20 کاربر، روترهای SOHO کافی هستند. برای 20-50 کاربر، روترهای SMB و برای بیش از 50 کاربر، روترهای سازمانی مناسب‌ترند.
            
            3. **قابلیت‌های امنیتی**: فایروال، VPN، فیلترینگ محتوا، و سیستم تشخیص و جلوگیری از نفوذ (IDS/IPS) از قابلیت‌های مهم هستند.
            
            4. **پورت‌های WAN**: آیا نیاز به اتصال به چندین ISP دارید؟
            
            ### توصیه‌ها
            
            - **سازمان‌های کوچک (کمتر از 20 کاربر)**:
              - میکروتیک hEX یا RB750Gr3
              - TP-Link ER605
              
            - **سازمان‌های متوسط (20-50 کاربر)**:
              - میکروتیک RB4011
              - فورتینت FortiGate 40F
              
            - **سازمان‌های بزرگ‌تر (50+ کاربر)**:
              - میکروتیک CCR1009
              - سیسکو ISR 1100 Series
              - فورتینت FortiGate 60F
            
            ## سوئیچ‌ها
            
            ### نکات کلیدی در انتخاب سوئیچ
            
            1. **تعداد پورت‌ها**: تعداد دستگاه‌های متصل فعلی و پیش‌بینی رشد آینده
            
            2. **سرعت پورت‌ها**: 1Gbps برای اکثر کاربردها کافی است، اما پورت‌های 10Gbps برای سرورها و نقاط تجمع مفید هستند.
            
            3. **پشتیبانی از PoE**: برای تغذیه دستگاه‌هایی مانند تلفن‌های IP، دوربین‌های نظارتی و اکسس پوینت‌ها
            
            4. **مدیریت‌پذیری**: سوئیچ‌های مدیریتی امکان پیکربندی VLAN، QoS و مانیتورینگ را فراهم می‌کنند.
            
            ### توصیه‌ها
            
            - **سوئیچ‌های غیرمدیریتی برای شبکه‌های ساده**:
              - TP-Link TL-SG1024
              - نت‌گیر GS324
              
            - **سوئیچ‌های مدیریتی L2 برای اکثر SMBها**:
              - میکروتیک CSS326
              - TP-Link TL-SG3428
              - یوبیکوییتی UniFi Switch USW-24-POE
              
            - **سوئیچ‌های L3 برای محیط‌های پیچیده‌تر**:
              - میکروتیک CRS328
              - سیسکو SG350X-24
              
            ## تجهیزات شبکه بی‌سیم
            
            ### نکات کلیدی در انتخاب تجهیزات بی‌سیم
            
            1. **استانداردهای Wi-Fi**: Wi-Fi 6 (802.11ax) برای محیط‌های با تراکم کاربر بالا مناسب است.
            
            2. **پوشش**: تعداد و جانمایی اکسس پوینت‌ها برای پوشش مناسب فضا
            
            3. **ظرفیت**: تعداد کاربران همزمان تحت پوشش هر اکسس پوینت
            
            4. **مدیریت مرکزی**: سیستم‌های کنترلر-محور برای شبکه‌های با چندین اکسس پوینت
            
            ### توصیه‌ها
            
            - **محیط‌های کوچک (یک یا دو AP)**:
              - یوبیکوییتی UniFi U6-Lite
              - TP-Link EAP245
              
            - **محیط‌های متوسط (چندین AP)**:
              - سیستم یوبیکوییتی UniFi با کنترلر
              - TP-Link Omada با کنترلر
              - انجنیوس EnGenius Cloud با مدیریت ابری
              
            - **محیط‌های بزرگ با نیازهای امنیتی بالا**:
              - اکسس پوینت‌های سیسکو با کنترلر
              - اکسس پوینت‌های آروبا با کنترلر
            
            ## راهکارهای یکپارچه
            
            گاهی استفاده از اکوسیستم یکپارچه یک تولیدکننده، مدیریت شبکه را ساده‌تر می‌کند. برخی از بهترین اکوسیستم‌ها برای SMBها:
            
            1. **یوبیکوییتی UniFi**: روتر، سوئیچ، اکسس پوینت و دوربین‌های نظارتی با مدیریت یکپارچه
            
            2. **میکروتیک**: راهکارهای کامل شبکه با کیفیت بالا و قیمت مناسب
            
            3. **TP-Link Omada**: راهکار مقرون به صرفه برای شبکه‌های کوچک و متوسط
            
            ## استراتژی خرید
            
            1. **خرید تدریجی**: به‌جای خرید همه تجهیزات یکباره، با توجه به اولویت‌ها خرید کنید و تدریجاً توسعه دهید.
            
            2. **آینده‌نگری**: تجهیزاتی انتخاب کنید که حداقل 3-5 سال نیازهای شما را پوشش دهند.
            
            3. **توازن قیمت و کیفیت**: همیشه گران‌ترین گزینه بهترین نیست. به دنبال تعادل بین قیمت، کیفیت و قابلیت‌ها باشید.
            
            4. **گارانتی و پشتیبانی**: برای تجهیزات کلیدی شبکه، گارانتی و پشتیبانی مناسب را در نظر بگیرید.
            
            ## نتیجه‌گیری
            
            انتخاب تجهیزات شبکه مناسب، تأثیر مستقیمی بر بهره‌وری، امنیت و هزینه‌های سازمان شما دارد. با ارزیابی دقیق نیازها، بودجه و برنامه‌های آینده‌تان، می‌توانید تصمیم‌گیری آگاهانه‌ای داشته باشید. همچنین، مشاوره با یک متخصص شبکه می‌تواند در انتخاب بهترین راهکار برای کسب‌وکار شما کمک زیادی کند.
            """,
            "category": "راهنمای خرید",
            "content_type": "article"
        },
        {
            "title": "مفاهیم پایه شبکه",
            "content": """
            # مفاهیم پایه شبکه

            ## اصطلاحات پایه
            
            ### LAN (شبکه محلی)
            شبکه‌ای که در یک محدوده جغرافیایی کوچک مانند یک ساختمان یا مجموعه ساختمان‌ها قرار دارد.
            
            ### WAN (شبکه گسترده)
            شبکه‌ای که محدوده جغرافیایی بزرگی را پوشش می‌دهد و معمولاً چندین LAN را به هم متصل می‌کند.
            
            ### IP Address (آدرس آی‌پی)
            شناسه منحصر به فردی که به هر دستگاه در شبکه اختصاص داده می‌شود. آدرس‌های IPv4 به صورت چهار عدد بین 0 تا 255 نمایش داده می‌شوند که با نقطه از هم جدا شده‌اند (مثل 192.168.1.1).
            
            ### Subnet Mask (ماسک شبکه)
            عددی که مشخص می‌کند کدام بخش از آدرس IP به شناسه شبکه و کدام بخش به شناسه میزبان اختصاص دارد.
            
            ### Default Gateway (دروازه پیش‌فرض)
            آدرس IP روتری که ترافیک شبکه را به شبکه‌های دیگر (معمولاً اینترنت) هدایت می‌کند.
            
            ### DNS (سیستم نام دامنه)
            سیستمی که نام‌های دامنه (مثل google.com) را به آدرس‌های IP ترجمه می‌کند.
            
            ### DHCP (پروتکل پیکربندی میزبان پویا)
            پروتکلی که به صورت خودکار آدرس IP، ماسک شبکه، دروازه پیش‌فرض و سرور DNS را به دستگاه‌های شبکه اختصاص می‌دهد.
            
            ## تجهیزات شبکه
            
            ### Router (روتر)
            دستگاهی که ترافیک را بین شبکه‌های مختلف (مثلاً LAN و WAN) مسیریابی می‌کند. روترها در لایه 3 مدل OSI (لایه شبکه) کار می‌کنند.
            
            ### Switch (سوییچ)
            دستگاهی که چندین دستگاه را در یک شبکه محلی به هم متصل می‌کند. سوییچ‌ها در لایه 2 مدل OSI (لایه پیوند داده) کار می‌کنند و بر اساس آدرس MAC تصمیم‌گیری می‌کنند.
            
            ### Access Point (نقطه دسترسی)
            دستگاهی که امکان اتصال بی‌سیم به شبکه را فراهم می‌کند و به عنوان پل بین دستگاه‌های بی‌سیم و شبکه سیمی عمل می‌کند.
            
            ### Firewall (فایروال)
            سیستمی که ترافیک ورودی و خروجی شبکه را بر اساس قوانین امنیتی کنترل می‌کند.
            
            ### Modem (مودم)
            دستگاهی که سیگنال‌های دیجیتال کامپیوتر را به سیگنال‌های آنالوگ قابل انتقال از طریق خطوط تلفن یا کابل تبدیل می‌کند و بالعکس.
            
            ## پروتکل‌های شبکه
            
            ### TCP/IP (پروتکل کنترل انتقال/پروتکل اینترنت)
            مجموعه‌ای از پروتکل‌های ارتباطی که اساس اینترنت و اکثر شبکه‌های کامپیوتری امروزی را تشکیل می‌دهند.
            
            ### HTTP (پروتکل انتقال ابرمتن)
            پروتکلی که برای انتقال داده در وب استفاده می‌شود. HTTPS نسخه امن آن است که از رمزگذاری استفاده می‌کند.
            
            ### FTP (پروتکل انتقال فایل)
            پروتکلی برای انتقال فایل بین کامپیوترها در شبکه.
            
            ### SMTP (پروتکل انتقال ساده پست الکترونیکی)
            پروتکلی برای ارسال ایمیل.
            
            ### POP3 و IMAP
            پروتکل‌هایی برای دریافت ایمیل از سرور.
            
            ## مفاهیم امنیتی شبکه
            
            ### VPN (شبکه خصوصی مجازی)
            فناوری‌ای که امکان ایجاد یک اتصال امن و رمزگذاری شده از طریق یک شبکه عمومی مانند اینترنت را فراهم می‌کند.
            
            ### NAT (ترجمه آدرس شبکه)
            فرآیندی که در آن یک روتر آدرس‌های IP داخلی را به یک یا چند آدرس IP عمومی ترجمه می‌کند.
            
            ### Firewall (فایروال)
            سیستم امنیتی که ترافیک شبکه را بر اساس قوانین از پیش تعیین شده کنترل می‌کند.
            
            ### IDS/IPS (سیستم تشخیص/جلوگیری از نفوذ)
            سیستم‌هایی که فعالیت‌های مشکوک در شبکه را شناسایی و/یا از آن‌ها جلوگیری می‌کنند.
            
            ## توپولوژی‌های شبکه
            
            ### Star (ستاره‌ای)
            توپولوژی‌ای که در آن همه دستگاه‌ها به یک نقطه مرکزی (معمولاً یک سوییچ) متصل می‌شوند.
            
            ### Bus (باس)
            توپولوژی‌ای که در آن همه دستگاه‌ها به یک کابل اصلی متصل می‌شوند.
            
            ### Ring (حلقوی)
            توپولوژی‌ای که در آن هر دستگاه به دو دستگاه دیگر متصل است و یک حلقه بسته تشکیل می‌دهد.
            
            ### Mesh (مش)
            توپولوژی‌ای که در آن هر دستگاه می‌تواند به چندین دستگاه دیگر متصل شود، که منجر به افزونگی و قابلیت اطمینان بالا می‌شود.
            
            ## نتیجه‌گیری
            
            درک مفاهیم پایه شبکه برای هر کسی که با کامپیوتر و اینترنت کار می‌کند، مفید است. این دانش به شما کمک می‌کند تا مشکلات شبکه را بهتر درک و عیب‌یابی کنید و تصمیمات آگاهانه‌تری در مورد نیازهای شبکه خود بگیرید.
            """,
            "category": "مفاهیم شبکه",
            "content_type": "guide"
        }
    ]
    
    for article in articles:
        content_id = db.add_educational_content(
            title=article["title"],
            content=article["content"],
            category=article["category"],
            content_type=article["content_type"]
        )
        logger.info(f"Created educational content: {article['title']} (ID: {content_id})")

def create_static_content(db):
    """Create static content for about and contact pages"""
    # Contact content
    contact_content = """
    <h2>تماس با ما</h2>
    <p>با ما از طریق شماره 1234567890+ یا ایمیل info@example.com در تماس باشید.</p>
    <h3>آدرس</h3>
    <p>تهران، خیابان ولیعصر، ساختمان ارتباطات، طبقه 3</p>
    <h3>ساعات کاری</h3>
    <p>شنبه تا چهارشنبه: 9 صبح تا 5 عصر<br>پنجشنبه: 9 صبح تا 12 ظهر</p>
    """
    
    db.update_static_content('contact', contact_content)
    logger.info("Created contact static content")
    
    # About content
    about_content = """
    <h2>درباره ما</h2>
    <p>ما یک شرکت فعال در زمینه تجهیزات الکترونیکی هستیم.</p>
    <p>با بیش از 10 سال سابقه در زمینه فروش و خدمات مرتبط با تجهیزات ارتباطی و شبکه، همواره کوشیده‌ایم بهترین محصولات و خدمات را به مشتریان ارائه دهیم.</p>
    <h3>چشم‌انداز ما</h3>
    <p>تبدیل شدن به معتبرترین مرجع تأمین تجهیزات ارتباطی و ارائه خدمات فنی-مهندسی در صنعت ICT کشور</p>
    <h3>مأموریت ما</h3>
    <p>ارائه راهکارهای جامع و یکپارچه ارتباطی با بهره‌گیری از فناوری‌های روز دنیا و نیروی متخصص، به منظور پاسخگویی به نیازهای مشتریان در کمترین زمان و بالاترین کیفیت</p>
    """
    
    db.update_static_content('about', about_content)
    logger.info("Created about static content")

if __name__ == "__main__":
    seed_database()