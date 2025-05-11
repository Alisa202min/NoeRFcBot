import pytest

@pytest.mark.asyncio
async def test_inquiry_submission(app, db, mocker):
    """Test inquiry submission and database sync."""
    with db.conn.cursor() as cur:
        cur.execute("INSERT INTO product_categories (name, level) VALUES (%s, %s) RETURNING id",
                   ('رادیوها', 1))
        cat_id = cur.fetchone()[0]
        cur.execute("INSERT INTO products (name, price, description, category_id) VALUES (%s, %s, %s, %s) RETURNING id",
                   ('رادیو UHF', 2000, 'رادیو پیشرفته', cat_id))
        product_id = cur.fetchone()[0]
        db.conn.commit()

    reply_mock = mocker.patch('telegram.Message.reply_text')
    update = Update(
        update_id=6,
        message=Message(
            message_id=6,
            chat=Chat(id=123, type="private"),
            from_user=User(id=456, is_bot=False, first_name="Test"),
            text="استعلام قیمت: رادیو UHF"
        )
    )
    await app.process_update(update)

    with db.conn.cursor() as cur:
        cur.execute("SELECT user_id, name, product_id FROM inquiries")
        inquiry = cur.fetchone()
        assert inquiry
        assert inquiry[0] == 456
        assert inquiry[1] == "Test"
        assert inquiry[2] == product_id