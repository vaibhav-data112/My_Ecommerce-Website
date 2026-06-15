"""
Acceptance-criteria tests for feature 09 — Admin Dashboard.
Run with:  python test_admin_dashboard.py
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


def _create_user(email, name='Test User', password='password123', is_admin=False):
    from werkzeug.security import generate_password_hash
    conn = _db_conn()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
        (name, email, generate_password_hash(password), int(is_admin))
    )
    uid = cur.lastrowid
    conn.commit()
    conn.close()
    return uid


def _create_product(name='Admin Spice', price=100.0, stock=50, category='Whole Spices'):
    conn = _db_conn()
    cur = conn.execute(
        "INSERT INTO products (name, description, price, stock, category) VALUES (?, ?, ?, ?, ?)",
        (name, 'Test desc', price, stock, category)
    )
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return pid


def _login(client, email, password='password123'):
    return client.post('/api/auth/login', json={'email': email, 'password': password})


def _place_order(client, product_id):
    client.post('/api/cart/add', json={'product_id': product_id, 'quantity': 1})
    r = client.post('/api/checkout', json={
        'shipping_name':    'Admin Test Customer',
        'shipping_phone':   '9876543210',
        'shipping_address': '123 Admin St, Mumbai',
    })
    return r.get_json().get('order_id')


# Create admin and non-admin users for all tests
_create_user('admin@test.com', name='Admin User', is_admin=True)
_create_user('regular@test.com', name='Regular User', is_admin=False)


# ---------------------------------------------------------------------------
# AC-1: Unauthenticated GET /api/admin -> 401
# ---------------------------------------------------------------------------

def test_ac1_unauthenticated_admin():
    c = app.test_client()
    r = c.get('/api/admin')
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print('AC-1 PASS: unauthenticated GET /api/admin returns 401')


# ---------------------------------------------------------------------------
# AC-2: Non-admin user gets 403
# ---------------------------------------------------------------------------

def test_ac2_non_admin_forbidden():
    c = app.test_client()
    _login(c, 'regular@test.com')
    r = c.get('/api/admin')
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    print('AC-2 PASS: non-admin user gets 403 on admin dashboard')


# ---------------------------------------------------------------------------
# AC-3: Admin can access dashboard with product_count, order_count, revenue
# ---------------------------------------------------------------------------

def test_ac3_admin_dashboard_data():
    c = app.test_client()
    _login(c, 'admin@test.com')
    r = c.get('/api/admin')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert 'product_count' in data
    assert 'order_count' in data
    assert 'revenue' in data
    assert 'categories' in data
    print('AC-3 PASS: admin dashboard returns product_count, order_count, revenue, categories')


# ---------------------------------------------------------------------------
# AC-4: Admin can list all products via GET /api/admin/products
# ---------------------------------------------------------------------------

def test_ac4_admin_list_products():
    c = app.test_client()
    _login(c, 'admin@test.com')
    r = c.get('/api/admin/products')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert 'products' in data
    assert isinstance(data['products'], list)
    print('AC-4 PASS: admin can list all products')


# ---------------------------------------------------------------------------
# AC-5: Admin can add a product via POST /api/admin/products/add
# ---------------------------------------------------------------------------

def test_ac5_admin_add_product():
    c = app.test_client()
    _login(c, 'admin@test.com')

    r = c.post('/api/admin/products/add', data={
        'name':        'Admin Added Cumin',
        'description': 'Premium cumin added by admin',
        'price':       '99.0',
        'stock':       '50',
        'category':    'Whole Spices',
        'image_url':   '',
    })
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.get_json()}"
    assert r.get_json().get('success') is True

    conn = _db_conn()
    row = conn.execute("SELECT * FROM products WHERE name='Admin Added Cumin'").fetchone()
    conn.close()
    assert row is not None, "Product not found in DB after admin add"
    print('AC-5 PASS: admin can add a product; it appears in DB')


# ---------------------------------------------------------------------------
# AC-6: Add product with missing name returns 422
# ---------------------------------------------------------------------------

def test_ac6_add_product_validation():
    c = app.test_client()
    _login(c, 'admin@test.com')

    r = c.post('/api/admin/products/add', data={
        'name':     '',
        'price':    '100',
        'stock':    '10',
        'category': 'Whole Spices',
    })
    assert r.status_code == 422, f"Expected 422 for missing name, got {r.status_code}"
    assert 'error' in r.get_json()
    print('AC-6 PASS: add product with missing name returns 422')


# ---------------------------------------------------------------------------
# AC-7: Admin can edit a product via POST /api/admin/products/<id>/edit
# ---------------------------------------------------------------------------

def test_ac7_admin_edit_product():
    pid = _create_product('Edit Me Spice', price=50.0)
    c = app.test_client()
    _login(c, 'admin@test.com')

    r = c.post(f'/api/admin/products/{pid}/edit', data={
        'name':        'Edited Spice Name',
        'description': 'Updated description',
        'price':       '75.0',
        'stock':       '30',
        'category':    'Ground Spices',
        'image_url':   '',
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.get_json()}"
    assert r.get_json().get('success') is True

    conn = _db_conn()
    row = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    conn.close()
    assert row['name'] == 'Edited Spice Name'
    assert row['price'] == 75.0
    assert row['category'] == 'Ground Spices'
    print('AC-7 PASS: admin can edit a product; changes reflected in DB')


# ---------------------------------------------------------------------------
# AC-8: Admin can delete a product
# ---------------------------------------------------------------------------

def test_ac8_admin_delete_product():
    pid = _create_product('Delete Me Spice')
    c = app.test_client()
    _login(c, 'admin@test.com')

    r = c.post(f'/api/admin/products/{pid}/delete')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.get_json().get('success') is True

    conn = _db_conn()
    row = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    conn.close()
    assert row is None, "Product still exists in DB after delete"
    print('AC-8 PASS: admin can delete a product; it is removed from DB')


# ---------------------------------------------------------------------------
# AC-9: Admin can list all orders via GET /api/admin/orders
# ---------------------------------------------------------------------------

def test_ac9_admin_list_orders():
    pid = _create_product('Order For Admin')
    c_user = app.test_client()
    _login(c_user, 'regular@test.com')
    _place_order(c_user, pid)

    c_admin = app.test_client()
    _login(c_admin, 'admin@test.com')
    r = c_admin.get('/api/admin/orders')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert 'orders' in data
    assert len(data['orders']) >= 1
    assert 'allowed_statuses' in data
    print('AC-9 PASS: admin can list all orders')


# ---------------------------------------------------------------------------
# AC-10: Admin can update order status
# ---------------------------------------------------------------------------

def test_ac10_admin_update_order_status():
    pid = _create_product('Status Update Spice')
    c_user = app.test_client()
    _login(c_user, 'regular@test.com')
    order_id = _place_order(c_user, pid)

    conn = _db_conn()
    conn.execute("UPDATE orders SET status='paid' WHERE id=?", (order_id,))
    conn.commit()
    conn.close()

    c_admin = app.test_client()
    _login(c_admin, 'admin@test.com')
    r = c_admin.post(f'/api/admin/orders/{order_id}/status', json={'status': 'shipped'})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.get_json()}"
    assert r.get_json().get('success') is True

    conn = _db_conn()
    order = conn.execute("SELECT status FROM orders WHERE id=?", (order_id,)).fetchone()
    conn.close()
    assert order['status'] == 'shipped', f"Expected status=shipped, got {order['status']}"
    print('AC-10 PASS: admin can update order status to shipped')


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_ac1_unauthenticated_admin,
        test_ac2_non_admin_forbidden,
        test_ac3_admin_dashboard_data,
        test_ac4_admin_list_products,
        test_ac5_admin_add_product,
        test_ac6_add_product_validation,
        test_ac7_admin_edit_product,
        test_ac8_admin_delete_product,
        test_ac9_admin_list_orders,
        test_ac10_admin_update_order_status,
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
