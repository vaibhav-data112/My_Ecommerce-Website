# Plan 12 — Wishlist (Saved Products)

## Overview

Build a per-user wishlist feature: heart icon toggle on product cards and detail pages, a dedicated `/wishlist` page, navbar link with count badge, and add-to-cart from wishlist. The pattern mirrors how `cart` and `reviews` features were built.

---

## Files to Create

| File | Purpose |
|------|---------|
| `wishlist.py` | Flask Blueprint — all wishlist routes |
| `templates/wishlist/wishlist.html` | My Wishlist page (product grid) |

## Files to Modify

| File | What changes |
|------|-------------|
| `db.py` | Add `wishlist_items` table (via `migrate_db()`), add 4 helper functions |
| `app.py` | Import + register `wishlist` blueprint; add `inject_wishlist_count()` context processor |
| `templates/base.html` | Add "Wishlist" nav link with count badge (next to "My Orders") |
| `templates/products/list.html` | Add heart icon button on each product card |
| `templates/products/detail.html` | Add heart icon button next to "Add to Cart" |
| `static/css/style.css` | Add `.wishlist-heart`, `.heart-filled`, `.heart-empty`, `.wishlist-grid` styles |

---

## Step-by-Step Implementation

### Step 1 — DB: `wishlist_items` table in `migrate_db()` (db.py)

Add this block inside `migrate_db()`, after the existing column checks:

```python
# wishlist_items table
conn.execute("""
    CREATE TABLE IF NOT EXISTS wishlist_items (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        added_at   TEXT    DEFAULT (datetime('now')),
        FOREIGN KEY (user_id)    REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id),
        UNIQUE (user_id, product_id)
    )
""")
```

Using `CREATE TABLE IF NOT EXISTS` so it is idempotent (no PRAGMA check needed — safer than ALTER TABLE for new tables).

### Step 2 — DB: 4 helper functions (db.py)

Add to the bottom of `db.py` under a `# Wishlist helpers` comment:

```python
def add_to_wishlist(user_id, product_id):
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO wishlist_items (user_id, product_id) VALUES (?, ?)",
            (user_id, product_id)
        )
        conn.commit()
    finally:
        conn.close()

def remove_from_wishlist(user_id, product_id):
    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM wishlist_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        conn.commit()
    finally:
        conn.close()

def get_user_wishlist(user_id):
    # Returns full product rows for wishlist items; skips deleted products via INNER JOIN
    conn = get_db()
    try:
        return conn.execute("""
            SELECT p.*
            FROM wishlist_items wi
            JOIN products p ON p.id = wi.product_id
            WHERE wi.user_id = ?
            ORDER BY wi.added_at DESC
        """, (user_id,)).fetchall()
    finally:
        conn.close()

def is_in_wishlist(user_id, product_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT 1 FROM wishlist_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        ).fetchone()
        return row is not None
    finally:
        conn.close()

def get_wishlist_count(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM wishlist_items WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return int(row[0])
    finally:
        conn.close()
```

`INSERT OR IGNORE` handles the UNIQUE constraint silently (no duplicate error).
`get_user_wishlist` uses INNER JOIN — deleted products are automatically excluded.

### Step 3 — Blueprint: `wishlist.py`

Three routes:

| Route | Method | Auth | Action |
|-------|--------|------|--------|
| `/wishlist` | GET | required | Show My Wishlist page |
| `/wishlist/toggle` | POST | required | Add or remove a product; redirects back |
| `/wishlist/add-to-cart` | POST | required | Add wishlist product to cart; stays on wishlist page |

