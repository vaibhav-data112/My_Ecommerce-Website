import functools
import os

from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for
)
from flask_login import (
    LoginManager, UserMixin, current_user, login_required as _login_required,
    login_user, logout_user
)
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db

auth = Blueprint('auth', __name__)


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------

class User(UserMixin):
    def __init__(self, row):
        self.id = str(row['id'])
        self.name = row['name']
        self.email = row['email']
        self.is_admin = bool(row['is_admin']) if 'is_admin' in row.keys() else False
        self.phone = row['phone'] if 'phone' in row.keys() else None
        self.avatar = row['avatar'] if 'avatar' in row.keys() else None
        self.notify_email = bool(row['notify_email']) if 'notify_email' in row.keys() else True


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
    lm.login_message = 'Please log in to access this page.'

    @lm.user_loader
    def user_loader(user_id):
        return load_user_by_id(user_id)


# ---------------------------------------------------------------------------
# login_required decorator (re-exports Flask-Login's but with `next` support)
# ---------------------------------------------------------------------------

login_required = _login_required


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------

@auth.route('/signup', methods=['GET'])
def signup():
    return render_template('auth/signup.html')


@auth.route('/signup', methods=['POST'])
def signup_post():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')

    error = None
    if not name:
        error = 'Name is required.'
    elif not email or '@' not in email:
        error = 'A valid email address is required.'
    elif len(password) < 8:
        error = 'Password must be at least 8 characters.'
    elif password != confirm:
        error = 'Passwords do not match.'

    if error:
        flash(error, 'error')
        return render_template('auth/signup.html', name=name, email=email)

    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            flash('An account with that email is already registered.', 'error')
            return render_template('auth/signup.html', name=name, email=email)

        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()

    login_user(User(row))
    return redirect(url_for('index'))


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@auth.route('/login', methods=['GET'])
def login():
    return render_template('auth/login.html')


@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    remember = bool(request.form.get('remember'))
    next_page = request.args.get('next') or request.form.get('next') or url_for('index')

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()

    if not row or not row['password_hash'] or not check_password_hash(row['password_hash'], password):
        flash('Invalid email or password.', 'error')
        return render_template('auth/login.html', email=email, next=next_page)

    login_user(User(row), remember=remember)
    return redirect(next_page)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@auth.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

def init_google_oauth(oauth):
    oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )


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
        flash('Google login failed. Please try again.', 'error')
        return redirect(url_for('auth.login'))

    info = token.get('userinfo') or current_app.oauth.google.userinfo(token=token)
    google_id = info['sub']
    email = info.get('email', '').lower()
    name = info.get('name', email)

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE google_id = ?", (google_id,)
        ).fetchone()

        if not row and email:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE users SET google_id = ? WHERE id = ?",
                    (google_id, row['id']),
                )
                conn.commit()
                row = conn.execute(
                    "SELECT * FROM users WHERE id = ?", (row['id'],)
                ).fetchone()

        if not row:
            conn.execute(
                "INSERT INTO users (name, email, google_id) VALUES (?, ?, ?)",
                (name, email, google_id),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM users WHERE google_id = ?", (google_id,)
            ).fetchone()
    finally:
        conn.close()

    login_user(User(row))
    return redirect(url_for('index'))
