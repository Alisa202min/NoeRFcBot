from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import Database
import os

db = Database()

async def start(update, context):
    await update.message.reply_text("سلام! به ربات فروشگاه تجهیزات فرکانس رادیویی خوش آمدید!")

async def products(update, context):
    categories = db.get_categories('product')
    keyboard = [[InlineKeyboardButton(cat['name'], callback_data=f'category:product:{cat["id"]}')]
               for cat in categories if cat['level'] == 1]
    await update.message.reply_text("دسته‌بندی محصولات:", reply_markup=InlineKeyboardMarkup(keyboard))

async def services(update, context):
    categories = db.get_categories('service')
    keyboard = [[InlineKeyboardButton(cat['name'], callback_data=f'category:service:{cat["id"]}')]
               for cat in categories if cat['level'] == 1]
    await update.message.reply_text("دسته‌بندی خدمات:", reply_markup=InlineKeyboardMarkup(keyboard))

async def education(update, context):
    categories = db.get_categories('educational')
    keyboard = [[InlineKeyboardButton(cat['name'], callback_data=f'category:educational:{cat["id"]}')]
               for cat in categories if cat['level'] == 1]
    await update.message.reply_text("دسته‌بندی مطالب آموزشی:", reply_markup=InlineKeyboardMarkup(keyboard))

async def callback_query_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data.split(':')
    if data[0] == 'category':
        cat_type, cat_id = data[1], int(data[2])
        categories = db.get_categories(cat_type)
        subcategories = [cat for cat in categories if cat['parent_id'] == cat_id]
        if subcategories:
            keyboard = [[InlineKeyboardButton(cat['name'], callback_data=f'category:{cat_type}:{cat["id"]}')]
                       for cat in subcategories]
            await query.message.reply_text("زیرگروه‌ها:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            items = db.get_items_by_category(cat_type, cat_id)  # Implement in Database class
            response = "\n".join([f"{item['name']}: {item['price']}" for item in items])
            await query.message.reply_text(response or "هیچ موردی یافت نشد.")

async def inquiries(update, context):
    text = update.message.text
    if text.startswith("استعلام قیمت: "):
        product_name = text.replace("استعلام قیمت: ", "")
        with db.conn.cursor() as cur:
            cur.execute("SELECT id FROM products WHERE name = %s", (product_name,))
            product = cur.fetchone()
            if product:
                cur.execute("INSERT INTO inquiries (user_id, name, product_id) VALUES (%s, %s, %s)",
                           (update.message.from_user.id, update.message.from_user.first_name, product[0]))
                db.conn.commit()
                await update.message.reply_text("استعلام شما ثبت شد!")
            else:
                await update.message.reply_text("محصول یافت نشد.")

def main():
    app = Application.builder().token(os.environ.get("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("products", products))
    app.add_handler(CommandHandler("services", services))
    app.add_handler(CommandHandler("education", education))
    app.add_handler(CommandHandler("inquiries", inquiries))
    app.add_handler(CallbackQueryHandler(callback_query_handler))
    app.run_polling()

if __name__ == "__main__":
    main()