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


def _create_product(name='Review Spice', price=100.0, stock=50):
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


def _place_order_and_pay(client, product_id):
    client.post('/api/cart/add', json={'product_id': product_id, 'quantity': 1})
    r = client.post('/api/checkout', json={
        'shipping_name':    'Test Customer',
        'shipping_phone':   '9876543210',
        'shipping_address': '123 Test St, Mumbai',
    })
    order_id = r.get_json().get('order_id')
    conn = _db_conn()
    conn.execute("UPDATE orders SET status='paid' WHERE id=?", (order_id,))
    conn.commit()
    conn.close()
    return order_id


# ---------------------------------------------------------------------------
# AC-1: Unauthenticated POST /api/products/<id>/review -> 401
# ---------------------------------------------------------------------------

def test_ac1_unauthenticated_review():
    c = app.test_client()
    r = c.post('/api/products/1/review', json={'rating': 5, 'comment': 'Great!'})
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print('AC-1 PASS: unauthenticated review returns 401')


# ---------------------------------------------------------------------------
# AC-2: User who hasn't purchased cannot review (403)
# ---------------------------------------------------------------------------

def test_ac2_non_buyer_cannot_review():
    _create_user('rev2@test.com')
    pid = _create_product('Rev2 Spice')
    c = app.test_client()
    _login(c, 'rev2@test.com')

    r = c.post(f'/api/products/{pid}/review', json={'rating': 4, 'comment': 'Nice!'})
    assert r.status_code == 403, f"Expected 403 (not a buyer), got {r.status_code}"
    data = r.get_json()
    assert 'error' in data
    print('AC-2 PASS: non-buyer cannot review (403 returned)')


# ---------------------------------------------------------------------------
# AC-3: Verified buyer can submit a review
# ---------------------------------------------------------------------------

def test_ac3_buyer_can_review():
    _create_user('rev3@test.com')
    pid = _create_product('Rev3 Spice')
    c = app.test_client()
    _login(c, 'rev3@test.com')
    _place_order_and_pay(c, pid)

    r = c.post(f'/api/products/{pid}/review', json={'rating': 5, 'comment': 'Excellent spice!'})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.get_json()}"
    assert r.get_json().get('success') is True
    print('AC-3 PASS: verified buyer can submit a review')


# ---------------------------------------------------------------------------
# AC-4: Review appears in product detail response
# ---------------------------------------------------------------------------

def test_ac4_review_in_product_detail():
    _create_user('rev4@test.com')
    pid = _create_product('Rev4 Spice')
    c = app.test_client()
    _login(c, 'rev4@test.com')
    _place_order_and_pay(c, pid)
    c.post(f'/api/products/{pid}/review', json={'rating': 4, 'comment': 'Very aromatic!'})

    r = c.get(f'/api/products/{pid}')
    data = r.get_json()
    assert len(data['reviews']) > 0
    assert data['review_count'] >= 1
    assert any(rv['comment'] == 'Very aromatic!' for rv in data['reviews'])
    print('AC-4 PASS: review appears in product detail response')


# ---------------------------------------------------------------------------
# AC-5: Rating out of range (0 or 6) returns 400
# ---------------------------------------------------------------------------

def test_ac5_invalid_rating():
    _create_user('rev5@test.com')
    pid = _create_product('Rev5 Spice')
    c = app.test_client()
    _login(c, 'rev5@test.com')
    _place_order_and_pay(c, pid)

    r0 = c.post(f'/api/products/{pid}/review', json={'rating': 0})
    assert r0.status_code == 400, f"Expected 400 for rating=0, got {r0.status_code}"

    r6 = c.post(f'/api/products/{pid}/review', json={'rating': 6})
    assert r6.status_code == 400, f"Expected 400 for rating=6, got {r6.status_code}"
    print('AC-5 PASS: rating=0 and rating=6 both return 400')


# ---------------------------------------------------------------------------
# AC-6: User cannot review the same product twice (409)
# ---------------------------------------------------------------------------

def test_ac6_duplicate_review_blocked():
    _create_user('rev6@test.com')
    pid = _create_product('Rev6 Spice')
    c = app.test_client()
    _login(c, 'rev6@test.com')
    _place_order_and_pay(c, pid)

    c.post(f'/api/products/{pid}/review', json={'rating': 5, 'comment': 'First review'})
    r2 = c.post(f'/api/products/{pid}/review', json={'rating': 3, 'comment': 'Second review'})
    assert r2.status_code == 409, f"Expected 409 for duplicate review, got {r2.status_code}"
    print('AC-6 PASS: duplicate review returns 409')


# ---------------------------------------------------------------------------
# AC-7: Average rating is calculated correctly
# ---------------------------------------------------------------------------

