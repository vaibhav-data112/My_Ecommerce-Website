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
import unittest.mock as mock

os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('GOOGLE_CLIENT_ID', 'test')
os.environ.setdefault('GOOGLE_CLIENT_SECRET', 'test')
os.environ['RAZORPAY_KEY_ID'] = 'rzp_test_testkey'
os.environ['RAZORPAY_KEY_SECRET'] = 'test_secret_key'

_tmp = tempfile.mkdtemp()
_test_db = os.path.join(_tmp, 'test.db')

import db as _db
_db.DATABASE = _test_db

from app import app

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False


# --- Razorpay mock -----------------------------------------------------------

class FakeRzOrder:
    def __init__(self):
        self.data = {'id': 'order_test_123'}

    def create(self, params):
        return self.data


class FakeRzClient:
    def __init__(self, *args, **kwargs):
        self.order = FakeRzOrder()


def _make_signature(order_id, payment_id, secret='test_secret_key'):
    msg = f"{order_id}|{payment_id}".encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


# --- Helpers -----------------------------------------------------------------

def get_client():
    return app.test_client()


def login(client, email='demo@example.com', password='demo1234'):
    return client.post('/login', data={'email': email, 'password': password},
                       follow_redirects=True)


def _create_pending_order(user_id=1):
    conn = sqlite3.connect(_test_db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.execute("""
        INSERT INTO orders (user_id, status, subtotal, shipping_fee, total,
                            shipping_name, shipping_phone, shipping_address)
        VALUES (?, 'pending', 69.98, 0.0, 69.98, 'Test User', '9876543210', '123 Test St')
    """, (user_id,))
    order_id = cursor.lastrowid
    conn.execute("""
        INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity, line_total)
        VALUES (?, 1, 'Wireless Earbuds', 29.99, 2, 59.98)
    """, (order_id,))
    conn.execute("""
        INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity, line_total)
        VALUES (?, 2, 'Cotton T-Shirt', 9.99, 1, 9.99)
    """, (order_id,))
    conn.commit()
    conn.close()
    return order_id


def _create_second_user():
    conn = sqlite3.connect(_test_db)
    from werkzeug.security import generate_password_hash
    conn.execute(
        "INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ('User B', 'userb@example.com', generate_password_hash('pass1234'))
    )
    conn.commit()
    user_id = conn.execute("SELECT id FROM users WHERE email = 'userb@example.com'").fetchone()[0]
    conn.close()
    return user_id


# --- Tests -------------------------------------------------------------------

def test_ac8_login_required():
    c = get_client()
    r = c.get('/payment/1', follow_redirects=False)
    assert r.status_code == 302
    assert 'login' in r.headers.get('Location', '').lower()
    print('AC-8 PASS: logged-out user redirected to login')


def test_ac1_owner_sees_pay_page():
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM orders WHERE user_id = 1")
    conn.commit()
    conn.close()

    order_id = _create_pending_order(user_id=1)

    with mock.patch('payment._rz_client', return_value=FakeRzClient()):
        c = get_client()
        login(c)
        r = c.get(f'/payment/{order_id}', follow_redirects=False)

    assert r.status_code == 200
    assert b'69.98' in r.data
    assert b'order_test_123' in r.data or b'rzp_test_testkey' in r.data
    print('AC-1 PASS: owner sees payment page with correct amount')


def test_ac2_non_owner_blocked():
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM orders WHERE user_id = 1")
    conn.commit()
    conn.close()

    order_id = _create_pending_order(user_id=1)
    _create_second_user()

    with mock.patch('payment._rz_client', return_value=FakeRzClient()):
        c = get_client()
        login(c, email='userb@example.com', password='pass1234')
        r = c.get(f'/payment/{order_id}', follow_redirects=False)

    assert r.status_code == 403
    print('AC-2 PASS: non-owner gets 403')


def test_ac3_valid_payment_marks_paid():
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM orders WHERE user_id = 1")
    conn.commit()
    conn.close()

    order_id = _create_pending_order(user_id=1)

    # Simulate the gateway already stored payment_order_id
    conn = sqlite3.connect(_test_db)
    conn.execute("UPDATE orders SET payment_order_id = 'order_test_123' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

    valid_sig = _make_signature('order_test_123', 'pay_test_456')

    c = get_client()
    login(c)
    r = c.post('/payment/verify', data={
        'razorpay_order_id':  'order_test_123',
        'razorpay_payment_id': 'pay_test_456',
        'razorpay_signature':  valid_sig,
    }, follow_redirects=False)

    assert r.status_code == 302
    assert 'success' in r.headers.get('Location', '').lower()

    conn = sqlite3.connect(_test_db)
    order = conn.execute("SELECT status, payment_id FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    assert order[0] == 'paid', f'Expected paid, got {order[0]}'
    assert order[1] == 'pay_test_456'
    print('AC-3 PASS: valid payment marks order paid and stores payment_id')


def test_ac4_invalid_signature_rejected():
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM orders WHERE user_id = 1")
    conn.commit()
    conn.close()

    order_id = _create_pending_order(user_id=1)

    conn = sqlite3.connect(_test_db)
    conn.execute("UPDATE orders SET payment_order_id = 'order_tampered_789' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

    c = get_client()
    login(c)
    r = c.post('/payment/verify', data={
        'razorpay_order_id':  'order_tampered_789',
        'razorpay_payment_id': 'pay_fake_000',
        'razorpay_signature':  'totally_fake_signature',
    }, follow_redirects=True)

    assert r.status_code == 200
    assert b'failed' in r.data.lower() or b'verif' in r.data.lower()

    conn = sqlite3.connect(_test_db)
    order = conn.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    assert order[0] == 'pending', f'Expected pending, got {order[0]}'
    print('AC-4 PASS: tampered signature rejected, order stays pending')


def test_ac5_cancel_keeps_order_pending():
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM orders WHERE user_id = 1")
    conn.commit()
    conn.close()

    order_id = _create_pending_order(user_id=1)

    with mock.patch('payment._rz_client', return_value=FakeRzClient()):
        c = get_client()
        login(c)
        # User opens pay page but never submits the verify form (simulates cancel)
        r = c.get(f'/payment/{order_id}')

    assert r.status_code == 200

    conn = sqlite3.connect(_test_db)
    order = conn.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
    conn.close()
    assert order[0] == 'pending', f'Expected pending after cancel, got {order[0]}'
    print('AC-5 PASS: opening pay page without completing keeps order pending')


def test_ac6_already_paid_redirects_to_success():
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM orders WHERE user_id = 1")
    conn.commit()
    conn.close()

    order_id = _create_pending_order(user_id=1)

    conn = sqlite3.connect(_test_db)
    conn.execute(
        "UPDATE orders SET status = 'paid', payment_id = 'pay_already_done' WHERE id = ?",
        (order_id,)
    )
    conn.commit()
    conn.close()

    with mock.patch('payment._rz_client', return_value=FakeRzClient()):
        c = get_client()
        login(c)
        r = c.get(f'/payment/{order_id}', follow_redirects=False)

    assert r.status_code == 302
    assert 'success' in r.headers.get('Location', '').lower()
    print('AC-6 PASS: already-paid order redirects to success page')


def test_ac7_amount_from_db():
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM orders WHERE user_id = 1")
    conn.commit()
    conn.close()

    order_id = _create_pending_order(user_id=1)

    captured = {}

    class SpyRzOrder:
        def create(self, params):
            captured['amount'] = params['amount']
            return {'id': 'order_spy_999'}

    class SpyRzClient:
        def __init__(self, *a, **kw):
            self.order = SpyRzOrder()

    with mock.patch('payment._rz_client', return_value=SpyRzClient()):
        c = get_client()
        login(c)
        c.get(f'/payment/{order_id}')

    assert captured.get('amount') == 6998, f"Expected 6998 paisa, got {captured.get('amount')}"
    print('AC-7 PASS: Razorpay order amount taken from DB (6998 paisa = Rs.69.98)')


def test_ac9_secret_not_in_pay_page():
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM orders WHERE user_id = 1")
    conn.commit()
    conn.close()

    order_id = _create_pending_order(user_id=1)

    with mock.patch('payment._rz_client', return_value=FakeRzClient()):
        c = get_client()
        login(c)
        r = c.get(f'/payment/{order_id}')

    assert b'test_secret_key' not in r.data
    assert b'RAZORPAY_KEY_SECRET' not in r.data
    print('AC-9 PASS: Razorpay secret key is NOT present in the pay page HTML')


if __name__ == '__main__':
    tests = [
        test_ac8_login_required,
        test_ac1_owner_sees_pay_page,
        test_ac2_non_owner_blocked,
        test_ac3_valid_payment_marks_paid,
        test_ac4_invalid_signature_rejected,
        test_ac5_cancel_keeps_order_pending,
        test_ac6_already_paid_redirects_to_success,
        test_ac7_amount_from_db,
        test_ac9_secret_not_in_pay_page,
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
