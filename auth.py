import os

from flask import (
    Blueprint, jsonify, redirect, request, url_for
)
from flask_login import (
    LoginManager, UserMixin, current_user, login_required as _login_required,
    login_user, logout_user
)
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db

auth = Blueprint('auth', __name__)

login_required = _login_required


class User(UserMixin):
    def __init__(self, row):
        self.id = str(row['id'])
        self.name = row['name']
        self.email = row['email']
        self.is_admin = bool(row['is_admin']) if 'is_admin' in row.keys() else False
        self.phone = row['phone'] if 'phone' in row.keys() else None
        self.avatar = row['avatar'] if 'avatar' in row.keys() else None
        self.notify_email = bool(row['notify_email']) if 'notify_email' in row.keys() else True

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'is_admin': self.is_admin,
            'phone': self.phone,
            'avatar': self.avatar,
            'notify_email': self.notify_email,
        }


def load_user_by_id(user_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return User(row) if row else None
    finally:
        conn.close()


def init_login_manager(app):
    lm = LoginManager(app)
    lm.login_view = 'auth.login'

    @lm.user_loader
    def user_loader(user_id):
        return load_user_by_id(user_id)

    @lm.unauthorized_handler
    def unauthorized():
        return jsonify({'error': 'Authentication required', 'login_required': True}), 401


# ---------------------------------------------------------------------------
# JSON API — signup / login / logout / me
# ---------------------------------------------------------------------------

@auth.route('/api/auth/signup', methods=['POST'])
def api_signup():
    data = request.get_json(silent=True) or {}
    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm  = data.get('confirm_password', '')

    if not name:
        return jsonify({'error': 'Name is required.'}), 400
    if not email or '@' not in email:
        return jsonify({'error': 'A valid email address is required.'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400
    if password != confirm:
        return jsonify({'error': 'Passwords do not match.'}), 400

    conn = get_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return jsonify({'error': 'An account with that email already exists.'}), 409
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()

    user = User(row)
    login_user(user)
    return jsonify({'user': user.to_dict()}), 201


@auth.route('/api/auth/login', methods=['POST'])
def api_login():
    data     = request.get_json(silent=True) or {}
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')
    remember = bool(data.get('remember', False))

    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()

    if not row or not row['password_hash'] or not check_password_hash(row['password_hash'], password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    user = User(row)
    login_user(user, remember=remember)
    return jsonify({'user': user.to_dict()})


@auth.route('/api/auth/logout', methods=['POST'])
def api_logout():
    logout_user()
    return jsonify({'success': True})


@auth.route('/api/auth/me')
def api_me():
    if current_user.is_authenticated:
        return jsonify({'user': current_user.to_dict()})
    return jsonify({'user': None})


# ---------------------------------------------------------------------------
# Google OAuth (keep original paths — uses redirects)
# ---------------------------------------------------------------------------

@auth.route('/login/google')
def google_login():
    from flask import current_app
    callback = url_for('auth.google_callback', _external=True)
    return current_app.oauth.google.authorize_redirect(callback)


@auth.route('/login/google/callback')
def google_callback():
    from flask import current_app
    try:
        token = current_app.oauth.google.authorize_access_token()
    except Exception:
        return redirect('/?error=google_login_failed')

    info = token.get('userinfo') or current_app.oauth.google.userinfo(token=token)
    google_id = info['sub']
    email = info.get('email', '').lower()
    name = info.get('name', email)

    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE google_id = ?", (google_id,)).fetchone()

        if not row and email:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if row:
                conn.execute("UPDATE users SET google_id = ? WHERE id = ?", (google_id, row['id']))
                conn.commit()
                row = conn.execute("SELECT * FROM users WHERE id = ?", (row['id'],)).fetchone()

        if not row:
            conn.execute(
                "INSERT INTO users (name, email, google_id) VALUES (?, ?, ?)",
                (name, email, google_id),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM users WHERE google_id = ?", (google_id,)).fetchone()
    finally:
        conn.close()

    login_user(User(row))
    return redirect('/')


def init_google_oauth(oauth):
    oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )
