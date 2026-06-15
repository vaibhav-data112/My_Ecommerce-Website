"""
Acceptance-criteria tests for feature 07 — Payment (Razorpay).
Run with:  python test_payment.py
"""
import hashlib
import hmac
import os
import shutil
import sqlite3
import tempfile

os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('GOOGLE_CLIENT_ID', 'test')
os.environ.setdefault('GOOGLE_CLIENT_SECRET', 'test')
os.environ.setdefault('RAZORPAY_KEY_ID', 'test_key_id')
os.environ.setdefault('RAZORPAY_KEY_SECRET', 'test_key_secret')

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


def _create_product(name='Pay Spice', price=100.0, stock=50):
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


def _set_order_paid(order_id, payment_id='pay_test123'):
    conn = _db_conn()
    conn.execute(
        "UPDATE orders SET status='paid', payment_id=? WHERE id=?",
        (payment_id, order_id)
    )
    conn.commit()
    conn.close()


def _set_payment_order_id(order_id, rz_order_id):
    conn = _db_conn()
    conn.execute(
        "UPDATE orders SET payment_order_id=? WHERE id=?",
        (rz_order_id, order_id)
    )
    conn.commit()
    conn.close()


def _make_signature(rz_order_id, rz_payment_id, secret='test_key_secret'):
    msg = f"{rz_order_id}|{rz_payment_id}".encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# AC-1: Unauthenticated GET /api/payment/<id> -> 401
# ---------------------------------------------------------------------------

def test_ac1_unauthenticated_payment():
    c = app.test_client()
    r = c.get('/api/payment/1')
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print('AC-1 PASS: unauthenticated GET /api/payment/<id> returns 401')


# ---------------------------------------------------------------------------
# AC-2: Unauthenticated POST /api/payment/verify -> 401
# ---------------------------------------------------------------------------

def test_ac2_unauthenticated_verify():
    c = app.test_client()
    r = c.post('/api/payment/verify', json={})
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print('AC-2 PASS: unauthenticated POST /api/payment/verify returns 401')


# ---------------------------------------------------------------------------
# AC-3: GET /api/payment/<id> for non-existent order -> 404
# ---------------------------------------------------------------------------

def test_ac3_payment_nonexistent_order():
    _create_user('pay3@test.com')
    c = app.test_client()
    _login(c, 'pay3@test.com')
    r = c.get('/api/payment/99999')
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    print('AC-3 PASS: payment for non-existent order returns 404')


# ---------------------------------------------------------------------------
# AC-4: GET /api/payment/<id> for another user's order -> 403
# ---------------------------------------------------------------------------

def test_ac4_payment_wrong_user():
    _create_user('pay4a@test.com', name='Pay4 Alice')
    _create_user('pay4b@test.com', name='Pay4 Bob')
    pid = _create_product('Pay4 Spice')

    c_a = app.test_client()
    _login(c_a, 'pay4a@test.com')
    order_id = _place_order(c_a, pid)

    c_b = app.test_client()
    _login(c_b, 'pay4b@test.com')
    r = c_b.get(f'/api/payment/{order_id}')
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    print('AC-4 PASS: accessing another user\'s payment returns 403')


# ---------------------------------------------------------------------------
# AC-5: Paid order returns already_paid=True
# ---------------------------------------------------------------------------

def test_ac5_already_paid_order():
    _create_user('pay5@test.com')
    pid = _create_product('Pay5 Spice')
    c = app.test_client()
    _login(c, 'pay5@test.com')
    order_id = _place_order(c, pid)
    _set_order_paid(order_id)

    r = c.get(f'/api/payment/{order_id}')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert data.get('already_paid') is True
    print('AC-5 PASS: GET /api/payment/<id> for paid order returns already_paid=True')


# ---------------------------------------------------------------------------
# AC-6: Payment verify with valid HMAC signature marks order as paid
# ---------------------------------------------------------------------------

def test_ac6_verify_valid_signature():
    _create_user('pay6@test.com')
    pid = _create_product('Pay6 Spice', price=250.0)
    c = app.test_client()
    _login(c, 'pay6@test.com')
    order_id = _place_order(c, pid)

    rz_order_id   = 'order_test_abc123'
    rz_payment_id = 'pay_test_xyz789'
    _set_payment_order_id(order_id, rz_order_id)
    signature = _make_signature(rz_order_id, rz_payment_id)

    r = c.post('/api/payment/verify', json={
        'razorpay_order_id':   rz_order_id,
        'razorpay_payment_id': rz_payment_id,
        'razorpay_signature':  signature,
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.get_json()}"
    data = r.get_json()
    assert data.get('success') is True

    conn = _db_conn()
    order = conn.execute("SELECT status, payment_id FROM orders WHERE id=?", (order_id,)).fetchone()
    conn.close()
    assert order['status'] == 'paid', f"Expected status=paid, got {order['status']}"
    assert order['payment_id'] == rz_payment_id
    print('AC-6 PASS: valid HMAC signature marks order as paid in DB')


# ---------------------------------------------------------------------------
# AC-7: Payment verify with invalid signature returns 400
# ---------------------------------------------------------------------------

def test_ac7_verify_invalid_signature():
    _create_user('pay7@test.com')
    pid = _create_product('Pay7 Spice')
    c = app.test_client()
    _login(c, 'pay7@test.com')
    order_id = _place_order(c, pid)

    rz_order_id = 'order_test_fake'
    _set_payment_order_id(order_id, rz_order_id)

    r = c.post('/api/payment/verify', json={
        'razorpay_order_id':   rz_order_id,
        'razorpay_payment_id': 'pay_fake',
        'razorpay_signature':  'invalidsignature',
    })
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    data = r.get_json()
    assert 'error' in data
    print('AC-7 PASS: invalid HMAC signature returns 400')


# ---------------------------------------------------------------------------
# AC-8: GET /api/order/<id>/success returns order and items for paid order
# ---------------------------------------------------------------------------

def test_ac8_order_success_endpoint():
    _create_user('pay8@test.com')
    pid = _create_product('Pay8 Spice')
    c = app.test_client()
    _login(c, 'pay8@test.com')
    order_id = _place_order(c, pid)
    _set_order_paid(order_id)

    r = c.get(f'/api/order/{order_id}/success')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert 'order' in data
    assert 'items' in data
    assert data['order']['id'] == order_id
    print('AC-8 PASS: GET /api/order/<id>/success returns order and items')


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_ac1_unauthenticated_payment,
        test_ac2_unauthenticated_verify,
        test_ac3_payment_nonexistent_order,
        test_ac4_payment_wrong_user,
        test_ac5_already_paid_order,
        test_ac6_verify_valid_signature,
        test_ac7_verify_invalid_signature,
        test_ac8_order_success_endpoint,
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
