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


def _seed_products():
    conn = sqlite3.connect(_test_db)
    # Clear seeded products to control test data precisely
    conn.execute("DELETE FROM products")
    products = [
        ('Wireless Earbuds',       'Bluetooth earbuds', 29.99, 50,  'Electronics'),
        ('Wired Headphones',       'Over-ear wired',    19.99, 30,  'Electronics'),
        ('Cotton T-Shirt',         'Everyday wear',      9.99, 100, 'Clothing'),
        ('Denim Jacket',           'Classic jacket',    49.99, 20,  'Clothing'),
        ('Yoga Mat',               'Non-slip mat',      24.99, 40,  'Sports'),
        ('Python Programming Book','Learn Python',      39.99, 20,  'Books'),
        ('Face Moisturizer',       'Hydrating cream',   14.99, 60,  'Beauty'),
        ('Ceramic Mug Set',        'Set of 4 mugs',     12.99, 75,  'Home'),
    ]
    conn.executemany(
        "INSERT INTO products (name, description, price, stock, category) VALUES (?, ?, ?, ?, ?)",
        products,
    )
    conn.commit()
    conn.close()


def _seed_many_products(n=15):
    """Seed n products for pagination tests."""
    conn = sqlite3.connect(_test_db)
    conn.execute("DELETE FROM products")
    rows = [(f'Product {i}', 'desc', float(i), 10, 'Other') for i in range(1, n + 1)]
    conn.executemany(
        "INSERT INTO products (name, description, price, stock, category) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()


def get_client():
    return app.test_client()


def test_ac1_search_by_name():
    _seed_products()
    c = get_client()
    r = c.get('/products?q=earbuds')
    assert r.status_code == 200
    body = r.data.decode()
    assert 'Wireless Earbuds' in body, 'AC-1 fail: matching product not shown'
    assert 'Wired Headphones' not in body, 'AC-1 fail: non-matching product shown'
    assert 'Cotton T-Shirt' not in body, 'AC-1 fail: unrelated product shown'
    print('AC-1 PASS: search by name returns only matching products')


def test_ac2_case_insensitive_search():
    _seed_products()
    c = get_client()
    r = c.get('/products?q=WIRELESS')
    assert r.status_code == 200
    body = r.data.decode()
    assert 'Wireless Earbuds' in body, 'AC-2 fail: uppercase search did not match'
    print('AC-2 PASS: search is case-insensitive')


def test_ac2b_partial_match():
    _seed_products()
    c = get_client()
    r = c.get('/products?q=ear')
    assert r.status_code == 200
    body = r.data.decode()
    assert 'Wireless Earbuds' in body, 'AC-2b fail: partial search did not match'
    print('AC-2b PASS: partial-word search works')


def test_ac3_filter_by_category():
    _seed_products()
    c = get_client()
    r = c.get('/products?category=Electronics')
    assert r.status_code == 200
    body = r.data.decode()
    assert 'Wireless Earbuds' in body, 'AC-3 fail: Electronics product missing'
    assert 'Wired Headphones' in body, 'AC-3 fail: Electronics product missing'
    assert 'Cotton T-Shirt' not in body, 'AC-3 fail: non-Electronics product shown'
    assert 'Yoga Mat' not in body, 'AC-3 fail: non-Electronics product shown'
    print('AC-3 PASS: category filter shows only the selected category')


def test_ac4a_sort_price_asc():
    _seed_products()
    c = get_client()
    r = c.get('/products?sort=price_asc')
    assert r.status_code == 200
    body = r.data.decode()
    # Cheapest is Cotton T-Shirt (9.99), most expensive is Denim Jacket (49.99)
    pos_cheap = body.index('Cotton T-Shirt')
    pos_expensive = body.index('Denim Jacket')
    assert pos_cheap < pos_expensive, 'AC-4a fail: cheapest product not before most expensive'
    print('AC-4a PASS: sort price low-to-high works')


def test_ac4b_sort_price_desc():
    _seed_products()
    c = get_client()
    r = c.get('/products?sort=price_desc')
    assert r.status_code == 200
    body = r.data.decode()
    pos_cheap = body.index('Cotton T-Shirt')
    pos_expensive = body.index('Denim Jacket')
    assert pos_expensive < pos_cheap, 'AC-4b fail: most expensive product not before cheapest'
    print('AC-4b PASS: sort price high-to-low works')


def test_ac5_combined_search_category_sort():
    _seed_products()
    c = get_client()
    # "head" matches Wired Headphones and nothing else in Electronics
    r = c.get('/products?q=head&category=Electronics&sort=price_asc')
    assert r.status_code == 200
    body = r.data.decode()
    assert 'Wired Headphones' in body, 'AC-5 fail: combined filter missing result'
    assert 'Wireless Earbuds' not in body, 'AC-5 fail: non-matching product shown'
    assert 'Cotton T-Shirt' not in body, 'AC-5 fail: wrong category product shown'
    print('AC-5 PASS: search + category + sort combined works correctly')


def test_ac6_pagination():
    _seed_many_products(15)
    c = get_client()

    # Use price_asc so order is deterministic: Product 1 (price=1) first, Product 15 last.
    # Page 1 = products 1–12; Page 2 = products 13–15.
    r1 = c.get('/products?sort=price_asc&page=1')
    assert r1.status_code == 200
    body1 = r1.data.decode()
    assert 'Product 12' in body1, 'AC-6 fail: Product 12 not on page 1'
    assert 'Product 13' not in body1, 'AC-6 fail: page-2 product shown on page 1'

    r2 = c.get('/products?sort=price_asc&page=2')
    assert r2.status_code == 200
    body2 = r2.data.decode()
    assert 'Product 13' in body2, 'AC-6 fail: Product 13 not on page 2'
    assert 'Product 12' not in body2, 'AC-6 fail: page-1 product shown on page 2'

    # Pagination controls present
    assert 'Next' in body1 or 'page=2' in body1, 'AC-6 fail: no pagination controls'
    print('AC-6 PASS: pagination splits products across pages with correct controls')


def test_ac7_no_results_message():
    _seed_products()
    c = get_client()
    r = c.get('/products?q=xyznotexistproduct99')
    assert r.status_code == 200
    body = r.data.decode()
    assert 'No products found' in body, 'AC-7 fail: no "No products found" message'
    assert 'Clear filters' in body or 'Clear' in body, 'AC-7 fail: no clear-filters link'
    print('AC-7 PASS: no-results message shown with clear filters link')


def test_ac8_empty_search_shows_all():
    _seed_products()
    c = get_client()
    r = c.get('/products')
    assert r.status_code == 200
    body = r.data.decode()
    for name in ['Wireless Earbuds', 'Cotton T-Shirt', 'Yoga Mat',
                 'Python Programming Book', 'Face Moisturizer', 'Ceramic Mug Set']:
        assert name in body, f'AC-8 fail: "{name}" not shown in full listing'
    print('AC-8 PASS: empty search shows all products')


def test_ac9_filters_reflected_in_url():
    _seed_products()
    c = get_client()
    r = c.get('/products?q=mug&category=Home&sort=price_asc')
    assert r.status_code == 200
    body = r.data.decode()
    assert 'Ceramic Mug Set' in body, 'AC-9 fail: filtered result missing'
    # Verify the input/select values are preserved in the page HTML
    assert 'value="mug"' in body or 'value=mug' in body, 'AC-9 fail: q not reflected in form'
    assert 'price_asc' in body, 'AC-9 fail: sort not reflected in page'
    print('AC-9 PASS: filter state is reflected in the URL and page elements')


def test_invalid_page_number():
    _seed_products()
    c = get_client()
    r = c.get('/products?page=999')
    assert r.status_code == 200, 'Invalid page number crashed the app'
    r2 = c.get('/products?page=notanumber')
    assert r2.status_code == 200, 'Non-numeric page number crashed the app'
    print('ERROR HANDLING PASS: invalid page numbers handled gracefully')


def test_invalid_sort_value():
    _seed_products()
    c = get_client()
    r = c.get('/products?sort=hacky_sort_injection')
    assert r.status_code == 200, 'Invalid sort value crashed the app'
    print('ERROR HANDLING PASS: invalid sort value handled gracefully')


def test_unknown_category_ignored():
    _seed_products()
    c = get_client()
    r = c.get('/products?category=FakeCategory')
    assert r.status_code == 200, 'Unknown category crashed the app'
    body = r.data.decode()
    # Should fall back to showing all products
    assert 'Wireless Earbuds' in body, 'Unknown category should fall back to showing all products'
    print('ERROR HANDLING PASS: unknown category treated as no filter')


if __name__ == '__main__':
    tests = [
        test_ac1_search_by_name,
        test_ac2_case_insensitive_search,
        test_ac2b_partial_match,
        test_ac3_filter_by_category,
        test_ac4a_sort_price_asc,
        test_ac4b_sort_price_desc,
        test_ac5_combined_search_category_sort,
        test_ac6_pagination,
        test_ac7_no_results_message,
        test_ac8_empty_search_shows_all,
        test_ac9_filters_reflected_in_url,
        test_invalid_page_number,
        test_invalid_sort_value,
        test_unknown_category_ignored,
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
