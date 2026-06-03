# Plan 13 — My Account Hub

## Overview

Build a full account management area: avatar circle in the navbar with a click-to-open dropdown, a `/account` page with left-sidebar layout, profile editing (name, phone, photo upload), saved addresses (add/edit/delete/default), password change, and notification preferences. Pattern mirrors how the `wishlist` and `admin` features were built.

---

## Files to Create

| File | Purpose |
|------|---------|
| `account.py` | Flask Blueprint — all `/account/*` routes |
| `templates/account/layout.html` | Shared sidebar+content base for all account pages |
| `templates/account/dashboard.html` | `/account` — greeting, avatar, quick-link cards |
| `templates/account/profile.html` | Profile edit (name, phone, photo upload) |
| `templates/account/addresses.html` | Saved addresses list + add form |
| `templates/account/settings.html` | Password change + notification preferences |

## Files to Modify

| File | What changes |
|------|-------------|
| `db.py` | 3 new `users` columns via `migrate_db()`, new `addresses` table, 8+ helper functions |
| `auth.py` | Add `phone`, `avatar`, `notify_email` fields to the `User` model |
| `app.py` | Import + register `account` blueprint; add `os.makedirs` for avatars upload dir |
| `templates/base.html` | Replace flat nav (user-name span, logout, admin link) with avatar circle + CSS dropdown |
| `static/css/style.css` | Avatar circle, dropdown, account layout, sidebar, quick-link cards, address cards |

---

## Step-by-Step Implementation

### Step 1 — DB: 3 columns in `users` + new `addresses` table (`db.py → migrate_db()`)

Append to `migrate_db()`, after the `wishlist_items` block:

```python
# users — phone, avatar, notify_email
users_cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
for col, ddl in [
    ('phone',        "ALTER TABLE users ADD COLUMN phone TEXT"),
    ('avatar',       "ALTER TABLE users ADD COLUMN avatar TEXT"),
    ('notify_email', "ALTER TABLE users ADD COLUMN notify_email INTEGER NOT NULL DEFAULT 1"),
]:
    if col not in users_cols:
        conn.execute(ddl)

# addresses table
conn.execute("""
    CREATE TABLE IF NOT EXISTS addresses (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER NOT NULL,
        full_name    TEXT    NOT NULL,
        phone        TEXT    NOT NULL,
        address_line TEXT    NOT NULL,
        city         TEXT    NOT NULL,
        state        TEXT    NOT NULL,
        pincode      TEXT    NOT NULL,
        is_default   INTEGER NOT NULL DEFAULT 0,
        created_at   TEXT    DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")
```

`created_at` already exists on `users` (from `init_db()`), so no migration needed for it.

### Step 2 — DB: Helper functions (`db.py`)

Add a `# Account helpers` section after the wishlist helpers:

