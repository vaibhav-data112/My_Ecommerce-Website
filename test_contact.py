"""
Acceptance-criteria tests for Feature 17 — Contact Us + WhatsApp.
Run with:  python test_contact.py
"""
import os
import sqlite3
import sys
import tempfile

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('GOOGLE_CLIENT_ID', 'test')
os.environ.setdefault('GOOGLE_CLIENT_SECRET', 'test')
os.environ.setdefault('RAZORPAY_KEY_ID', 'rzp_test_fake')
os.environ.setdefault('RAZORPAY_KEY_SECRET', 'fake_secret')

_tmp     = tempfile.mkdtemp()
_test_db = os.path.join(_tmp, 'test.db')

import db as _db
_db.DATABASE = _test_db

from app import app

app.config['TESTING']          = True
app.config['WTF_CSRF_ENABLED'] = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _conn():
    conn = sqlite3.connect(_test_db)
    conn.row_factory = sqlite3.Row
    return conn


def _create_user(email, name='Test User', password='pass1234', is_admin=False):
    from werkzeug.security import generate_password_hash
    conn = _conn()
    cur  = conn.execute(
        "INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
        (name, email, generate_password_hash(password), 1 if is_admin else 0),
    )
    uid = cur.lastrowid
    conn.commit(); conn.close()
    return uid


def _login(client, email, password='pass1234'):
    return client.post('/api/auth/login',
                       json={'email': email, 'password': password})


def _submit(client, **kwargs):
    payload = {
        'name':         'Ramesh Kumar',
        'email':        'ramesh@example.com',
        'order_number': '',
        'category':     'Order issue',
        'message':      'Mera order nahi aaya.',
        'website':      '',          # honeypot empty
    }
    payload.update(kwargs)
    return client.post('/api/contact', json=payload)


def _count_messages():
    conn = _conn()
    n = conn.execute("SELECT COUNT(*) FROM contact_messages").fetchone()[0]
    conn.close()
    return n


PASS = '✅'
FAIL = '❌'

results = []


def check(name, condition, detail=''):
    status = PASS if condition else FAIL
    results.append((status, name, detail))
    print(f"  {status}  {name}" + (f" — {detail}" if detail else ''))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

