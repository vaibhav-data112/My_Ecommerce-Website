"""
Acceptance-criteria tests for feature 10 — Reviews & Ratings.
Run with:  python test_reviews_ratings.py
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


def _create_order(user_id, status='paid', total=100.0):
    conn = _db_conn()
    cur = conn.execute(
        """INSERT INTO orders
           (user_id, status, subtotal, shipping_fee, total,
            shipping_name, shipping_phone, shipping_address)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, status, 60.0, 40.0, total,
         'Test User', '9876543210', '123 Test Street')
    )
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id


def _create_order_item(order_id, product_id=1, price=50.0, qty=1):
    conn = _db_conn()
    conn.execute(
        """INSERT INTO order_items
           (order_id, product_id, product_name, unit_price, quantity, line_total)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (order_id, product_id, 'Test Product', price, qty, round(price * qty, 2))
    )
    conn.commit()
    conn.close()


def _login(client, email):
    return client.post('/login', data={'email': email, 'password': 'password123'},
                       follow_redirects=True)


# ── AC-1: Buyer can leave a review ───────────────────────────────────────────
def test_ac1_buyer_can_review():
    user_id = _create_user('ac1rv@test.com', 'Alice')
    order_id = _create_order(user_id, status='paid')
    _create_order_item(order_id, product_id=1)

    c = app.test_client()
    _login(c, 'ac1rv@test.com')
    r = c.post('/products/1/review',
               data={'rating': '5', 'comment': 'Excellent product!'},
               follow_redirects=True)
    assert r.status_code == 200

    conn = _db_conn()
    row = conn.execute("SELECT * FROM reviews WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    assert row is not None
    assert row['rating'] == 5
    assert row['comment'] == 'Excellent product!'
    print('AC-1 PASS: verified buyer can leave a review')


# ── AC-2: Non-buyer cannot review ────────────────────────────────────────────
def test_ac2_nonbuyer_cannot_review():
    user_id = _create_user('ac2rv@test.com')
    # No order created — user is not a buyer

    c = app.test_client()
    _login(c, 'ac2rv@test.com')
    r = c.post('/products/1/review',
               data={'rating': '4', 'comment': 'Nice!'},
               follow_redirects=True)
    assert r.status_code == 200

    conn = _db_conn()
    row = conn.execute("SELECT * FROM reviews WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    assert row is None
    print('AC-2 PASS: non-buyer cannot review')


# ── AC-3: Average rating shown on product page ───────────────────────────────
def test_ac3_average_rating():
    user_id = _create_user('ac3rv@test.com')
    order_id = _create_order(user_id, status='paid')
    _create_order_item(order_id, product_id=1)

    c = app.test_client()
    _login(c, 'ac3rv@test.com')
    c.post('/products/1/review', data={'rating': '4'}, follow_redirects=True)

    r = c.get('/products/1')
    assert r.status_code == 200
    assert b'4' in r.data
    print('AC-3 PASS: average rating shown on product page')


# ── AC-4: Reviews listed with name, stars, comment, date ─────────────────────
def test_ac4_reviews_listed():
    user_id = _create_user('ac4rv@test.com', 'Bobby')
    order_id = _create_order(user_id, status='paid')
    _create_order_item(order_id, product_id=1)

    c = app.test_client()
    _login(c, 'ac4rv@test.com')
    c.post('/products/1/review',
           data={'rating': '3', 'comment': 'Average quality item'},
           follow_redirects=True)

    r = c.get('/products/1')
    assert r.status_code == 200
    assert b'Average quality item' in r.data
    assert b'Bobby' in r.data
    print('AC-4 PASS: review listed with reviewer name and comment')


# ── AC-5: One review per user per product ────────────────────────────────────
def test_ac5_one_review_per_user():
    user_id = _create_user('ac5rv@test.com')
    order_id = _create_order(user_id, status='paid')
    _create_order_item(order_id, product_id=1)

    c = app.test_client()
    _login(c, 'ac5rv@test.com')
    c.post('/products/1/review', data={'rating': '5', 'comment': 'First'}, follow_redirects=True)
    c.post('/products/1/review', data={'rating': '1', 'comment': 'Second attempt'}, follow_redirects=True)

    conn = _db_conn()
    count = conn.execute("SELECT COUNT(*) FROM reviews WHERE user_id = ?", (user_id,)).fetchone()[0]
    conn.close()
    assert count == 1
    print('AC-5 PASS: only one review per user per product')


# ── AC-6: Edit own review ─────────────────────────────────────────────────────
def test_ac6_edit_review():
    user_id = _create_user('ac6rv@test.com')
    order_id = _create_order(user_id, status='paid')
    _create_order_item(order_id, product_id=1)

    c = app.test_client()
    _login(c, 'ac6rv@test.com')
    c.post('/products/1/review', data={'rating': '3', 'comment': 'OK product'}, follow_redirects=True)

    conn = _db_conn()
    review = conn.execute("SELECT id FROM reviews WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    review_id = review['id']

    r = c.post(f'/reviews/{review_id}/edit',
               data={'rating': '5', 'comment': 'Actually great!'},
               follow_redirects=True)
    assert r.status_code == 200

    conn = _db_conn()
    updated = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
    conn.close()
    assert updated['rating'] == 5
    assert updated['comment'] == 'Actually great!'
    print('AC-6 PASS: user can edit own review')


# ── AC-7: Delete own review ───────────────────────────────────────────────────
def test_ac7_delete_review():
    user_id = _create_user('ac7rv@test.com')
    order_id = _create_order(user_id, status='paid')
    _create_order_item(order_id, product_id=1)

    c = app.test_client()
    _login(c, 'ac7rv@test.com')
    c.post('/products/1/review', data={'rating': '2'}, follow_redirects=True)

    conn = _db_conn()
    review = conn.execute("SELECT id FROM reviews WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    review_id = review['id']

    r = c.post(f'/reviews/{review_id}/delete', follow_redirects=True)
    assert r.status_code == 200

    conn = _db_conn()
    deleted = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
    conn.close()
    assert deleted is None
    print('AC-7 PASS: user can delete own review')


# ── AC-8: Cannot edit or delete another user's review ────────────────────────
def test_ac8_cannot_edit_others_review():
    user_a = _create_user('ac8arv@test.com', 'UserA')
    user_b = _create_user('ac8brv@test.com', 'UserB')
    order_id = _create_order(user_a, status='paid')
    _create_order_item(order_id, product_id=1)

    c = app.test_client()
    _login(c, 'ac8arv@test.com')
    c.post('/products/1/review', data={'rating': '5', 'comment': 'A wrote this'}, follow_redirects=True)

    conn = _db_conn()
    review = conn.execute("SELECT id FROM reviews WHERE user_id = ?", (user_a,)).fetchone()
    conn.close()
    review_id = review['id']

    _login(c, 'ac8brv@test.com')
    c.post(f'/reviews/{review_id}/edit',
           data={'rating': '1', 'comment': 'B tampered'},
           follow_redirects=True)

    conn = _db_conn()
    row = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
    conn.close()
    assert row['rating'] == 5
    assert row['comment'] == 'A wrote this'
    print('AC-8 PASS: user B cannot edit user A\'s review')


# ── AC-9: Invalid rating rejected ────────────────────────────────────────────
def test_ac9_invalid_rating():
    user_id = _create_user('ac9rv@test.com')
    order_id = _create_order(user_id, status='paid')
    _create_order_item(order_id, product_id=1)

    c = app.test_client()
    _login(c, 'ac9rv@test.com')

    c.post('/products/1/review', data={'rating': '6', 'comment': 'Out of range'}, follow_redirects=True)
    conn = _db_conn()
    row = conn.execute("SELECT * FROM reviews WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    assert row is None

    c.post('/products/1/review', data={'comment': 'No rating at all'}, follow_redirects=True)
    conn = _db_conn()
    row = conn.execute("SELECT * FROM reviews WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    assert row is None
    print('AC-9 PASS: invalid ratings are rejected')


# ── AC-10: Login required to review, public can read ─────────────────────────
def test_ac10_login_required():
    c = app.test_client()
    r = c.post('/products/1/review', data={'rating': '5'}, follow_redirects=False)
    assert r.status_code == 302
    assert 'login' in r.headers.get('Location', '').lower()

    r = c.get('/products/1')
    assert r.status_code == 200
    print('AC-10 PASS: login required to review; product page readable without login')


# ── AC-11: No reviews shows friendly message ─────────────────────────────────
def test_ac11_no_reviews_state():
    conn = _db_conn()
    cur = conn.execute(
        "INSERT INTO products (name, description, price, stock, category) VALUES (?, ?, ?, ?, ?)",
        ('Brand New Item', 'A fresh product', 9.99, 10, 'Other')
    )
    new_product_id = cur.lastrowid
    conn.commit()
    conn.close()

    c = app.test_client()
    r = c.get(f'/products/{new_product_id}')
    assert r.status_code == 200
    assert b'No reviews' in r.data or b'no reviews' in r.data.lower()
    print('AC-11 PASS: product with no reviews shows friendly message')


if __name__ == '__main__':
    tests = [
        test_ac1_buyer_can_review,
        test_ac2_nonbuyer_cannot_review,
        test_ac3_average_rating,
        test_ac4_reviews_listed,
        test_ac5_one_review_per_user,
        test_ac6_edit_review,
        test_ac7_delete_review,
        test_ac8_cannot_edit_others_review,
        test_ac9_invalid_rating,
        test_ac10_login_required,
        test_ac11_no_reviews_state,
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
