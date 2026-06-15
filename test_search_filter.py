"""
Acceptance-criteria tests for feature 04 — Search & Filter.
Run with:  python test_search_filter.py
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


def _create_product(name, category='Whole Spices', price=100.0, stock=50):
    conn = _db_conn()
    cur = conn.execute(
        "INSERT INTO products (name, description, price, stock, category) VALUES (?, ?, ?, ?, ?)",
        (name, f'Description for {name}', price, stock, category)
    )
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return pid


# Seed test products once
_create_product('SF Cumin Whole',     category='Whole Spices',  price=75.0)
_create_product('SF Turmeric Powder', category='Ground Spices', price=89.0)
_create_product('SF Garam Masala',    category='Spice Blends',  price=120.0)
_create_product('SF Organic Pepper',  category='Organic',       price=150.0)
_create_product('SF Black Pepper',    category='Whole Spices',  price=110.0)


# ---------------------------------------------------------------------------
# AC-1: Search by name returns matching products
# ---------------------------------------------------------------------------

def test_ac1_search_by_name():
    c = app.test_client()
    r = c.get('/api/products?q=Cumin')
    assert r.status_code == 200
    data = r.get_json()
    names = [p['name'] for p in data['products']]
    assert any('Cumin' in n for n in names), f"Expected Cumin in results, got: {names}"
    print('AC-1 PASS: search by name returns matching products')


# ---------------------------------------------------------------------------
# AC-2: Search with no results returns empty list (not error)
# ---------------------------------------------------------------------------

def test_ac2_search_no_results():
    c = app.test_client()
    r = c.get('/api/products?q=XYZNONEXISTENT')
    assert r.status_code == 200
    data = r.get_json()
    assert data['products'] == []
    assert data['total'] == 0
    print('AC-2 PASS: search with no results returns empty list')


# ---------------------------------------------------------------------------
# AC-3: Filter by category returns only that category's products
# ---------------------------------------------------------------------------

def test_ac3_filter_by_category():
    c = app.test_client()
    r = c.get('/api/products?category=Ground+Spices')
    assert r.status_code == 200
    data = r.get_json()
    for p in data['products']:
        assert p['category'] == 'Ground Spices', \
            f"Expected Ground Spices, got {p['category']} for {p['name']}"
    print('AC-3 PASS: category filter returns only matching-category products')


# ---------------------------------------------------------------------------
# AC-4: Invalid category is ignored (returns all products, category cleared)
# ---------------------------------------------------------------------------

def test_ac4_invalid_category_ignored():
    c = app.test_client()
    r = c.get('/api/products?category=FAKECATEGORY')
    assert r.status_code == 200
    data = r.get_json()
    assert data['category'] == '', f"Invalid category should be cleared, got: {data['category']}"
    print('AC-4 PASS: invalid category ignored, all products returned')


# ---------------------------------------------------------------------------
# AC-5: Sort by price_asc returns products in ascending price order
# ---------------------------------------------------------------------------

def test_ac5_sort_price_asc():
    c = app.test_client()
    r = c.get('/api/products?sort=price_asc')
    assert r.status_code == 200
    prices = [p['price'] for p in r.get_json()['products']]
    assert prices == sorted(prices), f"Expected ascending prices, got: {prices}"
    print('AC-5 PASS: sort=price_asc returns products in ascending price order')


# ---------------------------------------------------------------------------
# AC-6: Sort by price_desc returns products in descending price order
# ---------------------------------------------------------------------------

def test_ac6_sort_price_desc():
    c = app.test_client()
    r = c.get('/api/products?sort=price_desc')
    assert r.status_code == 200
    prices = [p['price'] for p in r.get_json()['products']]
    assert prices == sorted(prices, reverse=True), f"Expected descending prices, got: {prices}"
    print('AC-6 PASS: sort=price_desc returns products in descending price order')


# ---------------------------------------------------------------------------
# AC-7: Invalid sort value falls back to default (no error)
# ---------------------------------------------------------------------------

def test_ac7_invalid_sort_ignored():
    c = app.test_client()
    r = c.get('/api/products?sort=INVALID')
    assert r.status_code == 200
    data = r.get_json()
    assert 'products' in data
    print('AC-7 PASS: invalid sort value falls back gracefully')


# ---------------------------------------------------------------------------
# AC-8: Pagination — page=1 returns first page with total_pages field
# ---------------------------------------------------------------------------

def test_ac8_pagination_fields():
    c = app.test_client()
    r = c.get('/api/products?page=1')
    assert r.status_code == 200
    data = r.get_json()
    assert data['page'] == 1
    assert 'total_pages' in data
    assert 'total' in data
    print('AC-8 PASS: pagination fields present in response')


# ---------------------------------------------------------------------------
# AC-9: Page beyond last returns empty products list (no crash)
# ---------------------------------------------------------------------------

def test_ac9_page_beyond_last():
    c = app.test_client()
    r = c.get('/api/products?page=9999')
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data['products'], list)
    print('AC-9 PASS: page beyond last returns empty list without error')


# ---------------------------------------------------------------------------
# AC-10: Response includes categories list
# ---------------------------------------------------------------------------

def test_ac10_categories_in_response():
    c = app.test_client()
    r = c.get('/api/products')
    data = r.get_json()
    assert 'categories' in data
    assert isinstance(data['categories'], list)
    assert len(data['categories']) > 0
    print('AC-10 PASS: response includes categories list')


# ---------------------------------------------------------------------------
# AC-11: Combined search + category filter works
# ---------------------------------------------------------------------------

def test_ac11_search_and_category_combined():
    c = app.test_client()
    r = c.get('/api/products?q=Pepper&category=Whole+Spices')
    assert r.status_code == 200
    data = r.get_json()
    for p in data['products']:
        assert p['category'] == 'Whole Spices'
    print('AC-11 PASS: search + category combined filter works')


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_ac1_search_by_name,
        test_ac2_search_no_results,
        test_ac3_filter_by_category,
        test_ac4_invalid_category_ignored,
        test_ac5_sort_price_asc,
        test_ac6_sort_price_desc,
        test_ac7_invalid_sort_ignored,
        test_ac8_pagination_fields,
        test_ac9_page_beyond_last,
        test_ac10_categories_in_response,
        test_ac11_search_and_category_combined,
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
