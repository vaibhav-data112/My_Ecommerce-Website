"""
Acceptance-criteria tests for feature 13 — My Account Hub.
Run with:  python test_account.py
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


def _create_user(email, name='Test User', password='password123', is_admin=0):
    from werkzeug.security import generate_password_hash
    conn = _db_conn()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
        (name, email, generate_password_hash(password), is_admin)
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id


def _create_google_only_user(email, name='Google User'):
    """Insert a user with no password_hash (Google OAuth only account)."""
    conn = _db_conn()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash, google_id) VALUES (?, ?, ?, ?)",
        (name, email, '', 'fake-google-id-' + email)
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id


def _create_product(name='Test Product', price=99.0, stock=10):
    conn = _db_conn()
    cur = conn.execute(
        "INSERT INTO products (name, description, price, stock, category) VALUES (?, ?, ?, ?, ?)",
        (name, 'A test spice product', price, stock, 'Spice Blends')
    )
    product_id = cur.lastrowid
    conn.commit()
    conn.close()
    return product_id


def _create_order(user_id, status='paid', total=150.0):
    conn = _db_conn()
    cur = conn.execute(
        """INSERT INTO orders
           (user_id, status, subtotal, shipping_fee, total, shipping_name, shipping_phone, shipping_address)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, status, 110.0, 40.0, total, 'Test User', '9876543210', '123 Test Street')
    )
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id


def _login(client, email, password='password123'):
    return client.post(
        '/api/auth/login',
        json={'email': email, 'password': password}
    )


def _add_address(client, overrides=None):
    """POST a valid address payload; override individual fields via dict."""
    payload = {
        'full_name': 'Ravi Kumar',
        'phone': '9876543210',
        'address_line': '12 MG Road',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'pincode': '400001',
    }
    if overrides:
        payload.update(overrides)
    return client.post('/api/account/addresses/new', json=payload)


# ---------------------------------------------------------------------------
# AC-1: Unauthenticated access to any /api/account/* route -> 401
# ---------------------------------------------------------------------------

def test_ac1_unauthenticated_access():
    c = app.test_client()
    routes = [
        ('GET',  '/api/account/'),
        ('GET',  '/api/account/profile'),
        ('POST', '/api/account/profile'),
        ('POST', '/api/account/profile/delete-avatar'),
        ('GET',  '/api/account/addresses'),
        ('POST', '/api/account/addresses/new'),
        ('GET',  '/api/account/settings'),
        ('POST', '/api/account/settings/password'),
        ('POST', '/api/account/settings/notifications'),
    ]
    for method, url in routes:
        if method == 'GET':
            r = c.get(url)
        else:
            r = c.post(url, json={})
        assert r.status_code == 401, \
            f"Expected 401 for {method} {url}, got {r.status_code}"
    print('AC-1 PASS: all /api/account/* routes return 401 when not logged in')


# ---------------------------------------------------------------------------
# AC-2: Dashboard returns user info, order_count, wishlist_count
# ---------------------------------------------------------------------------

def test_ac2_dashboard_returns_summary():
    uid = _create_user('ac2dash@test.com', name='AC2 Dash User')
    _create_order(uid, total=200.0)
    _create_order(uid, total=300.0)

    # Add a wishlist item
    pid = _create_product(name='AC2 Wishlist Product')
    import db
    db.add_to_wishlist(uid, pid)

    c = app.test_client()
    _login(c, 'ac2dash@test.com')

    r = c.get('/api/account/')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()

    assert 'user' in data
    assert 'order_count' in data
    assert 'wishlist_count' in data
    assert data['order_count'] == 2, f"Expected 2 orders, got {data['order_count']}"
    assert data['wishlist_count'] == 1, f"Expected 1 wishlist item, got {data['wishlist_count']}"
    assert data['user']['email'] == 'ac2dash@test.com'
    print('AC-2 PASS: dashboard returns user info, correct order_count and wishlist_count')


# ---------------------------------------------------------------------------
# AC-3: GET /api/account/profile returns user without password_hash field
# ---------------------------------------------------------------------------

