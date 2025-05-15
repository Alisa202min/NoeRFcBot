"""
اسکریپت برای ساخت داده‌های آزمایشی دسته‌بندی‌های محصولات و خدمات
"""
from app import app
from models import ProductCategory, ServiceCategory, EducationalCategory, db

# داده‌های آزمایشی برای دسته‌بندی‌های محصولات
product_categories = [
    # دسته‌بندی‌های اصلی
    {"name": "تجهیزات مخابراتی", "parent_id": None},
    {"name": "تجهیزات شبکه", "parent_id": None},
    {"name": "آنتن‌ها", "parent_id": None},
    {"name": "کابل و کانکتور", "parent_id": None},
    
    # زیردسته‌های تجهیزات مخابراتی
    {"name": "رادیو مخابراتی", "parent_id": 1},
    {"name": "تکرارکننده‌ها", "parent_id": 1},
    {"name": "گیرنده‌های حرفه‌ای", "parent_id": 1},
    
    # زیردسته‌های تجهیزات شبکه
    {"name": "روتر", "parent_id": 2},
    {"name": "سوییچ", "parent_id": 2},
    {"name": "مودم", "parent_id": 2},
    
    # زیردسته‌های آنتن‌ها
    {"name": "آنتن یاگی", "parent_id": 3},
    {"name": "آنتن دیپل", "parent_id": 3},
    {"name": "آنتن پنل", "parent_id": 3},
    {"name": "آنتن بشقابی", "parent_id": 3},
]

# داده‌های آزمایشی برای دسته‌بندی‌های خدمات
service_categories = [
    # دسته‌بندی‌های اصلی
    {"name": "نصب و راه‌اندازی", "parent_id": None},
    {"name": "تعمیرات", "parent_id": None},
    {"name": "مشاوره و طراحی", "parent_id": None},
    {"name": "آموزش", "parent_id": None},
    
    # زیردسته‌های نصب و راه‌اندازی
    {"name": "نصب تجهیزات مخابراتی", "parent_id": 1},
    {"name": "راه‌اندازی شبکه", "parent_id": 1},
    {"name": "نصب آنتن", "parent_id": 1},
    
    # زیردسته‌های تعمیرات
    {"name": "تعمیر رادیو", "parent_id": 2},
    {"name": "تعمیر روتر", "parent_id": 2},
    {"name": "تعمیر آنتن", "parent_id": 2},
    
    # زیردسته‌های مشاوره و طراحی
    {"name": "طراحی شبکه", "parent_id": 3},
    {"name": "بهینه‌سازی سیستم‌های مخابراتی", "parent_id": 3},
]

# داده‌های آزمایشی برای دسته‌بندی‌های محتوای آموزشی
educational_categories = [
    # دسته‌بندی‌های اصلی
    {"name": "اصول مخابرات", "parent_id": None},
    {"name": "شبکه‌های رادیویی", "parent_id": None},
    {"name": "آنتن و انتشار امواج", "parent_id": None},
    
    # زیردسته‌های اصول مخابرات
    {"name": "مدولاسیون‌ها", "parent_id": 1},
    {"name": "فیلترها", "parent_id": 1},
    
    # زیردسته‌های شبکه‌های رادیویی
    {"name": "بی‌سیم‌های دیجیتال", "parent_id": 2},
    {"name": "سیستم‌های مخابراتی", "parent_id": 2},
]

def seed_product_categories():
    """ساخت داده‌های آزمایشی برای جدول دسته‌بندی محصولات"""
    print("در حال ساخت داده‌های آزمایشی برای دسته‌بندی محصولات...")
    
    # حذف تمام داده‌های موجود
    ProductCategory.query.delete()
    
    # ساخت دسته‌بندی‌های جدید
    for cat_data in product_categories:
        cat = ProductCategory(name=cat_data["name"])
        
        # اگر parent_id وجود داشته باشد، آن را بعداً تنظیم می‌کنیم
        # برای جلوگیری از وابستگی به ترتیب ایجاد
        db.session.add(cat)
    
    # ذخیره برای گرفتن ID‌ها
    db.session.commit()
    
    # حالا parent_id را تنظیم می‌کنیم
    cats = ProductCategory.query.all()
    for i, cat_data in enumerate(product_categories):
        if cat_data["parent_id"]:
            parent_index = cat_data["parent_id"] - 1  # شروع از 0 برای فهرست
            cats[i].parent_id = cats[parent_index].id
    
    db.session.commit()
    print(f"{len(cats)} دسته‌بندی محصول با موفقیت اضافه شد.")

def seed_service_categories():
    """ساخت داده‌های آزمایشی برای جدول دسته‌بندی خدمات"""
    print("در حال ساخت داده‌های آزمایشی برای دسته‌بندی خدمات...")
    
    # حذف تمام داده‌های موجود
    ServiceCategory.query.delete()
    
    # ساخت دسته‌بندی‌های جدید
    for cat_data in service_categories:
        cat = ServiceCategory(name=cat_data["name"])
        db.session.add(cat)
    
    # ذخیره برای گرفتن ID‌ها
    db.session.commit()
    
    # حالا parent_id را تنظیم می‌کنیم
    cats = ServiceCategory.query.all()
    for i, cat_data in enumerate(service_categories):
        if cat_data["parent_id"]:
            parent_index = cat_data["parent_id"] - 1  # شروع از 0 برای فهرست
            cats[i].parent_id = cats[parent_index].id
    
    db.session.commit()
    print(f"{len(cats)} دسته‌بندی خدمات با موفقیت اضافه شد.")

def seed_educational_categories():
    """ساخت داده‌های آزمایشی برای جدول دسته‌بندی محتوای آموزشی"""
    print("در حال ساخت داده‌های آزمایشی برای دسته‌بندی محتوای آموزشی...")
    
    # حذف تمام داده‌های موجود
    EducationalCategory.query.delete()
    
    # ساخت دسته‌بندی‌های جدید
    for cat_data in educational_categories:
        cat = EducationalCategory(name=cat_data["name"])
        db.session.add(cat)
    
    # ذخیره برای گرفتن ID‌ها
    db.session.commit()
    
    # حالا parent_id را تنظیم می‌کنیم
    cats = EducationalCategory.query.all()
    for i, cat_data in enumerate(educational_categories):
        if cat_data["parent_id"]:
            parent_index = cat_data["parent_id"] - 1  # شروع از 0 برای فهرست
            cats[i].parent_id = cats[parent_index].id
    
    db.session.commit()
    print(f"{len(cats)} دسته‌بندی محتوای آموزشی با موفقیت اضافه شد.")

if __name__ == "__main__":
    with app.app_context():
        seed_product_categories()
        seed_service_categories()
        seed_educational_categories()