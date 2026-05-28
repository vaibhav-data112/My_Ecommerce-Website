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


def get_client():
    return app.test_client()


def test_ac1_listing_shows_all_products():
    c = get_client()
    r = c.get('/products')
    assert r.status_code == 200
    body = r.data.decode()
    expected = [
        'Wireless Earbuds', 'Cotton T-Shirt', 'Yoga Mat',
        'Python Programming Book', 'Face Moisturizer', 'Ceramic Mug Set',
    ]
    for name in expected:
        assert name in body, f'AC-1 fail: "{name}" not in listing'
    print('AC-1 PASS: listing shows all 6 seeded products')


def test_ac2_browse_without_login():
    c = get_client()
    r = c.get('/products', follow_redirects=False)
    assert r.status_code == 200, f'AC-2 fail: listing redirected ({r.status_code})'

    conn = sqlite3.connect(_test_db)
    first_id = conn.execute("SELECT id FROM products LIMIT 1").fetchone()[0]
    conn.close()

    r2 = c.get(f'/products/{first_id}', follow_redirects=False)
    assert r2.status_code == 200, f'AC-2 fail: detail redirected ({r2.status_code})'
    print('AC-2 PASS: catalog browsable without login')


def test_ac3_card_links_to_detail():
    c = get_client()
    r = c.get('/products')
    body = r.data.decode()
    assert '/products/1' in body or '/products/2' in body, \
        f'AC-3 fail: no /products/<id> links found'
    print('AC-3 PASS: listing contains links to detail pages')


def test_ac4_detail_shows_full_info():
    conn = sqlite3.connect(_test_db)
    row = conn.execute("SELECT * FROM products WHERE name='Wireless Earbuds'").fetchone()
    conn.close()
    pid = row[0]

    c = get_client()
    r = c.get(f'/products/{pid}')
    assert r.status_code == 200
    body = r.data.decode()
    assert 'Wireless Earbuds' in body, 'AC-4: name missing'
    assert 'Bluetooth' in body, 'AC-4: description missing'
    assert '29.99' in body, 'AC-4: price missing'
    assert 'Electronics' in body, 'AC-4: category missing'
    assert 'stock' in body.lower(), 'AC-4: stock status missing'
    print('AC-4 PASS: detail shows name, description, price, category, stock')


def test_ac5_out_of_stock_display():
    conn = sqlite3.connect(_test_db)
    conn.execute("INSERT INTO products (name, description, price, stock, category) VALUES (?, ?, ?, ?, ?)",
                 ('Test OOS', 'desc', 9.99, 0, 'Other'))
    conn.commit()
    pid = conn.execute("SELECT id FROM products WHERE name='Test OOS'").fetchone()[0]
    conn.close()

    c = get_client()
    r = c.get(f'/products/{pid}')
    body = r.data.decode()
    assert 'Out of Stock' in body or 'Out of stock' in body, \
        f'AC-5 fail: OOS label missing'
    assert 'Add to Cart' not in body or 'btn-disabled' in body, \
        'AC-5 fail: Add to Cart button shown for OOS product'
    print('AC-5 PASS: out-of-stock product shows OOS label and disabled button')


def test_ac6_invalid_id_404():
    c = get_client()
    r = c.get('/products/99999')
    assert r.status_code == 404, f'AC-6 fail: status={r.status_code}'
    body = r.data.decode()
    assert 'not found' in body.lower(), 'AC-6 fail: no friendly message'
    print('AC-6 PASS: invalid product id returns 404 with friendly page')


def test_ac7_add_to_cart_placeholder():
    c = get_client()
    conn = sqlite3.connect(_test_db)
    pid = conn.execute("SELECT id FROM products WHERE stock > 0 LIMIT 1").fetchone()[0]
    conn.close()

    r = c.get(f'/products/{pid}')
    assert 'Add to Cart' in r.data.decode(), 'AC-7 fail: Add to Cart button missing'

    r2 = c.post('/cart/add', data={'product_id': str(pid)}, follow_redirects=True)
    assert r2.status_code == 200
    assert 'coming soon' in r2.data.decode().lower(), \
        'AC-7 fail: cart placeholder flash missing'
    print('AC-7 PASS: Add to Cart button present; placeholder flash shown on POST')


def test_ac8_nav_shows_auth_state():
    c = get_client()
    r = c.get('/products')
    body = r.data.decode()
    assert 'Login' in body or 'Sign Up' in body, \
        'AC-8 fail: nav auth links missing for logged-out user'
    print('AC-8 PASS: nav shows Login/Sign Up for logged-out visitor')


if __name__ == '__main__':
    tests = [
        test_ac1_listing_shows_all_products,
        test_ac2_browse_without_login,
        test_ac3_card_links_to_detail,
        test_ac4_detail_shows_full_info,
        test_ac5_out_of_stock_display,
        test_ac6_invalid_id_404,
        test_ac7_add_to_cart_placeholder,
        test_ac8_nav_shows_auth_state,
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
