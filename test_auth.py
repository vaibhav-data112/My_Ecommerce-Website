"""
Acceptance-criteria tests for feature 02 — User Authentication.
Run with:  python test_auth.py
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

def _login(client, email, password='password123'):
    return client.post('/api/auth/login', json={'email': email, 'password': password})


def _signup(client, name, email, password='password123'):
    return client.post('/api/auth/signup', json={
        'name': name, 'email': email,
        'password': password, 'confirm_password': password,
    })


# ---------------------------------------------------------------------------
# AC-1: Signup creates a user row in DB and returns user object
# ---------------------------------------------------------------------------

def test_ac1_signup_creates_user():
    c = app.test_client()
    r = _signup(c, 'Alice', 'alice@test.com')
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.get_json()}"
    data = r.get_json()
    assert 'user' in data
    assert data['user']['email'] == 'alice@test.com'
    assert data['user']['name'] == 'Alice'

    conn = sqlite3.connect(_test_db)
    row = conn.execute("SELECT * FROM users WHERE email='alice@test.com'").fetchone()
    conn.close()
    assert row is not None, "User row not found in DB after signup"
    print('AC-1 PASS: signup creates user and returns user object')


# ---------------------------------------------------------------------------
# AC-2: Duplicate email returns 409
# ---------------------------------------------------------------------------

def test_ac2_duplicate_email_blocked():
    c = app.test_client()
    r = _signup(c, 'Alice2', 'alice@test.com')
    assert r.status_code == 409, f"Expected 409, got {r.status_code}"
    data = r.get_json()
    assert 'error' in data
    assert 'already' in data['error'].lower()
    print('AC-2 PASS: duplicate email returns 409 with error message')


# ---------------------------------------------------------------------------
# AC-3: Password validation — too short / mismatched
# ---------------------------------------------------------------------------

def test_ac3_password_rules():
    c = app.test_client()

    r = c.post('/api/auth/signup', json={
        'name': 'X', 'email': 'new@test.com',
        'password': 'short', 'confirm_password': 'short',
    })
    assert r.status_code == 400, f"AC-3a: Expected 400 for short password, got {r.status_code}"
    assert '8' in r.get_json().get('error', '')
    print('AC-3a PASS: short password returns 400')

    r2 = c.post('/api/auth/signup', json={
        'name': 'X', 'email': 'new@test.com',
        'password': 'longpassword1', 'confirm_password': 'different',
    })
    assert r2.status_code == 400, f"AC-3b: Expected 400 for mismatched passwords, got {r2.status_code}"
    assert 'match' in r2.get_json().get('error', '').lower()
    print('AC-3b PASS: mismatched passwords return 400')


# ---------------------------------------------------------------------------
# AC-4: Correct login returns user object with 200
# ---------------------------------------------------------------------------

def test_ac4_correct_login():
    c = app.test_client()
    r = _login(c, 'alice@test.com')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.get_json()}"
    data = r.get_json()
    assert 'user' in data
    assert data['user']['email'] == 'alice@test.com'
    print('AC-4 PASS: correct login returns 200 with user object')


# ---------------------------------------------------------------------------
# AC-5: Wrong credentials return 401 with generic message
# ---------------------------------------------------------------------------

def test_ac5_wrong_credentials_generic():
    c = app.test_client()

    r = _login(c, 'alice@test.com', 'wrongpass')
    assert r.status_code == 401, f"AC-5a: Expected 401, got {r.status_code}"
    data = r.get_json()
    assert 'Invalid' in data.get('error', '')

    r2 = _login(c, 'nobody@test.com', 'whatever')
    assert r2.status_code == 401, f"AC-5b: Expected 401, got {r2.status_code}"
    assert 'Invalid' in r2.get_json().get('error', '')
    print('AC-5 PASS: wrong credentials return 401 with generic error')


# ---------------------------------------------------------------------------
# AC-6: Password is stored hashed (not plaintext)
# ---------------------------------------------------------------------------

def test_ac6_password_stored_hashed():
    conn = sqlite3.connect(_test_db)
    row = conn.execute("SELECT password_hash FROM users WHERE email='alice@test.com'").fetchone()
    conn.close()
    h = row[0]
    assert h is not None
    assert not h.startswith('password')
    assert len(h) > 30
    print(f'AC-6 PASS: password stored hashed ({h[:20]}...)')


# ---------------------------------------------------------------------------
# AC-7: /api/auth/me returns current user when logged in
# ---------------------------------------------------------------------------

def test_ac7_me_endpoint():
    c = app.test_client()
    _login(c, 'alice@test.com')
    r = c.get('/api/auth/me')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert data['user'] is not None
    assert data['user']['email'] == 'alice@test.com'
    print('AC-7 PASS: /api/auth/me returns logged-in user')


# ---------------------------------------------------------------------------
# AC-8: /api/auth/me returns null user when not logged in
# ---------------------------------------------------------------------------

def test_ac8_me_unauthenticated():
    c = app.test_client()
    r = c.get('/api/auth/me')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.get_json()
    assert data['user'] is None
    print('AC-8 PASS: /api/auth/me returns null user when not logged in')


# ---------------------------------------------------------------------------
# AC-9: Logout returns success; subsequent /api/auth/me shows null user
# ---------------------------------------------------------------------------

def test_ac9_logout():
    c = app.test_client()
    _login(c, 'alice@test.com')

    r = c.post('/api/auth/logout')
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.get_json().get('success') is True

    r2 = c.get('/api/auth/me')
    assert r2.get_json()['user'] is None
    print('AC-9 PASS: logout clears session; /api/auth/me returns null afterwards')


# ---------------------------------------------------------------------------
# AC-10: Protected route returns 401 for unauthenticated user
# ---------------------------------------------------------------------------

def test_ac10_login_required():
    c = app.test_client()
    r = c.get('/api/cart')
    assert r.status_code == 401, f"Expected 401 for unauthenticated /api/cart, got {r.status_code}"
    data = r.get_json()
    assert 'login_required' in data or 'error' in data
    print('AC-10 PASS: protected route returns 401 for unauthenticated user')


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    tests = [
        test_ac1_signup_creates_user,
        test_ac2_duplicate_email_blocked,
        test_ac3_password_rules,
        test_ac4_correct_login,
        test_ac5_wrong_credentials_generic,
        test_ac6_password_stored_hashed,
        test_ac7_me_endpoint,
        test_ac8_me_unauthenticated,
        test_ac9_logout,
        test_ac10_login_required,
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
