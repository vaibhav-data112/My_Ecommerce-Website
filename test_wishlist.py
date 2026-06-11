"""
Acceptance-criteria tests for feature 12 — Wishlist (Saved Products).
Run with:  python test_wishlist.py
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
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id


def _create_product(name='Cumin Seeds 100g', price=75.0, stock=50):
    conn = _db_conn()
    cur = conn.execute(
        "INSERT INTO products (name, description, price, stock, category) VALUES (?, ?, ?, ?, ?)",
        (name, 'Test product description', price, stock, 'Whole Spices')
    )
    product_id = cur.lastrowid
    conn.commit()
    conn.close()
    return product_id


def _login(client, email, password='password123'):
    return client.post(
        '/api/auth/login',
        json={'email': email, 'password': password}
    )


def _wishlist_rows_in_db(user_id, product_id):
    conn = _db_conn()
    row = conn.execute(
        "SELECT COUNT(*) FROM wishlist_items WHERE user_id = ? AND product_id = ?",
        (user_id, product_id)
    ).fetchone()
    conn.close()
    return int(row[0])


# ---------------------------------------------------------------------------
# AC-1: Unauthenticated GET /api/wishlist -> 401
# ---------------------------------------------------------------------------

def test_ac1_unauthenticated_get_wishlist():
    c = app.test_client()
    r = c.get('/api/wishlist')
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    data = r.get_json()
    assert data is not None
    assert 'error' in data or 'login_required' in data
    print('AC-1 PASS: unauthenticated GET /api/wishlist returns 401')


# ---------------------------------------------------------------------------
# AC-2: Unauthenticated POST /api/wishlist/toggle -> 401
# ---------------------------------------------------------------------------

def test_ac2_unauthenticated_toggle():
    c = app.test_client()
    r = c.post('/api/wishlist/toggle', json={'product_id': 1})
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print('AC-2 PASS: unauthenticated POST /api/wishlist/toggle returns 401')


# ---------------------------------------------------------------------------
# AC-3: Authenticated user with empty wishlist gets empty list, count=0
# ---------------------------------------------------------------------------

def test_ac3_empty_wishlist():
    _create_user('ac3@test.com', name='AC3 User')
    c = app.test_client()
    _login(c, 'ac3@test.com')
    r = c.get('/api/wishlist')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert 'items' in data
    assert 'wishlist_count' in data
    assert data['items'] == [], f"Expected empty list, got {data['items']}"
    assert data['wishlist_count'] == 0, f"Expected 0, got {data['wishlist_count']}"
    print('AC-3 PASS: empty wishlist returns empty items list and count=0')


# ---------------------------------------------------------------------------
# AC-4: Toggle adds a product to wishlist (in_wishlist=True, count incremented)
# ---------------------------------------------------------------------------

def test_ac4_toggle_adds_product():
    uid = _create_user('ac4@test.com', name='AC4 User')
    pid = _create_product(name='AC4 Turmeric')
    c = app.test_client()
    _login(c, 'ac4@test.com')

    r = c.post('/api/wishlist/toggle', json={'product_id': pid})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert data.get('success') is True
    assert data.get('in_wishlist') is True
    assert data.get('wishlist_count') == 1
    assert 'Added' in data.get('message', '')

    # Verify the row actually exists in the DB
    assert _wishlist_rows_in_db(uid, pid) == 1, "Expected 1 wishlist row in DB"
    print('AC-4 PASS: toggle adds product to wishlist, in_wishlist=True, count=1')


# ---------------------------------------------------------------------------
# AC-5: Toggle same product again removes it (in_wishlist=False, count back to 0)
# ---------------------------------------------------------------------------

def test_ac5_toggle_removes_product():
    uid = _create_user('ac5@test.com', name='AC5 User')
    pid = _create_product(name='AC5 Black Pepper')
    c = app.test_client()
    _login(c, 'ac5@test.com')

    # First toggle: add
    c.post('/api/wishlist/toggle', json={'product_id': pid})

    # Second toggle: remove
    r = c.post('/api/wishlist/toggle', json={'product_id': pid})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert data.get('success') is True
    assert data.get('in_wishlist') is False
    assert data.get('wishlist_count') == 0
    assert 'Removed' in data.get('message', '')

    # Verify the row is gone from the DB
    assert _wishlist_rows_in_db(uid, pid) == 0, "Expected 0 wishlist rows after removal"
    print('AC-5 PASS: second toggle removes product from wishlist, in_wishlist=False, count=0')


# ---------------------------------------------------------------------------
# AC-6: Toggling same product twice does NOT create duplicate (UNIQUE constraint)
# ---------------------------------------------------------------------------

def test_ac6_no_duplicate_rows():
    uid = _create_user('ac6@test.com', name='AC6 User')
    pid = _create_product(name='AC6 Cardamom')
    c = app.test_client()
    _login(c, 'ac6@test.com')

    # Add via toggle (first add)
    c.post('/api/wishlist/toggle', json={'product_id': pid})

    # Try to add directly a second time via db helper — INSERT OR IGNORE must not create a second row
    import db
    db.add_to_wishlist(uid, pid)

    rows = _wishlist_rows_in_db(uid, pid)
    assert rows == 1, f"Expected exactly 1 row, found {rows} — duplicate was created!"
    print('AC-6 PASS: INSERT OR IGNORE prevents duplicate wishlist rows')


# ---------------------------------------------------------------------------
# AC-7: GET /api/wishlist returns correct items after adding products
# ---------------------------------------------------------------------------

def test_ac7_get_wishlist_returns_items():
    _create_user('ac7@test.com', name='AC7 User')
    pid1 = _create_product(name='AC7 Garam Masala')
    pid2 = _create_product(name='AC7 Coriander Powder')
    c = app.test_client()
    _login(c, 'ac7@test.com')

    c.post('/api/wishlist/toggle', json={'product_id': pid1})
    c.post('/api/wishlist/toggle', json={'product_id': pid2})

    r = c.get('/api/wishlist')
    assert r.status_code == 200
    data = r.get_json()
    assert 'items' in data
    assert data['wishlist_count'] == 2

    item_ids = [item['id'] for item in data['items']]
    assert pid1 in item_ids, f"pid1={pid1} not found in returned items {item_ids}"
    assert pid2 in item_ids, f"pid2={pid2} not found in returned items {item_ids}"
    print('AC-7 PASS: GET /api/wishlist returns all added products with correct count')


# ---------------------------------------------------------------------------
# AC-8: POST /api/wishlist/add-to-cart adds item to cart; cart_count increments
# ---------------------------------------------------------------------------

def test_ac8_add_to_cart_from_wishlist():
    uid = _create_user('ac8@test.com', name='AC8 User')
    pid = _create_product(name='AC8 Himalayan Salt', stock=20)
    c = app.test_client()
    _login(c, 'ac8@test.com')

    # Add to wishlist first (realistic flow)
    c.post('/api/wishlist/toggle', json={'product_id': pid})

    r = c.post('/api/wishlist/add-to-cart', json={'product_id': pid})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert data.get('success') is True
    assert data.get('cart_count') >= 1

    # Verify cart row in DB
    conn = _db_conn()
    cart_row = conn.execute(
        "SELECT quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
        (uid, pid)
    ).fetchone()
    conn.close()
    assert cart_row is not None, "Expected a cart_items row after add-to-cart"
    assert cart_row['quantity'] >= 1
    print('AC-8 PASS: add-to-cart from wishlist creates cart row, cart_count >= 1')


# ---------------------------------------------------------------------------
# AC-9: POST /api/wishlist/add-to-cart with missing product_id -> 400
# ---------------------------------------------------------------------------

def test_ac9_add_to_cart_missing_product_id():
    _create_user('ac9@test.com', name='AC9 User')
    c = app.test_client()
    _login(c, 'ac9@test.com')

    r = c.post('/api/wishlist/add-to-cart', json={})
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    data = r.get_json()
    assert 'error' in data
    print('AC-9 PASS: add-to-cart with missing product_id returns 400')


# ---------------------------------------------------------------------------
# AC-10: POST /api/wishlist/toggle with missing product_id -> 400
# ---------------------------------------------------------------------------

def test_ac10_toggle_missing_product_id():
    _create_user('ac10@test.com', name='AC10 User')
    c = app.test_client()
    _login(c, 'ac10@test.com')

    r = c.post('/api/wishlist/toggle', json={})
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    data = r.get_json()
    assert 'error' in data
    print('AC-10 PASS: toggle with missing product_id returns 400')


# ---------------------------------------------------------------------------
# AC-11: Privacy — user A cannot see user B's wishlist items
# ---------------------------------------------------------------------------

def test_ac11_privacy_separate_wishlists():
    _create_user('ac11a@test.com', name='AC11 Alice')
    _create_user('ac11b@test.com', name='AC11 Bob')
    pid_a = _create_product(name='AC11 Alice Only Product')
    pid_b = _create_product(name='AC11 Bob Only Product')

    # Alice adds her product
    c_a = app.test_client()
    _login(c_a, 'ac11a@test.com')
    c_a.post('/api/wishlist/toggle', json={'product_id': pid_a})

    # Bob adds his product
    c_b = app.test_client()
    _login(c_b, 'ac11b@test.com')
    c_b.post('/api/wishlist/toggle', json={'product_id': pid_b})

    # Alice fetches her wishlist — must only see pid_a, NOT pid_b
    r_a = c_a.get('/api/wishlist')
    assert r_a.status_code == 200
    data_a = r_a.get_json()
    item_ids_a = [item['id'] for item in data_a['items']]
    assert pid_a in item_ids_a, "Alice should see her own product"
    assert pid_b not in item_ids_a, "Alice should NOT see Bob's product"
    assert data_a['wishlist_count'] == 1

    # Bob fetches his wishlist — must only see pid_b, NOT pid_a
    r_b = c_b.get('/api/wishlist')
    assert r_b.status_code == 200
    data_b = r_b.get_json()
    item_ids_b = [item['id'] for item in data_b['items']]
    assert pid_b in item_ids_b, "Bob should see his own product"
    assert pid_a not in item_ids_b, "Bob should NOT see Alice's product"
    assert data_b['wishlist_count'] == 1

    print('AC-11 PASS: each user sees only their own wishlist (privacy enforced)')


# ---------------------------------------------------------------------------
# AC-12: Deleted product is gracefully absent from wishlist (no crash)
# ---------------------------------------------------------------------------

def test_ac12_deleted_product_absent_from_wishlist():
    uid = _create_user('ac12@test.com', name='AC12 User')
    pid = _create_product(name='AC12 Soon Deleted Product')
    c = app.test_client()
    _login(c, 'ac12@test.com')

    # Add product to wishlist
    c.post('/api/wishlist/toggle', json={'product_id': pid})
    assert _wishlist_rows_in_db(uid, pid) == 1

    # Admin hard-deletes the product — remove wishlist ref first (FK), then product
    conn = _db_conn()
    conn.execute("DELETE FROM wishlist_items WHERE product_id = ?", (pid,))
    conn.execute("DELETE FROM products WHERE id = ?", (pid,))
    conn.commit()
    conn.close()

    # GET /api/wishlist must not crash and must not include the deleted product
    r = c.get('/api/wishlist')
    assert r.status_code == 200, f"Expected 200 (no crash after product delete), got {r.status_code}"
    data = r.get_json()
    item_ids = [item['id'] for item in data.get('items', [])]
    assert pid not in item_ids, "Deleted product must not appear in wishlist response"
    print('AC-12 PASS: deleted product is absent from wishlist without server crash')


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_ac1_unauthenticated_get_wishlist,
        test_ac2_unauthenticated_toggle,
        test_ac3_empty_wishlist,
        test_ac4_toggle_adds_product,
        test_ac5_toggle_removes_product,
        test_ac6_no_duplicate_rows,
        test_ac7_get_wishlist_returns_items,
        test_ac8_add_to_cart_from_wishlist,
        test_ac9_add_to_cart_missing_product_id,
        test_ac10_toggle_missing_product_id,
        test_ac11_privacy_separate_wishlists,
        test_ac12_deleted_product_absent_from_wishlist,
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
