"""
Acceptance-criteria tests for Feature 15 — Order Tracking Timeline.
Run with:  python test_order_tracking.py
"""
import json
import os
import shutil
import sqlite3
import tempfile

os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('GOOGLE_CLIENT_ID', 'test')
os.environ.setdefault('GOOGLE_CLIENT_SECRET', 'test')

_tmp    = tempfile.mkdtemp()
_test_db = os.path.join(_tmp, 'test.db')

import db as _db
_db.DATABASE = _test_db

from app import app

app.config['TESTING']        = True
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


def _create_product(name='Track Spice', price=100.0, stock=50):
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


def _admin_update(client, order_id, status, note=None, courier=None, tracking=None):
    payload = {'status': status}
    if note:     payload['note']            = note
    if courier:  payload['courier_name']    = courier
    if tracking: payload['tracking_number'] = tracking
    return client.post(f'/api/admin/orders/{order_id}/status', json=payload)


# ---------------------------------------------------------------------------
# Module-level setup — runs once
# ---------------------------------------------------------------------------

with app.app_context():
    _db.init_db()
    _db.migrate_db()

_create_user('admin@track.com', name='Admin', is_admin=True)
_create_user('user@track.com',  name='User')


# ---------------------------------------------------------------------------
# AC-1: order detail returns status_history as a LIST, not a string
# ---------------------------------------------------------------------------

def test_ac1_status_history_is_list():
    pid = _create_product('AC1 Spice')
    c   = app.test_client()
    _login(c, 'user@track.com')
    oid = _place_order(c, pid)

    r    = c.get(f'/api/orders/{oid}')
    assert r.status_code == 200
    order = r.get_json()['order']
    assert 'status_history' in order, "status_history field missing from order detail"
    assert isinstance(order['status_history'], list), \
        f"Expected list, got {type(order['status_history'])}"
    print('AC-1 PASS: order detail returns status_history as a list')


# ---------------------------------------------------------------------------
# AC-2: admin advances status → history entry appended with timestamp
# ---------------------------------------------------------------------------

def test_ac2_admin_advance_status_appends_history():
    pid = _create_product('AC2 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@track.com')
    _login(c_user,  'user@track.com')
    oid = _place_order(c_user, pid)

    r = _admin_update(c_admin, oid, 'packed')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.get_json()}"

    # Verify DB — history has an entry for 'packed'
    conn = _conn()
    row  = conn.execute("SELECT status, status_history FROM orders WHERE id=?", (oid,)).fetchone()
    conn.close()
    assert row['status'] == 'packed', f"Status should be packed, got {row['status']}"
    hist = json.loads(row['status_history'])
    statuses = [e['status'] for e in hist]
    assert 'packed' in statuses, f"'packed' not in history: {statuses}"
    # Timestamp must be present and non-empty
    packed_entry = next(e for e in hist if e['status'] == 'packed')
    assert packed_entry.get('at'), "Timestamp missing from history entry"
    print('AC-2 PASS: admin status advance appends history entry with timestamp')


# ---------------------------------------------------------------------------
# AC-3: admin ships with courier + tracking → saved in DB + returned in detail
# ---------------------------------------------------------------------------

def test_ac3_shipped_saves_courier_and_tracking():
    pid     = _create_product('AC3 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@track.com')
    _login(c_user,  'user@track.com')
    oid = _place_order(c_user, pid)

    r = _admin_update(c_admin, oid, 'shipped',
                      note='Kanpur warehouse se nikal gaya',
                      courier='BlueDart',
                      tracking='BD7712345')
    assert r.status_code == 200

    # Verify DB
    conn = _conn()
    row  = conn.execute(
        "SELECT courier_name, tracking_number FROM orders WHERE id=?", (oid,)
    ).fetchone()
    conn.close()
    assert row['courier_name']    == 'BlueDart',   f"courier_name mismatch: {row['courier_name']}"
    assert row['tracking_number'] == 'BD7712345', f"tracking_number mismatch: {row['tracking_number']}"

    # Verify API response includes them
    detail = c_user.get(f'/api/orders/{oid}').get_json()['order']
    assert detail['courier_name']    == 'BlueDart'
    assert detail['tracking_number'] == 'BD7712345'
    print('AC-3 PASS: shipped status saves courier + tracking; returned in detail')


# ---------------------------------------------------------------------------
# AC-4: note saved in history entry
# ---------------------------------------------------------------------------

def test_ac4_note_saved_in_history():
    pid     = _create_product('AC4 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@track.com')
    _login(c_user,  'user@track.com')
    oid = _place_order(c_user, pid)

    _admin_update(c_admin, oid, 'packed', note='Packing in progress')

    conn = _conn()
    hist = json.loads(conn.execute(
        "SELECT status_history FROM orders WHERE id=?", (oid,)
    ).fetchone()['status_history'])
    conn.close()

    packed_entry = next((e for e in hist if e['status'] == 'packed'), None)
    assert packed_entry is not None
    assert packed_entry['note'] == 'Packing in progress', \
        f"Note mismatch: {packed_entry['note']}"
    print('AC-4 PASS: note is saved in status history entry')


# ---------------------------------------------------------------------------
# AC-5: multiple status updates → all entries in history in correct order
# ---------------------------------------------------------------------------

def test_ac5_multiple_updates_build_history():
    pid     = _create_product('AC5 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@track.com')
    _login(c_user,  'user@track.com')
    oid = _place_order(c_user, pid)

    for status in ('packed', 'shipped', 'out_for_delivery', 'delivered'):
        rv = _admin_update(c_admin, oid, status)
        assert rv.status_code == 200, f"Failed on status={status}: {rv.get_json()}"

    detail = c_user.get(f'/api/orders/{oid}').get_json()['order']
    hist   = detail['status_history']
    statuses_in_hist = [e['status'] for e in hist]

    for s in ('packed', 'shipped', 'out_for_delivery', 'delivered'):
        assert s in statuses_in_hist, f"'{s}' missing from history: {statuses_in_hist}"
    assert detail['status'] == 'delivered'
    print('AC-5 PASS: all 4 status updates appear in history; final status = delivered')