```python
def get_user_by_id(user_id):
    # Returns the full row (used in account pages to get phone, avatar, notify_email)
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()

def update_profile(user_id, name, phone, avatar_path=None):
    conn = get_db()
    try:
        if avatar_path is not None:
            conn.execute(
                "UPDATE users SET name=?, phone=?, avatar=? WHERE id=?",
                (name, phone or None, avatar_path, user_id)
            )
        else:
            conn.execute(
                "UPDATE users SET name=?, phone=? WHERE id=?",
                (name, phone or None, user_id)
            )
        conn.commit()
    finally:
        conn.close()

def change_password(user_id, new_hash):
    conn = get_db()
    try:
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user_id))
        conn.commit()
    finally:
        conn.close()

def update_notify_pref(user_id, notify_email):
    conn = get_db()
    try:
        conn.execute("UPDATE users SET notify_email=? WHERE id=?", (int(notify_email), user_id))
        conn.commit()
    finally:
        conn.close()

def get_addresses(user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM addresses WHERE user_id=? ORDER BY is_default DESC, created_at ASC",
            (user_id,)
        ).fetchall()
    finally:
        conn.close()

def get_address_by_id(address_id):
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM addresses WHERE id=?", (address_id,)).fetchone()
    finally:
        conn.close()

def add_address(user_id, full_name, phone, address_line, city, state, pincode):
    conn = get_db()
    try:
        # If this is the user's first address, make it default
        count = conn.execute(
            "SELECT COUNT(*) FROM addresses WHERE user_id=?", (user_id,)
        ).fetchone()[0]
        is_default = 1 if count == 0 else 0
        conn.execute("""
            INSERT INTO addresses (user_id, full_name, phone, address_line, city, state, pincode, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, full_name, phone, address_line, city, state, pincode, is_default))
        conn.commit()
    finally:
        conn.close()

def update_address(address_id, full_name, phone, address_line, city, state, pincode):
    conn = get_db()
    try:
        conn.execute("""
            UPDATE addresses SET full_name=?, phone=?, address_line=?, city=?, state=?, pincode=?
            WHERE id=?
        """, (full_name, phone, address_line, city, state, pincode, address_id))
        conn.commit()
    finally:
        conn.close()

def delete_address(user_id, address_id):
    conn = get_db()
    try:
        addr = conn.execute("SELECT is_default FROM addresses WHERE id=? AND user_id=?",
                            (address_id, user_id)).fetchone()
        conn.execute("DELETE FROM addresses WHERE id=? AND user_id=?", (address_id, user_id))
        # If deleted address was default, promote the next one
        if addr and addr['is_default']:
            next_addr = conn.execute(
                "SELECT id FROM addresses WHERE user_id=? ORDER BY created_at ASC LIMIT 1",
                (user_id,)
            ).fetchone()
            if next_addr:
                conn.execute("UPDATE addresses SET is_default=1 WHERE id=?", (next_addr['id'],))
        conn.commit()
    finally:
        conn.close()

def set_default_address(user_id, address_id):
    conn = get_db()
    try:
        conn.execute("UPDATE addresses SET is_default=0 WHERE user_id=?", (user_id,))
        conn.execute("UPDATE addresses SET is_default=1 WHERE id=? AND user_id=?",
                     (address_id, user_id))
        conn.commit()
    finally:
        conn.close()
```

### Step 3 — Update `User` model (`auth.py`)

Add `phone`, `avatar`, `notify_email` to `User.__init__`. Use `.keys()` check (same pattern as `is_admin`) to stay backward-safe during startup before `migrate_db()` runs:

```python
class User(UserMixin):
    def __init__(self, row):
        self.id = str(row['id'])
        self.name = row['name']
        self.email = row['email']
        self.is_admin = bool(row['is_admin']) if 'is_admin' in row.keys() else False
        self.phone = row['phone'] if 'phone' in row.keys() else None
        self.avatar = row['avatar'] if 'avatar' in row.keys() else None
        self.notify_email = bool(row['notify_email']) if 'notify_email' in row.keys() else True
```

### Step 4 — Blueprint: `account.py`

Eight routes:

| Route | Method | Action |
|-------|--------|--------|
| `/account` | GET | Dashboard — greeting, avatar, quick links |
| `/account/profile` | GET/POST | Edit name, phone, upload avatar photo |
| `/account/addresses` | GET | List saved addresses |
| `/account/addresses/new` | POST | Add new address |
| `/account/addresses/<id>/edit` | GET/POST | Edit existing address |
| `/account/addresses/<id>/delete` | POST | Delete address |
| `/account/addresses/<id>/default` | POST | Set as default |
| `/account/settings` | GET/POST | Password change + notification pref (one page) |

Privacy enforcement: for address routes, always check `address['user_id'] == current_user.id` after fetching; `abort(403)` if mismatch.

Avatar upload: save to `static/uploads/avatars/`, filename `{user_id}_{secure_filename}`. Validate extension (jpg/jpeg/png/webp) and size (max 5 MB). Store path relative to `static/` in the DB (e.g. `uploads/avatars/1_photo.jpg`).

Password change logic: 
- If `current_user.is_google_only` (password_hash is NULL in DB) → show friendly message, skip form.
- Else: verify old password with `check_password_hash`, check new == confirm, then `change_password()`.

