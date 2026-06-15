"""
Acceptance-criteria tests for feature 05 — Shopping Cart.
Run with:  python test_cart.py
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


def _create_product(name='Cumin Seeds', price=75.0, stock=50):
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


# ---------------------------------------------------------------------------
# AC-1: Unauthenticated GET /api/cart -> 401
# ---------------------------------------------------------------------------

def test_ac1_unauthenticated_cart():
    c = app.test_client()
    r = c.get('/api/cart')
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print('AC-1 PASS: unauthenticated GET /api/cart returns 401')


# ---------------------------------------------------------------------------
# AC-2: Unauthenticated POST /api/cart/add -> 401
# ---------------------------------------------------------------------------

def test_ac2_unauthenticated_add():
    c = app.test_client()
    r = c.post('/api/cart/add', json={'product_id': 1})
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print('AC-2 PASS: unauthenticated POST /api/cart/add returns 401')


# ---------------------------------------------------------------------------
# AC-3: Authenticated user with empty cart gets empty items list
# ---------------------------------------------------------------------------

def test_ac3_empty_cart():
    _create_user('cart3@test.com')
    c = app.test_client()
    _login(c, 'cart3@test.com')
    r = c.get('/api/cart')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert 'items' in data
    assert data['items'] == []
    assert data['cart_count'] == 0
    print('AC-3 PASS: empty cart returns empty items list and count=0')


# ---------------------------------------------------------------------------
# AC-4: Add a product to cart; it appears in GET /api/cart
# ---------------------------------------------------------------------------

def test_ac4_add_product_to_cart():
    _create_user('cart4@test.com')
    pid = _create_product('Cart Test Cumin')
    c = app.test_client()
    _login(c, 'cart4@test.com')

    r = c.post('/api/cart/add', json={'product_id': pid, 'quantity': 1})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.get_json()}"
    data = r.get_json()
    assert data['success'] is True
    assert data['cart_count'] == 1

    r2 = c.get('/api/cart')
    items = r2.get_json()['items']
    assert any(i['product_id'] == pid for i in items), f"Product {pid} not found in cart"
    print('AC-4 PASS: add product to cart; appears in GET /api/cart')


# ---------------------------------------------------------------------------
# AC-5: Adding same product increments quantity (no duplicates)
# ---------------------------------------------------------------------------

def test_ac5_add_same_product_increments_qty():
    _create_user('cart5@test.com')
    pid = _create_product('Cart Test Turmeric')
    c = app.test_client()
    _login(c, 'cart5@test.com')

    c.post('/api/cart/add', json={'product_id': pid, 'quantity': 1})
    c.post('/api/cart/add', json={'product_id': pid, 'quantity': 2})

    r = c.get('/api/cart')
    items = r.get_json()['items']
    product_items = [i for i in items if i['product_id'] == pid]
    assert len(product_items) == 1, "Expected exactly one cart row per product"
    assert product_items[0]['quantity'] == 3, f"Expected qty=3, got {product_items[0]['quantity']}"
    print('AC-5 PASS: adding same product twice increments quantity to 3')


# ---------------------------------------------------------------------------
# AC-6: Update cart quantity via /api/cart/update
# ---------------------------------------------------------------------------

def test_ac6_update_cart_quantity():
    _create_user('cart6@test.com')
    pid = _create_product('Cart Test Garam Masala')
    c = app.test_client()
    _login(c, 'cart6@test.com')

    c.post('/api/cart/add', json={'product_id': pid, 'quantity': 1})
    r = c.post('/api/cart/update', json={'product_id': pid, 'quantity': 5})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.get_json()['success'] is True

    r2 = c.get('/api/cart')
    items = r2.get_json()['items']
    item = next(i for i in items if i['product_id'] == pid)
    assert item['quantity'] == 5, f"Expected qty=5, got {item['quantity']}"
    print('AC-6 PASS: update quantity sets cart item to new quantity')


# ---------------------------------------------------------------------------
# AC-7: Remove item via /api/cart/remove
# ---------------------------------------------------------------------------

def test_ac7_remove_from_cart():
    _create_user('cart7@test.com')
    pid = _create_product('Cart Test Pepper')
    c = app.test_client()
    _login(c, 'cart7@test.com')

    c.post('/api/cart/add', json={'product_id': pid})
    r = c.post('/api/cart/remove', json={'product_id': pid})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.get_json()['success'] is True

    r2 = c.get('/api/cart')
    items = r2.get_json()['items']
    assert not any(i['product_id'] == pid for i in items), "Item still in cart after remove"
    print('AC-7 PASS: remove item clears it from cart')


# ---------------------------------------------------------------------------
# AC-8: Cannot add more than available stock
# ---------------------------------------------------------------------------

def test_ac8_stock_limit_enforced():
    _create_user('cart8@test.com')
    pid = _create_product('Limited Stock Spice', stock=3)
    c = app.test_client()
    _login(c, 'cart8@test.com')

    r = c.post('/api/cart/add', json={'product_id': pid, 'quantity': 10})
    data = r.get_json()
    if r.status_code == 200 and data.get('success'):
        cart_r = c.get('/api/cart')
        items = cart_r.get_json()['items']
        item = next((i for i in items if i['product_id'] == pid), None)
        if item:
            assert item['quantity'] <= 3, \
                f"Cart qty {item['quantity']} exceeds stock of 3"
    else:
        assert r.status_code in (400, 200), f"Unexpected status: {r.status_code}"
    print('AC-8 PASS: cart quantity does not exceed available stock')


# ---------------------------------------------------------------------------
# AC-9: Cart count in response matches number of distinct items
# ---------------------------------------------------------------------------

def test_ac9_cart_count_correct():
    _create_user('cart9@test.com')
    pid1 = _create_product('Cart9 Spice A')
    pid2 = _create_product('Cart9 Spice B')
    c = app.test_client()
    _login(c, 'cart9@test.com')

    c.post('/api/cart/add', json={'product_id': pid1})
    c.post('/api/cart/add', json={'product_id': pid2})

    r = c.get('/api/cart')
    data = r.get_json()
    assert data['cart_count'] == 2, f"Expected cart_count=2, got {data['cart_count']}"
    print('AC-9 PASS: cart_count matches number of distinct items')


# ---------------------------------------------------------------------------
# AC-10: Cart response includes subtotal
# ---------------------------------------------------------------------------

def test_ac10_subtotal_in_response():
    _create_user('cart10@test.com')
    pid = _create_product('Cart10 Subtotal Spice', price=100.0)
    c = app.test_client()
    _login(c, 'cart10@test.com')

    c.post('/api/cart/add', json={'product_id': pid, 'quantity': 2})
    r = c.get('/api/cart')
    data = r.get_json()
    assert 'subtotal' in data, "Expected subtotal in cart response"
    assert data['subtotal'] >= 200.0, f"Expected subtotal >= 200, got {data['subtotal']}"
    print('AC-10 PASS: cart response includes subtotal')


# ---------------------------------------------------------------------------
# AC-11: Privacy — user A cannot see user B's cart
# ---------------------------------------------------------------------------

def test_ac11_cart_privacy():
    _create_user('cartpriva@test.com', name='Cart User A')
    _create_user('cartprivb@test.com', name='Cart User B')
    pid = _create_product('Private Spice')

    c_a = app.test_client()
    lr_a = _login(c_a, 'cartpriva@test.com')
    assert lr_a.status_code == 200, f"User A login failed: {lr_a.get_json()}"
    c_a.post('/api/cart/add', json={'product_id': pid})

    c_b = app.test_client()
    lr_b = _login(c_b, 'cartprivb@test.com')
    assert lr_b.status_code == 200, f"User B login failed: {lr_b.get_json()}"
    r_b = c_b.get('/api/cart')
    assert r_b.status_code == 200, f"Expected 200 for user B cart, got {r_b.status_code}"
    items_b = r_b.get_json()['items']
    assert not any(i['product_id'] == pid for i in items_b), \
        "User B can see User A's cart item — privacy violation"
    print('AC-11 PASS: users cannot see each other\'s carts')


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_ac1_unauthenticated_cart,
        test_ac2_unauthenticated_add,
        test_ac3_empty_cart,
        test_ac4_add_product_to_cart,
        test_ac5_add_same_product_increments_qty,
        test_ac6_update_cart_quantity,
        test_ac7_remove_from_cart,
        test_ac8_stock_limit_enforced,
        test_ac9_cart_count_correct,
        test_ac10_subtotal_in_response,
        test_ac11_cart_privacy,
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
