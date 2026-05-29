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


def _db_conn():
    conn = sqlite3.connect(_test_db)
    conn.row_factory = sqlite3.Row
    return conn


def _create_user(email, name='Test User', is_admin=0):
    from werkzeug.security import generate_password_hash
    conn = _db_conn()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
        (name, email, generate_password_hash('password123'), is_admin)
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id


def _create_product(name='Widget', price=9.99, stock=10, category='Other'):
    conn = _db_conn()
    cur = conn.execute(
        "INSERT INTO products (name, description, price, stock, category) VALUES (?, ?, ?, ?, ?)",
        (name, 'A test product', price, stock, category)
    )
    product_id = cur.lastrowid
    conn.commit()
    conn.close()
    return product_id


def _create_order(user_id, status='paid', total=100.0):
    conn = _db_conn()
    cur = conn.execute(
        """INSERT INTO orders
           (user_id, status, subtotal, shipping_fee, total, shipping_name, shipping_phone, shipping_address)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, status, 60.0, 40.0, total, 'Test User', '9876543210', '123 Test Street')
    )
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id


def _login(client, email):
    return client.post('/login', data={'email': email, 'password': 'password123'},
                       follow_redirects=True)


# ── AC-1: Normal user cannot access /admin ────────────────────────────────────
def test_ac1_normal_user_blocked():
    _create_user('ac1normal@test.com', is_admin=0)
    c = app.test_client()
    _login(c, 'ac1normal@test.com')
    r = c.get('/admin', follow_redirects=True)
    assert r.status_code == 200
    assert b'Not authorised' in r.data or b'authoris' in r.data.lower(), \
        'Expected "Not authorised" flash message'
    print('AC-1 PASS: normal logged-in user is blocked from /admin')


# ── AC-2: Logged-out user is redirected to login ─────────────────────────────
def test_ac2_logged_out_redirected():
    c = app.test_client()
    r = c.get('/admin', follow_redirects=True)
    assert r.status_code == 200
    assert b'login' in r.data.lower() or b'Log in' in r.data or b'Login' in r.data, \
        'Expected login page'
    print('AC-2 PASS: logged-out visitor redirected to login')


# ── AC-3: Admin can view dashboard ───────────────────────────────────────────
def test_ac3_admin_dashboard():
    _create_user('ac3admin@test.com', is_admin=1)
    c = app.test_client()
    _login(c, 'ac3admin@test.com')
    r = c.get('/admin', follow_redirects=True)
    assert r.status_code == 200
    assert b'Manage Products' in r.data
    assert b'Manage Orders' in r.data
    print('AC-3 PASS: admin can open dashboard with links')


# ── AC-4: Admin can add a product ────────────────────────────────────────────
def test_ac4_add_product():
    _create_user('ac4admin@test.com', is_admin=1)
    c = app.test_client()
    _login(c, 'ac4admin@test.com')
    r = c.post('/admin/products/add', data={
        'name': 'New Test Product',
        'description': 'A brand new product',
        'price': '19.99',
        'stock': '25',
        'category': 'Electronics',
        'image_url': '',
    }, follow_redirects=True)
    assert r.status_code == 200
    assert b'New Test Product' in r.data

    r2 = c.get('/products', follow_redirects=True)
    assert b'New Test Product' in r2.data
    print('AC-4 PASS: admin added product appears in admin list and public catalog')


# ── AC-5: Add product validation ─────────────────────────────────────────────
def test_ac5_add_product_validation():
    _create_user('ac5admin@test.com', is_admin=1)
    c = app.test_client()
    _login(c, 'ac5admin@test.com')

    # missing name
    r = c.post('/admin/products/add', data={
        'name': '', 'description': '', 'price': '10', 'stock': '5', 'category': 'Books'
    }, follow_redirects=True)
    assert r.status_code == 200
    assert b'required' in r.data.lower()

    # negative price
    r2 = c.post('/admin/products/add', data={
        'name': 'Bad Product', 'description': '', 'price': '-5', 'stock': '5', 'category': 'Books'
    }, follow_redirects=True)
    assert r2.status_code == 200
    assert b'price' in r2.data.lower() or b'0 or greater' in r2.data.lower()

    # negative stock
    r3 = c.post('/admin/products/add', data={
        'name': 'Bad Stock', 'description': '', 'price': '5', 'stock': '-1', 'category': 'Sports'
    }, follow_redirects=True)
    assert r3.status_code == 200
    assert b'stock' in r3.data.lower() or b'0 or greater' in r3.data.lower()

    print('AC-5 PASS: validation rejects missing name, negative price, negative stock')


# ── AC-6: Admin can edit a product ───────────────────────────────────────────
def test_ac6_edit_product():
    _create_user('ac6admin@test.com', is_admin=1)
    product_id = _create_product(name='Edit Me', price=5.00, stock=10, category='Home')
    c = app.test_client()
    _login(c, 'ac6admin@test.com')
    r = c.post(f'/admin/products/{product_id}/edit', data={
        'name': 'Edited Product',
        'description': 'Updated desc',
        'price': '99.99',
        'stock': '3',
        'category': 'Home',
        'image_url': '',
    }, follow_redirects=True)
    assert r.status_code == 200
    assert b'Edited Product' in r.data

    r2 = c.get('/products', follow_redirects=True)
    assert b'Edited Product' in r2.data
    assert b'99.99' in r2.data
    print('AC-6 PASS: edited product change shows in catalog')


# ── AC-7: Admin can delete a product ─────────────────────────────────────────
def test_ac7_delete_product():
    _create_user('ac7admin@test.com', is_admin=1)
    product_id = _create_product(name='Delete Me Product', price=1.00)
    c = app.test_client()
    _login(c, 'ac7admin@test.com')
    r = c.post(f'/admin/products/{product_id}/delete', follow_redirects=True)
    assert r.status_code == 200

    conn = _db_conn()
    row = conn.execute("SELECT id FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    assert row is None, 'Product should be removed from the database'
    print('AC-7 PASS: deleted product removed from catalog')


# ── AC-8: Admin can view all orders ──────────────────────────────────────────
def test_ac8_view_all_orders():
    user_a = _create_user('ac8a@test.com', name='Alice')
    user_b = _create_user('ac8b@test.com', name='Bob')
    _create_order(user_a, total=111.0)
    _create_order(user_b, total=222.0)
    _create_user('ac8admin@test.com', is_admin=1)

    c = app.test_client()
    _login(c, 'ac8admin@test.com')
    r = c.get('/admin/orders')
    assert r.status_code == 200
    assert b'111.00' in r.data
    assert b'222.00' in r.data
    assert b'Alice' in r.data
    assert b'Bob' in r.data
    print('AC-8 PASS: admin sees all orders across all customers')


# ── AC-9: Admin can update order status ──────────────────────────────────────
def test_ac9_update_order_status():
    user_id = _create_user('ac9customer@test.com', name='Customer')
    order_id = _create_order(user_id, status='paid')
    _create_user('ac9admin@test.com', is_admin=1)

    c_admin = app.test_client()
    _login(c_admin, 'ac9admin@test.com')
    r = c_admin.post(f'/admin/orders/{order_id}/status',
                     data={'status': 'shipped'}, follow_redirects=True)
    assert r.status_code == 200

    conn = _db_conn()
    row = conn.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    assert row['status'] == 'shipped'

    c_customer = app.test_client()
    _login(c_customer, 'ac9customer@test.com')
    r2 = c_customer.get('/orders')
    assert r2.status_code == 200
    assert b'shipped' in r2.data
    print('AC-9 PASS: status updated and customer sees new status')


# ── AC-10: No public self-promotion to admin ──────────────────────────────────
def test_ac10_no_self_promotion():
    c = app.test_client()
    r = c.post('/signup', data={
        'name': 'Attacker', 'email': 'attacker@test.com',
        'password': 'password123', 'confirm_password': 'password123',
        'is_admin': '1',
    }, follow_redirects=True)
    assert r.status_code == 200

    conn = _db_conn()
    row = conn.execute("SELECT is_admin FROM users WHERE email = ?",
                       ('attacker@test.com',)).fetchone()
    conn.close()
    assert row is not None
    assert row['is_admin'] == 0, 'User should not be able to self-promote to admin via signup'
    print('AC-10 PASS: signup cannot create an admin user')


if __name__ == '__main__':
    tests = [
        test_ac1_normal_user_blocked,
        test_ac2_logged_out_redirected,
        test_ac3_admin_dashboard,
        test_ac4_add_product,
        test_ac5_add_product_validation,
        test_ac6_edit_product,
        test_ac7_delete_product,
        test_ac8_view_all_orders,
        test_ac9_update_order_status,
        test_ac10_no_self_promotion,
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
