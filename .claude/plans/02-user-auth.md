# Implementation Plan — 02 User Authentication

## Context

Feature 01 established the database layer: `db.py` (`get_db`, `init_db`, `seed_db`), `app.py` (Flask entry point), and `ecommerce.db` (SQLite). The `users` table already has `id`, `name`, `email`, `password_hash`, `created_at`. `werkzeug` password hashing is already in use.

This plan adds email/password auth and Google OAuth login, session management, a `current_user` helper, and a `login_required` decorator.

Tech additions: **Flask-Login** (session management), **Authlib** (Google OAuth), `python-dotenv` (secret management).

---

## Database Migration

The `users` table needs two safe changes:
1. `password_hash` becomes nullable (Google-only users have no password).
2. A new `google_id TEXT UNIQUE` column is added.

SQLite cannot alter column constraints, so the migration adds `google_id` via `ALTER TABLE` and handles the nullable `password_hash` at the application level (the column is already `TEXT NOT NULL` but we will add the column and then manage constraints in code — existing rows keep their hashes).

Add a `migrate_db()` function to `db.py` that runs once and is idempotent:

```python
def migrate_db():
    conn = get_db()
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if 'google_id' not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN google_id TEXT UNIQUE")
            conn.commit()
    finally:
        conn.close()
```

Call `migrate_db()` in `app.py` alongside `init_db()`.

---

## Files to Create

### `auth.py` — Authentication blueprint

Register as a Flask Blueprint (`url_prefix='/'`). Contains all auth routes and helpers.

**Routes:**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/signup` | Render signup form |
| POST | `/signup` | Create account |
| GET | `/login` | Render login form |
| POST | `/login` | Authenticate user |
| GET | `/login/google` | Start Google OAuth flow |
| GET | `/login/google/callback` | Handle Google OAuth callback |
| GET/POST | `/logout` | End session |

**Helpers:**

- `get_current_user()` — returns the logged-in `User` object or `None`.
- `login_required` decorator — redirects to `/login` (with `next` param) if not authenticated.

**User class** (for Flask-Login):

```python
class User(UserMixin):
    def __init__(self, row):   # row is a sqlite3.Row
        self.id = row['id']
        self.name = row['name']
        self.email = row['email']
```

**Signup logic (`POST /signup`):**
1. Validate: name non-empty, valid email format, password ≥ 8 chars, passwords match.
2. Check email not already in `users`.
3. `generate_password_hash(password)` → insert user.
4. Log in via Flask-Login, redirect to `/`.

**Login logic (`POST /login`):**
1. Look up user by email.
2. `check_password_hash(stored, submitted)`.
3. On success: `login_user(user, remember=bool(form.remember))`, redirect to `next` or `/`.
4. On failure: generic "Invalid email or password" flash — never reveal which field was wrong.

**Google OAuth (`/login/google` and `/login/google/callback`):**
1. `/login/google` → `oauth.google.authorize_redirect(callback_url)`.
2. Callback: `token = oauth.google.authorize_access_token()`, extract `userinfo`.
3. Look up user by `google_id`; if none, try by email (link accounts); if still none, create new user (no `password_hash`).
4. Log in user, redirect to `/`.

**Logout (`/logout`):**
- `logout_user()`, redirect to `/login`.

### `templates/auth/signup.html`

Extends `base.html`. Form fields: name, email, password, confirm password. "Continue with Google" button linking to `/login/google`. Shows flashed errors.

### `templates/auth/login.html`

Extends `base.html`. Form fields: email, password, "Remember me" checkbox. "Continue with Google" button. Shows flashed errors. Link to `/signup`.

### `templates/base.html`

Minimal base template with a nav bar showing:
- Logged-out: "Login" and "Sign Up" links.
- Logged-in: user name and "Logout" button.

### `.env` (not committed)

```
SECRET_KEY=<random string>
GOOGLE_CLIENT_ID=<from Google Cloud Console>
GOOGLE_CLIENT_SECRET=<from Google Cloud Console>
```

---

## Files to Change

### `db.py`
- Add `migrate_db()` (see above).

### `app.py`
- Load `.env` via `python-dotenv` before app creation.
- Set `app.secret_key` from `os.environ['SECRET_KEY']`.
- Call `migrate_db()` on startup.
- Init Flask-Login: `LoginManager(app)`, set `login_view = 'auth.login'`.
- Register `auth` blueprint.
- Init Authlib OAuth with Google provider using env vars.
- Add a root route `GET /` that renders a simple home page (placeholder until feature 03).

### `requirements.txt`
```
flask>=3.0.0
flask-login>=0.6.3
authlib>=1.3.0
python-dotenv>=1.0.0
requests>=2.31.0
```

### `.gitignore`
Add `.env` if not already present.

---

## Security Rules

- Passwords: `generate_password_hash` / `check_password_hash` only (werkzeug PBKDF2).
- Generic login error: never say "email not found" vs "wrong password".
- Google Client ID/Secret: loaded from `.env`; never hardcoded or committed.
- `SECRET_KEY`: loaded from `.env`; never hardcoded.
- All SQL: parameterised `?` placeholders only.
- `login_required` decorator stores `next` URL and redirects back after login.
- Sessions: Flask's signed cookie sessions (secure when `SECRET_KEY` is strong).

---

## Google Cloud Setup (one-time, manual)

1. Go to [console.cloud.google.com](https://console.cloud.google.com), create a project.
2. Enable **Google+ API** (or People API).
3. Create OAuth 2.0 credentials (Web application type).
4. Add `http://127.0.0.1:5000/login/google/callback` as an authorised redirect URI.
5. Copy Client ID and Secret into `.env`.

---

## Verification (Acceptance Criteria)

```bash
pip install -r requirements.txt
# Create .env with SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
python app.py

# AC-1: signup with new email → user created, redirected home
# AC-2: signup with existing email → "email already registered" error shown
# AC-3: short password / mismatched → validation error shown
# AC-4: login with correct credentials → redirected home
# AC-5: wrong credentials → generic "Invalid email or password"
# AC-6: check DB: SELECT password_hash FROM users → hashed value, not plain text
# AC-7: navigate between pages while logged in → stays logged in
# AC-8: "Remember me" checked → session survives browser close
# AC-9: logout → /login, protected pages redirect back to /login
# AC-10: visit protected page while logged out → redirect to /login?next=...
# AC-11/12: Google login → new account created or existing account matched
```

---

## Definition of Done

- [ ] User can sign up with name, email, and password.
- [ ] Duplicate email rejected with a clear message.
- [ ] Password rules (≥8 chars, must match) enforced at signup.
- [ ] Passwords stored as hashed values only.
- [ ] User can log in with correct email + password.
- [ ] Wrong credentials show a generic error message.
- [ ] User stays logged in while browsing pages.
- [ ] "Remember me" controls session persistence across browser close.
- [ ] Logout ends the session.
- [ ] Protected pages redirect logged-out users to login, then back.
- [ ] "Continue with Google" creates a new account for first-time Google users.
- [ ] "Continue with Google" logs returning Google users into their existing account (no duplicates).
- [ ] Google Client ID/Secret are NOT committed to GitHub (`.env` in `.gitignore`).