```python
from flask import Blueprint, redirect, request, url_for
from flask_login import current_user, login_required

from db import (add_to_cart, add_to_wishlist, get_user_wishlist,
                is_in_wishlist, remove_from_wishlist)
from flask import flash, render_template

wishlist = Blueprint('wishlist', __name__)


@wishlist.route('/wishlist')
@login_required
def view_wishlist():
    items = get_user_wishlist(int(current_user.id))
    return render_template('wishlist/wishlist.html', items=items)


@wishlist.route('/wishlist/toggle', methods=['POST'])
@login_required
def toggle_wishlist():
    product_id = request.form.get('product_id', type=int)
    next_url = request.form.get('next', url_for('catalog.product_list'))
    if product_id:
        uid = int(current_user.id)
        if is_in_wishlist(uid, product_id):
            remove_from_wishlist(uid, product_id)
            flash('Removed from wishlist.', 'info')
        else:
            add_to_wishlist(uid, product_id)
            flash('Added to wishlist!', 'success')
    return redirect(next_url)


@wishlist.route('/wishlist/add-to-cart', methods=['POST'])
@login_required
def wishlist_add_to_cart():
    product_id = request.form.get('product_id', type=int)
    if product_id:
        ok, msg = add_to_cart(int(current_user.id), product_id, 1)
        flash(msg, 'success' if ok else 'error')
    return redirect(url_for('wishlist.view_wishlist'))
```

### Step 4 — Template: `templates/wishlist/wishlist.html`

Extend `base.html`. Show a product grid matching the catalog card style. Each card has:
- Product image / placeholder
- Name, price, category
- "Add to Cart" form (disabled if out of stock)
- "Remove" heart/button form

Empty state: friendly message + "Shop Now" link.

### Step 5 — Heart icon on product list (`templates/products/list.html`)

Inside each product card `<a>` tag, add a heart button form overlaid (top-right corner, `position:absolute`):

```html
{% if current_user.is_authenticated %}
  <form method="post" action="{{ url_for('wishlist.toggle_wishlist') }}"
        onclick="event.stopPropagation()">
    <input type="hidden" name="product_id" value="{{ p['id'] }}">
    <input type="hidden" name="next" value="{{ request.url }}">
    <button type="submit" class="heart-btn {% if p['id'] in wishlist_ids %}heart-filled{% else %}heart-empty{% endif %}"
            title="{% if p['id'] in wishlist_ids %}Remove from wishlist{% else %}Save to wishlist{% endif %}">
      {% if p['id'] in wishlist_ids %}♥{% else %}♡{% endif %}
    </button>
  </form>
{% else %}
  <a class="heart-btn heart-empty" href="{{ url_for('auth.login') }}?next={{ request.url }}" 
     onclick="event.stopPropagation()" title="Login to save">♡</a>
{% endif %}
```

The `wishlist_ids` set is injected via the context processor (Step 6).

### Step 6 — Heart icon on product detail (`templates/products/detail.html`)

Add a heart toggle button next to "Add to Cart" in the `detail-actions` div:

```html
{% if current_user.is_authenticated %}
  <form method="post" action="{{ url_for('wishlist.toggle_wishlist') }}" style="display:inline">
    <input type="hidden" name="product_id" value="{{ product['id'] }}">
    <input type="hidden" name="next" value="{{ request.url }}">
    <button type="submit" class="btn-heart {% if in_wishlist %}heart-filled{% else %}heart-empty{% endif %}">
      {% if in_wishlist %}♥ Saved{% else %}♡ Save{% endif %}
    </button>
  </form>
{% else %}
  <a href="{{ url_for('auth.login') }}?next={{ request.url }}" class="btn-heart heart-empty">♡ Save</a>
{% endif %}
```

`in_wishlist` is passed by `catalog.product_detail` view (needs a small addition — Step 7).

### Step 7 — Update `catalog.py` to pass `in_wishlist`

In `product_detail` view, add:

```python
from db import is_in_wishlist  # add to imports

in_wishlist = False
if current_user.is_authenticated:
    in_wishlist = is_in_wishlist(current_user.id, product_id)

return render_template(..., in_wishlist=in_wishlist)
```

### Step 8 — Register blueprint + context processors (`app.py`)