with app.test_client() as c:
    with app.app_context():
        _db.init_db()
        _db.migrate_db()

    print("\n=== Feature 17: Contact Us ===\n")

    # ------------------------------------------------------------------
    # Test 1 — Valid submit as guest → 200, user_id NULL
    # ------------------------------------------------------------------
    print("Test 1: Valid submit (guest)")
    r = _submit(c)
    data = r.get_json()
    check("Status 200",            r.status_code == 200)
    check("success=True",          data.get('success') is True)
    check("Message saved in DB",   _count_messages() == 1)
    conn = _conn()
    row = conn.execute("SELECT * FROM contact_messages ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    check("user_id is NULL (guest)", row['user_id'] is None)
    check("status = 'new'",          row['status'] == 'new')
    check("category saved",          row['category'] == 'Order issue')

    # ------------------------------------------------------------------
    # Test 2 — Valid submit logged-in → user_id set
    # ------------------------------------------------------------------
    print("\nTest 2: Valid submit (logged-in user)")
    uid = _create_user('customer@example.com', name='Priya')
    _login(c, 'customer@example.com')
    before = _count_messages()
    r = _submit(c, name='Priya', email='customer@example.com',
                category='Product issue', message='Masala kharab nikla.')
    check("Status 200",           r.status_code == 200)
    check("Message count +1",     _count_messages() == before + 1)
    conn = _conn()
    row = conn.execute("SELECT * FROM contact_messages ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    check("user_id matches login", row['user_id'] == uid)

    # Log out after test 2
    c.post('/api/auth/logout')

    # ------------------------------------------------------------------
    # Test 3 — Missing name → 400
    # ------------------------------------------------------------------
    print("\nTest 3: Missing name → 400")
    before = _count_messages()
    r = _submit(c, name='')
    check("Status 400",        r.status_code == 400)
    check("No message saved",  _count_messages() == before)

    # ------------------------------------------------------------------
    # Test 4 — Missing / bad email → 400
    # ------------------------------------------------------------------
    print("\nTest 4: Bad email → 400")
    r = _submit(c, email='')
    check("Empty email → 400",         r.status_code == 400)
    r = _submit(c, email='notanemail')
    check("No @ email → 400",          r.status_code == 400)
    r = _submit(c, email='bad@nodot')
    check("No dot in domain → 400",    r.status_code == 400)

    # ------------------------------------------------------------------
    # Test 5 — Missing message → 400
    # ------------------------------------------------------------------
    print("\nTest 5: Missing message → 400")
    r = _submit(c, message='')
    check("Status 400",   r.status_code == 400)

    # ------------------------------------------------------------------
    # Test 6 — Invalid category → 400
    # ------------------------------------------------------------------
    print("\nTest 6: Invalid category → 400")
    r = _submit(c, category='Hack attempt')
    check("Status 400",   r.status_code == 400)
    r = _submit(c, category='')
    check("Empty category → 400",   r.status_code == 400)

    # ------------------------------------------------------------------
    # Test 7 — Honeypot filled → 200 but NOT saved
    # ------------------------------------------------------------------
    print("\nTest 7: Honeypot filled → silently discarded")
    before = _count_messages()
    r = _submit(c, website='http://spam.bot')
    check("Status 200 (silent)",   r.status_code == 200)
    check("NOT saved in DB",       _count_messages() == before)

    # ------------------------------------------------------------------
    # Test 8 — Admin GET /admin/contacts → returns messages
    # ------------------------------------------------------------------
    print("\nTest 8: Admin GET /admin/contacts")
    admin_uid = _create_user('admin@karvii.com', name='Admin', is_admin=True)
    _login(c, 'admin@karvii.com')
    r = c.get('/api/admin/contacts')
    data = r.get_json()
    check("Status 200",               r.status_code == 200)
    check("'messages' key present",   'messages' in data)
    check("Has messages",             len(data['messages']) > 0)

    # ------------------------------------------------------------------
    # Test 9 — Admin filter ?status=new
    # ------------------------------------------------------------------
    print("\nTest 9: Admin filter ?status=new")
    r = c.get('/api/admin/contacts?status=new')
    data = r.get_json()
    check("Status 200",               r.status_code == 200)
    all_new = all(m['status'] == 'new' for m in data['messages'])
    check("All returned are 'new'",   all_new)

    # ------------------------------------------------------------------
    # Test 10 — Admin resolve → status = resolved
    # ------------------------------------------------------------------
    print("\nTest 10: Admin mark resolved")
    conn = _conn()
    first = conn.execute("SELECT id FROM contact_messages WHERE status='new' LIMIT 1").fetchone()
    conn.close()
    msg_id = first['id']
    r = c.patch(f'/api/admin/contacts/{msg_id}/resolve')
    check("Status 200",   r.status_code == 200)
    conn = _conn()
    updated = conn.execute("SELECT status FROM contact_messages WHERE id=?", (msg_id,)).fetchone()
    conn.close()
    check("status = 'resolved' in DB",   updated['status'] == 'resolved')

    r = c.patch('/api/admin/contacts/99999/resolve')
    check("Unknown ID → 404",   r.status_code == 404)

    c.post('/api/auth/logout')

    # ------------------------------------------------------------------
    # Test 11 — Unauthenticated → 401
    # ------------------------------------------------------------------
    print("\nTest 11: Unauthenticated admin endpoints → 401")
    r = c.get('/api/admin/contacts')
    check("GET unauthenticated → 401",   r.status_code == 401)
    r = c.patch(f'/api/admin/contacts/{msg_id}/resolve')
    check("PATCH unauthenticated → 401", r.status_code == 401)

    # ------------------------------------------------------------------
    # Test 12 — Non-admin → 403
    # ------------------------------------------------------------------
    print("\nTest 12: Non-admin → 403")
    _login(c, 'customer@example.com')
    r = c.get('/api/admin/contacts')
    check("GET non-admin → 403",   r.status_code == 403)
    r = c.patch(f'/api/admin/contacts/{msg_id}/resolve')
    check("PATCH non-admin → 403", r.status_code == 403)
    c.post('/api/auth/logout')


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
passed = sum(1 for s, _, _ in results if s == PASS)
failed = sum(1 for s, _, _ in results if s == FAIL)
print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed out of {len(results)} checks")
if failed == 0:
    print("ALL TESTS PASSED — Feature 17 is ready.")
else:
    print("SOME TESTS FAILED — review output above.")
print('='*50)
sys.exit(0 if failed == 0 else 1)
