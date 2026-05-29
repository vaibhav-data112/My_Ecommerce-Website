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


def _db_conn():
    conn = sqlite3.connect(_test_db)
    conn.row_factory = sqlite3.Row
    return conn


def _create_user(email, name='Test User'):
    from werkzeug.security import generate_password_hash
    conn = _db_conn()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, generate_password_hash('password123'))
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id


def _create_order(user_id, status='pending', total=100.0, created_at=None):
    conn = _db_conn()
    cur = conn.execute(
        """INSERT INTO orders
           (user_id, status, subtotal, shipping_fee, total, shipping_name, shipping_phone, shipping_address, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, status, 60.0, 40.0, total,
         'Test User', '9876543210', '123 Test Street',
         created_at or '2024-01-01 10:00:00')
    )
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id


def _create_order_item(order_id, name='Widget', price=50.0, qty=2):
    conn = _db_conn()
    conn.execute(
        """INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity, line_total)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (order_id, 1, name, price, qty, round(price * qty, 2))
    )
    conn.commit()
    conn.close()


def _login(client, email):
    return client.post('/login', data={'email': email, 'password': 'password123'},
                       follow_redirects=True)


# ── AC-1: Order history lists the user's orders ──────────────────────────────
def test_ac1_order_history_lists_orders():
    user_id = _create_user('ac1@test.com')
    _create_order(user_id, total=100.0)
    _create_order(user_id, total=200.0)
    _create_order(user_id, total=300.0)

    c = app.test_client()
    _login(c, 'ac1@test.com')
    r = c.get('/orders')
    assert r.status_code == 200
    assert b'100.00' in r.data
    assert b'200.00' in r.data
    assert b'300.00' in r.data
    print('AC-1 PASS: order history lists all 3 orders')


# ── AC-2: Newest order appears first ─────────────────────────────────────────
def test_ac2_newest_order_first():
    user_id = _create_user('ac2@test.com')
    _create_order(user_id, total=111.0, created_at='2024-01-01 10:00:00')
    _create_order(user_id, total=222.0, created_at='2024-06-01 10:00:00')
    _create_order(user_id, total=333.0, created_at='2024-12-01 10:00:00')

    c = app.test_client()
    _login(c, 'ac2@test.com')
    r = c.get('/orders')
    assert r.status_code == 200
    page = r.data.decode()
    pos_333 = page.find('333.00')
    pos_111 = page.find('111.00')
    assert pos_333 < pos_111, 'Newest order (333) should appear before oldest (111)'
    print('AC-2 PASS: newest order appears first')


# ── AC-3: Order detail shows full info ───────────────────────────────────────
def test_ac3_order_detail_shows_info():
    user_id = _create_user('ac3@test.com')
    order_id = _create_order(user_id, status='paid', total=140.0)
    _create_order_item(order_id, name='Fancy Gadget', price=70.0, qty=2)

    c = app.test_client()
    _login(c, 'ac3@test.com')
    r = c.get(f'/orders/{order_id}')
    assert r.status_code == 200
    assert b'Fancy Gadget' in r.data
    assert b'70.00' in r.data
    assert b'123 Test Street' in r.data
    assert b'paid' in r.data.lower()
    print('AC-3 PASS: order detail shows items, address and status')


# ── AC-4: Prices reflect purchase-time snapshot ───────────────────────────────
def test_ac4_snapshot_price():
    user_id = _create_user('ac4@test.com')
    order_id = _create_order(user_id, total=100.0)
    _create_order_item(order_id, name='Old Price Item', price=100.0, qty=1)

    conn = _db_conn()
    conn.execute("UPDATE products SET price = 999.0 WHERE id = 1")
    conn.commit()
    conn.close()

    c = app.test_client()
    _login(c, 'ac4@test.com')
    r = c.get(f'/orders/{order_id}')
    assert r.status_code == 200
    assert b'100.00' in r.data
    assert b'999.00' not in r.data
    print('AC-4 PASS: detail uses snapshot price, not current product price')


# ── AC-5: Users see only their own orders ─────────────────────────────────────
def test_ac5_isolation():
    user_a = _create_user('ac5a@test.com')
    user_b = _create_user('ac5b@test.com')
    order_a = _create_order(user_a, total=50.0)

    c = app.test_client()
    _login(c, 'ac5b@test.com')
    r = c.get(f'/orders/{order_a}')
    assert r.status_code == 404
    assert b'Order Not Found' in r.data or b'not found' in r.data.lower()
    print('AC-5 PASS: user B cannot see user A\'s order')


# ── AC-6: Login required ──────────────────────────────────────────────────────
def test_ac6_login_required():
    c = app.test_client()
    r = c.get('/orders', follow_redirects=False)
    assert r.status_code == 302
    assert 'login' in r.headers.get('Location', '').lower()

    user_id = _create_user('ac6@test.com')
    order_id = _create_order(user_id)
    r2 = c.get(f'/orders/{order_id}', follow_redirects=False)
    assert r2.status_code == 302
    assert 'login' in r2.headers.get('Location', '').lower()
    print('AC-6 PASS: both order routes redirect logged-out users to login')


# ── AC-7: No orders message ───────────────────────────────────────────────────
def test_ac7_empty_state():
    _create_user('ac7@test.com')
    c = app.test_client()
    _login(c, 'ac7@test.com')
    r = c.get('/orders')
    assert r.status_code == 200
    assert b"haven't placed any orders" in r.data or b'no orders' in r.data.lower()
    assert b'Browse Products' in r.data or b'catalog' in r.data.lower()
    print('AC-7 PASS: empty state message shown with link to products')


# ── AC-8: Status is shown clearly ────────────────────────────────────────────
def test_ac8_status_display():
    user_id = _create_user('ac8@test.com')
    _create_order(user_id, status='paid',      total=10.0)
    _create_order(user_id, status='shipped',   total=20.0)
    _create_order(user_id, status='delivered', total=30.0)

    c = app.test_client()
    _login(c, 'ac8@test.com')
    r = c.get('/orders')
    assert r.status_code == 200
    assert b'paid' in r.data
    assert b'shipped' in r.data
    assert b'delivered' in r.data
    print('AC-8 PASS: all statuses shown on history page')


# ── AC-9: "My Orders" link works ─────────────────────────────────────────────
def test_ac9_nav_link():
    _create_user('ac9@test.com')
    c = app.test_client()
    _login(c, 'ac9@test.com')
    r = c.get('/', follow_redirects=True)
    assert r.status_code == 200
    assert b'/orders' in r.data
    assert b'My Orders' in r.data
    print('AC-9 PASS: "My Orders" link present in nav for logged-in user')


if __name__ == '__main__':
    tests = [
        test_ac1_order_history_lists_orders,
        test_ac2_newest_order_first,
        test_ac3_order_detail_shows_info,
        test_ac4_snapshot_price,
        test_ac5_isolation,
        test_ac6_login_required,
        test_ac7_empty_state,
        test_ac8_status_display,
        test_ac9_nav_link,
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