`is_google_only` helper property: check `password_hash IS NULL` by fetching the raw row via `get_user_by_id`.

### Step 5 — Register blueprint + avatar dir (`app.py`)

```python
from account import account as account_blueprint
app.register_blueprint(account_blueprint)
os.makedirs(os.path.join('static', 'uploads', 'avatars'), exist_ok=True)
```

### Step 6 — Navbar revamp (`templates/base.html`)

**Design (revised):** No avatar circle, no click-to-open dropdown. Every account link is directly visible in the navbar.

**Authenticated nav — all links shown directly:**
- My Profile → `/account/`
- My Orders → `/orders`
- My Wishlist (with badge) → `/wishlist`
- Saved Addresses → `/account/addresses`
- Settings → `/account/settings`
- Cart (with badge) → `/cart`
- Admin (gold, if admin) → `/admin`
- Logout button (styled as nav item)

**Guest nav — Login + hover-preview dropdown:**
- "Login" button: on hover shows a CSS dropdown listing My Profile, My Orders, My Wishlist, Saved Addresses, Settings — all greyed-out/disabled (cursor: not-allowed, opacity 0.55). This previews what becomes available after login.
- "Sign Up" button stays as-is.

```html
<!-- Authenticated nav -->
<a href="{{ url_for('account.dashboard') }}">My Profile</a>
<a href="{{ url_for('orders.order_history') }}">My Orders</a>
<a href="{{ url_for('wishlist.view_wishlist') }}">
    My Wishlist{% if wishlist_count > 0 %}<span class="cart-badge">{{ wishlist_count }}</span>{% endif %}
</a>
<a href="{{ url_for('account.addresses') }}">Saved Addresses</a>
<a href="{{ url_for('account.settings') }}">Settings</a>
<a href="{{ url_for('cart.view_cart') }}">
    Cart{% if cart_count > 0 %}<span class="cart-badge">{{ cart_count }}</span>{% endif %}
</a>
{% if current_user.is_admin %}
    <a href="{{ url_for('admin.dashboard') }}" class="admin-link">Admin</a>
{% endif %}
<form method="post" action="/logout" style="display:inline">
    <button type="submit" class="nav-logout-btn">Logout</button>
</form>

<!-- Guest nav -->
<div class="login-hover-wrap">
    <a href="/login" class="btn btn-outline nav-login-btn">Login</a>
    <div class="login-preview-dropdown">
        <div class="preview-header">Login to access</div>
        <span class="preview-link">My Profile</span>
        <span class="preview-link">My Orders</span>
        <span class="preview-link">My Wishlist</span>
        <span class="preview-link">Saved Addresses</span>
        <span class="preview-link">Settings</span>
    </div>
</div>
<a href="/signup" class="btn btn-primary">Sign Up</a>
```

CSS key classes: `.nav-logout-btn` (styled button as link), `.login-hover-wrap` (relative container), `.login-preview-dropdown` (shown on `:hover`), `.preview-link` (disabled appearance).

### Step 7 — Account layout template (`templates/account/layout.html`)

Extends `base.html`. Defines the two-column layout (sidebar + content) and a new `{% block account_content %}` for child pages:

```html
{% extends 'base.html' %}
{% block content %}
<div class="account-layout">

  <aside class="account-sidebar">
    <div class="sidebar-avatar">
      <!-- large avatar circle or photo -->
    </div>
    <nav class="sidebar-nav">
      <a href="/account" class="{% if active=='dashboard' %}active{% endif %}">My Profile</a>
      <a href="/account/addresses" class="{% if active=='addresses' %}active{% endif %}">Saved Addresses</a>
      <a href="/account/settings" class="{% if active=='settings' %}active{% endif %}">Settings & Password</a>
      <a href="{{ url_for('orders.order_history') }}">My Orders</a>
      <a href="{{ url_for('wishlist.view_wishlist') }}">My Wishlist</a>
    </nav>
  </aside>

  <main class="account-content">
    {% block account_content %}{% endblock %}
  </main>

</div>
{% endblock %}
```