def test_ac3_profile_no_password_hash():
    _create_user('ac3prof@test.com', name='AC3 Profile User')
    c = app.test_client()
    _login(c, 'ac3prof@test.com')

    r = c.get('/api/account/profile')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()

    assert 'user' in data
    assert 'password_hash' not in data['user'], "password_hash must NOT be exposed in profile response"
    assert data['user']['email'] == 'ac3prof@test.com'
    assert data['user']['name'] == 'AC3 Profile User'
    print('AC-3 PASS: GET /api/account/profile returns user without password_hash')


# ---------------------------------------------------------------------------
# AC-4: POST /api/account/profile with valid name updates and returns updated user
# ---------------------------------------------------------------------------

def test_ac4_profile_update_name():
    uid = _create_user('ac4upd@test.com', name='Old Name')
    c = app.test_client()
    _login(c, 'ac4upd@test.com')

    r = c.post('/api/account/profile', data={'name': 'New Name', 'phone': '9999988888'})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert data.get('success') is True
    assert data['user']['name'] == 'New Name'
    assert 'password_hash' not in data['user']

    # Verify change persisted in DB
    conn = _db_conn()
    row = conn.execute("SELECT name, phone FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    assert row['name'] == 'New Name', "Name was not updated in DB"
    assert row['phone'] == '9999988888', "Phone was not updated in DB"
    print('AC-4 PASS: POST /api/account/profile updates name and phone in DB')


# ---------------------------------------------------------------------------
# AC-5: POST /api/account/profile with empty name -> 400
# ---------------------------------------------------------------------------

def test_ac5_profile_empty_name_rejected():
    _create_user('ac5empty@test.com', name='AC5 User')
    c = app.test_client()
    _login(c, 'ac5empty@test.com')

    r = c.post('/api/account/profile', data={'name': '  ', 'phone': ''})
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    data = r.get_json()
    assert 'error' in data
    print('AC-5 PASS: empty name in profile update returns 400')


# ---------------------------------------------------------------------------
# AC-6: POST /api/account/profile/delete-avatar clears avatar in DB
# ---------------------------------------------------------------------------

def test_ac6_delete_avatar():
    uid = _create_user('ac6avatar@test.com', name='AC6 Avatar User')
    # Manually set a fake avatar path in the DB (no real file needed for this test)
    conn = _db_conn()
    conn.execute("UPDATE users SET avatar = ? WHERE id = ?", ('uploads/avatars/fake.png', uid))
    conn.commit()
    conn.close()

    c = app.test_client()
    _login(c, 'ac6avatar@test.com')

    r = c.post('/api/account/profile/delete-avatar')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert data.get('success') is True

    # Verify avatar is NULL in DB
    conn = _db_conn()
    row = conn.execute("SELECT avatar FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    assert row['avatar'] is None, f"Expected avatar=NULL in DB, got {row['avatar']}"
    print('AC-6 PASS: delete-avatar clears avatar field in DB')


# ---------------------------------------------------------------------------
# AC-7: GET /api/account/addresses returns empty list initially
# ---------------------------------------------------------------------------

def test_ac7_addresses_empty_initially():
    _create_user('ac7addr@test.com', name='AC7 Addr User')
    c = app.test_client()
    _login(c, 'ac7addr@test.com')

    r = c.get('/api/account/addresses')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert 'addresses' in data
    assert data['addresses'] == [], f"Expected empty list, got {data['addresses']}"
    print('AC-7 PASS: GET /api/account/addresses returns empty list for new user')


# ---------------------------------------------------------------------------
# AC-8: POST /api/account/addresses/new with all fields -> 201 and address in list
# ---------------------------------------------------------------------------

def test_ac8_add_address_success():
    uid = _create_user('ac8newaddr@test.com', name='AC8 Addr User')
    c = app.test_client()
    _login(c, 'ac8newaddr@test.com')

    r = _add_address(c)
    assert r.status_code == 201, f"Expected 201, got {r.status_code}"
    data = r.get_json()
    assert data.get('success') is True
    assert 'addresses' in data
    assert len(data['addresses']) == 1

    saved = data['addresses'][0]
    assert saved['full_name'] == 'Ravi Kumar'
    assert saved['city'] == 'Mumbai'
    assert saved['pincode'] == '400001'

    # First address should be auto-set as default
    assert saved['is_default'] == 1

    # Verify in DB
    conn = _db_conn()
    row = conn.execute(
        "SELECT * FROM addresses WHERE user_id = ?", (uid,)
    ).fetchone()
    conn.close()
    assert row is not None, "Address should exist in DB"
    assert row['city'] == 'Mumbai'
    print('AC-8 PASS: new address created with 201, appears in list, first address is default')


# ---------------------------------------------------------------------------
# AC-9: POST /api/account/addresses/new with missing field -> 400
# ---------------------------------------------------------------------------

def test_ac9_add_address_missing_field():
    _create_user('ac9missingfield@test.com', name='AC9 Addr User')
    c = app.test_client()
    _login(c, 'ac9missingfield@test.com')

    # Missing pincode
    r = _add_address(c, overrides={'pincode': ''})
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    data = r.get_json()
    assert 'error' in data

    # Missing full_name
    r2 = _add_address(c, overrides={'full_name': ''})
    assert r2.status_code == 400, f"Expected 400 for missing full_name, got {r2.status_code}"
    print('AC-9 PASS: add address with missing fields returns 400')


# ---------------------------------------------------------------------------
# AC-10: PUT /api/account/addresses/<id> updates address
# ---------------------------------------------------------------------------

def test_ac10_update_address():
    uid = _create_user('ac10upd@test.com', name='AC10 Update User')
    c = app.test_client()
    _login(c, 'ac10upd@test.com')

    # Create an address first
    r_create = _add_address(c)
    assert r_create.status_code == 201
    addr_id = r_create.get_json()['addresses'][0]['id']

    # Update it
    r = c.put(f'/api/account/addresses/{addr_id}', json={
        'full_name': 'Updated Name',
        'phone': '8888877777',
        'address_line': '99 New Street',
        'city': 'Pune',
        'state': 'Maharashtra',
        'pincode': '411001',
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert data.get('success') is True

    # Verify change in DB
    conn = _db_conn()
    row = conn.execute("SELECT * FROM addresses WHERE id = ?", (addr_id,)).fetchone()
    conn.close()
    assert row['city'] == 'Pune', "City was not updated in DB"
    assert row['full_name'] == 'Updated Name', "full_name was not updated in DB"
    print('AC-10 PASS: PUT /api/account/addresses/<id> updates address in DB')


# ---------------------------------------------------------------------------
# AC-11: PUT /api/account/addresses/<id> by another user -> 403
# ---------------------------------------------------------------------------

def test_ac11_update_address_by_wrong_user():
    uid_owner = _create_user('ac11owner@test.com', name='AC11 Owner')
    _create_user('ac11thief@test.com', name='AC11 Thief')

    # Owner creates address
    c_owner = app.test_client()
    _login(c_owner, 'ac11owner@test.com')
    r_create = _add_address(c_owner)
    assert r_create.status_code == 201
    addr_id = r_create.get_json()['addresses'][0]['id']

    # Thief tries to update owner's address
    c_thief = app.test_client()
    _login(c_thief, 'ac11thief@test.com')
    r = c_thief.put(f'/api/account/addresses/{addr_id}', json={
        'full_name': 'Thief Name',
        'phone': '1111111111',
        'address_line': 'Thief Lane',
        'city': 'Delhi',
        'state': 'Delhi',
        'pincode': '110001',
    })
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    print('AC-11 PASS: updating another user\'s address returns 403')


# ---------------------------------------------------------------------------
# AC-12: POST /api/account/addresses/<id>/delete removes address
# ---------------------------------------------------------------------------

def test_ac12_delete_address():
    uid = _create_user('ac12del@test.com', name='AC12 Delete User')
    c = app.test_client()
    _login(c, 'ac12del@test.com')

    r_create = _add_address(c)
    assert r_create.status_code == 201
    addr_id = r_create.get_json()['addresses'][0]['id']

    r = c.post(f'/api/account/addresses/{addr_id}/delete')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert data.get('success') is True

    # Verify row is gone from DB
    conn = _db_conn()
    row = conn.execute("SELECT id FROM addresses WHERE id = ?", (addr_id,)).fetchone()
    conn.close()
    assert row is None, "Address should have been deleted from DB"
    print('AC-12 PASS: POST /api/account/addresses/<id>/delete removes row from DB')


# ---------------------------------------------------------------------------
# AC-13: POST /api/account/addresses/<id>/delete by another user -> 403
# ---------------------------------------------------------------------------

def test_ac13_delete_address_by_wrong_user():
    uid_owner = _create_user('ac13owner@test.com', name='AC13 Owner')
    _create_user('ac13thief@test.com', name='AC13 Thief')

    c_owner = app.test_client()
    _login(c_owner, 'ac13owner@test.com')
    r_create = _add_address(c_owner)
    assert r_create.status_code == 201
    addr_id = r_create.get_json()['addresses'][0]['id']

    c_thief = app.test_client()
    _login(c_thief, 'ac13thief@test.com')
    r = c_thief.post(f'/api/account/addresses/{addr_id}/delete')
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    print('AC-13 PASS: deleting another user\'s address returns 403')


# ---------------------------------------------------------------------------
# AC-14: POST /api/account/addresses/<id>/default sets is_default=1 and clears others
# ---------------------------------------------------------------------------

def test_ac14_set_default_address():
    uid = _create_user('ac14default@test.com', name='AC14 Default User')
    c = app.test_client()
    _login(c, 'ac14default@test.com')

    # Create two addresses
    r1 = _add_address(c, overrides={'city': 'Mumbai', 'pincode': '400001'})
    assert r1.status_code == 201
    addr1_id = r1.get_json()['addresses'][0]['id']

    r2 = _add_address(c, overrides={'city': 'Delhi', 'pincode': '110001'})
    assert r2.status_code == 201
    # addr2_id is the second one in the list
    addr2_id = r2.get_json()['addresses'][1]['id']

    # Set addr2 as default
    r = c.post(f'/api/account/addresses/{addr2_id}/default')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert data.get('success') is True

    # Verify in DB: addr2 is default, addr1 is not
    conn = _db_conn()
    row1 = conn.execute("SELECT is_default FROM addresses WHERE id = ?", (addr1_id,)).fetchone()
    row2 = conn.execute("SELECT is_default FROM addresses WHERE id = ?", (addr2_id,)).fetchone()
    conn.close()
    assert row2['is_default'] == 1, "addr2 should be marked as default"
    assert row1['is_default'] == 0, "addr1 should no longer be default"
    print('AC-14 PASS: set default address marks only the chosen address, clears others')


# ---------------------------------------------------------------------------
# AC-15: POST /api/account/addresses/<id>/default by another user -> 403
# ---------------------------------------------------------------------------

def test_ac15_set_default_address_by_wrong_user():
    uid_owner = _create_user('ac15owner@test.com', name='AC15 Owner')
    _create_user('ac15thief@test.com', name='AC15 Thief')

    c_owner = app.test_client()
    _login(c_owner, 'ac15owner@test.com')
    r_create = _add_address(c_owner)
    assert r_create.status_code == 201
    addr_id = r_create.get_json()['addresses'][0]['id']

    c_thief = app.test_client()
    _login(c_thief, 'ac15thief@test.com')
    r = c_thief.post(f'/api/account/addresses/{addr_id}/default')
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    print('AC-15 PASS: setting default on another user\'s address returns 403')


# ---------------------------------------------------------------------------
# AC-16: GET /api/account/settings returns is_google_only=False for password user
# ---------------------------------------------------------------------------

def test_ac16_settings_not_google_only():
    _create_user('ac16settings@test.com', name='AC16 Settings User')
    c = app.test_client()
    _login(c, 'ac16settings@test.com')

    r = c.get('/api/account/settings')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert 'user' in data
    assert 'is_google_only' in data
    assert data['is_google_only'] is False, \
        f"Expected is_google_only=False for password user, got {data['is_google_only']}"
    assert 'password_hash' not in data['user']
    print('AC-16 PASS: settings returns is_google_only=False for normal password user')


# ---------------------------------------------------------------------------
# AC-17: POST /api/account/settings/password with wrong current password -> 400
# ---------------------------------------------------------------------------

def test_ac17_wrong_current_password():
    _create_user('ac17wrongpw@test.com', name='AC17 Wrong PW User', password='correctpass1')
    c = app.test_client()
    _login(c, 'ac17wrongpw@test.com', password='correctpass1')

    r = c.post('/api/account/settings/password', json={
        'current_password': 'wrongpassword',
        'new_password': 'newpassword1',
        'confirm_password': 'newpassword1',
    })
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    data = r.get_json()
    assert 'error' in data
    assert 'incorrect' in data['error'].lower() or 'wrong' in data['error'].lower() \
        or 'invalid' in data['error'].lower() or 'password' in data['error'].lower()
    print('AC-17 PASS: wrong current password returns 400 with error message')


# ---------------------------------------------------------------------------
# AC-18: POST /api/account/settings/password with non-matching new passwords -> 400
# ---------------------------------------------------------------------------

def test_ac18_mismatched_new_passwords():
    _create_user('ac18mismatch@test.com', name='AC18 Mismatch User', password='currentpass1')
    c = app.test_client()
    _login(c, 'ac18mismatch@test.com', password='currentpass1')

    r = c.post('/api/account/settings/password', json={
        'current_password': 'currentpass1',
        'new_password': 'newpassword1',
        'confirm_password': 'differentpassword1',
    })
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    data = r.get_json()
    assert 'error' in data
    assert 'match' in data['error'].lower()
    print('AC-18 PASS: mismatched new passwords return 400')


# ---------------------------------------------------------------------------
# AC-19: POST /api/account/settings/password with too-short new password -> 400
# ---------------------------------------------------------------------------

def test_ac19_too_short_new_password():
    _create_user('ac19short@test.com', name='AC19 Short PW User', password='validpass1')
    c = app.test_client()
    _login(c, 'ac19short@test.com', password='validpass1')

    r = c.post('/api/account/settings/password', json={
        'current_password': 'validpass1',
        'new_password': 'abc',
        'confirm_password': 'abc',
    })
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    data = r.get_json()
    assert 'error' in data
    assert '8' in data['error'] or 'characters' in data['error'].lower() or 'short' in data['error'].lower()
    print('AC-19 PASS: too-short new password returns 400 mentioning minimum length')


# ---------------------------------------------------------------------------
# AC-20: POST /api/account/settings/password happy path: changes pw, can login with new pw
# ---------------------------------------------------------------------------

def test_ac20_password_change_happy_path():
    uid = _create_user('ac20change@test.com', name='AC20 PW Change User', password='oldpassword1')
    c = app.test_client()
    _login(c, 'ac20change@test.com', password='oldpassword1')

    r = c.post('/api/account/settings/password', json={
        'current_password': 'oldpassword1',
        'new_password': 'newpassword2',
        'confirm_password': 'newpassword2',
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert data.get('success') is True

    # Old password should now fail login
    c2 = app.test_client()
    r_old = c2.post('/api/auth/login', json={'email': 'ac20change@test.com', 'password': 'oldpassword1'})
    assert r_old.status_code == 401, "Old password should no longer work after change"

    # New password should work
    r_new = c2.post('/api/auth/login', json={'email': 'ac20change@test.com', 'password': 'newpassword2'})
    assert r_new.status_code == 200, "New password should allow login after change"
    print('AC-20 PASS: password changed successfully; old pw fails, new pw works')


# ---------------------------------------------------------------------------
# AC-21: POST /api/account/settings/notifications saves notify_email preference
# ---------------------------------------------------------------------------

def test_ac21_notifications_save_preference():
    uid = _create_user('ac21notif@test.com', name='AC21 Notif User')
    c = app.test_client()
    _login(c, 'ac21notif@test.com')

    # Turn notifications off
    r = c.post('/api/account/settings/notifications', json={'notify_email': False})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert data.get('success') is True

    # Verify in DB: notify_email should be 0
    conn = _db_conn()
    row = conn.execute("SELECT notify_email FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    assert row['notify_email'] == 0, f"Expected notify_email=0 in DB, got {row['notify_email']}"

    # Turn notifications back on
    r2 = c.post('/api/account/settings/notifications', json={'notify_email': True})
    assert r2.status_code == 200

    conn = _db_conn()
    row2 = conn.execute("SELECT notify_email FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    assert row2['notify_email'] == 1, f"Expected notify_email=1 in DB, got {row2['notify_email']}"
    print('AC-21 PASS: notification preference is saved and persisted in DB')


# ---------------------------------------------------------------------------
# AC-22: Google-only user (no password_hash) -> POST /api/account/settings/password -> 400
# ---------------------------------------------------------------------------

def test_ac22_google_only_user_cannot_change_password():
    # Google-only user has empty password_hash
    uid = _create_google_only_user('ac22google@test.com', name='AC22 Google User')

    # Log in by patching the DB directly — Google users cannot log in via the password route,
    # so we use a workaround: set a temp password, log in, then remove it.
    from werkzeug.security import generate_password_hash
    conn = _db_conn()
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                 (generate_password_hash('temppass123'), uid))
    conn.commit()
    conn.close()

    c = app.test_client()
    _login(c, 'ac22google@test.com', password='temppass123')

    # Now clear the password_hash to simulate Google-only state
    conn = _db_conn()
    conn.execute("UPDATE users SET password_hash = '' WHERE id = ?", (uid,))
    conn.commit()
    conn.close()

    r = c.post('/api/account/settings/password', json={
        'current_password': 'temppass123',
        'new_password': 'newpassword1',
        'confirm_password': 'newpassword1',
    })
    assert r.status_code == 400, f"Expected 400 for Google-only user, got {r.status_code}"
    data = r.get_json()
    assert 'error' in data
    assert 'google' in data['error'].lower() or 'password' in data['error'].lower()
    print('AC-22 PASS: Google-only user attempting password change gets 400')


# ---------------------------------------------------------------------------
# AC-23: Privacy — user A cannot access user B's addresses (403)
# ---------------------------------------------------------------------------

def test_ac23_privacy_cannot_access_other_users_address():
    _create_user('ac23owner@test.com', name='AC23 Owner')
    _create_user('ac23other@test.com', name='AC23 Other')

    # Owner creates an address
    c_owner = app.test_client()
    _login(c_owner, 'ac23owner@test.com')
    r_create = _add_address(c_owner)
    assert r_create.status_code == 201
    addr_id = r_create.get_json()['addresses'][0]['id']

    # Other user tries to update, delete, and set-default on the owner's address
    c_other = app.test_client()
    _login(c_other, 'ac23other@test.com')

    valid_address_payload = {
        'full_name': 'Intruder', 'phone': '0000000000',
        'address_line': 'Evil St', 'city': 'Badcity',
        'state': 'Evilstate', 'pincode': '000000',
    }

    r_update = c_other.put(f'/api/account/addresses/{addr_id}', json=valid_address_payload)
    assert r_update.status_code == 403, f"PUT expected 403, got {r_update.status_code}"

    r_delete = c_other.post(f'/api/account/addresses/{addr_id}/delete')
    assert r_delete.status_code == 403, f"DELETE expected 403, got {r_delete.status_code}"

    r_default = c_other.post(f'/api/account/addresses/{addr_id}/default')
    assert r_default.status_code == 403, f"DEFAULT expected 403, got {r_default.status_code}"

    # Verify the address was not modified in DB
    conn = _db_conn()
    row = conn.execute("SELECT full_name FROM addresses WHERE id = ?", (addr_id,)).fetchone()
    conn.close()
    assert row is not None, "Address should still exist after failed intrusion attempts"
    assert row['full_name'] == 'Ravi Kumar', \
        f"Address was modified by another user! Got {row['full_name']}"
    print('AC-23 PASS: another user cannot update/delete/default someone else\'s address (403)')


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_ac1_unauthenticated_access,
        test_ac2_dashboard_returns_summary,
        test_ac3_profile_no_password_hash,
        test_ac4_profile_update_name,
        test_ac5_profile_empty_name_rejected,
        test_ac6_delete_avatar,
        test_ac7_addresses_empty_initially,
        test_ac8_add_address_success,
        test_ac9_add_address_missing_field,
        test_ac10_update_address,
        test_ac11_update_address_by_wrong_user,
        test_ac12_delete_address,
        test_ac13_delete_address_by_wrong_user,
        test_ac14_set_default_address,
        test_ac15_set_default_address_by_wrong_user,
        test_ac16_settings_not_google_only,
        test_ac17_wrong_current_password,
        test_ac18_mismatched_new_passwords,
        test_ac19_too_short_new_password,
        test_ac20_password_change_happy_path,
        test_ac21_notifications_save_preference,
        test_ac22_google_only_user_cannot_change_password,
        test_ac23_privacy_cannot_access_other_users_address,
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