```python
from wishlist import wishlist as wishlist_blueprint
from db import get_wishlist_count, get_user_wishlist

app.register_blueprint(wishlist_blueprint)

@app.context_processor
def inject_wishlist_count():
    if current_user.is_authenticated:
        count = get_wishlist_count(int(current_user.id))
        ids = {item['id'] for item in get_user_wishlist(int(current_user.id))}
    else:
        count, ids = 0, set()
    return dict(wishlist_count=count, wishlist_ids=ids)
```

`wishlist_ids` (a Python `set`) lets every template check `p['id'] in wishlist_ids` without extra DB calls.

### Step 9 — Navbar link (`templates/base.html`)

Inside the `{% if current_user.is_authenticated %}` block, add after "My Orders":

```html
<a href="{{ url_for('wishlist.view_wishlist') }}">
    Wishlist{% if wishlist_count > 0 %}<span class="cart-badge">{{ wishlist_count }}</span>{% endif %}
</a>
```

The existing `.cart-badge` CSS style works for the wishlist count too.

### Step 10 — CSS additions (`static/css/style.css`)

Add to the bottom of the file:

```css
/* ── Wishlist heart button ── */
.heart-btn {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  background: var(--color-surface);
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  text-decoration: none;
  z-index: 2;
  transition: transform 0.15s;
}
.heart-btn:hover { transform: scale(1.15); }
.heart-filled { color: var(--color-gold-dark); }
.heart-empty  { color: var(--color-text-soft); }

/* ── Detail page heart ── */
.btn-heart {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  border: 2px solid var(--color-gold);
  border-radius: var(--radius);
  background: transparent;
  font-family: var(--font-body);
  font-size: var(--fs-sm);
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.2s, color 0.2s;
}
.btn-heart.heart-filled { background: var(--color-gold); color: var(--color-plum); }
.btn-heart.heart-empty  { color: var(--color-plum); }
.btn-heart:hover        { background: var(--color-gold-dark); color: var(--color-plum); }
```

---

## Edge Cases Handled

| Case | How |
|------|-----|
| Duplicate add | `INSERT OR IGNORE` + UNIQUE constraint — silent no-op |
| Guest clicks heart | Redirected to login (no `@login_required` on toggle; manual guard in template links) — actually toggle route has `@login_required`, so Flask-Login auto-redirects |
| Deleted product in wishlist | `INNER JOIN products` in `get_user_wishlist` — deleted rows simply absent |
| Out-of-stock in wishlist | Shown with "Out of Stock" badge; "Add to Cart" button disabled |
| Empty wishlist | Friendly "Wishlist khaali hai" message + "Shop Now" CTA |
| Privacy | All queries filter by `user_id = current_user.id` |

---

## Implementation Order

1. `db.py` — table + helpers (no UI risk, fully backward-compatible)
2. `wishlist.py` — blueprint routes
3. `app.py` — register blueprint + context processor
4. `templates/base.html` — navbar link
5. `templates/wishlist/wishlist.html` — wishlist page
6. `catalog.py` — pass `in_wishlist` to detail template
7. `templates/products/detail.html` — heart button
8. `templates/products/list.html` — heart button on cards
9. `static/css/style.css` — heart + wishlist page styles
10. Manual browser test + `test_wishlist.py` acceptance test

---

## Acceptance Criteria Mapping (from Spec §10)

- [x] `wishlist_items` table — Step 1
- [x] Heart on product card — Steps 5, 10
- [x] Heart on detail page — Steps 6, 7, 10
- [x] Heart toggle add/remove — Step 3 (`toggle_wishlist`)
- [x] Guest → login redirect — Step 3 (`@login_required`)
- [x] Navbar link + count badge — Steps 8, 9
- [x] My Wishlist page grid — Steps 3, 4
- [x] Add to Cart from wishlist — Step 3 (`wishlist_add_to_cart`)
- [x] Remove from wishlist page — Step 3 (toggle from wishlist page)
- [x] Empty wishlist message — Step 4 template
- [x] Privacy (per-user) — Step 2 (`WHERE user_id = ?`)
- [x] Design follows ecommerce-ui-design — Step 10 (gold heart, plum/cream)
- [x] Browser tested — Step 10 (manual)
