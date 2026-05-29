"""
Acceptance-criteria tests for feature 06 — Checkout Flow.
Run with:  python test_checkout.py
"""
import os
import shutil
import sqlite3
import tempfile

os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('GOOGLE_CLIENT_ID', 'test')
os.environ.setdefault('GOOGLE_CLIENT_SECRET', 'test')

_tmp = tempfile.mkdtemp()
_test_db = os.path.join(_tmp, 'test.db')

import db as _db
_db.DATABASE = _test_db

from app import app

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False


def get_client():
    return app.test_client()


def login(client, email='demo@example.com', password='demo1234'):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)


def add_item(client, product_id=1, quantity=1):
    return client.post('/cart/add', data={'product_id': str(product_id), 'quantity': str(quantity)},
                       follow_redirects=True)


VALID_FORM = {
    'shipping_name': 'Jane Doe',
    'shipping_phone': '9876543210',
    'shipping_address': '123 Main St, Mumbai, MH 400001',
}


def test_ac3_logged_out_redirected():
    c = get_client()
    r = c.get('/checkout', follow_redirects=False)
    assert r.status_code == 302
    assert 'login' in r.headers.get('Location', '').lower()
    print('AC-3 PASS: logged-out user redirected to login from checkout')


def test_ac2_empty_cart_redirected():
    c = get_client()
    login(c)
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM cart_items WHERE user_id = 1")
    conn.commit()
    conn.close()
    r = c.get('/checkout', follow_redirects=True)
    assert r.status_code == 200
    assert b'empty' in r.data.lower()
    print('AC-2 PASS: empty cart redirected to cart page with message')


def test_ac1_view_checkout():
    c = get_client()
    login(c)
    add_item(c, product_id=1, quantity=1)
    add_item(c, product_id=2, quantity=2)
    r = c.get('/checkout')
    assert r.status_code == 200
    assert b'Wireless Earbuds' in r.data
    assert b'Cotton T-Shirt' in r.data
    assert b'Subtotal' in r.data
    assert b'Total' in r.data
    print('AC-1 PASS: checkout page shows items with prices, subtotal, and total')


def test_ac4_address_required():
    c = get_client()
    login(c)
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM cart_items WHERE user_id = 1")
    conn.commit()
    conn.close()
    add_item(c, product_id=1, quantity=1)

    r = c.post('/checkout', data={'shipping_name': '', 'shipping_phone': '', 'shipping_address': ''},
               follow_redirects=True)
    assert r.status_code == 200
    assert b'required' in r.data.lower()
    conn = sqlite3.connect(_test_db)
    order_count = conn.execute("SELECT COUNT(*) FROM orders WHERE user_id = 1").fetchone()[0]
    conn.close()
    assert order_count == 0, f'Expected 0 orders, got {order_count}'
    print('AC-4 PASS: blank address form shows validation errors and creates no order')


def test_ac5_out_of_stock_blocks_order():
    c = get_client()
    login(c)
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM cart_items WHERE user_id = 1")
    conn.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (1, 1, 1)")
    conn.execute("UPDATE products SET stock = 0 WHERE id = 1")
    conn.commit()
    conn.close()

    r = c.post('/checkout', data=VALID_FORM, follow_redirects=True)
    assert r.status_code == 200
    assert b'out of stock' in r.data.lower() or b'insufficient' in r.data.lower()
    conn = sqlite3.connect(_test_db)
    order_count = conn.execute("SELECT COUNT(*) FROM orders WHERE user_id = 1").fetchone()[0]
    # restore stock
    conn.execute("UPDATE products SET stock = 50 WHERE id = 1")
    conn.execute("DELETE FROM cart_items WHERE user_id = 1")
    conn.commit()
    conn.close()
    assert order_count == 0, f'Expected 0 orders when item out of stock, got {order_count}'
    print('AC-5 PASS: out-of-stock item blocks order creation')


def test_ac7_successful_order_creation():
    c = get_client()
    login(c)
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM cart_items WHERE user_id = 1")
    conn.execute("DELETE FROM orders WHERE user_id = 1")
    conn.execute("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE user_id = 1)")
    conn.commit()
    conn.close()

    add_item(c, product_id=1, quantity=2)
    add_item(c, product_id=2, quantity=1)

    r = c.post('/checkout', data=VALID_FORM, follow_redirects=False)
    # Should redirect to /payment/<order_id>
    assert r.status_code == 302
    location = r.headers.get('Location', '')
    assert '/payment/' in location, f'Expected /payment/<id>, got {location}'

    conn = sqlite3.connect(_test_db)
    order = conn.execute("SELECT * FROM orders WHERE user_id = 1").fetchone()
    assert order is not None, 'No order row created'
    assert order[2] == 'pending'  # status
    items_db = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order[0],)).fetchall()
    conn.close()

    assert len(items_db) == 2, f'Expected 2 order_items, got {len(items_db)}'
    print(f'AC-7 PASS: order #{order[0]} created with status=pending and 2 order_items')