Each account sub-page sets `active` via `{% set active = 'profile' %}` before `{% extends %}`.

### Step 8 — Account page templates

**`dashboard.html`** — greeting banner + quick-link cards:
- "Hello, [Name]!" heading with large avatar
- Member since date (from `user['created_at']`)
- Two quick-link cards: "My Orders → [count]" and "My Wishlist → [count]"

**`profile.html`** — edit form:
- Avatar preview (photo or letter circle) + file upload input
- Name field (pre-filled), Phone field (optional), Email field (readonly)
- Save button → POST → success flash → redirect back

**`addresses.html`** — combined list + add form (one page):
- Address cards with Edit / Delete / "Set as default" per address
- "Default" gold badge on the default address
- Inline add form (collapsible via `<details>`) or always-visible form at bottom

**`settings.html`** — two sections on one page:
- Section 1: Change Password (3 fields; hidden/message for Google-only users)
- Section 2: Notification Preferences (checkbox, Save)

### Step 9 — CSS additions (`static/css/style.css`)

```css
/* ── Navbar avatar circle ── */
.avatar-circle {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: var(--color-gold);
  color: var(--color-plum);
  font-family: var(--font-head);
  font-size: var(--fs-sm);
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  user-select: none;
  list-style: none;   /* suppress <summary> marker */
  flex-shrink: 0;
}
.avatar-circle .avatar-img {
  width: 36px; height: 36px;
  border-radius: 50%;
  object-fit: cover;
}
.avatar-circle::-webkit-details-marker { display: none; }

/* ── Account dropdown ── */
.account-menu { position: relative; }
.account-dropdown {
  display: none;
  position: absolute;
  right: 0; top: calc(100% + 8px);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  min-width: 200px;
  z-index: 200;
  overflow: hidden;
}
.account-menu[open] .account-dropdown { display: block; }
.dropdown-header {
  padding: var(--space-3) var(--space-3) var(--space-2);
  font-size: var(--fs-xs);
  color: var(--color-text-soft);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.account-dropdown a {
  display: block;
  padding: 10px var(--space-3);
  color: var(--color-text);
  font-size: var(--fs-sm);
  font-weight: 500;
  border-top: 1px solid var(--color-border);
}
.account-dropdown a:hover { background: var(--color-cream); color: var(--color-plum); }
.dropdown-admin { color: var(--color-gold-dark) !important; font-weight: 700 !important; }
.dropdown-divider { border-top: 2px solid var(--color-border); margin-top: var(--space-1); }
.dropdown-logout {
  display: block; width: 100%;
  padding: 10px var(--space-3);
  background: none; border: none;
  color: var(--color-danger);
  font-size: var(--fs-sm); font-weight: 600;
  text-align: left; cursor: pointer;
  font-family: var(--font-body);
  border-top: 1px solid var(--color-border);
}
.dropdown-logout:hover { background: #fff0ee; }

/* ── Account page layout (sidebar + content) ── */
.account-layout {
  display: flex;
  gap: var(--space-5);
  padding: var(--space-4) 0;
  align-items: flex-start;
}
.account-sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}
.sidebar-avatar {
  background: var(--color-plum);
  padding: var(--space-4) var(--space-3);
  text-align: center;
}
.sidebar-avatar .avatar-lg {
  width: 64px; height: 64px;
  border-radius: 50%;
  background: var(--color-gold);
  color: var(--color-plum);
  font-family: var(--font-head);
  font-size: 1.5rem;
  font-weight: 700;
  display: inline-flex; align-items: center; justify-content: center;
  margin-bottom: var(--space-2);
  object-fit: cover;
}
.sidebar-avatar .sidebar-name {
  color: var(--color-cream);
  font-size: var(--fs-sm);
  font-weight: 600;
}
.sidebar-avatar .sidebar-email {
  color: var(--color-gold);
  font-size: var(--fs-xs);
  margin-top: 2px;
}
.sidebar-nav a {
  display: block;
  padding: 12px var(--space-3);
  font-size: var(--fs-sm);
  font-weight: 500;
  color: var(--color-text);
  border-top: 1px solid var(--color-border);
  transition: background 0.15s, color 0.15s;
}
.sidebar-nav a:hover { background: var(--color-cream); color: var(--color-plum); }
.sidebar-nav a.active { background: var(--color-cream); color: var(--color-plum); font-weight: 700; border-left: 3px solid var(--color-gold); }

.account-content { flex: 1; min-width: 0; }

/* Quick-link cards on dashboard */
.quick-links { display: flex; gap: var(--space-3); flex-wrap: wrap; margin-top: var(--space-4); }
.quick-link-card {
  flex: 1; min-width: 160px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  text-align: center;
  text-decoration: none;
  transition: transform 0.2s, box-shadow 0.2s;
}
.quick-link-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.quick-link-card .ql-icon { font-size: 2rem; margin-bottom: var(--space-2); }
.quick-link-card .ql-label { font-size: var(--fs-sm); font-weight: 600; color: var(--color-plum); }

/* Address cards */
.address-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-3);
  margin-bottom: var(--space-3);
  position: relative;
}
.address-card.is-default { border-color: var(--color-gold); border-width: 2px; }
.default-badge {
  display: inline-block;
  background: var(--color-gold);
  color: var(--color-plum);
  font-size: var(--fs-xs);
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius);
  margin-bottom: var(--space-2);
}
.address-actions { margin-top: var(--space-2); display: flex; gap: var(--space-2); flex-wrap: wrap; }

/* Mobile: stack sidebar on top */
@media (max-width: 700px) {
  .account-layout { flex-direction: column; }
  .account-sidebar { width: 100%; }
}
```

