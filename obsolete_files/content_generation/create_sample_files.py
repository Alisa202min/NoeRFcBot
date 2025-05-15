import os
import sys
import random
import shutil
import time
from PIL import Image, ImageDraw, ImageFont, ImageColor
import io

def create_sample_directory():
    """Create sample directories for uploads"""
    # Create uploads directory
    uploads_path = os.path.join('static', 'uploads')
    os.makedirs(uploads_path, exist_ok=True)
    print(f"Created directory: {uploads_path}")

def create_sample_image(filename, text, width=800, height=600, background_color=None):
    """Create a sample image with specified text"""
    # Define colors
    colors = ["#1E88E5", "#E53935", "#43A047", "#FDD835", "#5E35B1", "#FB8C00"]
    
    # Use provided color or pick a random one
    if background_color is None:
        background_color = random.choice(colors)
    
    # Create a new image with specified background color
    img = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(img)
    
    # Add a white rectangle in the center
    rect_width = width * 0.8
    rect_height = height * 0.6
    rect_x = (width - rect_width) / 2
    rect_y = (height - rect_height) / 2
    draw.rectangle(
        [(rect_x, rect_y), (rect_x + rect_width, rect_y + rect_height)],
        fill="white"
    )
    
    # Add text
    # Since we might not have fonts installed, use default
    # Calculate font size based on image dimensions
    font_size = int(min(width, height) / 20)
    
    # Position text in the center of the white rectangle
    text_x = width // 2
    text_y = height // 2 - font_size
    
    # Split text into lines
    lines = text.split('\n')
    line_height = font_size * 1.5
    
    # Draw each line
    for i, line in enumerate(lines):
        # Calculate position for this line
        y_position = text_y + (i * line_height)
        
        # Calculate text width to center it
        text_width = len(line) * (font_size * 0.6)  # Rough estimate
        x_position = text_x - (text_width / 2)
        
        draw.text((x_position, y_position), line, fill="black")
    
    # Add a border around the image
    border_width = 5
    border_color = "black"
    for i in range(border_width):
        draw.rectangle(
            [(i, i), (width - i - 1, height - i - 1)],
            outline=border_color
        )
    
    # Save the image
    filepath = os.path.join('static', 'uploads', filename)
    img.save(filepath)
    print(f"Created image: {filepath}")
    return filepath

