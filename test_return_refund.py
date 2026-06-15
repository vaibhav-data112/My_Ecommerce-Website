"""
Acceptance-criteria tests for Feature 16 — Customer Self-Return + Refund.
Run with:  python test_return_refund.py
"""
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

# Force UTF-8 output so Rs/arrow chars don't crash on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('GOOGLE_CLIENT_ID', 'test')
os.environ.setdefault('GOOGLE_CLIENT_SECRET', 'test')
os.environ.setdefault('RAZORPAY_KEY_ID', 'rzp_test_fake')
os.environ.setdefault('RAZORPAY_KEY_SECRET', 'fake_secret')

_tmp     = tempfile.mkdtemp()
_test_db = os.path.join(_tmp, 'test.db')

import db as _db
_db.DATABASE = _test_db

from app import app

app.config['TESTING']          = True
app.config['WTF_CSRF_ENABLED'] = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _conn():
    conn = sqlite3.connect(_test_db)
    conn.row_factory = sqlite3.Row
    return conn


def _create_user(email, name='Test User', password='pass1234', is_admin=False):
    from werkzeug.security import generate_password_hash
    conn = _conn()
    cur  = conn.execute(
        "INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
        (name, email, generate_password_hash(password), 1 if is_admin else 0),
    )
    uid = cur.lastrowid
    conn.commit(); conn.close()
    return uid


def _create_product(name='Spice', price=100.0, stock=50):
    conn = _conn()
    cur  = conn.execute(
        "INSERT INTO products (name, description, price, stock, category)"
        " VALUES (?, ?, ?, ?, ?)",
        (name, 'desc', price, stock, 'Whole Spices'),
    )
    pid = cur.lastrowid
    conn.commit(); conn.close()
    return pid


def _login(client, email, password='pass1234'):
    return client.post('/api/auth/login',
                       json={'email': email, 'password': password})


def _place_order(client, product_id, qty=1):
    client.post('/api/cart/add', json={'product_id': product_id, 'quantity': qty})
    r = client.post('/api/checkout', json={
        'shipping_name':    'Test Customer',
        'shipping_phone':   '9876543210',
        'shipping_address': '123 Test St, Delhi',
    })
    return r.get_json().get('order_id')


def _set_status(order_id, status, history_days_ago=0):
    """Force order status + inject a status_history entry (optionally back-dated)."""
    conn = _conn()
    if history_days_ago:
        ts = (datetime.now(timezone.utc) - timedelta(days=history_days_ago)).strftime('%Y-%m-%dT%H:%M:%S')
    else:
        ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    hist = json.dumps([{"status": status, "at": ts, "note": None}])
    conn.execute(
        "UPDATE orders SET status=?, status_history=? WHERE id=?",
        (status, hist, order_id)
    )
    conn.commit(); conn.close()


def _set_payment_id(order_id, payment_id='pay_test123'):
    conn = _conn()
    conn.execute("UPDATE orders SET payment_id=? WHERE id=?", (payment_id, order_id))
    conn.commit(); conn.close()


def _set_totals(order_id, total, shipping_fee):
    conn = _conn()
    conn.execute("UPDATE orders SET total=?, shipping_fee=? WHERE id=?",
                 (total, shipping_fee, order_id))
    conn.commit(); conn.close()


def _get_order(order_id):
    conn = _conn()
    row  = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def _mock_razorpay(refund_id='rfnd_test001'):
    """Patch razorpay.Client so payment.refund() returns a fake success response."""
    mock_client = MagicMock()
    mock_client.payment.refund.return_value = {'id': refund_id}
    return patch('razorpay.Client', return_value=mock_client)


# ---------------------------------------------------------------------------
# Module-level setup (runs once)
# ---------------------------------------------------------------------------

with app.app_context():
    _db.init_db()
    _db.migrate_db()

_create_user('admin@ret.com', name='Admin', is_admin=True)
# Separate users per test to avoid lifetime-limit cross-contamination
_create_user('u_ac1@ret.com')
_create_user('u_ac2@ret.com')
_create_user('u_ac3@ret.com')
_create_user('u_ac4@ret.com')
_create_user('u_ac5a@ret.com')
_create_user('u_ac5b@ret.com')
_create_user('u_ac6@ret.com')
_create_user('u_ac7@ret.com')
_create_user('u_ac8@ret.com')
_create_user('u_ac9@ret.com')
_create_user('u_ac10@ret.com')
_create_user('u_ac11@ret.com')
_create_user('u_ac12@ret.com')
_create_user('u_ac13@ret.com')
_create_user('u_ac16@ret.com')
_create_user('u_ac17@ret.com')


