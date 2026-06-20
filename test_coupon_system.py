"""
test_coupon_system.py — Feature 18 Acceptance Tests
Run: python test_coupon_system.py
Uses an isolated temp DB — safe to run at any time.
"""
import json
import os
import tempfile
import unittest

_TMP = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
_TMP.close()

import db as _db
_db.DATABASE = _TMP.name

from app import app


def _register_and_login(client, email, password='pass1234', is_admin=False):
    with _db.get_db() as conn:
        from werkzeug.security import generate_password_hash
        conn.execute(
            "INSERT OR IGNORE INTO users (name, email, password_hash, is_admin) VALUES (?,?,?,?)",
            ('Test', email, generate_password_hash(password), 1 if is_admin else 0)
        )
        conn.commit()
    client.post('/api/auth/login', json={'email': email, 'password': password})


def _add_coupon(conn, code, discount_type='percentage', discount_value=10,
                min_order_amount=0, max_uses=0, used_count=0,
                expiry_date=None, is_active=1):
    conn.execute("""
        INSERT INTO coupons
          (code, discount_type, discount_value, min_order_amount,
           max_uses, used_count, expiry_date, is_active)
        VALUES (?,?,?,?,?,?,?,?)
    """, (code, discount_type, discount_value, min_order_amount,
          max_uses, used_count, expiry_date, is_active))
    conn.commit()


class TestCouponSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _db.init_db()
        _db.migrate_db()
        _db.seed_db()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        try:
            os.unlink(_TMP.name)
        except OSError:
            pass

    def setUp(self):
        conn = _db.get_db()
        conn.execute("DELETE FROM coupons")
        conn.commit()
        conn.close()

    # ── AC-1: Valid percentage coupon ──────────────────────────────────────
    def test_ac1_valid_percentage(self):
        conn = _db.get_db()
        _add_coupon(conn, 'SAVE10', 'percentage', 10)
        conn.close()
        _register_and_login(self.client, 'ac1@test.com')
        r = self.client.post('/api/coupons/validate',
                             json={'code': 'SAVE10', 'subtotal': 500})
        d = r.get_json()
        self.assertTrue(d['valid'])
        self.assertAlmostEqual(d['discount_amount'], 50.0)
        # 500 - 50 = 450 < 500 so shipping = 40, total = 490
        self.assertAlmostEqual(d['new_total'], 490.0)

    # ── AC-2: Valid fixed coupon ───────────────────────────────────────────
    def test_ac2_valid_fixed(self):
        conn = _db.get_db()
        _add_coupon(conn, 'FLAT50', 'fixed', 50)
        conn.close()
        _register_and_login(self.client, 'ac2@test.com')
        r = self.client.post('/api/coupons/validate',
                             json={'code': 'FLAT50', 'subtotal': 200})
        d = r.get_json()
        self.assertTrue(d['valid'])
        self.assertAlmostEqual(d['discount_amount'], 50.0)
        self.assertAlmostEqual(d['new_subtotal'], 150.0)
        self.assertAlmostEqual(d['new_shipping_fee'], 40.0)
        self.assertAlmostEqual(d['new_total'], 190.0)

    # ── AC-3: Free shipping re-calculation ────────────────────────────────
    def test_ac3_free_shipping_recalc(self):
        conn = _db.get_db()
        _add_coupon(conn, 'BIG100', 'fixed', 100)
        conn.close()
        _register_and_login(self.client, 'ac3@test.com')
        r = self.client.post('/api/coupons/validate',
                             json={'code': 'BIG100', 'subtotal': 550})
        d = r.get_json()
        self.assertTrue(d['valid'])
        self.assertAlmostEqual(d['new_subtotal'], 450.0)
        self.assertAlmostEqual(d['new_shipping_fee'], 40.0)

    # ── AC-4: Discount capped at subtotal ─────────────────────────────────
    def test_ac4_discount_capped(self):
        conn = _db.get_db()
        _add_coupon(conn, 'MEGA500', 'fixed', 500)
        conn.close()
        _register_and_login(self.client, 'ac4@test.com')
        r = self.client.post('/api/coupons/validate',
                             json={'code': 'MEGA500', 'subtotal': 200})
        d = r.get_json()
        self.assertTrue(d['valid'])
        self.assertAlmostEqual(d['discount_amount'], 200.0)
        self.assertAlmostEqual(d['new_subtotal'], 0.0)
        self.assertAlmostEqual(d['new_total'], 40.0)

    # ── AC-5: Invalid code ────────────────────────────────────────────────
    def test_ac5_invalid_code(self):
        _register_and_login(self.client, 'ac5@test.com')
        r = self.client.post('/api/coupons/validate',
                             json={'code': 'FAKECODE', 'subtotal': 200})
        d = r.get_json()
        self.assertFalse(d['valid'])
        self.assertEqual(d['error'], 'Invalid coupon code.')

    # ── AC-6: Inactive coupon ─────────────────────────────────────────────
    def test_ac6_inactive(self):
        conn = _db.get_db()
        _add_coupon(conn, 'OLD10', 'percentage', 10, is_active=0)
        conn.close()
        _register_and_login(self.client, 'ac6@test.com')
        r = self.client.post('/api/coupons/validate',
                             json={'code': 'OLD10', 'subtotal': 200})
        d = r.get_json()
        self.assertFalse(d['valid'])
        self.assertIn('no longer active', d['error'])

    # ── AC-7: Expired coupon ──────────────────────────────────────────────
    def test_ac7_expired(self):
        conn = _db.get_db()
        _add_coupon(conn, 'EXP10', 'percentage', 10, expiry_date='2020-01-01')
        conn.close()
        _register_and_login(self.client, 'ac7@test.com')
        r = self.client.post('/api/coupons/validate',
                             json={'code': 'EXP10', 'subtotal': 200})
        d = r.get_json()
        self.assertFalse(d['valid'])
        self.assertIn('expired', d['error'])

    # ── AC-8: Max uses reached ────────────────────────────────────────────
    def test_ac8_max_uses_reached(self):
        conn = _db.get_db()
        _add_coupon(conn, 'MAX5', 'percentage', 10, max_uses=5, used_count=5)
        conn.close()
        _register_and_login(self.client, 'ac8@test.com')
        r = self.client.post('/api/coupons/validate',
                             json={'code': 'MAX5', 'subtotal': 200})
        d = r.get_json()
        self.assertFalse(d['valid'])
        self.assertIn('usage limit', d['error'])

    # ── AC-9: Min order not met ───────────────────────────────────────────
    def test_ac9_min_order(self):
        conn = _db.get_db()
        _add_coupon(conn, 'BIG500', 'percentage', 10, min_order_amount=500)
        conn.close()
        _register_and_login(self.client, 'ac9@test.com')
        r = self.client.post('/api/coupons/validate',
                             json={'code': 'BIG500', 'subtotal': 300})
        d = r.get_json()
        self.assertFalse(d['valid'])
        self.assertIn('Minimum order', d['error'])

    # ── AC-10: used_count increments on order ─────────────────────────────
    def test_ac10_used_count_increments(self):
        conn = _db.get_db()
        _add_coupon(conn, 'TEST10', 'percentage', 10)
        conn.execute(
            "INSERT OR IGNORE INTO products (name, description, price, stock, category)"
            " VALUES ('TestSpice','desc',200,10,'Whole Spices')"
        )
        conn.commit()
        product_id = conn.execute(
            "SELECT id FROM products WHERE name='TestSpice' LIMIT 1"
        ).fetchone()['id']
        conn.close()

        _register_and_login(self.client, 'ac10@test.com')
        self.client.post('/api/cart/add', json={'product_id': product_id, 'quantity': 1})
        r = self.client.post('/api/checkout', json={
            'shipping_name': 'Test User',
            'shipping_phone': '9876543210',
            'shipping_address': '123 Main St, Mumbai',
            'coupon_code': 'TEST10',
        })
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertTrue(d['success'])

        conn = _db.get_db()
        coupon = conn.execute("SELECT used_count FROM coupons WHERE code='TEST10'").fetchone()
        order  = conn.execute(
            "SELECT coupon_code, discount_amount FROM orders WHERE id=?",
            (d['order_id'],)
        ).fetchone()
        conn.close()

        self.assertEqual(coupon['used_count'], 1)
        self.assertEqual(order['coupon_code'], 'TEST10')
        self.assertGreater(order['discount_amount'], 0)

    # ── AC-11: Server re-validates at order time ──────────────────────────
    def test_ac11_server_revalidates(self):
        conn = _db.get_db()
        _add_coupon(conn, 'DEACT10', 'percentage', 10)
        product_id = conn.execute("SELECT id FROM products LIMIT 1").fetchone()['id']
        conn.close()

        _register_and_login(self.client, 'ac11@test.com')
        self.client.post('/api/cart/add', json={'product_id': product_id, 'quantity': 1})

        conn = _db.get_db()
        conn.execute("UPDATE coupons SET is_active=0 WHERE code='DEACT10'")
        conn.commit()
        conn.close()

        r = self.client.post('/api/checkout', json={
            'shipping_name': 'Test User',
            'shipping_phone': '9876543210',
            'shipping_address': '123 Main St, Mumbai',
            'coupon_code': 'DEACT10',
        })
        self.assertEqual(r.status_code, 400)
        self.assertIn('no longer active', r.get_json()['error'])

    # ── AC-12: Guest cannot validate coupon ──────────────────────────────
    def test_ac12_guest_blocked(self):
        self.client.post('/api/auth/logout')
        r = self.client.post('/api/coupons/validate',
                             json={'code': 'SAVE10', 'subtotal': 200})
        self.assertEqual(r.status_code, 401)

    # ── AC-13: Admin create coupon ────────────────────────────────────────
    def test_ac13_admin_create(self):
        _register_and_login(self.client, 'admin13@test.com', is_admin=True)
        r = self.client.post('/api/admin/coupons', json={
            'code': 'ADMIN10',
            'discount_type': 'percentage',
            'discount_value': 10,
            'min_order_amount': 0,
            'max_uses': 0,
            'expiry_date': None,
        })
        self.assertEqual(r.status_code, 201)
        conn = _db.get_db()
        coupon = conn.execute("SELECT code FROM coupons WHERE code='ADMIN10'").fetchone()
        conn.close()
        self.assertIsNotNone(coupon)
        self.assertEqual(coupon['code'], 'ADMIN10')

    # ── AC-14: Duplicate code rejected ────────────────────────────────────
    def test_ac14_duplicate_code(self):
        conn = _db.get_db()
        _add_coupon(conn, 'DUP10')
        conn.close()
        _register_and_login(self.client, 'admin14@test.com', is_admin=True)
        r = self.client.post('/api/admin/coupons', json={
            'code': 'DUP10',
            'discount_type': 'percentage',
            'discount_value': 5,
        })
        self.assertEqual(r.status_code, 409)

    # ── AC-15: Percentage > 100 rejected ──────────────────────────────────
    def test_ac15_percentage_over_100(self):
        _register_and_login(self.client, 'admin15@test.com', is_admin=True)
        r = self.client.post('/api/admin/coupons', json={
            'code': 'BAD150',
            'discount_type': 'percentage',
            'discount_value': 150,
        })
        self.assertEqual(r.status_code, 400)
        self.assertIn('100', r.get_json()['error'])

    # ── AC-16: Toggle coupon ───────────────────────────────────────────────
    def test_ac16_toggle(self):
        conn = _db.get_db()
        _add_coupon(conn, 'TOG10', is_active=1)
        coupon_id = conn.execute(
            "SELECT id FROM coupons WHERE code='TOG10'"
        ).fetchone()['id']
        conn.close()

        _register_and_login(self.client, 'admin16@test.com', is_admin=True)
        r = self.client.patch(f'/api/admin/coupons/{coupon_id}/toggle')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['coupon']['is_active'], 0)
        r = self.client.patch(f'/api/admin/coupons/{coupon_id}/toggle')
        self.assertEqual(r.get_json()['coupon']['is_active'], 1)

    # ── AC-17: Non-admin blocked ───────────────────────────────────────────
    def test_ac17_non_admin_blocked(self):
        _register_and_login(self.client, 'user17@test.com', is_admin=False)
        r = self.client.get('/api/admin/coupons')
        self.assertEqual(r.status_code, 403)

    # ── AC-18: Unauthenticated admin endpoint ─────────────────────────────
    def test_ac18_unauthenticated_admin(self):
        self.client.post('/api/auth/logout')
        r = self.client.get('/api/admin/coupons')
        self.assertEqual(r.status_code, 401)


if __name__ == '__main__':
    unittest.main(verbosity=2)
