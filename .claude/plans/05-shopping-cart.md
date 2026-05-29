# Plan — 05 Shopping Cart

## Context

Feature 03 (product catalog) placed an "Add to Cart" button on the product detail page that currently calls a placeholder route (`catalog.cart_add_placeholder`) which only flashes "Shopping cart coming soon!" and redirects back. The `cart_items` table already exists in the database (created in feature 01). This plan wires everything together: a real cart blueprint with full CRUD, a cart page template, nav badge injection, and AC tests.

---

## Files to Create

| File | Purpose |
|---|---|
| `cart.py` | New Flask Blueprint — 4 routes + no DB helpers (DB helpers live in `db.py`) |
| `templates/cart/cart.html` | Cart page (list of items, quantities, totals, checkout placeholder) |
| `test_cart.py` | AC tests following the same pattern as `test_auth.py` |

## Files to Modify

| File | Change |
|---|---|
| `db.py` | Add 6 cart helper functions |
| `catalog.py` | Remove `cart_add_placeholder` route |
| `templates/products/detail.html` | Update form action to `cart.add_to_cart`; add quantity `<input>` |
| `templates/base.html` | Add cart badge to nav (shows count when authenticated) |
| `app.py` | Register `cart` blueprint; add `cart_count` context processor |

---

## Step-by-Step Implementation

### Step 1 — `db.py`: Add cart helper functions

Add these 6 functions after the existing product helpers:

**`get_cart_items(user_id)`**
```sql
SELECT ci.id, ci.product_id, ci.quantity,
       p.name, p.price, p.image_url, p.stock,
       (p.price * ci.quantity) AS line_total
FROM cart_items ci
JOIN products p ON p.id = ci.product_id
WHERE ci.user_id = ?
ORDER BY ci.created_at
```
Returns a list of `sqlite3.Row` objects.

**`calculate_cart_total(items)`**
`return sum(item['line_total'] for item in items)` — single source of truth.

**`get_cart_count(user_id)`**
`SELECT COALESCE(SUM(quantity), 0) FROM cart_items WHERE user_id = ?` — returns int.

**`add_to_cart(user_id, product_id, qty=1)`**
1. Fetch product; if not found return `(False, 'Product not found')`.
2. Look up existing cart row for `(user_id, product_id)`.
3. If exists: new_qty = min(existing + qty, product['stock']); UPDATE.
4. If not: new_qty = min(qty, product['stock']); INSERT.
5. Return `(True, message)` where message notes if quantity was capped.

**`update_cart_item(user_id, product_id, qty)`**
- `qty == 0` → call `remove_cart_item`; return `(True, 'Item removed')`.
- Else: cap at stock; UPDATE; return `(True, message)`.

**`remove_cart_item(user_id, product_id)`**
`DELETE FROM cart_items WHERE user_id = ? AND product_id = ?` — always succeeds silently.

All functions use `get_db()` with parameterized `?` queries.

---

### Step 2 — `cart.py`: Blueprint with 4 routes

```python
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from db import (add_to_cart, calculate_cart_total, get_cart_items,
                remove_cart_item, update_cart_item)

cart = Blueprint('cart', __name__)
```

**`POST /cart/add`** (`add_to_cart` view)
- `@login_required`
- Read `product_id` and `quantity` (default 1, coerce to int, clamp to ≥1) from form.
- Call `db.add_to_cart(user_id, product_id, qty)`.
- Flash result message; redirect to `request.referrer or url_for('catalog.product_detail', product_id=product_id)`.

**`GET /cart`** (`view_cart` view)
- `@login_required`
- Call `get_cart_items(user_id)`; `calculate_cart_total(items)`.
- Render `cart/cart.html` with `items` and `subtotal`.

**`POST /cart/update`** (`update_quantity` view)
- `@login_required`
- Read `product_id`, `quantity` from form.
- Call `update_cart_item(user_id, product_id, qty)`.
- Flash result; redirect to `url_for('cart.view_cart')`.

**`POST /cart/remove`** (`remove_item` view)
- `@login_required`
- Read `product_id` from form.
- Call `remove_cart_item(user_id, product_id)`.
- Flash "Item removed"; redirect to `url_for('cart.view_cart')`.

All views read `current_user.id` cast to `int`.

---

### Step 3 — `catalog.py`: Remove placeholder

Delete the `cart_add_placeholder` route function entirely (no other changes to catalog.py).

---

### Step 4 — `templates/products/detail.html`: Wire up real cart

Replace:
```html
<form method="post" action="{{ url_for('catalog.cart_add_placeholder') }}">
    <input type="hidden" name="product_id" value="{{ product['id'] }}">
    <button type="submit" class="btn btn-primary">Add to Cart</button>
</form>
```
With:
```html
<form method="post" action="{{ url_for('cart.add_to_cart') }}">
    <input type="hidden" name="product_id" value="{{ product['id'] }}">
    <label for="qty">Qty:</label>
    <input type="number" id="qty" name="quantity" value="1"
           min="1" max="{{ product['stock'] }}" style="width:4rem;">
    <button type="submit" class="btn btn-primary">Add to Cart</button>
</form>
```

---

### Step 5 — `templates/base.html`: Cart badge in nav

Inside the `{% if current_user.is_authenticated %}` block, add a cart link before the username span:
```html
<a href="{{ url_for('cart.view_cart') }}" class="nav-cart">
    Cart{% if cart_count > 0 %} ({{ cart_count }}){% endif %}
</a>
```
`cart_count` is injected by a context processor in `app.py`.

---

### Step 6 — `app.py`: Register blueprint + context processor

```python
from cart import cart
from db import get_cart_count

app.register_blueprint(cart)

@app.context_processor
def inject_cart_count():
    count = get_cart_count(int(current_user.id)) if current_user.is_authenticated else 0
    return dict(cart_count=count)
```
Import `current_user` from `flask_login`.

---

### Step 7 — `templates/cart/cart.html`: Cart page

Extends `base.html`. Two states:

**Empty:** Friendly message + "Browse Products" link.

**Non-empty:** Table with columns: Image | Product | Unit Price | Qty (update form) | Line Total | Remove button. Below table: subtotal and "Proceed to Checkout" button (links to `#` placeholder until feature 06). Each row's qty field is a small form POSTing to `/cart/update` with `product_id` + `quantity`. Remove is a form POSTing to `/cart/remove` with `product_id`. Format prices as `₹{{ "%.2f"|format(val) }}`.

---

### Step 8 — `test_cart.py`: AC tests

Follow exact pattern of `test_auth.py`:
- Temp DB, env vars set before import, `app.test_client()`.
- Test each AC in spec: AC-1 through AC-12.
- `print('AC-N PASS: ...')` on success; manual runner counts pass/fail.
- Key tests: add product → in cart (AC-1), add again → qty increments not duplicate row (AC-2), logged-out redirect (AC-3), cart total math (AC-4), update qty (AC-5), qty=0 removes (AC-6), remove button (AC-7), stock cap (AC-8), empty cart message (AC-9), cart count in nav context (AC-10), persistence (AC-11), user isolation (AC-12).

---

## Verification

```bash
# Run AC tests
python test_cart.py

# Start server and manually verify:
# 1. Log in as demo@example.com / demo1234
# 2. Browse to a product, add to cart → flash message, nav badge shows "Cart (1)"
# 3. Go to /cart — item listed with correct price, total
# 4. Update quantity → total recalculates
# 5. Set qty to 0 → item removed
# 6. Remove button → item gone
# 7. Log out → log back in → cart items still present
python app.py
```