# ---------------------------------------------------------------------------
# AC-1: eligible delivered order -> return_requested, history updated
# ---------------------------------------------------------------------------

def test_ac1_eligible_return_request():
    pid    = _create_product('AC1 Spice')
    c      = app.test_client()
    _login(c, 'u_ac1@ret.com')
    oid = _place_order(c, pid)
    _set_status(oid, 'delivered')

    r = c.post(f'/api/orders/{oid}/return-request',
               json={'reason': 'Product quality not as expected'})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.get_json()}"

    order = _get_order(oid)
    assert order['status'] == 'return_requested'
    assert order['return_reason'] == 'Product quality not as expected'
    assert order['return_requested_at'] is not None
    hist = json.loads(order['status_history'])
    assert any(e['status'] == 'return_requested' for e in hist)
    print('AC-1 PASS: eligible return request accepted; status = return_requested')


# ---------------------------------------------------------------------------
# AC-2: user already has a returned order -> 403 (lifetime limit)
# ---------------------------------------------------------------------------

def test_ac2_ineligible_lifetime_limit():
    pid = _create_product('AC2 Spice')
    c   = app.test_client()
    _login(c, 'u_ac2@ret.com')

    oid_old = _place_order(c, pid)
    _set_status(oid_old, 'returned')   # simulate already-used self-return

    oid_new = _place_order(c, pid)
    _set_status(oid_new, 'delivered')

    r = c.post(f'/api/orders/{oid_new}/return-request', json={'reason': 'Trying again'})
    assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.get_json()}"
    assert 'limit' in r.get_json().get('error', '').lower()
    print('AC-2 PASS: second return attempt blocked (lifetime limit)')


# ---------------------------------------------------------------------------
# AC-3: delivered > 7 days ago -> 403 (window expired)
# ---------------------------------------------------------------------------

def test_ac3_outside_return_window():
    pid = _create_product('AC3 Spice')
    c   = app.test_client()
    _login(c, 'u_ac3@ret.com')
    oid = _place_order(c, pid)
    _set_status(oid, 'delivered', history_days_ago=8)

    r = c.post(f'/api/orders/{oid}/return-request', json={'reason': 'Late return'})
    assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.get_json()}"
    assert 'window' in r.get_json().get('error', '').lower()
    print('AC-3 PASS: return request outside 7-day window blocked')


# ---------------------------------------------------------------------------
# AC-4: missing reason -> 400
# ---------------------------------------------------------------------------

def test_ac4_missing_reason():
    pid = _create_product('AC4 Spice')
    c   = app.test_client()
    _login(c, 'u_ac4@ret.com')
    oid = _place_order(c, pid)
    _set_status(oid, 'delivered')

    r = c.post(f'/api/orders/{oid}/return-request', json={'reason': '  '})
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    print('AC-4 PASS: empty reason returns 400')


# ---------------------------------------------------------------------------
# AC-5: another user's order -> 404
# ---------------------------------------------------------------------------

def test_ac5_wrong_user_order():
    pid = _create_product('AC5 Spice')
    c_a = app.test_client()
    c_b = app.test_client()
    _login(c_a, 'u_ac5a@ret.com')
    _login(c_b, 'u_ac5b@ret.com')
    oid = _place_order(c_a, pid)
    _set_status(oid, 'delivered')

    r = c_b.post(f'/api/orders/{oid}/return-request', json={'reason': 'Not mine'})
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    print('AC-5 PASS: return request on another user\'s order returns 404')


# ---------------------------------------------------------------------------
# AC-6: admin approve -> status = returned
# ---------------------------------------------------------------------------

def test_ac6_admin_approve():
    pid     = _create_product('AC6 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@ret.com')
    _login(c_user,  'u_ac6@ret.com')
    oid = _place_order(c_user, pid)
    # Set directly to avoid lifetime-limit side effects from prior tests
    _set_status(oid, 'return_requested')

    r = c_admin.post(f'/api/admin/orders/{oid}/return-approve')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.get_json()}"

    order = _get_order(oid)
    assert order['status'] == 'returned'
    hist = json.loads(order['status_history'])
    assert any(e['status'] == 'returned' for e in hist)
    print('AC-6 PASS: admin approve -> status = returned, history logged')


# ---------------------------------------------------------------------------
# AC-7: admin reject with reason -> status = delivered, reason saved
# ---------------------------------------------------------------------------

