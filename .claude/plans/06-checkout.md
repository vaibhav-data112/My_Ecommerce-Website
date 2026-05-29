# Plan: Feature 06 — Checkout Flow

## Context

The shopping cart (feature 05) is complete. Checkout is the bridge that turns a cart into a
confirmed, payable order. This feature adds `GET /checkout` (review page + address form) and
`POST /checkout` (validate → create order atomically → hand off to payment). Payment (feature 07)
is out of scope; we redirect to `/payment/<order_id>` which will be wired up in the next feature.

---

## Schema Gap — Migration Required

The existing `orders` table is missing columns required by the spec. The existing `order_items`
table is missing `line_total`. Both must be added via `migrate_db()` using `PRAGMA table_info`
guard (ALTER TABLE only if column absent — same pattern as the `google_id` migration).

**Add to `orders`:** `shipping_name TEXT NOT NULL DEFAULT ''`,
`shipping_phone TEXT NOT NULL DEFAULT ''`, `subtotal REAL NOT NULL DEFAULT 0`,
`shipping_fee REAL NOT NULL DEFAULT 0`

**Add to `order_items`:** `line_total REAL NOT NULL DEFAULT 0`

---

## Files to Modify

### 1. `db.py`

**A. `migrate_db()`** — add the five new columns (guarded by `PRAGMA table_info` check for each):
```python
orders_cols = [r[1] for r in conn.execute("PRAGMA table_info(orders)").fetchall()]
for col, ddl in [
    ('shipping_name',  "ALTER TABLE orders ADD COLUMN shipping_name TEXT NOT NULL DEFAULT ''"),
    ('shipping_phone', "ALTER TABLE orders ADD COLUMN shipping_phone TEXT NOT NULL DEFAULT ''"),
    ('subtotal',       "ALTER TABLE orders ADD COLUMN subtotal REAL NOT NULL DEFAULT 0"),
    ('shipping_fee',   "ALTER TABLE orders ADD COLUMN shipping_fee REAL NOT NULL DEFAULT 0"),
]:
    if col not in orders_cols:
        conn.execute(ddl)

oi_cols = [r[1] for r in conn.execute("PRAGMA table_info(order_items)").fetchall()]
if 'line_total' not in oi_cols:
    conn.execute("ALTER TABLE order_items ADD COLUMN line_total REAL NOT NULL DEFAULT 0")
conn.commit()
```

**B. Add `calculate_totals(items)`** — single source of truth for money math:
```python
SHIPPING_FEE = 40.0  # flat ₹40; free for orders >= ₹500

def calculate_totals(items):
    subtotal = round(sum(item['price'] * item['quantity'] for item in items), 2)
    shipping_fee = 0.0 if subtotal >= 500 else SHIPPING_FEE
    total = round(subtotal + shipping_fee, 2)
    return {'subtotal': subtotal, 'shipping_fee': shipping_fee, 'total': total}
```

**C. Add `place_order(user_id, shipping_name, shipping_phone, shipping_address)`** — atomic
transaction; re-reads cart and product data from DB (never trusts browser input):
```python
def place_order(user_id, shipping_name, shipping_phone, shipping_address):
    conn = get_db()
    try:
        items = conn.execute("""
            SELECT ci.product_id, ci.quantity, p.name, p.price, p.stock
            FROM cart_items ci JOIN products p ON p.id = ci.product_id
            WHERE ci.user_id = ?
            ORDER BY ci.created_at
        """, (user_id,)).fetchall()

        if not items:
            return False, 'Your cart is empty', None

        for item in items:
            if item['stock'] < item['quantity']:
                return False, f"'{item['name']}' is out of stock or has insufficient quantity", None

        totals = calculate_totals(items)

        conn.execute("BEGIN")
        cursor = conn.execute("""
            INSERT INTO orders
              (user_id, status, subtotal, shipping_fee, total,
               shipping_name, shipping_phone, shipping_address)
            VALUES (?, 'pending', ?, ?, ?, ?, ?, ?)
        """, (user_id, totals['subtotal'], totals['shipping_fee'], totals['total'],
              shipping_name, shipping_phone, shipping_address))
        order_id = cursor.lastrowid

        for item in items:
            line_total = round(item['price'] * item['quantity'], 2)
            conn.execute("""
                INSERT INTO order_items
                  (order_id, product_id, product_name, unit_price, quantity, line_total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (order_id, item['product_id'], item['name'],
                  item['price'], item['quantity'], line_total))

        conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
        conn.commit()
        return True, 'Order placed successfully', order_id
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return False, 'Could not place order, please try again', None
    finally:
        conn.close()
```