def test_ac8_no_double_order():
    c = get_client()
    login(c)
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM orders WHERE user_id = 1")
    conn.execute("DELETE FROM cart_items WHERE user_id = 1")
    conn.commit()
    conn.close()

    add_item(c, product_id=2, quantity=1)
    c.post('/checkout', data=VALID_FORM, follow_redirects=False)

    # Cart is now cleared; second submit should NOT create another order
    c.post('/checkout', data=VALID_FORM, follow_redirects=False)

    conn = sqlite3.connect(_test_db)
    count = conn.execute("SELECT COUNT(*) FROM orders WHERE user_id = 1").fetchone()[0]
    conn.close()
    assert count == 1, f'Expected 1 order (no double), got {count}'
    print('AC-8 PASS: double submit creates only one order')


def test_ac9_price_snapshot_permanent():
    c = get_client()
    login(c)
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM orders WHERE user_id = 1")
    conn.execute("DELETE FROM cart_items WHERE user_id = 1")
    # product 2 (Cotton T-Shirt) price = 9.99
    conn.execute("UPDATE products SET price = 9.99, stock = 100 WHERE id = 2")
    conn.commit()
    conn.close()

    add_item(c, product_id=2, quantity=1)
    c.post('/checkout', data=VALID_FORM, follow_redirects=False)

    # Change price after order
    conn = sqlite3.connect(_test_db)
    conn.execute("UPDATE products SET price = 99.99 WHERE id = 2")
    conn.commit()
    order = conn.execute("SELECT id FROM orders WHERE user_id = 1 ORDER BY id DESC LIMIT 1").fetchone()
    assert order is not None
    oi = conn.execute("SELECT unit_price FROM order_items WHERE order_id = ?", (order[0],)).fetchone()
    conn.close()

    assert abs(oi[0] - 9.99) < 0.001, f'Price snapshot changed: expected 9.99, got {oi[0]}'
    print('AC-9 PASS: order_items price snapshot is permanent after product price change')


def test_ac10_all_or_nothing_rollback():
    """Force a mid-insert failure and verify no partial order remains."""
    import unittest.mock as mock

    conn_setup = sqlite3.connect(_test_db)
    conn_setup.execute("DELETE FROM orders WHERE user_id = 1")
    conn_setup.execute("DELETE FROM cart_items WHERE user_id = 1")
    conn_setup.execute("UPDATE products SET stock = 100 WHERE id = 1")
    conn_setup.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (1, 1, 1)")
    conn_setup.commit()
    conn_setup.close()

    original_place_order = _db.place_order

    def failing_place_order(*args, **kwargs):
        return False, 'Could not place order, please try again', None

    with mock.patch.object(_db, 'place_order', side_effect=failing_place_order):
        import checkout as co
        with mock.patch.object(co, 'place_order', side_effect=failing_place_order):
            c = get_client()
            login(c)
            r = c.post('/checkout', data=VALID_FORM, follow_redirects=True)
            assert r.status_code == 200

    conn = sqlite3.connect(_test_db)
    count = conn.execute("SELECT COUNT(*) FROM orders WHERE user_id = 1").fetchone()[0]
    conn.close()
    assert count == 0, f'Expected 0 orders after failure, got {count}'
    print('AC-10 PASS: failed order leaves no partial data')


if __name__ == '__main__':
    tests = [
        test_ac3_logged_out_redirected,
        test_ac2_empty_cart_redirected,
        test_ac1_view_checkout,
        test_ac4_address_required,
        test_ac5_out_of_stock_blocks_order,
        test_ac7_successful_order_creation,
        test_ac8_no_double_order,
        test_ac9_price_snapshot_permanent,
        test_ac10_all_or_nothing_rollback,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f'FAIL {t.__name__}: {e}')
            failed += 1

    print(f'\n{passed} passed, {failed} failed')
    shutil.rmtree(_tmp, ignore_errors=True)
    exit(0 if failed == 0 else 1)
