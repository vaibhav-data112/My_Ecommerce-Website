# Plan: 07 — Payment (Razorpay Integration)

## Context

Checkout (feature 06) already creates a `pending` order and redirects to `/payment/{order_id}` — a route that does not exist yet. This feature wires up that endpoint: it integrates Razorpay (Test Mode) to collect payment, verifies the result server-side, and marks the order `paid`. The critical invariant is that an order is only ever marked paid after the Razorpay signature is verified with the secret key — this prevents fake payments.

---

## Pre-Implementation: Razorpay Test Keys

Before coding, the developer must:
1. Sign up at [razorpay.com](https://razorpay.com) (free).
2. In the dashboard → **Settings → API Keys → Test Mode** → Generate Key.
3. Copy **Key ID** (`rzp_test_…`) and **Key Secret**.
4. Add to `.env`:
   ```
   RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxxxxx
   RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
   ```

---

## Step 1 — Install Razorpay SDK

Add to `requirements.txt`:
```
razorpay>=1.4.1
```
Run: `python -m pip install -r requirements.txt`

---

## Step 2 — Database Migration (`db.py`)

In `migrate_db()`, add two new columns to the `orders` table using the existing PRAGMA-guard pattern:

```python
# orders — payment columns
orders_cols = [r[1] for r in conn.execute("PRAGMA table_info(orders)").fetchall()]
if 'payment_id' not in orders_cols:
    conn.execute("ALTER TABLE orders ADD COLUMN payment_id TEXT")
if 'payment_order_id' not in orders_cols:
    conn.execute("ALTER TABLE orders ADD COLUMN payment_order_id TEXT")
```

Also add a helper function `get_order_by_id(order_id)` (select from `orders` where `id = ?`) and `get_order_items(order_id)` (select from `order_items` where `order_id = ?`) to `db.py` for reuse across payment and future order-management features.

---

## Step 3 — Payment Blueprint (`payment.py`)

New file: `payment.py` — Flask Blueprint named `payment`.

### Environment / Razorpay client setup
```python
import razorpay, hmac, hashlib, os

def _rz_client():
    return razorpay.Client(auth=(
        os.environ.get('RAZORPAY_KEY_ID', ''),
        os.environ.get('RAZORPAY_KEY_SECRET', '')
    ))
```

### Route A — `GET /payment/<int:order_id>`
- `@login_required`
- Fetch order from DB with `get_order_by_id(order_id)`.
- Guard: order must exist, belong to `current_user.id`, and have `status == 'pending'`. Otherwise: if `paid` → redirect to `payment.order_success`; else → 403/flash + redirect home.
- Call Razorpay API to create a payment order:
  ```python
  rz_order = _rz_client().order.create({
      'amount': int(order['total'] * 100),  # paisa; amount from DB only
      'currency': 'INR',
      'receipt': str(order_id),
      'payment_capture': 1
  })
  ```
- Store `rz_order['id']` in DB: `UPDATE orders SET payment_order_id = ? WHERE id = ?`.
- Render `payment/pay.html` with: `order`, `rz_order_id`, `key_id` (Key ID only — never secret), `amount_paisa`.

### Route B — `POST /payment/verify`
- `@login_required`
- Receive form fields: `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`.
- Re-fetch the order by matching `payment_order_id = razorpay_order_id` and `user_id = current_user.id` (never trust order_id from browser).
- **Signature verification** (critical security step):
  ```python
  msg = f"{razorpay_order_id}|{razorpay_payment_id}".encode()
  expected = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
  valid = hmac.compare_digest(expected, razorpay_signature)
  ```
- If valid: `UPDATE orders SET status='paid', payment_id=? WHERE id=?` then redirect to `payment.order_success`.
- If invalid: flash error, redirect back to `GET /payment/<order_id>` (order stays `pending`).

### Route C — `GET /order/<int:order_id>/success`
- `@login_required`
- Fetch order; guard ownership and `status == 'paid'`.
- Fetch `order_items` for the order.
- Render `payment/success.html` with order + items.

---

## Step 4 — Templates

### `templates/payment/pay.html`
Extends `base.html`. Shows:
- Order ID, total amount in ₹.
- A **Pay Now** button that triggers the Razorpay Checkout.js widget (loaded via CDN).
- A hidden `<form method="POST" action="/payment/verify">` with fields; the Razorpay `handler` JS populates and submits it on success.
- A "Cancel / Pay later" link back to the catalog.

Razorpay widget JS pattern:
```javascript
var options = {
  key: "{{ key_id }}",          // Key ID only — secret never here
  amount: "{{ amount_paisa }}",
  currency: "INR",
  order_id: "{{ rz_order_id }}",
  handler: function(response) {
    document.getElementById('rz_order_id').value   = response.razorpay_order_id;
    document.getElementById('rz_payment_id').value = response.razorpay_payment_id;
    document.getElementById('rz_signature').value  = response.razorpay_signature;
    document.getElementById('verify-form').submit();
  }
};
```

### `templates/payment/success.html`
Extends `base.html`. Shows:
- "Payment Successful!" heading.
- Order ID, payment ID, total paid.
- Table of order items (name, qty, unit price, line total).
- Link to continue shopping.

---

## Step 5 — Register Blueprint (`app.py`)

```python
from payment import payment
app.register_blueprint(payment)
```

---

## Step 6 — Test File (`test_payment.py`)

Tests covering all ACs from the spec, using a temp DB and mocked Razorpay client:

| Test | AC covered |
|------|-----------|
| Owner can load pay page for pending order | AC-1 |
| Non-owner gets 403 | AC-2 |
| Valid signature → order marked paid, payment_id stored | AC-3 |
| Tampered signature → order stays pending | AC-4 |
| Opening pay page without submitting keeps order pending | AC-5 |
| Already-paid order redirects to success | AC-6 |
| Amount taken from DB (not browser) | AC-7 |
| Logged-out user redirected to login | AC-8 |
| Secret key not in response HTML | AC-9 |

---

## Files Changed / Created

| File | Action |
|------|--------|
| `requirements.txt` | Add `razorpay>=1.4.1` |
| `db.py` | `migrate_db()` adds 2 columns; add `get_order_by_id()`, `get_order_items()` |
| `payment.py` | New blueprint: 3 routes + `_rz_client()` helper |
| `app.py` | Register payment blueprint |
| `templates/payment/pay.html` | New: payment page with Razorpay widget |
| `templates/payment/success.html` | New: order confirmation page |
| `.env` | Developer adds `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` (never committed) |
| `test_payment.py` | New: acceptance-criteria tests |

---

## Verification

1. `python -m pip install -r requirements.txt` — installs razorpay package.
2. Add Razorpay test keys to `.env`.
3. `python app.py` — server starts, `migrate_db()` adds `payment_id` / `payment_order_id` columns.
4. Log in → add items to cart → checkout → redirected to `/payment/<order_id>`.
5. Click **Pay Now** → Razorpay modal opens with correct amount.
6. Use Razorpay test card `4111 1111 1111 1111` (any future expiry, any CVV) → payment succeeds.
7. Redirected to `/order/<id>/success` showing paid status and order items.
8. Try visiting `/payment/<id>` again → redirected to success (no double-pay).
9. `python test_payment.py` — all 9 tests pass.
