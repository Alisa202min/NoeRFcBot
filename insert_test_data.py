"""
اسکریپت برای ساخت داده‌های آزمایشی در دسته‌بندی‌های محصولات و خدمات
"""
from app import db, app
from models import ProductCategory, ServiceCategory

def create_product_categories():
    """ساخت دسته‌های آزمایشی محصولات"""
    
    # دسته‌های اصلی
    main_categories = [
        "تجهیزات مخابراتی",
        "تجهیزات شبکه",
        "آنتن‌ها",
        "کابل و کانکتور"
    ]
    
    main_cats = {}
    for name in main_categories:
        cat = ProductCategory()
        cat.name = name
        db.session.add(cat)
        db.session.flush()  # گرفتن ID بدون commit
        main_cats[name] = cat
    
    # زیردسته‌های تجهیزات مخابراتی
    telecom_subcategories = [
        "رادیو مخابراتی",
        "تکرارکننده‌ها",
        "گیرنده‌های حرفه‌ای"
    ]
    
    for name in telecom_subcategories:
        cat = ProductCategory()
        cat.name = name
        cat.parent_id = main_cats["تجهیزات مخابراتی"].id
        db.session.add(cat)
    
    # زیردسته‌های تجهیزات شبکه
    network_subcategories = [
        "روتر",
        "سوییچ",
        "مودم"
    ]
    
    for name in network_subcategories:
        cat = ProductCategory()
        cat.name = name
        cat.parent_id = main_cats["تجهیزات شبکه"].id
        db.session.add(cat)
    
    # زیردسته‌های آنتن‌ها
    antenna_subcategories = [
        "آنتن یاگی",
        "آنتن دیپل",
        "آنتن پنل",
        "آنتن بشقابی"
    ]
    
    for name in antenna_subcategories:
        cat = ProductCategory()
        cat.name = name
        cat.parent_id = main_cats["آنتن‌ها"].id
        db.session.add(cat)
    
    db.session.commit()
    print(f"{len(main_categories) + len(telecom_subcategories) + len(network_subcategories) + len(antenna_subcategories)} دسته‌بندی محصول ایجاد شد")

def create_service_categories():
    """ساخت دسته‌های آزمایشی خدمات"""
    
    # دسته‌های اصلی
    main_categories = [
        "نصب و راه‌اندازی",
        "تعمیرات",
        "مشاوره و طراحی",
        "آموزش"
    ]
    
    main_cats = {}
    for name in main_categories:
        cat = ServiceCategory()
        cat.name = name
        db.session.add(cat)
        db.session.flush()  # گرفتن ID بدون commit
        main_cats[name] = cat
    
    # زیردسته‌های نصب و راه‌اندازی
    installation_subcategories = [
        "نصب تجهیزات مخابراتی",
        "راه‌اندازی شبکه",
        "نصب آنتن"
    ]
    
    for name in installation_subcategories:
        cat = ServiceCategory()
        cat.name = name
        cat.parent_id = main_cats["نصب و راه‌اندازی"].id
        db.session.add(cat)
    
    # زیردسته‌های تعمیرات
    repair_subcategories = [
        "تعمیر رادیو",
        "تعمیر روتر",
        "تعمیر آنتن"
    ]
    
    for name in repair_subcategories:
        cat = ServiceCategory()
        cat.name = name
        cat.parent_id = main_cats["تعمیرات"].id
        db.session.add(cat)
    
    # زیردسته‌های مشاوره و طراحی
    consulting_subcategories = [
        "طراحی شبکه",
        "بهینه‌سازی سیستم‌های مخابراتی"
    ]
    
    for name in consulting_subcategories:
        cat = ServiceCategory()
        cat.name = name
        cat.parent_id = main_cats["مشاوره و طراحی"].id
        db.session.add(cat)
    
    db.session.commit()
    print(f"{len(main_categories) + len(installation_subcategories) + len(repair_subcategories) + len(consulting_subcategories)} دسته‌بندی خدمات ایجاد شد")

if __name__ == "__main__":
    with app.app_context():
        # پاک کردن داده‌های موجود
        ProductCategory.query.delete()
        ServiceCategory.query.delete()
        db.session.commit()
        
        # ساخت داده‌های جدید
        create_product_categories()
        create_service_categories()
        
        print("داده‌های آزمایشی با موفقیت ایجاد شدند!")