def test_ac7_admin_reject_with_reason():
    pid     = _create_product('AC7 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@ret.com')
    _login(c_user,  'u_ac7@ret.com')
    oid = _place_order(c_user, pid)
    _set_status(oid, 'return_requested')

    r = c_admin.post(f'/api/admin/orders/{oid}/return-reject',
                     json={'reason': 'Return window conditions not met'})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.get_json()}"

    order = _get_order(oid)
    assert order['status'] == 'delivered', f"Status should revert to delivered, got {order['status']}"
    assert order['return_rejected_reason'] == 'Return window conditions not met'
    print('AC-7 PASS: admin reject reverts status to delivered, saves rejection reason')


# ---------------------------------------------------------------------------
# AC-8: admin reject without reason -> 400
# ---------------------------------------------------------------------------

def test_ac8_admin_reject_no_reason():
    pid     = _create_product('AC8 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@ret.com')
    _login(c_user,  'u_ac8@ret.com')
    oid = _place_order(c_user, pid)
    _set_status(oid, 'return_requested')

    r = c_admin.post(f'/api/admin/orders/{oid}/return-reject', json={'reason': ''})
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    print('AC-8 PASS: admin reject without reason returns 400')


# ---------------------------------------------------------------------------
# AC-9: refund = total - shipping_fee (699 - 49 = 650)
# ---------------------------------------------------------------------------

def test_ac9_refund_amount_calculation():
    pid     = _create_product('AC9 Spice', price=650.0)
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@ret.com')
    _login(c_user,  'u_ac9@ret.com')
    oid = _place_order(c_user, pid)
    _set_totals(oid, total=699.0, shipping_fee=49.0)
    _set_status(oid, 'returned')
    _set_payment_id(oid, 'pay_ac9test')

    with _mock_razorpay('rfnd_ac9') as mock_cls:
        r = c_admin.post(f'/api/admin/orders/{oid}/refund')

    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.get_json()}"
    data = r.get_json()
    assert data['refund_amount'] == 650.0, \
        f"Expected 650.0, got {data['refund_amount']}"

    mock_instance = mock_cls.return_value
    mock_instance.payment.refund.assert_called_once_with(
        'pay_ac9test', {'amount': 65000, 'speed': 'normal'}
    )

    order = _get_order(oid)
    assert order['status']             == 'refunded'
    assert order['refund_amount']      == 650.0
    assert order['razorpay_refund_id'] == 'rfnd_ac9'
    print('AC-9 PASS: refund = 699 - 49 = 650; Razorpay called with 65000 paise')


# ---------------------------------------------------------------------------
# AC-10: free delivery order -> full refund (shipping_fee = 0)
# ---------------------------------------------------------------------------

def test_ac10_free_delivery_full_refund():
    pid     = _create_product('AC10 Spice', price=800.0)
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@ret.com')
    _login(c_user,  'u_ac10@ret.com')
    oid = _place_order(c_user, pid)
    _set_totals(oid, total=800.0, shipping_fee=0.0)
    _set_status(oid, 'returned')
    _set_payment_id(oid, 'pay_ac10test')

    with _mock_razorpay('rfnd_ac10'):
        r = c_admin.post(f'/api/admin/orders/{oid}/refund')

    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.get_json()}"
    assert r.get_json()['refund_amount'] == 800.0, \
        f"Free delivery: full refund expected, got {r.get_json()['refund_amount']}"
    print('AC-10 PASS: free-delivery order -> full paid amount refunded')


# ---------------------------------------------------------------------------
# AC-11: double-refund blocked (razorpay_refund_id already set)
# ---------------------------------------------------------------------------

def test_ac11_double_refund_blocked():
    pid     = _create_product('AC11 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@ret.com')
    _login(c_user,  'u_ac11@ret.com')
    oid = _place_order(c_user, pid)
    _set_totals(oid, total=500.0, shipping_fee=40.0)
    _set_status(oid, 'returned')
    _set_payment_id(oid, 'pay_ac11test')

    # Pre-set refund ID to simulate already-refunded
    conn = _conn()
    conn.execute("UPDATE orders SET razorpay_refund_id='rfnd_already' WHERE id=?", (oid,))
    conn.commit(); conn.close()

    r = c_admin.post(f'/api/admin/orders/{oid}/refund')
    assert r.status_code == 400, f"Expected 400 (already refunded), got {r.status_code}: {r.get_json()}"
    assert 'already' in r.get_json().get('error', '').lower()
    print('AC-11 PASS: double-refund blocked when razorpay_refund_id already set')


# ---------------------------------------------------------------------------
# AC-12: refund on non-returned status -> 400
# ---------------------------------------------------------------------------

def test_ac12_refund_wrong_status():
    pid     = _create_product('AC12 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@ret.com')
    _login(c_user,  'u_ac12@ret.com')
    oid = _place_order(c_user, pid)
    _set_status(oid, 'delivered')
    _set_payment_id(oid)

    r = c_admin.post(f'/api/admin/orders/{oid}/refund')
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    print('AC-12 PASS: refund on non-returned order returns 400')


