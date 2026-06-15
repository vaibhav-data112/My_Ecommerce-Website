import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import db as _db

_test_db = tempfile.mktemp(suffix='.db')
_db.DATABASE = _test_db


def _create_user(app, email, password, is_admin=False):
    import db as _db2
    conn = _db2.get_db()
    from werkzeug.security import generate_password_hash
    conn.execute(
        'INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
        ('Test', email, generate_password_hash(password), 1 if is_admin else 0),
    )
    conn.commit()
    conn.close()


def _login(client, email, password):
    return client.post(
        '/api/auth/login',
        json={'email': email, 'password': password},
        content_type='application/json',
    )


def _add_product_via_db(name='Spice', category='Organic', price=99.0, stock=10):
    conn = _db.get_db()
    cur = conn.execute(
        'INSERT INTO products (name, description, price, stock, category, image_url) VALUES (?, ?, ?, ?, ?, ?)',
        (name, 'desc', price, stock, category, ''),
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


class TestProductImageUpload(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import app as _app
        _app.app.config['TESTING'] = True
        _app.app.config['WTF_CSRF_ENABLED'] = False
        _db.init_db()
        _db.migrate_db()
        cls.client = _app.app.test_client()
        cls.ctx    = _app.app.app_context()
        cls.ctx.push()
        _create_user(cls.client, 'admin@img.com', 'pass1234', is_admin=True)
        _create_user(cls.client, 'user@img.com',  'pass1234', is_admin=False)

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()
        if os.path.exists(_test_db):
            os.remove(_test_db)

    def _login_admin(self):
        return _login(self.client, 'admin@img.com', 'pass1234')

    def _login_user(self):
        return _login(self.client, 'user@img.com', 'pass1234')

    # ── helpers ─────────────────────────────────────────────────────────────

    def _post_add(self, extra=None, file_data=None):
        data = {
            'name':        'Test Spice',
            'description': 'A spice',
            'price':       '50',
            'stock':       '10',
            'category':    'Organic',
            'image_url':   '',
        }
        if extra:
            data.update(extra)
        if file_data:
            data['image_file'] = file_data
        return self.client.post(
            '/api/admin/products/add',
            data=data,
            content_type='multipart/form-data',
        )

    # ── AC-1: unauthenticated upload rejected ────────────────────────────────

    def test_01_unauthenticated_upload_rejected(self):
        with self.client.session_transaction() as sess:
            sess.clear()
        rv = self._post_add()
        self.assertEqual(rv.status_code, 401)

    # ── AC-2: non-admin upload rejected ─────────────────────────────────────

    def test_02_non_admin_upload_rejected(self):
        self._login_user()
        rv = self._post_add()
        self.assertEqual(rv.status_code, 403)

    # ── AC-3: add product with URL only (no file) works ─────────────────────

    def test_03_add_with_url_no_file(self):
        self._login_admin()
        rv = self._post_add(extra={'name': 'URL Spice', 'image_url': 'https://example.com/img.jpg'})
        self.assertEqual(rv.status_code, 201)
        conn = _db.get_db()
        row = conn.execute("SELECT image_url FROM products WHERE name='URL Spice'").fetchone()
        conn.close()
        self.assertEqual(row['image_url'], 'https://example.com/img.jpg')

    # ── AC-4: add product with valid image file ──────────────────────────────

    def test_04_add_with_valid_image_file(self):
        self._login_admin()
        fake_img = (io.BytesIO(b'\xff\xd8\xff\xe0' + b'x' * 100), 'photo.jpg')
        rv = self._post_add(extra={'name': 'File Spice'}, file_data=fake_img)
        self.assertEqual(rv.status_code, 201)
        conn = _db.get_db()
        row = conn.execute("SELECT image_url FROM products WHERE name='File Spice'").fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertTrue(row['image_url'].startswith('uploads/products/'))
        self.assertIn('.jpg', row['image_url'])
        # cleanup uploaded file
        saved = os.path.join('static', row['image_url'])
        if os.path.exists(saved):
            os.remove(saved)

    # ── AC-5: invalid file type returns 422 ─────────────────────────────────

    def test_05_invalid_file_type_rejected(self):
        self._login_admin()
        fake_pdf = (io.BytesIO(b'%PDF-1.4 fake'), 'doc.pdf')
        rv = self._post_add(extra={'name': 'PDF Spice'}, file_data=fake_pdf)
        self.assertEqual(rv.status_code, 422)
        data = rv.get_json()
        self.assertIn('error', data)
        self.assertIn('Invalid file type', data['error'])

    # ── AC-6: file too large returns 422 ─────────────────────────────────────

    def test_06_file_too_large_rejected(self):
        self._login_admin()
        large = (io.BytesIO(b'x' * (5 * 1024 * 1024 + 1)), 'big.jpg')
        rv = self._post_add(extra={'name': 'Big Spice'}, file_data=large)
        self.assertEqual(rv.status_code, 422)
        data = rv.get_json()
        self.assertIn('error', data)
        self.assertIn('5 MB', data['error'])

    # ── AC-7: edit product with new image replaces image_url ─────────────────

    def test_07_edit_product_replaces_image(self):
        self._login_admin()
        pid = _add_product_via_db('Editable Spice', 'Organic')
        fake_img = (io.BytesIO(b'\xff\xd8\xff' + b'y' * 50), 'new.jpg')
        rv = self.client.post(
            f'/api/admin/products/{pid}/edit',
            data={
                'name': 'Editable Spice', 'description': 'desc',
                'price': '99', 'stock': '5', 'category': 'Organic',
                'image_url': '', 'image_file': fake_img,
            },
            content_type='multipart/form-data',
        )
        self.assertEqual(rv.status_code, 200)
        conn = _db.get_db()
        row = conn.execute('SELECT image_url FROM products WHERE id=?', (pid,)).fetchone()
        conn.close()
        self.assertTrue(row['image_url'].startswith('uploads/products/'))
        saved = os.path.join('static', row['image_url'])
        if os.path.exists(saved):
            os.remove(saved)

    # ── AC-8: edit product with URL only keeps URL ────────────────────────────

    def test_08_edit_product_with_url_only(self):
        self._login_admin()
        pid = _add_product_via_db('URL Editable', 'Organic')
        rv = self.client.post(
            f'/api/admin/products/{pid}/edit',
            data={
                'name': 'URL Editable', 'description': 'desc',
                'price': '99', 'stock': '5', 'category': 'Organic',
                'image_url': 'https://example.com/new.jpg',
            },
            content_type='multipart/form-data',
        )
        self.assertEqual(rv.status_code, 200)
        conn = _db.get_db()
        row = conn.execute('SELECT image_url FROM products WHERE id=?', (pid,)).fetchone()
        conn.close()
        self.assertEqual(row['image_url'], 'https://example.com/new.jpg')

    # ── AC-9: product catalog returns correct image_url ──────────────────────

    def test_09_catalog_returns_image_url(self):
        self._login_admin()
        fake_img = (io.BytesIO(b'\xff\xd8\xff' + b'z' * 50), 'catalog.jpg')
        self._post_add(extra={'name': 'Catalog Spice'}, file_data=fake_img)
        rv = self.client.get('/api/products')
        self.assertEqual(rv.status_code, 200)
        products = rv.get_json()['products']
        match = next((p for p in products if p['name'] == 'Catalog Spice'), None)
        self.assertIsNotNone(match)
        self.assertTrue(match['image_url'].startswith('uploads/products/'))
        saved = os.path.join('static', match['image_url'])
        if os.path.exists(saved):
            os.remove(saved)

    # ── AC-10: old URL products are unaffected ───────────────────────────────

    def test_10_old_url_products_unaffected(self):
        conn = _db.get_db()
        conn.execute(
            'INSERT INTO products (name, description, price, stock, category, image_url) VALUES (?, ?, ?, ?, ?, ?)',
            ('Legacy Spice', 'old product', 100, 5, 'Organic', 'https://old.example.com/img.png'),
        )
        conn.commit()
        conn.close()
        rv = self.client.get('/api/products')
        products = rv.get_json()['products']
        match = next((p for p in products if p['name'] == 'Legacy Spice'), None)
        self.assertIsNotNone(match)
        self.assertEqual(match['image_url'], 'https://old.example.com/img.png')


if __name__ == '__main__':
    unittest.main()
