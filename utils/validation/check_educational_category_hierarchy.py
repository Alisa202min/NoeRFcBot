#!/usr/bin/env python3
"""
بررسی ساختار سلسله‌مراتبی دسته‌بندی‌های محتوای آموزشی
"""

import logging
from database import Database

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_educational_category_hierarchy():
    """بررسی ساختار سلسله‌مراتبی دسته‌بندی‌های محتوای آموزشی"""
    db = Database()
    
    logging.info("بررسی دسته‌بندی‌های محتوای آموزشی:")
    categories = db.get_educational_categories()
    
    parent_categories = [c for c in categories if c['parent_id'] is None]
    
    logging.info(f"تعداد کل دسته‌بندی‌ها: {len(categories)}")
    logging.info(f"تعداد دسته‌بندی‌های اصلی: {len(parent_categories)}")
    
    print("\n=== دسته‌بندی‌های اصلی ===")
    for category in parent_categories:
        print(f"- {category['name']} (ID: {category['id']}, تعداد محتوا: {category['content_count']}, تعداد زیردسته‌ها: {category['children_count']})")
        
        # Get subcategories
        if category['children_count'] > 0:
            subcategories = db.get_educational_subcategories(category['id'])
            for subcategory in subcategories:
                print(f"  |- {subcategory['name']} (ID: {subcategory['id']}, تعداد محتوا: {subcategory['content_count']})")
    
    print("\n=== محتوای آموزشی با مدیا ===")
    all_contents = db.get_all_educational_content()
    
    contents_with_media = [c for c in all_contents if c['media_count'] > 0]
    logging.info(f"تعداد کل محتوای آموزشی: {len(all_contents)}")
    logging.info(f"تعداد محتوای آموزشی با مدیا: {len(contents_with_media)}")
    
    for content in contents_with_media:
        print(f"- {content['title']} (ID: {content['id']}, دسته‌بندی: {content['category_name'] or content['category']}, تعداد مدیا: {content['media_count']})")
        
        # Get media details
        media_files = db.get_educational_content_media(content['id'])
        for media in media_files:
            print(f"  |- {media['file_type']} (ID: {media['id']}, file_id: {media['file_id'][:20]}...)")

if __name__ == "__main__":
    check_educational_category_hierarchy()