---

### 2. `checkout.py` (new file)

Blueprint `checkout`, registered at `/checkout`. Both routes use `@login_required`.

**GET `/checkout`:**
1. Load cart via `get_cart_items(user_id)`.
2. If empty → `flash('Your cart is empty', 'error')` → redirect to `cart.view_cart`.
3. Compute totals via `calculate_totals(items)`.
4. Render `checkout/checkout.html` with `items`, `subtotal`, `shipping_fee`, `total`.
   (Current DB prices are used — price changes are automatically reflected, satisfying AC-6.)

**POST `/checkout`:**
1. Read and strip `shipping_name`, `shipping_phone`, `shipping_address` from `request.form`.
2. Validate — return to checkout page with field-level errors if any field is blank or phone
   is fewer than 10 digits.
3. Call `place_order(user_id, ...)`.
4. On failure → `flash(message, 'error')` → redirect to `GET /checkout`.
5. On success → redirect to `/payment/<order_id>` (PRG; payment feature wires this up next).

Double-submit: client-side button disable via inline JS (`this.disabled=true` on submit);
server-side covered by PRG redirect after success.

---

### 3. `templates/checkout/checkout.html` (new file)

Extends `base.html`. Sections:
- **Order summary table**: product name | unit price | qty | line total (current DB prices).
- **Totals block**: subtotal row, shipping fee row (or "Free" badge), bold total row.
- **Address form** (POST to `/checkout`):
  - `shipping_name` (text, required)
  - `shipping_phone` (tel, required, minlength=10)
  - `shipping_address` (textarea, required)
  - Submit button with JS disable-on-click.
- Flash errors rendered inline above the form (re-uses base.html flash block).

---

### 4. `app.py` (modify)

Add two lines — import and register:
```python
from checkout import checkout   # after existing blueprint imports
app.register_blueprint(checkout)  # after existing register_blueprint calls
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `checkout.py` | Checkout blueprint (GET + POST routes) |
| `templates/checkout/checkout.html` | Checkout page template |
| `test_checkout.py` | Acceptance-criteria test suite |

---

## Test File: `test_checkout.py`

Same setup as `test_cart.py` (temp DB, patch `db.DATABASE`, `app.config['TESTING'] = True`).

| Test | AC covered |
|------|-----------|
| `test_ac3_logged_out_redirected` | AC-3 |
| `test_ac2_empty_cart_redirected` | AC-2 |
| `test_ac1_view_checkout` | AC-1 |
| `test_ac4_address_required` | AC-4 |
| `test_ac5_out_of_stock_blocks_order` | AC-5 |
| `test_ac7_successful_order_creation` | AC-7 |
| `test_ac8_no_double_order` | AC-8 |
| `test_ac9_price_snapshot_permanent` | AC-9 |
| `test_ac10_all_or_nothing_rollback` | AC-10 |

Each test verifies the database directly (via `sqlite3.connect(_test_db)`) in addition to HTTP
response assertions.

---

## Key Reused Code

- `get_cart_items(user_id)` — `db.py` (already exists; used by GET route)
- `get_db()` — `db.py` (connection factory for `place_order`)
- `login_required`, `current_user` — imported from `flask_login` (same as `cart.py`)
- Flash + redirect pattern — identical to `cart.py`

---

## Verification

```bash
python test_checkout.py    # all 9 ACs should pass
python app.py              # manual smoke test:
                           #   1. login → add items → /checkout → fill form → submit
                           #   2. confirm redirect to /payment/<id> with order in DB
                           #   3. empty cart → /checkout → redirected to cart
```
