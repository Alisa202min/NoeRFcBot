import pytest

def test_admin_categories_add(flask_client, db):
    """Test adding a category and verify bot sees it."""
    response = flask_client.post('/admin/product_categories/add', data={
        'name': 'آنتن‌های جدید',
        'parent_id': ''
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"دسته‌بندی آنتن‌های جدید با موفقیت ایجاد شد" in response.data

    # Verify in database
    with db.conn.cursor() as cur:
        cur.execute("SELECT name, level FROM product_categories WHERE name = %s", ('آنتن‌های جدید',))
        category = cur.fetchone()
        assert category
        assert category[0] == "آنتن‌های جدید"
        assert category[1] == 1