"""
Acceptance-criteria tests for feature 02 — User Authentication.
Run with:  python test_auth.py
"""
import sqlite3
import os
import tempfile
import shutil

os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('GOOGLE_CLIENT_ID', 'test')
os.environ.setdefault('GOOGLE_CLIENT_SECRET', 'test')

# Use a temp DB so tests don't touch ecommerce.db
_tmp = tempfile.mkdtemp()
_test_db = os.path.join(_tmp, 'test.db')

import db as _db
_db.DATABASE = _test_db

from app import app

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

# Register the protected route before any requests are handled
from auth import login_required as _lr

@app.route('/secret-page')
@_lr
def secret_page():
    return 'secret content'


def get_client():
    return app.test_client()


def _hash(val):
    from werkzeug.security import check_password_hash
    return check_password_hash


def test_ac1_signup_creates_user():
    c = get_client()
    r = c.post('/signup', data={
        'name': 'Alice', 'email': 'alice@test.com',
        'password': 'password123', 'confirm_password': 'password123'
    }, follow_redirects=True)
    assert r.status_code == 200
    assert b'Welcome' in r.data
    conn = sqlite3.connect(_test_db)
    row = conn.execute("SELECT * FROM users WHERE email='alice@test.com'").fetchone()
    conn.close()
    assert row is not None
    print('AC-1 PASS: signup creates user and redirects home')


def test_ac2_duplicate_email_blocked():
    c = get_client()
    r = c.post('/signup', data={
        'name': 'Alice2', 'email': 'alice@test.com',
        'password': 'password123', 'confirm_password': 'password123'
    })
    assert b'already registered' in r.data
    print('AC-2 PASS: duplicate email rejected')


def test_ac3_password_rules():
    c = get_client()
    r = c.post('/signup', data={
        'name': 'X', 'email': 'new@test.com',
        'password': 'short', 'confirm_password': 'short'
    })
    assert b'8 characters' in r.data
    print('AC-3a PASS: short password rejected')

    r2 = c.post('/signup', data={
        'name': 'X', 'email': 'new@test.com',
        'password': 'longpassword1', 'confirm_password': 'different'
    })
    assert b'do not match' in r2.data
    print('AC-3b PASS: mismatched passwords rejected')


def test_ac4_correct_login():
    c = get_client()
    r = c.post('/login', data={
        'email': 'alice@test.com', 'password': 'password123'
    }, follow_redirects=True)
    assert r.status_code == 200
    assert b'Welcome' in r.data
    print('AC-4 PASS: correct login redirects home')


def test_ac5_wrong_credentials_generic():
    c = get_client()
    r = c.post('/login', data={'email': 'alice@test.com', 'password': 'wrongpass'})
    assert b'Invalid email or password' in r.data
    r2 = c.post('/login', data={'email': 'nobody@test.com', 'password': 'whatever'})
    assert b'Invalid email or password' in r2.data
    print('AC-5 PASS: wrong credentials show generic error (not which field)')


def test_ac6_password_stored_hashed():
    conn = sqlite3.connect(_test_db)
    row = conn.execute("SELECT password_hash FROM users WHERE email='alice@test.com'").fetchone()
    conn.close()
    h = row[0]
    assert h is not None
    assert not h.startswith('pass')
    assert len(h) > 30
    print(f'AC-6 PASS: password stored hashed ({h[:20]}...)')


def test_ac9_logout():
    c = get_client()
    c.post('/login', data={'email': 'alice@test.com', 'password': 'password123'})
    r = c.get('/logout', follow_redirects=False)
    assert r.status_code == 302
    assert b'/login' in r.data or 'login' in r.headers.get('Location', '')
    print('AC-9 PASS: logout redirects to login')


def test_ac10_login_required():
    c = get_client()
    r = c.get('/secret-page', follow_redirects=False)
    assert r.status_code == 302
    location = r.headers.get('Location', '')
    assert 'login' in location
    print('AC-10 PASS: protected route redirects logged-out user to /login')


if __name__ == '__main__':
    tests = [
        test_ac1_signup_creates_user,
        test_ac2_duplicate_email_blocked,
        test_ac3_password_rules,
        test_ac4_correct_login,
        test_ac5_wrong_credentials_generic,
        test_ac6_password_stored_hashed,
        test_ac9_logout,
        test_ac10_login_required,
    ]
    passed = 0
    failed = 0
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
