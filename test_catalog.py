"""
Acceptance-criteria tests for feature 03 — Product Catalog.
Run with:  python test_catalog.py
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


def _create_product(name, description='Test desc', price=99.0, stock=50, category='Whole Spices', image_url=''):
    conn = _db_conn()
    cur = conn.execute(
        "INSERT INTO products (name, description, price, stock, category, image_url) VALUES (?, ?, ?, ?, ?, ?)",
        (name, description, price, stock, category, image_url)
    )
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return pid


def _login(client, email, password='password123'):
    return client.post('/api/auth/login', json={'email': email, 'password': password})


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


# ---------------------------------------------------------------------------
# AC-1: GET /api/products returns a list of products with expected fields
# ---------------------------------------------------------------------------

def test_ac1_listing_returns_products():
    pid = _create_product('Cumin Seeds Test')
    c = app.test_client()
    r = c.get('/api/products')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert 'products' in data
    assert isinstance(data['products'], list)
    assert len(data['products']) > 0

    names = [p['name'] for p in data['products']]
    assert 'Cumin Seeds Test' in names, f"Created product not in listing: {names}"
    print('AC-1 PASS: GET /api/products returns product list')


# ---------------------------------------------------------------------------
# AC-2: Catalog browsable without login (no 401)
# ---------------------------------------------------------------------------

def test_ac2_browse_without_login():
    c = app.test_client()
    r = c.get('/api/products')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"

    conn = _db_conn()
    pid = conn.execute("SELECT id FROM products LIMIT 1").fetchone()[0]
    conn.close()

    r2 = c.get(f'/api/products/{pid}')
    assert r2.status_code == 200, f"Expected 200 for product detail, got {r2.status_code}"
    print('AC-2 PASS: catalog browsable without login')


# ---------------------------------------------------------------------------
# AC-3: Product list response includes pagination fields
# ---------------------------------------------------------------------------

def test_ac3_listing_has_pagination():
    c = app.test_client()
    r = c.get('/api/products')
    data = r.get_json()
    assert 'total' in data
    assert 'page' in data
    assert 'total_pages' in data
    assert data['page'] == 1
    print('AC-3 PASS: product listing includes pagination fields')


# ---------------------------------------------------------------------------
# AC-4: GET /api/products/<id> returns full product info
# ---------------------------------------------------------------------------

def test_ac4_detail_shows_full_info():
    pid = _create_product(
        name='Turmeric Detail Test',
        description='Premium turmeric with high curcumin',
        price=89.0,
        stock=100,
        category='Ground Spices'
    )
    c = app.test_client()
    r = c.get(f'/api/products/{pid}')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert 'product' in data
    p = data['product']
    assert p['name'] == 'Turmeric Detail Test'
    assert 'curcumin' in p['description']
    assert p['price'] == 89.0
    assert p['category'] == 'Ground Spices'
    assert 'stock' in p
    print('AC-4 PASS: detail returns name, description, price, category, stock')


# ---------------------------------------------------------------------------
# AC-5: Out-of-stock product returns stock=0 in detail
# ---------------------------------------------------------------------------

def test_ac5_out_of_stock_product():
    pid = _create_product('OOS Test Product', stock=0)
    c = app.test_client()
    r = c.get(f'/api/products/{pid}')
    assert r.status_code == 200
    data = r.get_json()
    assert data['product']['stock'] == 0, "Expected stock=0 for OOS product"
    print('AC-5 PASS: out-of-stock product has stock=0 in response')


# ---------------------------------------------------------------------------
# AC-6: Invalid product ID returns 404
# ---------------------------------------------------------------------------

def test_ac6_invalid_id_404():
    c = app.test_client()
    r = c.get('/api/products/99999')
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    data = r.get_json()
    assert 'error' in data
    print('AC-6 PASS: invalid product ID returns 404 with error message')


# ---------------------------------------------------------------------------
# AC-7: Product detail includes reviews / avg_rating fields
# ---------------------------------------------------------------------------

def test_ac7_detail_includes_review_fields():
    pid = _create_product('Review Fields Test')
    c = app.test_client()
    r = c.get(f'/api/products/{pid}')
    data = r.get_json()
    assert 'reviews' in data
    assert 'avg_rating' in data
    assert 'review_count' in data
    assert isinstance(data['reviews'], list)
    print('AC-7 PASS: product detail includes reviews, avg_rating, review_count')


# ---------------------------------------------------------------------------
# AC-8: in_wishlist field present; False for unauthenticated, accessible for auth
# ---------------------------------------------------------------------------

def test_ac8_wishlist_field_in_detail():
    pid = _create_product('Wishlist Field Test')
    c = app.test_client()

    r = c.get(f'/api/products/{pid}')
    data = r.get_json()
    assert 'in_wishlist' in data
    assert data['in_wishlist'] is False, "Unauthenticated user should have in_wishlist=False"

    _create_user('catalog8@test.com')
    _login(c, 'catalog8@test.com')
    r2 = c.get(f'/api/products/{pid}')
    data2 = r2.get_json()
    assert 'in_wishlist' in data2
    print('AC-8 PASS: in_wishlist field present in product detail')


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_ac1_listing_returns_products,
        test_ac2_browse_without_login,
        test_ac3_listing_has_pagination,
        test_ac4_detail_shows_full_info,
        test_ac5_out_of_stock_product,
        test_ac6_invalid_id_404,
        test_ac7_detail_includes_review_fields,
        test_ac8_wishlist_field_in_detail,
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