def test_ac7_average_rating():
    _create_user('rev7a@test.com', name='Rev7 Alice')
    _create_user('rev7b@test.com', name='Rev7 Bob')
    pid = _create_product('Rev7 Spice')

    c_a = app.test_client()
    _login(c_a, 'rev7a@test.com')
    _place_order_and_pay(c_a, pid)
    c_a.post(f'/api/products/{pid}/review', json={'rating': 4})

    c_b = app.test_client()
    _login(c_b, 'rev7b@test.com')
    _place_order_and_pay(c_b, pid)
    c_b.post(f'/api/products/{pid}/review', json={'rating': 2})

    c = app.test_client()
    r = c.get(f'/api/products/{pid}')
    data = r.get_json()
    assert data['review_count'] == 2
    assert abs(data['avg_rating'] - 3.0) < 0.01, \
        f"Expected avg=3.0 for ratings [4,2], got {data['avg_rating']}"
    print('AC-7 PASS: average rating calculated correctly (avg of 4 and 2 = 3.0)')


# ---------------------------------------------------------------------------
# AC-8: Edit review changes rating and comment
# ---------------------------------------------------------------------------

def test_ac8_edit_review():
    _create_user('rev8@test.com')
    pid = _create_product('Rev8 Spice')
    c = app.test_client()
    _login(c, 'rev8@test.com')
    _place_order_and_pay(c, pid)
    c.post(f'/api/products/{pid}/review', json={'rating': 2, 'comment': 'Not great'})

    conn = _db_conn()
    review = conn.execute("SELECT id FROM reviews WHERE comment='Not great'").fetchone()
    conn.close()
    review_id = review['id']

    r = c.post(f'/api/reviews/{review_id}/edit', json={'rating': 5, 'comment': 'Changed my mind!'})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.get_json().get('success') is True

    conn = _db_conn()
    updated = conn.execute("SELECT rating, comment FROM reviews WHERE id=?", (review_id,)).fetchone()
    conn.close()
    assert updated['rating'] == 5
    assert updated['comment'] == 'Changed my mind!'
    print('AC-8 PASS: edit review updates rating and comment')


# ---------------------------------------------------------------------------
# AC-9: Delete review removes it from product detail
# ---------------------------------------------------------------------------

def test_ac9_delete_review():
    _create_user('rev9@test.com')
    pid = _create_product('Rev9 Spice')
    c = app.test_client()
    _login(c, 'rev9@test.com')
    _place_order_and_pay(c, pid)
    c.post(f'/api/products/{pid}/review', json={'rating': 3, 'comment': 'To be deleted'})

    conn = _db_conn()
    review = conn.execute("SELECT id FROM reviews WHERE comment='To be deleted'").fetchone()
    conn.close()
    review_id = review['id']

    r = c.post(f'/api/reviews/{review_id}/delete')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"

    r2 = c.get(f'/api/products/{pid}')
    reviews = r2.get_json()['reviews']
    assert not any(rv['id'] == review_id for rv in reviews), "Deleted review still appears"
    print('AC-9 PASS: delete review removes it from product detail')


# ---------------------------------------------------------------------------
# AC-10: User cannot edit/delete another user's review (403)
# ---------------------------------------------------------------------------

def test_ac10_edit_others_review_forbidden():
    _create_user('rev10a@test.com', name='Rev10 Alice')
    _create_user('rev10b@test.com', name='Rev10 Bob')
    pid = _create_product('Rev10 Spice')

    c_a = app.test_client()
    _login(c_a, 'rev10a@test.com')
    _place_order_and_pay(c_a, pid)
    c_a.post(f'/api/products/{pid}/review', json={'rating': 5, 'comment': 'Alice review'})

    conn = _db_conn()
    review = conn.execute("SELECT id FROM reviews WHERE comment='Alice review'").fetchone()
    conn.close()
    review_id = review['id']

    c_b = app.test_client()
    _login(c_b, 'rev10b@test.com')
    r_edit = c_b.post(f'/api/reviews/{review_id}/edit', json={'rating': 1, 'comment': 'Bob tamper'})
    assert r_edit.status_code == 403, f"Expected 403 for edit, got {r_edit.status_code}"

    r_del = c_b.post(f'/api/reviews/{review_id}/delete')
    assert r_del.status_code == 403, f"Expected 403 for delete, got {r_del.status_code}"
    print('AC-10 PASS: user cannot edit or delete another user\'s review (403)')


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_ac1_unauthenticated_review,
        test_ac2_non_buyer_cannot_review,
        test_ac3_buyer_can_review,
        test_ac4_review_in_product_detail,
        test_ac5_invalid_rating,
        test_ac6_duplicate_review_blocked,
        test_ac7_average_rating,
        test_ac8_edit_review,
        test_ac9_delete_review,
        test_ac10_edit_others_review_forbidden,
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
