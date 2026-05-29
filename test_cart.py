"""
Acceptance-criteria tests for feature 05 — Shopping Cart.
Run with:  python test_cart.py
"""
import sqlite3
import os
import tempfile
import shutil

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


def test_ac3_logged_out_redirected():
    c = get_client()
    r = c.post('/cart/add', data={'product_id': '1'}, follow_redirects=False)
    assert r.status_code == 302
    assert 'login' in r.headers.get('Location', '').lower()
    print('AC-3 PASS: logged-out user redirected to login when adding to cart')


def test_ac1_add_to_cart():
    c = get_client()
    login(c)
    r = c.post('/cart/add', data={'product_id': '1', 'quantity': '1'}, follow_redirects=True)
    assert r.status_code == 200
    conn = sqlite3.connect(_test_db)
    row = conn.execute(
        "SELECT quantity FROM cart_items WHERE user_id=1 AND product_id=1"
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == 1
    print('AC-1 PASS: product added to cart with quantity 1')


def test_ac2_add_same_product_increments():
    c = get_client()
    login(c)
    c.post('/cart/add', data={'product_id': '1', 'quantity': '1'}, follow_redirects=True)
    conn = sqlite3.connect(_test_db)
    rows = conn.execute(
        "SELECT quantity FROM cart_items WHERE user_id=1 AND product_id=1"
    ).fetchall()
    conn.close()
    assert len(rows) == 1, f'Expected 1 row, got {len(rows)} (duplicate created)'
    assert rows[0][0] == 2, f'Expected quantity 2, got {rows[0][0]}'
    print('AC-2 PASS: adding same product increments quantity (no duplicate row)')


def test_ac4_view_cart_shows_items_and_total():
    c = get_client()
    login(c)
    c.post('/cart/add', data={'product_id': '2', 'quantity': '1'}, follow_redirects=True)
    r = c.get('/cart')
    assert r.status_code == 200
    assert b'Wireless Earbuds' in r.data
    assert b'Cotton T-Shirt' in r.data
    assert b'Subtotal' in r.data
    print('AC-4 PASS: cart page shows all items with prices and subtotal')


def test_ac5_update_quantity():
    c = get_client()
    login(c)
    r = c.post('/cart/update', data={'product_id': '1', 'quantity': '5'}, follow_redirects=True)
    assert r.status_code == 200
    conn = sqlite3.connect(_test_db)
    row = conn.execute(
        "SELECT quantity FROM cart_items WHERE user_id=1 AND product_id=1"
    ).fetchone()
    conn.close()
    assert row[0] == 5, f'Expected 5, got {row[0]}'
    print('AC-5 PASS: quantity updated to 5')


def test_ac6_qty_zero_removes_item():
    c = get_client()
    login(c)
    c.post('/cart/update', data={'product_id': '2', 'quantity': '0'}, follow_redirects=True)
    conn = sqlite3.connect(_test_db)
    row = conn.execute(
        "SELECT * FROM cart_items WHERE user_id=1 AND product_id=2"
    ).fetchone()
    conn.close()
    assert row is None
    print('AC-6 PASS: setting quantity to 0 removes item from cart')


def test_ac7_remove_item():
    c = get_client()
    login(c)
    c.post('/cart/add', data={'product_id': '3', 'quantity': '1'}, follow_redirects=True)
    c.post('/cart/remove', data={'product_id': '3'}, follow_redirects=True)
    conn = sqlite3.connect(_test_db)
    row = conn.execute(
        "SELECT * FROM cart_items WHERE user_id=1 AND product_id=3"
    ).fetchone()
    conn.close()
    assert row is None
    print('AC-7 PASS: remove button deletes item from cart')


def test_ac8_cannot_exceed_stock():
    c = get_client()
    login(c)
    # Wireless Earbuds (product 1) has stock=50; current qty=5; try to set to 100
    c.post('/cart/update', data={'product_id': '1', 'quantity': '100'}, follow_redirects=True)
    conn = sqlite3.connect(_test_db)
    row = conn.execute(
        "SELECT quantity FROM cart_items WHERE user_id=1 AND product_id=1"
    ).fetchone()
    conn.close()
    assert row[0] <= 50, f'Quantity {row[0]} exceeds stock of 50'
    print(f'AC-8 PASS: quantity capped at stock ({row[0]} <= 50)')


def test_ac9_empty_cart_message():
    c = get_client()
    login(c)
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM cart_items WHERE user_id=1")
    conn.commit()
    conn.close()
    r = c.get('/cart')
    assert r.status_code == 200
    assert b'empty' in r.data.lower()
    print('AC-9 PASS: empty cart shows friendly message')


def test_ac10_cart_count_in_nav():
    c = get_client()
    login(c)
    c.post('/cart/add', data={'product_id': '1', 'quantity': '2'}, follow_redirects=True)
    r = c.get('/products')
    assert r.status_code == 200
    assert b'Cart (2)' in r.data
    print('AC-10 PASS: cart count badge shows correct count in nav')


def test_ac11_cart_persists_across_sessions():
    c = get_client()
    login(c)
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM cart_items WHERE user_id=1")
    conn.commit()
    conn.close()
    c.post('/cart/add', data={'product_id': '4', 'quantity': '1'}, follow_redirects=True)
    c.post('/logout')
    login(c)
    conn = sqlite3.connect(_test_db)
    row = conn.execute(
        "SELECT quantity FROM cart_items WHERE user_id=1 AND product_id=4"
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == 1
    print('AC-11 PASS: cart items persist after logout and re-login')


def test_ac12_user_isolation():
    c2 = get_client()
    c2.post('/signup', data={
        'name': 'CartUser2', 'email': 'cartuser2@test.com',
        'password': 'password123', 'confirm_password': 'password123'
    }, follow_redirects=True)
    login(c2, email='cartuser2@test.com', password='password123')
    r = c2.get('/cart')
    assert r.status_code == 200
    # User1 has Python Programming Book (product 4); user2 should not see it
    assert b'Python Programming Book' not in r.data
    assert b'empty' in r.data.lower()
    print('AC-12 PASS: users see only their own cart items')


if __name__ == '__main__':
    tests = [
        test_ac3_logged_out_redirected,
        test_ac1_add_to_cart,
        test_ac2_add_same_product_increments,
        test_ac4_view_cart_shows_items_and_total,
        test_ac5_update_quantity,
        test_ac6_qty_zero_removes_item,
        test_ac7_remove_item,
        test_ac8_cannot_exceed_stock,
        test_ac9_empty_cart_message,
        test_ac10_cart_count_in_nav,
        test_ac11_cart_persists_across_sessions,
        test_ac12_user_isolation,
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
