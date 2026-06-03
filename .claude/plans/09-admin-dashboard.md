# Plan: Feature 09 — Admin Dashboard

## Context

Customers can browse, buy, and track orders — but the store owner had no way to manage products or change order statuses without editing the database by hand. This feature adds a private `/admin` area that lets the owner add/edit/delete products and update order statuses (paid → shipped → delivered → cancelled). Access is locked to users with `is_admin = 1`; everyone else is blocked.

---

## Step 1 — Database: `db.py` — add `is_admin` column + admin helpers

### 1a. `migrate_db()` — safe migration

```python
cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
if 'is_admin' not in cols:
    conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")

admin_email = os.environ.get('ADMIN_EMAIL')
if admin_email:
    conn.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (admin_email.lower(),))
```

`ADMIN_EMAIL` is read from the `.env` file — the only controlled way to promote a user to admin; no public path exists.

### 1b. `seed_db()` — demo user is admin

```python
conn.execute(
    "INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, 1)",
    ("Demo User", "demo@example.com", generate_password_hash("demo1234")),
)
```

### 1c. Admin helper functions (append to `db.py`)

```python
def get_all_products():
    # SELECT * FROM products ORDER BY created_at DESC

def create_product(name, description, price, stock, category, image_url):
    # INSERT INTO products ...

def update_product(product_id, name, description, price, stock, category, image_url):
    # UPDATE products SET ... WHERE id = ?

def delete_product(product_id):
    # DELETE FROM products WHERE id = ?

def get_all_orders_admin():
    # SELECT o.*, u.name AS customer_name, u.email AS customer_email
    # FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC

def update_order_status(order_id, status):
    # UPDATE orders SET status = ? WHERE id = ?
```

All use parameterised `?` placeholders. No string interpolation.

---

## Step 2 — Auth: `auth.py` — expose `is_admin` on the User model

```python
# In User.__init__:
self.is_admin = bool(row['is_admin']) if 'is_admin' in row.keys() else False
```

This makes `current_user.is_admin` available in all templates and route guards.

---

## Step 3 — Blueprint: `admin.py`

New file. Blueprint registered with `url_prefix='/admin'`.

### `admin_required` decorator

```python
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Not authorised.', 'error')
            return redirect(url_for('catalog.product_list'))
        return f(*args, **kwargs)
    return decorated
```

Applied to **every** route in this blueprint.

### `_validate_product_form(form)` helper

Validates name (required), category (must be in `CATEGORIES`), price (float ≥ 0), stock (int ≥ 0). Returns `(error, name, description, price, stock, category, image_url)`.

### Routes

| Route | Method | Function | Template |
|-------|--------|----------|----------|
| `/admin` | GET | `dashboard()` | `admin/dashboard.html` |
| `/admin/products` | GET | `products()` | `admin/products.html` |
| `/admin/products/add` | GET + POST | `add_product()` | `admin/product_form.html` |
| `/admin/products/<id>/edit` | GET + POST | `edit_product(product_id)` | `admin/product_form.html` |
| `/admin/products/<id>/delete` | POST | `delete_product_route(product_id)` | redirect |
| `/admin/orders` | GET | `orders()` | `admin/orders.html` |
| `/admin/orders/<id>/status` | POST | `update_status(order_id)` | redirect |

`ALLOWED_STATUSES = ['paid', 'shipped', 'delivered', 'cancelled']`

Delete checks product exists first; shows flash on missing product. Edit pre-fills form with current product values (passes `form=product, product=product`). Add passes `form={}`.

---

## Step 4 — Templates

### `templates/admin/dashboard.html`
- Extends `base.html`.
- Shows product count and order count (passed from `dashboard()` via `get_db()` COUNT queries).
- Two prominent links: Manage Products, Manage Orders.

### `templates/admin/products.html`
- Lists all products in a table: name, category, price, stock.
- Edit button → `/admin/products/<id>/edit`.
- Delete form (POST, inline) with a confirmation dialog (`onclick="return confirm(...)"`).
- "Add Product" button at the top.

### `templates/admin/product_form.html`
- Shared for Add and Edit — action label (`Add` / `Edit`) passed from route.
- Fields: name (required), description (textarea), price (number, min=0, step=0.01), stock (number, min=0, step=1), category (select from `categories`), image_url (text).
- `enctype="multipart/form-data"` (file upload added in feature 11).
- Pre-fills values on edit: `form is mapping` check handles both `request.form` dict and `sqlite3.Row` object.
- Back link to products list.

### `templates/admin/orders.html`
- Lists all orders (across all users), newest first.
- Columns: order ID, customer name/email, total, status, date.
- Inline form per row: status dropdown (`allowed_statuses`) + Update button (POST to `/admin/orders/<id>/status`).

---

## Step 5 — `templates/base.html` — Admin nav link

```jinja
{% if current_user.is_admin %}
    <a href="{{ url_for('admin.dashboard') }}" class="admin-link">Admin</a>
{% endif %}
```

Placed inside the authenticated-user nav block.

---

## Step 6 — `app.py` — Register blueprint

```python
from admin import admin as admin_blueprint
app.register_blueprint(admin_blueprint)
```

---

## Files Created

| File | Purpose |
|------|---------|
| `admin.py` | Admin blueprint with all routes, `admin_required` guard, form validation |
| `templates/admin/dashboard.html` | Admin landing page with counts and nav links |
| `templates/admin/products.html` | Product list with edit/delete buttons |
| `templates/admin/product_form.html` | Shared add/edit product form |
| `templates/admin/orders.html` | All-orders list with inline status updater |

---

## Files Modified

| File | What changes |
|------|-------------|
| `db.py` | `migrate_db()` adds `is_admin` column; 6 new admin helper functions; `seed_db()` sets demo user as admin |
| `auth.py` | `User.__init__` exposes `self.is_admin` |
| `templates/base.html` | "Admin" nav link shown only to `current_user.is_admin` |
| `app.py` | Import + register `admin_blueprint` |

---

## Reused Utilities

| Utility | File | Purpose |
|---------|------|---------|
| `get_db()` | `db.py` | DB connection |
| `get_product_by_id()` | `db.py` | Fetch single product for edit/delete guard |
| `get_order_by_id()` | `db.py` | Fetch single order for status update guard |
| `CATEGORIES` | `catalog.py` | Fixed category list for validation + select options |
| `current_user` | `flask_login` | `is_authenticated` + `is_admin` checks |

---

## Security Notes

- No public route can set `is_admin = 1` — only `ADMIN_EMAIL` env var via `migrate_db()`.
- `admin_required` checks both authentication and `is_admin` — one cannot be bypassed without the other.
- Delete product does NOT break past orders — `order_items` already snapshots `product_name` and `unit_price` at purchase time (feature 06).
- All SQL uses `?` placeholders.