# ---------------------------------------------------------------------------
# AC-6: terminal status (cancelled) → appended to history, status updated
# ---------------------------------------------------------------------------

def test_ac6_terminal_status_cancelled():
    pid     = _create_product('AC6 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@track.com')
    _login(c_user,  'user@track.com')
    oid = _place_order(c_user, pid)

    _admin_update(c_admin, oid, 'packed')
    r = _admin_update(c_admin, oid, 'cancelled')
    assert r.status_code == 200

    conn  = _conn()
    row   = conn.execute("SELECT status, status_history FROM orders WHERE id=?", (oid,)).fetchone()
    conn.close()
    assert row['status'] == 'cancelled'
    hist  = json.loads(row['status_history'])
    stats = [e['status'] for e in hist]
    assert 'cancelled' in stats, f"'cancelled' not in history: {stats}"
    print('AC-6 PASS: cancelled terminal status appended to history')


# ---------------------------------------------------------------------------
# AC-7: invalid status → 400
# ---------------------------------------------------------------------------

def test_ac7_invalid_status_rejected():
    pid     = _create_product('AC7 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@track.com')
    _login(c_user,  'user@track.com')
    oid = _place_order(c_user, pid)

    r = _admin_update(c_admin, oid, 'flying')
    assert r.status_code == 400, f"Expected 400 for invalid status, got {r.status_code}"
    print('AC-7 PASS: invalid status value returns 400')


# ---------------------------------------------------------------------------
# AC-8: unauthenticated status update → 401
# ---------------------------------------------------------------------------

def test_ac8_unauthenticated_update_rejected():
    c = app.test_client()
    r = c.post('/api/admin/orders/1/status', json={'status': 'packed'})
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print('AC-8 PASS: unauthenticated status update returns 401')


# ---------------------------------------------------------------------------
# AC-9: non-admin user cannot update order status → 403
# ---------------------------------------------------------------------------

def test_ac9_non_admin_update_rejected():
    c = app.test_client()
    _login(c, 'user@track.com')
    r = c.post('/api/admin/orders/1/status', json={'status': 'packed'})
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    print('AC-9 PASS: non-admin status update returns 403')


# ---------------------------------------------------------------------------
# AC-10: non-existent order → 404
# ---------------------------------------------------------------------------

def test_ac10_nonexistent_order_404():
    c = app.test_client()
    _login(c, 'admin@track.com')
    r = _admin_update(c, 99999, 'packed')
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    print('AC-10 PASS: status update on non-existent order returns 404')


# ---------------------------------------------------------------------------
# AC-11: can_user_review fix — delivered order allows review
# ---------------------------------------------------------------------------

def test_ac11_delivered_order_can_review():
    _create_user('reviewer@track.com')
    pid     = _create_product('AC11 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@track.com')
    _login(c_user,  'reviewer@track.com')
    oid = _place_order(c_user, pid)

    # Advance order to delivered
    for status in ('packed', 'shipped', 'out_for_delivery', 'delivered'):
        _admin_update(c_admin, oid, status)

    # Manually set to 'delivered' in DB in case checkout left it as 'pending'
    conn = _conn()
    conn.execute("UPDATE orders SET status = 'delivered' WHERE id=?", (oid,))
    conn.commit()
    conn.close()

    # Customer should now be able to review the product
    from db import can_user_review
    # Get reviewer's user id
    conn = _conn()
    uid  = conn.execute(
        "SELECT id FROM users WHERE email=?", ('reviewer@track.com',)
    ).fetchone()['id']
    conn.close()

    result = can_user_review(uid, pid)
    assert result is True, \
        "can_user_review returned False for delivered order — bug not fixed"
    print('AC-11 PASS: can_user_review returns True for delivered order (bug fixed)')


# ---------------------------------------------------------------------------
# AC-12: courier details only saved when status is 'shipped'
# ---------------------------------------------------------------------------

def test_ac12_courier_not_saved_for_non_shipped():
    pid     = _create_product('AC12 Spice')
    c_admin = app.test_client()
    c_user  = app.test_client()
    _login(c_admin, 'admin@track.com')
    _login(c_user,  'user@track.com')
    oid = _place_order(c_user, pid)

    # Update to 'packed' with courier fields (should be ignored)
    _admin_update(c_admin, oid, 'packed',
                  courier='ShouldNotSave', tracking='000')

    conn = _conn()
    row  = conn.execute(
        "SELECT courier_name, tracking_number FROM orders WHERE id=?", (oid,)
    ).fetchone()
    conn.close()
    assert row['courier_name']    is None, \
        f"courier_name should be NULL for packed status, got: {row['courier_name']}"
    assert row['tracking_number'] is None, \
        f"tracking_number should be NULL for packed status, got: {row['tracking_number']}"
    print('AC-12 PASS: courier details not saved for non-shipped status')


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_ac1_status_history_is_list,
        test_ac2_admin_advance_status_appends_history,
        test_ac3_shipped_saves_courier_and_tracking,
        test_ac4_note_saved_in_history,
        test_ac5_multiple_updates_build_history,
        test_ac6_terminal_status_cancelled,
        test_ac7_invalid_status_rejected,
        test_ac8_unauthenticated_update_rejected,
        test_ac9_non_admin_update_rejected,
        test_ac10_nonexistent_order_404,
        test_ac11_delivered_order_can_review,
        test_ac12_courier_not_saved_for_non_shipped,
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
