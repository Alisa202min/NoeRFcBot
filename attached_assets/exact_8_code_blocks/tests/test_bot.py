import pytest
from telegram import Update, Message, Chat, User, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

@pytest.mark.asyncio
async def test_start_command(app, mocker):
    """Test the /start command."""
    reply_mock = mocker.patch('telegram.Message.reply_text')
    update = Update(
        update_id=1,
        message=Message(
            message_id=1,
            chat=Chat(id=123, type="private"),
            from_user=User(id=456, is_bot=False, first_name="Test"),
            text="/start"
        )
    )
    await app.process_update(update)
    reply_mock.assert_called_once()
    assert reply_mock.call_args[0][0] == "سلام! به ربات فروشگاه تجهیزات فرکانس رادیویی خوش آمدید!"

@pytest.mark.asyncio
async def test_products_button(app, db, mocker):
    """Test the Products button and category hierarchy."""
    # Setup category hierarchy
    with db.conn.cursor() as cur:
        cur.execute("INSERT INTO product_categories (name, level) VALUES (%s, %s) RETURNING id",
                   ('تجهیزات رادیویی', 1))
        cat1_id = cur.fetchone()[0]
        cur.execute("INSERT INTO product_categories (name, parent_id, level) VALUES (%s, %s, %s) RETURNING id",
                   ('رادیوها', cat1_id, 2))
        cat2_id = cur.fetchone()[0]
        cur.execute("INSERT INTO products (name, price, description, category_id) VALUES (%s, %s, %s, %s)",
                   ('رادیو VHF', 1000, 'رادیو با کیفیت', cat2_id))
        db.conn.commit()

    # Mock reply_markup to capture inline keyboard
    reply_mock = mocker.patch('telegram.Message.reply_text')
    update = Update(
        update_id=2,
        message=Message(
            message_id=2,
            chat=Chat(id=123, type="private"),
            from_user=User(id=456, is_bot=False, first_name="Test"),
            text="/products"
        )
    )
    await app.process_update(update)

    # Verify category hierarchy in response
    reply_mock.assert_called_once()
    keyboard = reply_mock.call_args[1]['reply_markup']
    assert isinstance(keyboard, InlineKeyboardMarkup)
    buttons = [button.text for row in keyboard.inline_keyboard for button in row]
    assert "تجهیزات رادیویی" in buttons

    # Simulate selecting 'تجهیزات رادیویی'
    callback_mock = mocker.patch('telegram.Update.callback_query.answer')
    update = Update(
        update_id=3,
        callback_query={
            'id': '123',
            'from': User(id=456, is_bot=False, first_name="Test"),
            'chat_instance': 'test',
            'data': f'category:product:{cat1_id}',
            'message': Message(
                message_id=3,
                chat=Chat(id=123, type="private")
            )
        }
    )
    await app.process_update(update)
    reply_mock.assert_called()
    keyboard = reply_mock.call_args[1]['reply_markup']
    buttons = [button.text for row in keyboard.inline_keyboard for button in row]
    assert "رادیوها" in buttons