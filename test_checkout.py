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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _db_conn():
    conn = sqlite3.connect(_test_db)
    conn.row_factory = sqlite3.Row
    return conn


def _create_user(email, name='Test User', password='password123'):
    from werkzeug.security import generate_password_hash
    conn = _db_conn()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, 0)",
        (name, email, generate_password_hash(password))
    )
    uid = cur.lastrowid
    conn.commit()
    conn.close()
    return uid


def _create_product(name='Checkout Spice', price=100.0, stock=50):
    conn = _db_conn()
    cur = conn.execute(
        "INSERT INTO products (name, description, price, stock, category) VALUES (?, ?, ?, ?, ?)",
        (name, 'Test desc', price, stock, 'Whole Spices')
    )
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return pid


def _login(client, email, password='password123'):
    return client.post('/api/auth/login', json={'email': email, 'password': password})


def _add_to_cart(client, product_id, quantity=1):
    return client.post('/api/cart/add', json={'product_id': product_id, 'quantity': quantity})


VALID_SHIPPING = {
    'shipping_name':    'Test Customer',
    'shipping_phone':   '9876543210',
    'shipping_address': '123 Test Street, Mumbai, Maharashtra 400001',
}


# ---------------------------------------------------------------------------
# AC-1: Unauthenticated GET /api/checkout -> 401
# ---------------------------------------------------------------------------

def test_ac1_unauthenticated_checkout():
    c = app.test_client()
    r = c.get('/api/checkout')
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print('AC-1 PASS: unauthenticated GET /api/checkout returns 401')


# ---------------------------------------------------------------------------
# AC-2: GET /api/checkout with empty cart returns 400
# ---------------------------------------------------------------------------

def test_ac2_checkout_empty_cart():
    _create_user('co2@test.com')
    c = app.test_client()
    _login(c, 'co2@test.com')
    r = c.get('/api/checkout')
    assert r.status_code == 400, f"Expected 400 for empty cart, got {r.status_code}"
    data = r.get_json()
    assert 'error' in data
    print('AC-2 PASS: checkout with empty cart returns 400')


# ---------------------------------------------------------------------------
# AC-3: GET /api/checkout with items returns cart and totals
# ---------------------------------------------------------------------------

def test_ac3_checkout_info_with_items():
    _create_user('co3@test.com')
    pid = _create_product('CO3 Spice', price=150.0)
    c = app.test_client()
    _login(c, 'co3@test.com')
    _add_to_cart(c, pid, 2)

    r = c.get('/api/checkout')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.get_json()}"
    data = r.get_json()
    assert 'items' in data
    assert 'subtotal' in data
    assert len(data['items']) > 0
    assert data['subtotal'] >= 300.0
    print('AC-3 PASS: GET /api/checkout returns items and subtotal')


# ---------------------------------------------------------------------------
# AC-4: POST /api/checkout with valid shipping creates an order
# ---------------------------------------------------------------------------

def test_ac4_place_order_success():
    _create_user('co4@test.com')
    pid = _create_product('CO4 Spice', price=200.0)
    c = app.test_client()
    _login(c, 'co4@test.com')
    _add_to_cart(c, pid, 1)

    r = c.post('/api/checkout', json=VALID_SHIPPING)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.get_json()}"
    data = r.get_json()
    assert data.get('success') is True
    assert 'order_id' in data
    assert isinstance(data['order_id'], int)
    print('AC-4 PASS: POST /api/checkout creates order and returns order_id')


# ---------------------------------------------------------------------------
# AC-5: Cart is cleared after successful checkout
# ---------------------------------------------------------------------------

def test_ac5_cart_cleared_after_order():
    _create_user('co5@test.com')
    pid = _create_product('CO5 Spice')
    c = app.test_client()
    _login(c, 'co5@test.com')
    _add_to_cart(c, pid)

    c.post('/api/checkout', json=VALID_SHIPPING)

    r = c.get('/api/cart')
    data = r.get_json()
    assert data['items'] == [], "Expected empty cart after checkout"
    assert data['cart_count'] == 0
    print('AC-5 PASS: cart is empty after successful checkout')


# ---------------------------------------------------------------------------
# AC-6: Missing shipping_name returns 422 with field error
# ---------------------------------------------------------------------------

def test_ac6_missing_name_validation():
    _create_user('co6@test.com')
    pid = _create_product('CO6 Spice')
    c = app.test_client()
    _login(c, 'co6@test.com')
    _add_to_cart(c, pid)

    bad_data = {**VALID_SHIPPING, 'shipping_name': ''}
    r = c.post('/api/checkout', json=bad_data)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
    data = r.get_json()
    assert 'errors' in data
    assert 'shipping_name' in data['errors']
    print('AC-6 PASS: missing shipping_name returns 422 with field error')


# ---------------------------------------------------------------------------
# AC-7: Invalid phone number returns 422 with field error
# ---------------------------------------------------------------------------

def test_ac7_invalid_phone_validation():
    _create_user('co7@test.com')
    pid = _create_product('CO7 Spice')
    c = app.test_client()
    _login(c, 'co7@test.com')
    _add_to_cart(c, pid)

    bad_data = {**VALID_SHIPPING, 'shipping_phone': '123'}
    r = c.post('/api/checkout', json=bad_data)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
    data = r.get_json()
    assert 'shipping_phone' in data.get('errors', {})
    print('AC-7 PASS: invalid phone returns 422 with field error')


# ---------------------------------------------------------------------------
# AC-8: Missing shipping_address returns 422
# ---------------------------------------------------------------------------

def test_ac8_missing_address_validation():
    _create_user('co8@test.com')
    pid = _create_product('CO8 Spice')
    c = app.test_client()
    _login(c, 'co8@test.com')
    _add_to_cart(c, pid)

    bad_data = {**VALID_SHIPPING, 'shipping_address': ''}
    r = c.post('/api/checkout', json=bad_data)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
    data = r.get_json()
    assert 'shipping_address' in data.get('errors', {})
    print('AC-8 PASS: missing shipping_address returns 422')


# ---------------------------------------------------------------------------
# AC-9: Order row exists in DB after successful checkout
# ---------------------------------------------------------------------------

def test_ac9_order_in_db():
    _create_user('co9@test.com')
    pid = _create_product('CO9 Spice', price=75.0)
    c = app.test_client()
    _login(c, 'co9@test.com')
    _add_to_cart(c, pid, 2)

    r = c.post('/api/checkout', json=VALID_SHIPPING)
    order_id = r.get_json()['order_id']

    conn = _db_conn()
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    conn.close()

    assert order is not None, "Order row not found in DB"
    assert order['shipping_name'] == 'Test Customer'
    assert len(items) == 1
    assert items[0]['product_id'] == pid
    assert items[0]['quantity'] == 2
    print('AC-9 PASS: order and order_items rows exist in DB after checkout')


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_ac1_unauthenticated_checkout,
        test_ac2_checkout_empty_cart,
        test_ac3_checkout_info_with_items,
        test_ac4_place_order_success,
        test_ac5_cart_cleared_after_order,
        test_ac6_missing_name_validation,
        test_ac7_invalid_phone_validation,
        test_ac8_missing_address_validation,
        test_ac9_order_in_db,
    ]
    passed = failed = 0
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
