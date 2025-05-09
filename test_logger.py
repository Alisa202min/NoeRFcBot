#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ماژول ثبت وقایع و نتایج تست‌ها

این ماژول برای ثبت نتایج تست‌ها و ارائه گزارشات نتایج تست به کار می‌رود.
"""

import os
import json
import logging
from datetime import datetime

# مسیر پوشه برای ذخیره گزارش‌های تست
TEST_RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_results')

# ایجاد پوشه اگر وجود نداشته باشد
os.makedirs(TEST_RESULTS_DIR, exist_ok=True)

# تنظیم لاگر
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

class TestLogger:
    """کلاس مدیریت ثبت وقایع تست‌ها"""
    
    def __init__(self, test_name, test_type='inquiry'):
        """مقداردهی اولیه ثبت کننده تست
        
        پارامترها:
            test_name (str): نام تست یا دسته تست
            test_type (str): نوع تست (inquiry, bot, admin, etc.)
        """
        self.test_name = test_name
        self.test_type = test_type
        self.start_time = datetime.now()
        self.end_time = None
        self.results = {
            'test_name': test_name,
            'test_type': test_type,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': None,
            'duration_seconds': None,
            'test_cases': [],
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'error_tests': 0,
            'success_rate': 0.0,
            'overall_result': 'pending'
        }
        
        # ثبت شروع تست
        logger.info(f"شروع اجرای تست‌های {test_name} ({test_type})")
    
    def log_test_case(self, test_case_name, status, message=None, details=None):
        """ثبت نتیجه یک مورد تست
        
        پارامترها:
            test_case_name (str): نام مورد تست
            status (str): وضعیت تست (pass, fail, error)
            message (str): پیام توضیحی
            details (dict): جزئیات بیشتر
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        test_case = {
            'name': test_case_name,
            'status': status,
            'timestamp': timestamp,
            'message': message or '',
            'details': details or {}
        }
        
        self.results['test_cases'].append(test_case)
        self.results['total_tests'] += 1
        
        if status == 'pass':
            self.results['passed_tests'] += 1
            logger.info(f"✅ {test_case_name}: موفق")
        elif status == 'fail':
            self.results['failed_tests'] += 1
            logger.warning(f"❌ {test_case_name}: شکست - {message}")
        elif status == 'error':
            self.results['error_tests'] += 1
            logger.error(f"⚠️ {test_case_name}: خطا - {message}")
    
    def finish(self):
        """اتمام ثبت نتایج تست و تولید گزارش نهایی"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        self.results['end_time'] = self.end_time.strftime('%Y-%m-%d %H:%M:%S')
        self.results['duration_seconds'] = duration
        
        # محاسبه نرخ موفقیت
        if self.results['total_tests'] > 0:
            success_rate = (self.results['passed_tests'] / self.results['total_tests']) * 100
            self.results['success_rate'] = round(success_rate, 2)
        
        # تعیین نتیجه کلی
        if self.results['failed_tests'] == 0 and self.results['error_tests'] == 0:
            self.results['overall_result'] = 'success'
        else:
            self.results['overall_result'] = 'failure'
        
        # ثبت اطلاعات در فایل
        filename = f"{self.test_type}_{self.test_name.replace(' ', '_')}_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(TEST_RESULTS_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # ثبت خلاصه نتایج
        summary = (
            f"\n=== خلاصه نتایج تست {self.test_name} ===\n"
            f"زمان اجرا: {self.results['duration_seconds']:.2f} ثانیه\n"
            f"تعداد کل تست‌ها: {self.results['total_tests']}\n"
            f"تست‌های موفق: {self.results['passed_tests']}\n"
            f"تست‌های ناموفق: {self.results['failed_tests']}\n"
            f"تست‌های با خطا: {self.results['error_tests']}\n"
            f"نرخ موفقیت: {self.results['success_rate']}%\n"
            f"نتیجه کلی: {'موفق' if self.results['overall_result'] == 'success' else 'ناموفق'}\n"
            f"فایل گزارش: {filepath}\n"
        )
        
        logger.info(summary)
        return self.results
    
    def create_html_report(self):
        """ایجاد گزارش HTML از نتایج تست‌ها"""
        if self.end_time is None:
            self.finish()
        
        # نام فایل HTML
        filename = f"{self.test_type}_{self.test_name.replace(' ', '_')}_{self.start_time.strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(TEST_RESULTS_DIR, filename)
        
        # ایجاد محتوای HTML
        html_content = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="fa">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>گزارش تست {self.test_name}</title>
            <style>
                body {{
                    font-family: Tahoma, Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f7f7f7;
                    direction: rtl;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                h1, h2, h3 {{
                    color: #333;
                }}
                .summary {{
                    margin: 20px 0;
                    padding: 15px;
                    background-color: #f0f0f0;
                    border-radius: 5px;
                }}
                .summary-row {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 10px;
                }}
                .test-cases {{
                    margin-top: 30px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    padding: 10px;
                    text-align: right;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                .pass {{
                    color: green;
                }}
                .fail {{
                    color: red;
                }}
                .error {{
                    color: orange;
                }}
                .badge {{
                    display: inline-block;
                    padding: 3px 8px;
                    border-radius: 3px;
                    color: white;
                }}
                .badge-success {{
                    background-color: #28a745;
                }}
                .badge-danger {{
                    background-color: #dc3545;
                }}
                .badge-warning {{
                    background-color: #ffc107;
                    color: #212529;
                }}
                .overall-success {{
                    background-color: #d4edda;
                    color: #155724;
                    padding: 15px;
                    border-radius: 5px;
                    border: 1px solid #c3e6cb;
                    margin-top: 20px;
                }}
                .overall-failure {{
                    background-color: #f8d7da;
                    color: #721c24;
                    padding: 15px;
                    border-radius: 5px;
                    border: 1px solid #f5c6cb;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>گزارش تست {self.test_name}</h1>
                <p>نوع تست: {self.test_type}</p>
                
                <div class="summary">
                    <div class="summary-row">
                        <span>زمان شروع:</span>
                        <span>{self.results['start_time']}</span>
                    </div>
                    <div class="summary-row">
                        <span>زمان پایان:</span>
                        <span>{self.results['end_time']}</span>
                    </div>
                    <div class="summary-row">
                        <span>مدت زمان اجرا:</span>
                        <span>{self.results['duration_seconds']:.2f} ثانیه</span>
                    </div>
                    <div class="summary-row">
                        <span>تعداد کل تست‌ها:</span>
                        <span>{self.results['total_tests']}</span>
                    </div>
                    <div class="summary-row">
                        <span>تست‌های موفق:</span>
                        <span>{self.results['passed_tests']}</span>
                    </div>
                    <div class="summary-row">
                        <span>تست‌های ناموفق:</span>
                        <span>{self.results['failed_tests']}</span>
                    </div>
                    <div class="summary-row">
                        <span>تست‌های با خطا:</span>
                        <span>{self.results['error_tests']}</span>
                    </div>
                    <div class="summary-row">
                        <span>نرخ موفقیت:</span>
                        <span>{self.results['success_rate']}%</span>
                    </div>
                </div>
                
                <div class="{'overall-success' if self.results['overall_result'] == 'success' else 'overall-failure'}">
                    <h3>نتیجه کلی: {'موفق' if self.results['overall_result'] == 'success' else 'ناموفق'}</h3>
                </div>
                
                <div class="test-cases">
                    <h2>جزئیات تست‌ها</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>نام تست</th>
                                <th>وضعیت</th>
                                <th>زمان</th>
                                <th>پیام</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # اضافه کردن ردیف برای هر مورد تست
        for i, test_case in enumerate(self.results['test_cases']):
            status_class = ""
            status_badge = ""
            
            if test_case['status'] == 'pass':
                status_class = "pass"
                status_badge = '<span class="badge badge-success">موفق</span>'
            elif test_case['status'] == 'fail':
                status_class = "fail"
                status_badge = '<span class="badge badge-danger">شکست</span>'
            elif test_case['status'] == 'error':
                status_class = "error"
                status_badge = '<span class="badge badge-warning">خطا</span>'
            
            html_content += f"""
                            <tr class="{status_class}">
                                <td>{i+1}</td>
                                <td>{test_case['name']}</td>
                                <td>{status_badge}</td>
                                <td>{test_case['timestamp']}</td>
                                <td>{test_case['message']}</td>
                            </tr>
            """
        
        # بستن قسمت‌های باقی‌مانده HTML
        html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        
        # ذخیره فایل HTML
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"گزارش HTML در فایل زیر ذخیره شد: {filepath}")
        return filepath


# مثال استفاده از کلاس TestLogger
if __name__ == "__main__":
    # ایجاد یک نمونه برای تست
    test_logger = TestLogger("نمونه تست", "inquiry")
    
    # ثبت چند نتیجه تست
    test_logger.log_test_case("تست اول", "pass")
    test_logger.log_test_case("تست دوم", "pass")
    test_logger.log_test_case("تست سوم", "fail", "خطا در مقایسه مقادیر")
    test_logger.log_test_case("تست چهارم", "error", "خطای اجرایی در تست")
    test_logger.log_test_case("تست پنجم", "pass")
    
    # اتمام و تولید گزارش
    results = test_logger.finish()
    
    # ایجاد گزارش HTML
    html_report = test_logger.create_html_report()
    
    print(f"گزارش HTML در مسیر زیر ایجاد شد: {html_report}")