def create_all_sample_files():
    """Create all sample files needed for the database"""
    print("Creating sample directories...")
    create_sample_directory()
    
    print("\nCreating sample images for products...")
    # Create product images
    create_sample_image("antenna1.jpg", "آنتن مرکزی\nUHF/VHF")
    create_sample_image("transmitter1.jpg", "فرستنده FM\n150 وات")
    create_sample_image("yagi1.jpg", "آنتن یاگی\n10 المانی")
    create_sample_image("directional1.jpg", "آنتن دایرکشنال\nپهن‌باند")
    create_sample_image("vhf_yagi.jpg", "آنتن یاگی\nVHF")
    create_sample_image("uhf_yagi.jpg", "آنتن یاگی\nUHF")
    create_sample_image("high_freq_yagi.jpg", "آنتن یاگی\nفرکانس بالا")
    create_sample_image("dual_band_yagi.jpg", "آنتن یاگی دوبانده\n15/20 متر")
    create_sample_image("tantalum_cap.jpg", "خازن تانتالیوم\n100 میکروفاراد")
    create_sample_image("resistor.jpg", "مقاومت کربنی\n10 کیلواهم")
    create_sample_image("oscilloscope.jpg", "اسیلوسکوپ دیجیتال\n100MHz")
    create_sample_image("freq_meter.jpg", "فرکانس‌متر دیجیتال\n3GHz")
    create_sample_image("wifi_antenna.jpg", "آنتن شبکه وای‌فای\nبلندبرد")
    create_sample_image("router.jpg", "روتر بی‌سیم\nN300")
    create_sample_image("arduino.jpg", "برد آردوینو\nUNO")
    create_sample_image("raspberry.jpg", "برد راسپبری پای 4")
    
    # Create product detail images
    create_sample_image("antenna1_detail1.jpg", "جزئیات آنتن مرکزی\nنمای جلو")
    create_sample_image("antenna1_detail2.jpg", "جزئیات آنتن مرکزی\nنمای پشت")
    create_sample_image("transmitter1_detail1.jpg", "جزئیات فرستنده FM\nپنل جلو")
    create_sample_image("transmitter1_detail2.jpg", "جزئیات فرستنده FM\nپنل پشت")
    create_sample_image("yagi1_detail1.jpg", "جزئیات آنتن یاگی\nالمان‌ها")
    create_sample_image("yagi1_detail2.jpg", "جزئیات آنتن یاگی\nمحل اتصال")
    create_sample_image("oscilloscope_detail1.jpg", "جزئیات اسیلوسکوپ\nصفحه نمایش")
    create_sample_image("oscilloscope_detail2.jpg", "جزئیات اسیلوسکوپ\nکنترل‌ها")
    
    print("\nCreating sample images for services...")
    # Create service images
    create_sample_image("antenna_repair.jpg", "عیب‌یابی و تعمیر آنتن")
    create_sample_image("transmitter_repair.jpg", "تعمیر فرستنده رادیویی")
    create_sample_image("antenna_install.jpg", "نصب آنتن مرکزی")
    create_sample_image("transmitter_install.jpg", "نصب و راه‌اندازی فرستنده")
    create_sample_image("system_design.jpg", "طراحی سیستم\nپخش رادیویی")
    create_sample_image("wireless_design.jpg", "طراحی شبکه\nبی‌سیم")
    create_sample_image("consultation.jpg", "مشاوره انتخاب\nتجهیزات")
    create_sample_image("license_consult.jpg", "مشاوره اخذ\nمجوزهای فرکانسی")
    create_sample_image("radio_course.jpg", "دوره آموزشی\nمبانی رادیو")
    create_sample_image("antenna_workshop.jpg", "کارگاه عملی\nتعمیر آنتن")
    create_sample_image("yagi_repair.jpg", "تعمیر و تنظیم\nآنتن یاگی")
    create_sample_image("yagi_restore.jpg", "بازسازی آنتن یاگی")
    create_sample_image("fm_repair_low.jpg", "تعمیر فرستنده FM\nکم‌توان")
    create_sample_image("fm_repair_high.jpg", "تعمیر فرستنده FM\nپرتوان")
    
    # Create service detail images
    create_sample_image("antenna_repair_detail1.jpg", "جزئیات تعمیر آنتن\nشناسایی مشکل")
    create_sample_image("antenna_repair_detail2.jpg", "جزئیات تعمیر آنتن\nرفع عیب")
    create_sample_image("antenna_install_detail1.jpg", "جزئیات نصب آنتن\nانتخاب محل")
    create_sample_image("antenna_install_detail2.jpg", "جزئیات نصب آنتن\nاتصالات")
    create_sample_image("system_design_detail1.jpg", "جزئیات طراحی سیستم\nنقشه")
    create_sample_image("system_design_detail2.jpg", "جزئیات طراحی سیستم\nتجهیزات")
    create_sample_image("radio_course_detail1.jpg", "جزئیات دوره آموزشی\nسرفصل‌ها")
    create_sample_image("radio_course_detail2.jpg", "جزئیات دوره آموزشی\nتجهیزات آموزشی")
    
    print("\nCreating sample video placeholders...")
    # For videos, create a text file as a placeholder (can't actually create videos easily)
    video_files = [
        "antenna1_video.mp4",
        "yagi1_video.mp4",
        "oscilloscope_video.mp4",
        "antenna_repair_video.mp4",
        "antenna_install_video.mp4",
        "radio_course_video.mp4"
    ]
    
    for video_file in video_files:
        filepath = os.path.join('static', 'uploads', video_file)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"This is a placeholder for video file: {video_file}\n")
            f.write("In a real application, this would be an actual MP4 video file.")
        print(f"Created video placeholder: {filepath}")
    
    print("\nAll sample files created successfully!")

if __name__ == "__main__":
    create_all_sample_files()