# ---------------------------------------------------------------------------
# AC-13: approve/reject on non-return_requested -> 400
# ---------------------------------------------------------------------------

def test_ac13_approve_reject_wrong_status():
    pid     = _create_product('AC13 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@ret.com')
    _login(c_user,  'u_ac13@ret.com')
    oid = _place_order(c_user, pid)
    _set_status(oid, 'delivered')

    r = c_admin.post(f'/api/admin/orders/{oid}/return-approve')
    assert r.status_code == 400, f"Expected 400 for approve on delivered, got {r.status_code}"

    r = c_admin.post(f'/api/admin/orders/{oid}/return-reject', json={'reason': 'Some reason'})
    assert r.status_code == 400, f"Expected 400 for reject on delivered, got {r.status_code}"
    print('AC-13 PASS: approve/reject on non-return_requested returns 400')


# ---------------------------------------------------------------------------
# AC-14: unauthenticated -> 401
# ---------------------------------------------------------------------------

def test_ac14_unauthenticated():
    c = app.test_client()
    assert c.post('/api/orders/1/return-request', json={'reason': 't'}).status_code == 401
    assert c.post('/api/admin/orders/1/return-approve').status_code              == 401
    assert c.post('/api/admin/orders/1/return-reject', json={'reason': 't'}).status_code == 401
    assert c.post('/api/admin/orders/1/refund').status_code                      == 401
    print('AC-14 PASS: all unauthenticated requests return 401')


# ---------------------------------------------------------------------------
# AC-15: non-admin -> 403 on all admin return endpoints
# ---------------------------------------------------------------------------

def test_ac15_non_admin_forbidden():
    c = app.test_client()
    _login(c, 'u_ac1@ret.com')  # regular user

    assert c.get('/api/admin/returns').status_code                               == 403
    assert c.post('/api/admin/orders/1/return-approve').status_code              == 403
    assert c.post('/api/admin/orders/1/return-reject', json={'reason': 't'}).status_code == 403
    assert c.post('/api/admin/orders/1/refund').status_code                      == 403
    print('AC-15 PASS: non-admin user gets 403 on all admin return endpoints')


# ---------------------------------------------------------------------------
# AC-16: GET /admin/returns lists only return_requested/returned orders
# ---------------------------------------------------------------------------

def test_ac16_admin_returns_list():
    pid     = _create_product('AC16 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@ret.com')
    _login(c_user,  'u_ac16@ret.com')

    oid_pending = _place_order(c_user, pid)
    _set_status(oid_pending, 'return_requested')

    oid_normal = _place_order(c_user, pid)
    _set_status(oid_normal, 'delivered')

    r = c_admin.get('/api/admin/returns')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    ids = [o['id'] for o in r.get_json()['orders']]
    assert oid_pending in ids, f"return_requested order #{oid_pending} not in returns list"
    assert oid_normal not in ids, f"Normal delivered order #{oid_normal} should not appear"
    print('AC-16 PASS: admin /returns lists only return_requested/returned orders')


# ---------------------------------------------------------------------------
# AC-17: can_self_return=True in order_detail for eligible order
# ---------------------------------------------------------------------------

def test_ac17_can_self_return_in_order_detail():
    pid    = _create_product('AC17 Spice')
    c_user = app.test_client()
    _login(c_user, 'u_ac17@ret.com')
    oid = _place_order(c_user, pid)
    _set_status(oid, 'delivered')

    r = c_user.get(f'/api/orders/{oid}')
    assert r.status_code == 200
    order = r.get_json()['order']
    assert 'can_self_return' in order, "can_self_return field missing"
    assert order['can_self_return'] is True, \
        f"Expected True for eligible delivered order, got {order['can_self_return']}"
    print('AC-17 PASS: order detail includes can_self_return=True for eligible order')


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_ac1_eligible_return_request,
        test_ac2_ineligible_lifetime_limit,
        test_ac3_outside_return_window,
        test_ac4_missing_reason,
        test_ac5_wrong_user_order,
        test_ac6_admin_approve,
        test_ac7_admin_reject_with_reason,
        test_ac8_admin_reject_no_reason,
        test_ac9_refund_amount_calculation,
        test_ac10_free_delivery_full_refund,
        test_ac11_double_refund_blocked,
        test_ac12_refund_wrong_status,
        test_ac13_approve_reject_wrong_status,
        test_ac14_unauthenticated,
        test_ac15_non_admin_forbidden,
        test_ac16_admin_returns_list,
        test_ac17_can_self_return_in_order_detail,
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