---

## Implementation Order

1. `db.py` — migrate_db additions + all helper functions
2. `auth.py` — User model fields update
3. `account.py` — blueprint (all 8 routes)
4. `app.py` — register blueprint + avatar dir
5. `templates/base.html` — navbar avatar + dropdown
6. `templates/account/layout.html` — sidebar+content base
7. `templates/account/dashboard.html`
8. `templates/account/profile.html`
9. `templates/account/addresses.html`
10. `templates/account/settings.html`
11. `static/css/style.css` — all account styles
12. Browser test per spec §11 test script

---

## Edge Cases Handled

| Case | How |
|------|-----|
| No name (Google user with only email) | Avatar shows `email[0].upper()`; handled in both navbar and sidebar |
| Google-only user (NULL password_hash) | Settings page detects NULL hash, shows info message instead of password form |
| First address auto-default | `add_address()` checks count == 0, sets `is_default=1` |
| Delete default address | `delete_address()` promotes next address to default |
| Large avatar upload (>5MB) | Check `len(file.read())` or `file.seek(0,2)` before saving; flash error |
| Invalid avatar extension | Whitelist check before saving |
| Another user's address | `get_address_by_id` → check `user_id == current_user.id` → `abort(403)` |
| `details` dropdown stays open on navigation | `<details>` closes on page load (it's not JS-persistent); safe behavior |

---

## Acceptance Criteria Mapping (from Spec §10)

- [ ] Avatar circle navbar right side — Step 5
- [ ] Full name removed from navbar — Step 5
- [ ] Dropdown opens on click with all links — Steps 5, 9
- [ ] Admin Dashboard link in dropdown for admins — Step 5
- [ ] Guest sees Login / Sign Up — Step 5
- [ ] `/account` sidebar+content layout — Steps 6, 7
- [ ] Profile edit (name, phone, photo) — Steps 3, 8
- [ ] Member since + email shown — Step 7
- [ ] Address add/edit/delete — Steps 1–3, 9
- [ ] Default address mark — Steps 1–3, 9
- [ ] Password change with verify — Steps 1–3, 10
- [ ] Notification on/off saves — Steps 1–3, 10
- [ ] Quick-link cards — Steps 7, 9
- [ ] Privacy (own data only) — Step 3 (abort 403 guard)
- [ ] Premium design — Step 11
- [ ] Browser tested — Step 12
