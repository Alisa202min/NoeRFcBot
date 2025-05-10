#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست اتوماتیک ربات تلگرام
این اسکریپت عملکردهای اصلی ربات را بدون نیاز به اتصال واقعی به تلگرام تست می‌کند
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.methods import SendMessage, AnswerCallbackQuery
from aiogram.types import Message, CallbackQuery, Update, User, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from app import app, db
from models import Product, Category, Inquiry
import handlers  # ماژول هندلرهای ربات

# تنظیم لاگر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# تنظیم مسیر ثابت برای ذخیره فایل‌های لاگ
LOG_FILE = "test_telegram_bot.log"

# ساختار تست
class TestBotSession:
    """کلاس برای تست ربات تلگرام"""
    def __init__(self):
        # مقادیر ثابت برای تست
        self.bot_token = os.environ.get("BOT_TOKEN", "test_token")
        self.user_id = 123456789
        self.username = "test_user"
        self.first_name = "Test"
        self.last_name = "User"
        self.chat_id = self.user_id
        self.message_id = 1
        self.callback_query_id = 1
        
        # ذخیره پاسخ‌های ربات
        self.responses = []
        self.callback_responses = []
        
        # زمان شروع تست‌ها
        self.start_time = datetime.now()
        
        # ساخت آبجکت‌های مورد نیاز
        self.bot = Bot(token=self.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        self.dp = Dispatcher()
        
        # تنظیم هندلرها
        if hasattr(handlers, 'register_handlers'):
            handlers.register_handlers(self.dp)
        
        # آماده‌سازی برای تست
        self._setup_mock_methods()
    
    def _setup_mock_methods(self):
        """جایگزینی متدهای ارسال پیام با نسخه‌های شبیه‌سازی‌شده"""
        
        # متد ارسال پیام جایگزین
        async def mock_send_message(text, chat_id=None, reply_markup=None, parse_mode=None, *args, **kwargs):
            self.message_id += 1
            response = {
                'message_id': self.message_id,
                'chat_id': chat_id or self.chat_id,
                'text': text,
                'has_keyboard': reply_markup is not None,
                'keyboard_type': type(reply_markup).__name__ if reply_markup else None,
                'buttons': self._extract_buttons(reply_markup)
            }
            self.responses.append(response)
            logger.info(f"📤 ارسال پیام: {text[:50]}..." if len(text) > 50 else f"📤 ارسال پیام: {text}")
            if reply_markup:
                logger.info(f"⌨️ دکمه‌ها: {self._extract_buttons(reply_markup)}")
            # Use datetime object instead of timestamp for newer aiogram versions
            return Message(
                message_id=self.message_id,
                date=datetime.now(),
                chat=Chat(id=chat_id or self.chat_id, type="private"),
                from_user=User(id=int(self.bot_token.split(':')[0]) if self.bot_token.split(':')[0].isdigit() else 0, 
                              is_bot=True, first_name="Test Bot"),
                text=text
            )
        
        # متد پاسخ به کال‌بک کوئری جایگزین
        async def mock_answer_callback_query(callback_query_id, text=None, show_alert=False, *args, **kwargs):
            response = {
                'callback_query_id': callback_query_id,
                'text': text,
                'show_alert': show_alert
            }
            self.callback_responses.append(response)
            if text:
                logger.info(f"🔔 پاسخ به کال‌بک: {text}")
            return True
        
        # جایگزینی متدها
        self.bot.send_message = mock_send_message
        self.bot.answer_callback_query = mock_answer_callback_query
    
    def _extract_buttons(self, markup):
        """استخراج دکمه‌ها از مارکاپ"""
        if not markup or not isinstance(markup, InlineKeyboardMarkup):
            return []
        
        buttons = []
        for row in markup.inline_keyboard:
            for btn in row:
                buttons.append({
                    'text': btn.text,
                    'callback_data': btn.callback_data
                })
        return buttons
    
    def create_message(self, text):
        """ساخت یک پیام جدید از طرف کاربر"""
        self.message_id += 1
        # Use datetime object instead of timestamp for newer aiogram versions
        return Message(
            message_id=self.message_id,
            date=datetime.now(),
            chat=Chat(id=self.chat_id, type="private"),
            from_user=User(
                id=self.user_id,
                is_bot=False,
                username=self.username,
                first_name=self.first_name,
                last_name=self.last_name
            ),
            text=text
        )
    
    def create_callback_query(self, data):
        """ساخت یک کال‌بک کوئری جدید از طرف کاربر"""
        self.callback_query_id += 1
        return CallbackQuery(
            id=str(self.callback_query_id),
            from_user=User(
                id=self.user_id,
                is_bot=False,
                username=self.username,
                first_name=self.first_name,
                last_name=self.last_name
            ),
            chat_instance=str(self.chat_id),
            message=Message(
                message_id=self.message_id,
                date=datetime.now(),
                chat=Chat(id=self.chat_id, type="private"),
                from_user=User(id=int(self.bot_token.split(':')[0]) if self.bot_token.split(':')[0].isdigit() else 0, 
                              is_bot=True, first_name="Test Bot"),
                text="پیام قبلی"
            ),
            data=data
        )
    
    async def process_message(self, text):
        """پردازش پیام کاربر و دریافت پاسخ"""
        logger.info(f"📥 پیام کاربر: {text}")
        message = self.create_message(text)
        update = Update(
            update_id=self.message_id,
            message=message
        )
        await self.dp.feed_update(bot=self.bot, update=update)
        # کمی صبر کنیم تا پاسخ ارسال شود
        await asyncio.sleep(0.1)
        return self.responses[-1] if self.responses else None
    
    async def process_callback(self, data):
        """پردازش کال‌بک کوئری کاربر و دریافت پاسخ"""
        logger.info(f"🔘 کلیک کاربر روی دکمه: {data}")
        query = self.create_callback_query(data)
        update = Update(
            update_id=self.message_id,
            callback_query=query
        )
        await self.dp.feed_update(bot=self.bot, update=update)
        # کمی صبر کنیم تا پاسخ ارسال شود
        await asyncio.sleep(0.1)
        return self.responses[-1] if self.responses else None
    
    def get_last_response(self):
        """دریافت آخرین پاسخ ربات"""
        return self.responses[-1] if self.responses else None
    
    def get_last_callback_response(self):
        """دریافت آخرین پاسخ کال‌بک ربات"""
        return self.callback_responses[-1] if self.callback_responses else None
    
    def clear_responses(self):
        """پاک کردن پاسخ‌های ذخیره‌شده"""
        self.responses = []
        self.callback_responses = []
    
    def get_last_message_buttons(self):
        """دریافت دکمه‌های آخرین پیام"""
        if not self.responses:
            return []
        return self.responses[-1].get('buttons', [])
    
    def log_test_result(self, test_name, success, error=None):
        """ثبت نتیجه تست در لاگ"""
        if success:
            logger.info(f"✅ تست {test_name}: موفق")
        else:
            logger.error(f"❌ تست {test_name}: ناموفق - {error}")
    
    async def close(self):
        """بستن اتصال‌ها"""
        # در اینجا هیچ اتصال واقعی نداریم که نیاز به بستن داشته باشد
        pass

class TestResult:
    """کلاس برای ذخیره نتایج تست‌ها"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.failures = []
    
    def add_pass(self, test_name):
        """افزودن تست موفق"""
        self.total += 1
        self.passed += 1
        logger.info(f"✅ تست {test_name}: موفق")
    
    def add_fail(self, test_name, error):
        """افزودن تست ناموفق"""
        self.total += 1
        self.failed += 1
        self.failures.append(f"{test_name}: {error}")
        logger.error(f"❌ تست {test_name}: ناموفق - {error}")
    
    def summary(self):
        """نمایش خلاصه نتایج"""
        success_rate = (self.passed / self.total) * 100 if self.total > 0 else 0
        logger.info(f"\n===== نتایج تست =====")
        logger.info(f"تعداد کل تست‌ها: {self.total}")
        logger.info(f"تست‌های موفق: {self.passed}")
        logger.info(f"تست‌های ناموفق: {self.failed}")
        logger.info(f"نرخ موفقیت: {success_rate:.2f}%")
        
        if self.failed > 0:
            logger.error("لیست خطاها:")
            for i, failure in enumerate(self.failures, 1):
                logger.error(f"{i}. {failure}")
        
        logger.info("======================")
        
        return self.failed == 0

async def test_start_command(session, results):
    """تست دستور /start"""
    try:
        response = await session.process_message("/start")
        
        if not response:
            results.add_fail("دستور /start", "هیچ پاسخی دریافت نشد")
            return False
        
        # بررسی پاسخ
        if "خوش آمدید" in response['text']:
            results.add_pass("دستور /start")
            return True
        else:
            results.add_fail("دستور /start", f"متن خوش‌آمدگویی یافت نشد: {response['text']}")
            return False
    except Exception as e:
        results.add_fail("دستور /start", str(e))
        return False

async def test_main_menu(session, results):
    """تست منوی اصلی"""
    try:
        response = await session.process_message("/menu")
        
        if not response:
            results.add_fail("منوی اصلی", "هیچ پاسخی دریافت نشد")
            return False
        
        # بررسی پاسخ
        if "منوی اصلی" in response['text']:
            # بررسی دکمه‌ها
            buttons = session.get_last_message_buttons()
            required_buttons = ["محصولات", "خدمات", "استعلام قیمت", "محتوای آموزشی", "درباره ما", "تماس با ما"]
            
            missing_buttons = [btn for btn in required_buttons if not any(b['text'] == btn for b in buttons)]
            
            if not missing_buttons:
                results.add_pass("منوی اصلی")
                return True
            else:
                results.add_fail("منوی اصلی", f"دکمه‌های {', '.join(missing_buttons)} یافت نشدند")
                return False
        else:
            results.add_fail("منوی اصلی", f"متن منوی اصلی یافت نشد: {response['text']}")
            return False
    except Exception as e:
        results.add_fail("منوی اصلی", str(e))
        return False

async def test_products_menu(session, results):
    """تست منوی محصولات"""
    try:
        # اول وارد منوی اصلی می‌شویم
        await session.process_message("/menu")
        
        # پیدا کردن دکمه محصولات
        buttons = session.get_last_message_buttons()
        product_button = next((b for b in buttons if b['text'] == "محصولات"), None)
        
        if not product_button:
            results.add_fail("منوی محصولات", "دکمه محصولات در منوی اصلی یافت نشد")
            return False
        
        # کلیک روی دکمه محصولات
        response = await session.process_callback(product_button['callback_data'])
        
        if not response:
            results.add_fail("منوی محصولات", "هیچ پاسخی بعد از کلیک روی دکمه محصولات دریافت نشد")
            return False
        
        # بررسی پاسخ
        if "دسته‌بندی‌های محصولات" in response['text']:
            results.add_pass("منوی محصولات")
            return True
        else:
            results.add_fail("منوی محصولات", f"متن دسته‌بندی‌های محصولات یافت نشد: {response['text']}")
            return False
    except Exception as e:
        results.add_fail("منوی محصولات", str(e))
        return False

async def test_product_categories(session, results):
    """تست دسته‌بندی‌های محصولات"""
    try:
        with app.app_context():
            # بررسی وجود دسته‌بندی‌ها در دیتابیس
            categories = Category.query.filter_by(cat_type="product", parent_id=None).all()
            
            if not categories:
                results.add_fail("دسته‌بندی‌های محصولات", "هیچ دسته‌بندی محصولی در دیتابیس یافت نشد")
                return False
            
            # اول وارد منوی اصلی می‌شویم
            await session.process_message("/menu")
            
            # سپس وارد منوی محصولات می‌شویم
            buttons = session.get_last_message_buttons()
            product_button = next((b for b in buttons if b['text'] == "محصولات"), None)
            
            if not product_button:
                results.add_fail("دسته‌بندی‌های محصولات", "دکمه محصولات در منوی اصلی یافت نشد")
                return False
            
            await session.process_callback(product_button['callback_data'])
            
            # بررسی نمایش دسته‌بندی‌ها
            buttons = session.get_last_message_buttons()
            
            if not buttons:
                results.add_fail("دسته‌بندی‌های محصولات", "هیچ دکمه‌ای در منوی دسته‌بندی‌های محصولات یافت نشد")
                return False
            
            # انتخاب اولین دسته‌بندی
            category_button = buttons[0]
            response = await session.process_callback(category_button['callback_data'])
            
            if not response:
                results.add_fail("دسته‌بندی‌های محصولات", "هیچ پاسخی بعد از کلیک روی دکمه دسته‌بندی دریافت نشد")
                return False
            
            # بررسی نمایش زیردسته‌ها یا محصولات
            if "محصولات" in response['text'] or "زیردسته‌ها" in response['text']:
                results.add_pass("دسته‌بندی‌های محصولات")
                return True
            else:
                results.add_fail("دسته‌بندی‌های محصولات", f"متن مورد انتظار یافت نشد: {response['text']}")
                return False
    except Exception as e:
        results.add_fail("دسته‌بندی‌های محصولات", str(e))
        return False

async def test_product_details(session, results):
    """تست جزئیات محصول"""
    try:
        with app.app_context():
            # بررسی وجود محصولات در دیتابیس
            products = Product.query.filter_by(product_type="product").all()
            
            if not products:
                results.add_fail("جزئیات محصول", "هیچ محصولی در دیتابیس یافت نشد")
                return False
            
            # اول وارد منوی محصولات می‌شویم
            await session.process_message("/products")
            
            # کلیک روی اولین دکمه (احتمالاً یک دسته‌بندی)
            buttons = session.get_last_message_buttons()
            
            if not buttons:
                results.add_fail("جزئیات محصول", "هیچ دکمه‌ای در منوی محصولات یافت نشد")
                return False
            
            await session.process_callback(buttons[0]['callback_data'])
            
            # کلیک روی دکمه‌های بعدی تا رسیدن به یک محصول
            max_depth = 3  # حداکثر عمق کلیک
            for _ in range(max_depth):
                buttons = session.get_last_message_buttons()
                
                if not buttons:
                    results.add_fail("جزئیات محصول", "هیچ دکمه‌ای در این سطح یافت نشد")
                    return False
                
                response = await session.process_callback(buttons[0]['callback_data'])
                
                # بررسی اینکه آیا به صفحه جزئیات محصول رسیده‌ایم
                if "قیمت" in response['text'] and ("تومان" in response['text'] or "ریال" in response['text']):
                    # بررسی وجود دکمه استعلام قیمت
                    buttons = session.get_last_message_buttons()
                    inquiry_button = next((b for b in buttons if "استعلام" in b['text']), None)
                    
                    if inquiry_button:
                        results.add_pass("جزئیات محصول")
                        return True
                    else:
                        results.add_fail("جزئیات محصول", "دکمه استعلام قیمت در صفحه جزئیات محصول یافت نشد")
                        return False
            
            results.add_fail("جزئیات محصول", "پس از چند کلیک همچنان به صفحه جزئیات محصول نرسیدیم")
            return False
    except Exception as e:
        results.add_fail("جزئیات محصول", str(e))
        return False

async def test_price_inquiry(session, results):
    """تست استعلام قیمت"""
    try:
        # وارد منوی اصلی می‌شویم
        await session.process_message("/menu")
        
        # کلیک روی دکمه استعلام قیمت
        buttons = session.get_last_message_buttons()
        inquiry_button = next((b for b in buttons if b['text'] == "استعلام قیمت"), None)
        
        if not inquiry_button:
            results.add_fail("استعلام قیمت", "دکمه استعلام قیمت در منوی اصلی یافت نشد")
            return False
        
        response = await session.process_callback(inquiry_button['callback_data'])
        
        if not response or "نام خود را وارد کنید" not in response['text']:
            results.add_fail("استعلام قیمت", "درخواست نام در فرآیند استعلام قیمت دریافت نشد")
            return False
        
        # وارد کردن نام
        response = await session.process_message("کاربر تست")
        
        if not response or "شماره تماس خود را وارد کنید" not in response['text']:
            results.add_fail("استعلام قیمت", "درخواست شماره تماس در فرآیند استعلام قیمت دریافت نشد")
            return False
        
        # وارد کردن شماره تماس
        response = await session.process_message("09123456789")
        
        if not response or "توضیحات خود را وارد کنید" not in response['text']:
            results.add_fail("استعلام قیمت", "درخواست توضیحات در فرآیند استعلام قیمت دریافت نشد")
            return False
        
        # وارد کردن توضیحات
        response = await session.process_message("این یک استعلام قیمت تستی است")
        
        # بررسی تکمیل فرآیند استعلام
        if not response or "استعلام قیمت شما با موفقیت ثبت شد" not in response['text']:
            results.add_fail("استعلام قیمت", "تأیید ثبت استعلام قیمت دریافت نشد")
            return False
        
        # بررسی ذخیره استعلام در دیتابیس
        with app.app_context():
            inquiry = Inquiry.query.filter_by(phone="09123456789").order_by(Inquiry.id.desc()).first()
            
            if inquiry and inquiry.name == "کاربر تست" and inquiry.description == "این یک استعلام قیمت تستی است":
                results.add_pass("استعلام قیمت")
                return True
            else:
                results.add_fail("استعلام قیمت", "استعلام قیمت در دیتابیس ذخیره نشده یا اطلاعات آن صحیح نیست")
                return False
    except Exception as e:
        results.add_fail("استعلام قیمت", str(e))
        return False

async def test_educational_content(session, results):
    """تست محتوای آموزشی"""
    try:
        # وارد منوی اصلی می‌شویم
        await session.process_message("/menu")
        
        # کلیک روی دکمه محتوای آموزشی
        buttons = session.get_last_message_buttons()
        content_button = next((b for b in buttons if b['text'] == "محتوای آموزشی"), None)
        
        if not content_button:
            results.add_fail("محتوای آموزشی", "دکمه محتوای آموزشی در منوی اصلی یافت نشد")
            return False
        
        response = await session.process_callback(content_button['callback_data'])
        
        if not response:
            results.add_fail("محتوای آموزشی", "هیچ پاسخی بعد از کلیک روی دکمه محتوای آموزشی دریافت نشد")
            return False
        
        # بررسی نمایش دسته‌بندی‌های محتوای آموزشی
        if "دسته‌بندی‌های محتوای آموزشی" in response['text']:
            results.add_pass("محتوای آموزشی")
            return True
        else:
            results.add_fail("محتوای آموزشی", f"متن دسته‌بندی‌های محتوای آموزشی یافت نشد: {response['text']}")
            return False
    except Exception as e:
        results.add_fail("محتوای آموزشی", str(e))
        return False

async def test_about_us(session, results):
    """تست درباره ما"""
    try:
        # وارد منوی اصلی می‌شویم
        await session.process_message("/menu")
        
        # کلیک روی دکمه درباره ما
        buttons = session.get_last_message_buttons()
        about_button = next((b for b in buttons if b['text'] == "درباره ما"), None)
        
        if not about_button:
            results.add_fail("درباره ما", "دکمه درباره ما در منوی اصلی یافت نشد")
            return False
        
        response = await session.process_callback(about_button['callback_data'])
        
        if not response:
            results.add_fail("درباره ما", "هیچ پاسخی بعد از کلیک روی دکمه درباره ما دریافت نشد")
            return False
        
        # بررسی نمایش محتوای درباره ما
        content_exists = any(word in response['text'] for word in ["درباره ما", "شرکت", "ماموریت", "چشم‌انداز"])
        
        if content_exists:
            results.add_pass("درباره ما")
            return True
        else:
            results.add_fail("درباره ما", f"محتوای مناسب درباره ما یافت نشد: {response['text']}")
            return False
    except Exception as e:
        results.add_fail("درباره ما", str(e))
        return False

async def test_contact_us(session, results):
    """تست تماس با ما"""
    try:
        # وارد منوی اصلی می‌شویم
        await session.process_message("/menu")
        
        # کلیک روی دکمه تماس با ما
        buttons = session.get_last_message_buttons()
        contact_button = next((b for b in buttons if b['text'] == "تماس با ما"), None)
        
        if not contact_button:
            results.add_fail("تماس با ما", "دکمه تماس با ما در منوی اصلی یافت نشد")
            return False
        
        response = await session.process_callback(contact_button['callback_data'])
        
        if not response:
            results.add_fail("تماس با ما", "هیچ پاسخی بعد از کلیک روی دکمه تماس با ما دریافت نشد")
            return False
        
        # بررسی نمایش محتوای تماس با ما
        content_exists = any(word in response['text'] for word in ["تماس با ما", "آدرس", "تلفن", "ایمیل"])
        
        if content_exists:
            results.add_pass("تماس با ما")
            return True
        else:
            results.add_fail("تماس با ما", f"محتوای مناسب تماس با ما یافت نشد: {response['text']}")
            return False
    except Exception as e:
        results.add_fail("تماس با ما", str(e))
        return False

async def test_back_buttons(session, results):
    """تست دکمه‌های بازگشت"""
    try:
        # وارد منوی محصولات می‌شویم
        await session.process_message("/products")
        
        # پیدا کردن دکمه بازگشت
        buttons = session.get_last_message_buttons()
        back_button = next((b for b in buttons if "بازگشت" in b['text'] or "منوی اصلی" in b['text']), None)
        
        if not back_button:
            results.add_fail("دکمه‌های بازگشت", "دکمه بازگشت در منوی محصولات یافت نشد")
            return False
        
        response = await session.process_callback(back_button['callback_data'])
        
        if not response:
            results.add_fail("دکمه‌های بازگشت", "هیچ پاسخی بعد از کلیک روی دکمه بازگشت دریافت نشد")
            return False
        
        # بررسی بازگشت به منوی اصلی
        if "منوی اصلی" in response['text']:
            results.add_pass("دکمه‌های بازگشت")
            return True
        else:
            results.add_fail("دکمه‌های بازگشت", f"بازگشت به منوی اصلی انجام نشد: {response['text']}")
            return False
    except Exception as e:
        results.add_fail("دکمه‌های بازگشت", str(e))
        return False

async def run_all_tests():
    """اجرای تمام تست‌ها"""
    # تنظیم هندلر لاگ فایل
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    logger.info("=== شروع تست‌های اتوماتیک ربات تلگرام ===")
    
    session = None
    results = TestResult()
    
    try:
        # بررسی وجود تابع register_handlers در ماژول handlers
        if not hasattr(handlers, 'register_handlers'):
            logger.error("تابع register_handlers در ماژول handlers یافت نشد")
            results.add_fail("آماده‌سازی", "تابع register_handlers در ماژول handlers یافت نشد")
            return False
            
        # ایجاد نشست تست
        session = TestBotSession()
        
        # اجرای تست‌ها به ترتیب وابستگی
        # ابتدا تست کمترین وابستگی (دستور /start) را اجرا می‌کنیم
        logger.info("\n----- شروع تست دستور /start -----")
        start_success = await test_start_command(session, results)
        session.clear_responses()
        
        # سپس منوی اصلی را تست می‌کنیم
        logger.info("\n----- شروع تست منوی اصلی -----")
        menu_success = await test_main_menu(session, results)
        session.clear_responses()
        
        # فقط اگر منوی اصلی با موفقیت تست شود، ادامه می‌دهیم
        if menu_success:
            # اجرای سایر تست‌ها
            additional_tests = [
                ("منوی محصولات", test_products_menu),
                ("محتوای آموزشی", test_educational_content),
                ("درباره ما", test_about_us),
                ("تماس با ما", test_contact_us),
                ("دکمه‌های بازگشت", test_back_buttons),
            ]
            
            for test_name, test_func in additional_tests:
                logger.info(f"\n----- شروع تست {test_name} -----")
                await test_func(session, results)
                session.clear_responses()
            
            # تست‌های پیچیده‌تر که ممکن است به سایر تست‌ها وابسته باشند
            advanced_tests = [
                ("دسته‌بندی‌های محصولات", test_product_categories),
                ("جزئیات محصول", test_product_details),
                ("استعلام قیمت", test_price_inquiry),
            ]
            
            for test_name, test_func in advanced_tests:
                logger.info(f"\n----- شروع تست {test_name} -----")
                try:
                    await test_func(session, results)
                except Exception as e:
                    logger.error(f"خطا در تست {test_name}: {str(e)}")
                    results.add_fail(test_name, f"خطای استثنا: {str(e)}")
                finally:
                    session.clear_responses()
    except Exception as e:
        logger.error(f"خطا در اجرای تست‌ها: {str(e)}")
        results.add_fail("کلی", str(e))
    finally:
        if session:
            await session.close()
    
    # نمایش نتایج
    success = results.summary()
    
    logger.info("=== پایان تست‌های اتوماتیک ربات تلگرام ===")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)