"""
Acceptance-criteria tests for feature 08 — Order Management.
Run with:  python test_order_management.py
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


def _create_product(name='Order Spice', price=100.0, stock=50):
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


def _place_order(client, product_id, qty=1):
    client.post('/api/cart/add', json={'product_id': product_id, 'quantity': qty})
    r = client.post('/api/checkout', json={
        'shipping_name':    'Test Customer',
        'shipping_phone':   '9876543210',
        'shipping_address': '123 Test St, Mumbai',
    })
    return r.get_json().get('order_id')


# ---------------------------------------------------------------------------
# AC-1: Unauthenticated GET /api/orders -> 401
# ---------------------------------------------------------------------------

def test_ac1_unauthenticated_orders():
    c = app.test_client()
    r = c.get('/api/orders')
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print('AC-1 PASS: unauthenticated GET /api/orders returns 401')


# ---------------------------------------------------------------------------
# AC-2: New user with no orders gets empty list
# ---------------------------------------------------------------------------

def test_ac2_empty_order_history():
    _create_user('ord2@test.com')
    c = app.test_client()
    _login(c, 'ord2@test.com')
    r = c.get('/api/orders')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert 'orders' in data
    assert data['orders'] == []
    print('AC-2 PASS: new user gets empty order history')


# ---------------------------------------------------------------------------
# AC-3: Order appears in history after checkout
# ---------------------------------------------------------------------------

def test_ac3_order_in_history():
    _create_user('ord3@test.com')
    pid = _create_product('Ord3 Spice')
    c = app.test_client()
    _login(c, 'ord3@test.com')
    order_id = _place_order(c, pid)

    r = c.get('/api/orders')
    data = r.get_json()
    order_ids = [o['id'] for o in data['orders']]
    assert order_id in order_ids, f"Order {order_id} not found in history: {order_ids}"
    print('AC-3 PASS: order appears in history after checkout')


# ---------------------------------------------------------------------------
# AC-4: GET /api/orders/<id> returns order details with items
# ---------------------------------------------------------------------------

def test_ac4_order_detail():
    _create_user('ord4@test.com')
    pid = _create_product('Ord4 Spice', price=150.0)
    c = app.test_client()
    _login(c, 'ord4@test.com')
    order_id = _place_order(c, pid, qty=2)

    r = c.get(f'/api/orders/{order_id}')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert 'order' in data
    assert 'items' in data
    assert data['order']['id'] == order_id
    assert len(data['items']) > 0
    assert data['items'][0]['product_id'] == pid
    assert data['items'][0]['quantity'] == 2
    print('AC-4 PASS: order detail returns order and items')


# ---------------------------------------------------------------------------
# AC-5: Order has status and shipping fields
# ---------------------------------------------------------------------------

def test_ac5_order_has_required_fields():
    _create_user('ord5@test.com')
    pid = _create_product('Ord5 Spice')
    c = app.test_client()
    _login(c, 'ord5@test.com')
    order_id = _place_order(c, pid)

    r = c.get(f'/api/orders/{order_id}')
    order = r.get_json()['order']
    assert 'status' in order
    assert 'shipping_name' in order
    assert 'shipping_phone' in order
    assert order['shipping_name'] == 'Test Customer'
    assert order['shipping_phone'] == '9876543210'
    print('AC-5 PASS: order has status, shipping_name, shipping_phone fields')


# ---------------------------------------------------------------------------
# AC-6: Accessing another user's order returns 404
# ---------------------------------------------------------------------------

def test_ac6_order_privacy():
    _create_user('ord6a@test.com', name='Ord6 Alice')
    _create_user('ord6b@test.com', name='Ord6 Bob')
    pid = _create_product('Ord6 Spice')

    c_a = app.test_client()
    _login(c_a, 'ord6a@test.com')
    order_id = _place_order(c_a, pid)

    c_b = app.test_client()
    _login(c_b, 'ord6b@test.com')
    r = c_b.get(f'/api/orders/{order_id}')
    assert r.status_code == 404, f"Expected 404 (access denied), got {r.status_code}"
    print('AC-6 PASS: user B cannot access user A\'s order (returns 404)')


# ---------------------------------------------------------------------------
# AC-7: Non-existent order ID returns 404
# ---------------------------------------------------------------------------

def test_ac7_nonexistent_order_404():
    _create_user('ord7@test.com')
    c = app.test_client()
    _login(c, 'ord7@test.com')
    r = c.get('/api/orders/99999')
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    print('AC-7 PASS: non-existent order returns 404')


# ---------------------------------------------------------------------------
# AC-8: Multiple orders appear in history (newest first)
# ---------------------------------------------------------------------------

def test_ac8_multiple_orders_in_history():
    _create_user('ord8@test.com')
    pid1 = _create_product('Ord8 SpiceA')
    pid2 = _create_product('Ord8 SpiceB')
    c = app.test_client()
    _login(c, 'ord8@test.com')
    oid1 = _place_order(c, pid1)
    oid2 = _place_order(c, pid2)

    r = c.get('/api/orders')
    order_ids = [o['id'] for o in r.get_json()['orders']]
    assert oid1 in order_ids and oid2 in order_ids, \
        f"Both orders should be in history, got: {order_ids}"
    print('AC-8 PASS: multiple orders all appear in history')


# ---------------------------------------------------------------------------
# AC-9: order_items snapshot captures product_name at time of purchase
# ---------------------------------------------------------------------------

def test_ac9_order_item_snapshots_name():
    _create_user('ord9@test.com')
    pid = _create_product('Ord9 Original Name', price=80.0)
    c = app.test_client()
    _login(c, 'ord9@test.com')
    order_id = _place_order(c, pid)

    conn = _db_conn()
    conn.execute("UPDATE products SET name = 'Changed Name' WHERE id = ?", (pid,))
    conn.commit()
    conn.close()

    r = c.get(f'/api/orders/{order_id}')
    items = r.get_json()['items']
    assert items[0]['product_name'] == 'Ord9 Original Name', \
        f"Expected original name in snapshot, got: {items[0]['product_name']}"
    print('AC-9 PASS: order_items snapshot preserves product name at purchase time')


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_ac1_unauthenticated_orders,
        test_ac2_empty_order_history,
        test_ac3_order_in_history,
        test_ac4_order_detail,
        test_ac5_order_has_required_fields,
        test_ac6_order_privacy,
        test_ac7_nonexistent_order_404,
        test_ac8_multiple_orders_in_history,
        test_ac9_order_item_snapshots_name,
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
