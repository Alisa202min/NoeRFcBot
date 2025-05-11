import pytest
from telegram import Update, Message, Chat, User, InlineKeyboardMarkup
from telegram.ext import Application

def compare_trees(bot_tree, db_tree):
    """Compare bot's category tree with database tree."""
    if len(bot_tree) != len(db_tree):
        return False
    for bot_node, db_node in zip(bot_tree, db_tree):
        if bot_node['name'] != db_node['name'] or bot_node['level'] != db_node['level']:
            return False
        if not compare_trees(bot_node.get('children', []), db_node.get('children', [])):
            return False
    return True

@pytest.mark.asyncio
async def test_products_category_hierarchy(app, db, mocker):
    """Test that Products button displays correct category hierarchy."""
    # Setup complex hierarchy
    with db.conn.cursor() as cur:
        cur.execute("INSERT INTO product_categories (name, level) VALUES (%s, %s) RETURNING id",
                   ('تجهیزات اصلی', 1))
        cat1_id = cur.fetchone()[0]
        cur.execute("INSERT INTO product_categories (name, parent_id, level) VALUES (%s, %s, %s) RETURNING id",
                   ('رادیوها', cat1_id, 2))
        cat2_id = cur.fetchone()[0]
        cur.execute("INSERT INTO product_categories (name, parent_id, level) VALUES (%s, %s, %s) RETURNING id",
                   ('رادیو VHF', cat2_id, 3))
        cat3_id = cur.fetchone()[0]
        cur.execute("INSERT INTO product_categories (name, parent_id, level) VALUES (%s, %s, %s)",
                   ('مدل خاص', cat3_id, 4))
        db.conn.commit()

    # Mock reply_markup to capture tree
    reply_mock = mocker.patch('telegram.Message.reply_text')
    update = Update(
        update_id=4,
        message=Message(
            message_id=4,
            chat=Chat(id=123, type="private"),
            from_user=User(id=456, is_bot=False, first_name="Test"),
            text="/products"
        )
    )
    await app.process_update(update)

    # Extract bot's tree from inline keyboard
    reply_mock.assert_called_once()
    keyboard = reply_mock.call_args[1]['reply_markup']
    bot_tree = [{'name': button.text, 'level': 1, 'children': []} for row in keyboard.inline_keyboard for button in row]

    # Get database tree
    db_tree = db.get_category_tree('product')

    # Compare trees
    assert compare_trees(bot_tree, db_tree[:len(bot_tree)])

    # Test deeper navigation
    callback_mock = mocker.patch('telegram.Update.callback_query.answer')
    update = Update(
        update_id=5,
        callback_query={
            'id': '123',
            'from': User(id=456, is_bot=False, first_name="Test"),
            'chat_instance': 'test',
            'data': f'category:product:{cat1_id}',
            'message': Message(
                message_id=5,
                chat=Chat(id=123, type="private")
            )
        }
    )
    await app.process_update(update)
    keyboard = reply_mock.call_args[1]['reply_markup']
    bot_subtree = [{'name': button.text, 'level': 2, 'children': []} for row in keyboard.inline_keyboard for button in row]
    db_subtree = db_tree[0]['children']
    assert compare_trees(bot_subtree, db_subtree)