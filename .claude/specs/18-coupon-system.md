# Spec 18 — Coupon / Discount Code System

> **Feature:** Admin coupon codes banaye (percentage ya fixed); customer checkout pe code enter kare; discount subtotal se kate; order mein record ho.
> **Branch:** `feature/coupon-system`
> **Builds on:** Spec 06 (checkout flow) + Spec 09 (admin dashboard). `calculate_totals()` aur `place_order()` mein changes honge.
> **⚠️ MONEY-TOUCHING:** Discount = paisa kam milna. Server-side re-validation zaroori — client-side trust bilkul nahi.

---

## ⚠️ 0. Confirm-before-implement (4 business decisions)

Defaults maine rakh diye hain — badalna ho to batao:

1. **Discount types:** Percentage (e.g. 10%) aur Fixed amount (e.g. ₹50) — dono supported. → **Default: haan, dono.**
2. **Per-user limit:** Ek user ek code ek baar hi use kar sakta hai? → **Default: nahi — global `max_uses` cap hi kaafi hai MVP ke liye. Per-user limit future mein.**
3. **Shipping pe discount:** Coupon sirf subtotal pe lagega, shipping fee pe nahi. → **Default: haan, sirf subtotal.**
4. **Ek order, ek coupon:** Ek order pe ek hi coupon allowed. → **Default: haan.**

---

## 1. Goal

Admin dashboard se coupon codes create aur manage ho sakein. Customer checkout pe code enter kare — validation server se ho, discount summary mein dikhe, order place hone par coupon `used_count` increment ho aur order record mein code save ho.

**In scope**
- Admin: coupon create, list, toggle active/inactive.
- Customer: checkout pe code enter → live validation → discount dikhna → order ke saath save hona.
- Validation rules: expiry, max_uses, min_order_amount, is_active.
- `orders` table mein `coupon_code` + `discount_amount` columns.

**NOT in scope**
- Per-user limit (1 use per email) → future feature.
- Product-specific / category-specific coupons → future.
- Auto-apply coupons (bina code ke) → future.
- Coupon stacking (multiple codes ek order pe) → future.
- Customer-facing coupon discovery page → future.

---

## 2. Data Model

### Naya table: `coupons` (`migrate_db()` mein)

```sql
CREATE TABLE IF NOT EXISTS coupons (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    code             TEXT    NOT NULL UNIQUE,
    discount_type    TEXT    NOT NULL CHECK (discount_type IN ('percentage', 'fixed')),
    discount_value   REAL    NOT NULL,
    min_order_amount REAL    NOT NULL DEFAULT 0,
    max_uses         INTEGER NOT NULL DEFAULT 0,   -- 0 = unlimited
    used_count       INTEGER NOT NULL DEFAULT 0,
    expiry_date      TEXT,                          -- ISO date 'YYYY-MM-DD', NULL = no expiry
    is_active        INTEGER NOT NULL DEFAULT 1,    -- 1=active, 0=inactive
    created_at       TEXT    DEFAULT (datetime('now'))
);
```

### `orders` table — 2 naye columns (`migrate_db()` mein ALTER TABLE):

```python
('coupon_code',     "ALTER TABLE orders ADD COLUMN coupon_code TEXT"),
('discount_amount', "ALTER TABLE orders ADD COLUMN discount_amount REAL NOT NULL DEFAULT 0"),
```

### Validation rules (server-side, `coupons.py`):

| Rule | Error message |
|------|---------------|
| Code nahi mila | "Invalid coupon code." |
| `is_active = 0` | "This coupon is no longer active." |
| `expiry_date` past mein | "This coupon has expired." |
| `max_uses > 0` AND `used_count >= max_uses` | "This coupon has reached its usage limit." |
| `subtotal < min_order_amount` | "Minimum order of ₹{min_order_amount} required for this coupon." |

### Discount calculation:

```python
if coupon['discount_type'] == 'percentage':
    discount = round(subtotal * coupon['discount_value'] / 100, 2)
else:  # fixed
    discount = coupon['discount_value']

discount = min(discount, subtotal)  # subtotal se zyada discount nahi
new_subtotal = round(subtotal - discount, 2)
# shipping_fee re-calculate hoga new_subtotal pe (free shipping threshold check)
```

---

## 3. Backend API

### New blueprint: `coupons.py`

```
url_prefix = '/api'
```

**Endpoints:**

#### `POST /api/coupons/validate` — customer (login required)

Request body:
```json
{ "code": "KARVII10", "subtotal": 450.0 }
```

Response (success):
```json
{
  "valid": true,
  "discount_type": "percentage",
  "discount_value": 10,
  "discount_amount": 45.0,
  "new_subtotal": 405.0,
  "new_shipping_fee": 40.0,
  "new_total": 445.0,
  "message": "Coupon applied! You save ₹45."
}
```

Response (error):
```json
{ "valid": false, "error": "This coupon has expired." }
```

Rules:
- `login_required` (guest cannot use coupons — prevents abuse)
- `code` uppercase strip karo before lookup
- `subtotal` client se aata hai lekin sirf validation ke liye — order place hone par server dobara calculate karega cart se

#### `GET /api/admin/coupons` — admin only

Returns all coupons list (latest first).

#### `POST /api/admin/coupons` — admin only

Request body:
```json
{
  "code": "DIWALI20",
  "discount_type": "percentage",
  "discount_value": 20,
  "min_order_amount": 300,
  "max_uses": 100,
  "expiry_date": "2026-11-15"
}
```

Validation:
- `code`: required, 3–20 chars, alphanumeric + hyphen only, auto-uppercase
- `discount_type`: must be `percentage` or `fixed`
- `discount_value`: > 0; if percentage then ≤ 100
- `min_order_amount`: ≥ 0
- `max_uses`: ≥ 0 (0 = unlimited)
- `expiry_date`: optional, must be future date if provided
- Duplicate code → 409 Conflict

#### `PATCH /api/admin/coupons/<int:coupon_id>/toggle` — admin only

Toggles `is_active` (1→0 or 0→1). Returns updated coupon.

### `checkout.py` changes:

`POST /api/checkout` request body mein optional `coupon_code` field add hoga:

```json
{
  "shipping_name": "...",
  "shipping_phone": "...",
  "shipping_address": "...",
  "coupon_code": "KARVII10"   ← optional
}
```

Server-side flow:
1. Cart items fetch karo
2. Subtotal calculate karo (existing `calculate_totals`)
3. Agar `coupon_code` present hai → coupon re-validate karo (same rules as validate endpoint)
4. `discount_amount` calculate karo
5. `place_order()` ko `coupon_code` + `discount_amount` pass karo
6. `place_order()` ke andar coupon `used_count` atomic increment karo

### `db.py` changes:

`calculate_totals(items, discount_amount=0.0)`:
```python
def calculate_totals(items, discount_amount=0.0):
    subtotal = round(sum(item['price'] * item['quantity'] for item in items), 2)
    discounted_subtotal = max(0.0, round(subtotal - discount_amount, 2))
    shipping_fee = 0.0 if discounted_subtotal >= 500 else SHIPPING_FEE
    total = round(discounted_subtotal + shipping_fee, 2)
    return {
        'subtotal': subtotal,
        'discount_amount': round(discount_amount, 2),
        'shipping_fee': shipping_fee,
        'total': total,
    }
```

`place_order(user_id, shipping_name, shipping_phone, shipping_address, coupon_code=None, discount_amount=0.0)`:
- `discount_amount` ke saath order INSERT karo
- `coupon_code` bhi INSERT karo
- Agar `coupon_code` present hai: `UPDATE coupons SET used_count = used_count + 1 WHERE code = ?` (same transaction mein — atomic)

---

## 4. Frontend Changes

### `frontend/src/api/coupons.js` (NEW)

```js
import client from './client'

export const validateCoupon = (code, subtotal) =>
  client.post('/coupons/validate', { code, subtotal })
```

### `frontend/src/pages/CheckoutPage.jsx` changes:

Coupon section (below cart summary, above "Place Order"):

```
[ Coupon Code Input ]  [ Apply ]
✅ "Coupon applied! You save ₹45." (green)  [ Remove ]
```

State additions:
```js
const [couponCode,    setCouponCode]    = useState('')
const [couponApplied, setCouponApplied] = useState(null)  // { code, discount_amount, message }
const [couponError,   setCouponError]   = useState(null)
const [couponBusy,    setCouponBusy]    = useState(false)
```

Order summary mein discount line:
```
Subtotal:           ₹450
Discount (KARVII10): −₹45
Shipping:           ₹40
─────────────────────────
Total:              ₹445
```

POST `/api/checkout` mein `coupon_code` bhi bhejo agar applied hai.

### `frontend/src/pages/admin/AdminCoupons.jsx` (NEW)

- List: table showing code, type, value, min_order, max_uses, used_count, expiry, status badge, Toggle button
- Create form: code, type (select), value, min_order, max_uses, expiry_date
- Flash messages (success/error)
- Uses `AdminSidebar` component with `active="coupons"`

### `frontend/src/components/AdminSidebar.jsx` changes:

Add coupons link to NAV array:
```js
{ to: '/admin/coupons', label: 'Coupons', key: 'coupons' },
```

### `frontend/src/App.jsx` changes:

```jsx
import AdminCoupons from './pages/admin/AdminCoupons'
// ...
<Route path="/admin/coupons" element={<AdminGuard><AdminCoupons /></AdminGuard>} />
```

### `frontend/src/api/admin.js` changes:

```js
export const getCoupons    = ()       => client.get('/admin/coupons')
export const createCoupon  = (data)   => client.post('/admin/coupons', data)
export const toggleCoupon  = (id)     => client.patch(`/admin/coupons/${id}/toggle`)
```

---

## 5. User Stories

- **Customer:** Main checkout pe "KARVII10" enter karun, discount turant dikhe, aur order confirm hone par discounted amount pay karun.
- **Customer:** Main coupon enter karun jo expired hai — clear error message mile, order block na ho.
- **Admin:** Main ek coupon "DIWALI20" banau — 20% off, min ₹300 order, 100 uses max, 15 Nov tak valid.
- **Admin:** Main ek coupon band karun (deactivate) bina delete kiye.
- **Admin:** Main dekh sakun ki kitne log ek specific coupon use kar chuke hain.

---

## 6. Acceptance Criteria (Given / When / Then)

**AC-1: Valid percentage coupon**
- Given: coupon `SAVE10` (10%, min ₹0, unlimited, active, not expired)
- When: customer `/coupons/validate` hit kare with `subtotal=500`
- Then: 200, `discount_amount=50.0`, `new_total=490.0` (500-50+40=490)

**AC-2: Valid fixed coupon**
- Given: coupon `FLAT50` (fixed ₹50, min ₹0, active)
- When: `subtotal=200`
- Then: 200, `discount_amount=50.0`, `new_subtotal=150.0`, `new_shipping_fee=40.0`, `new_total=190.0`

**AC-3: Free shipping re-calculation**
- Given: coupon `BIG100` (fixed ₹100, active)
- When: `subtotal=550` → after discount `new_subtotal=450` (< 500)
- Then: `new_shipping_fee=40.0` (shipping fee applicable — was free before coupon)

**AC-4: Discount cannot exceed subtotal**
- Given: coupon `MEGA500` (fixed ₹500, active)
- When: `subtotal=200`
- Then: `discount_amount=200.0` (capped at subtotal, not ₹500), `new_subtotal=0`, `new_total=40.0` (only shipping)

**AC-5: Invalid code**
- When: `code="FAKECODE"`
- Then: 200 with `valid=false`, `error="Invalid coupon code."`

**AC-6: Inactive coupon**
- Given: coupon `OLD10` with `is_active=0`
- Then: `valid=false`, `error="This coupon is no longer active."`

**AC-7: Expired coupon**
- Given: coupon with `expiry_date` = yesterday
- Then: `valid=false`, `error="This coupon has expired."`

**AC-8: Max uses reached**
- Given: coupon with `max_uses=5`, `used_count=5`
- Then: `valid=false`, `error="This coupon has reached its usage limit."`

**AC-9: Min order not met**
- Given: coupon with `min_order_amount=500`
- When: `subtotal=300`
- Then: `valid=false`, `error="Minimum order of ₹500 required for this coupon."`

**AC-10: used_count increments on order**
- Given: coupon `TEST10` with `used_count=2`
- When: customer valid order place kare with this coupon
- Then: DB mein `used_count=3`; order record mein `coupon_code="TEST10"`, `discount_amount=correct_value`

**AC-11: Server re-validates at order time**
- Given: customer ne coupon validate kiya (tab valid था), phir coupon deactivate hua, phir order place kiya
- When: POST `/api/checkout` with that coupon_code
- Then: 400 error "This coupon is no longer active." — order nahi bana

**AC-12: Guest cannot validate coupon**
- When: unauthenticated POST `/api/coupons/validate`
- Then: 401

**AC-13: Admin create coupon**
- When: admin POST `/api/admin/coupons` with valid data
- Then: 201, coupon DB mein save, `code` uppercase mein

**AC-14: Duplicate code rejected**
- When: admin same `code` dobara create kare
- Then: 409 Conflict

**AC-15: Percentage > 100 rejected**
- When: admin creates coupon with `discount_type=percentage`, `discount_value=150`
- Then: 400 validation error

**AC-16: Toggle coupon**
- Given: active coupon
- When: admin PATCH toggle
- Then: `is_active` flips; re-toggle → flips back

**AC-17: Non-admin cannot manage coupons**
- When: regular user GET/POST `/api/admin/coupons`
- Then: 403

**AC-18: Unauthenticated admin endpoint**
- When: no login, any admin coupon endpoint
- Then: 401

---

## 7. Security Requirements

- **Server-side re-validation at order time:** Client ne coupon validate karaya tha, phir checkout mein wahi code aaya — server dobara validate kare. Client-side `discount_amount` pe kabhi trust nahi karna.
- **Atomic `used_count` increment:** `UPDATE coupons SET used_count = used_count + 1` — same transaction as order INSERT. Race condition se bachne ke liye select-then-update nahi.
- **`login_required` on validate endpoint:** Guest coupon test nahi kar sakta (brute-force code guessing prevent kare).
- **Admin-only on admin endpoints:** `admin_required` from `utils.py`.
- **Input sanitization:** `code` field — alphanumeric + hyphen only, 3–20 chars max. Arbitrary strings DB mein nahi.
- **Expiry date validation:** Server-side `datetime.utcnow().date()` se compare; client date trust nahi.
- **No negative discount:** `discount = max(0, discount)` — negative discount_value create nahi ho sakta (server-side check).
- **`discount_amount` on order:** Always server-calculated — frontend se aaya hua `discount_amount` kabhi use nahi karna.

---

## 8. Definition of Done

- [ ] `coupons` table migration (idempotent)
- [ ] `orders` table — `coupon_code` + `discount_amount` columns migration
- [ ] `calculate_totals()` updated with `discount_amount` param (backward compatible)
- [ ] `place_order()` updated with coupon params + atomic `used_count` increment
- [ ] `coupons.py` blueprint: validate + admin CRUD endpoints
- [ ] `app.py` mein blueprint registered
- [ ] `AdminSidebar.jsx` mein Coupons link add
- [ ] `AdminCoupons.jsx` page: create form + list + toggle
- [ ] `App.jsx` mein `/admin/coupons` route
- [ ] `admin.js` API module mein coupon functions
- [ ] `CheckoutPage.jsx` mein coupon input + discount line in summary
- [ ] `api/coupons.js` module
- [ ] Existing tests pass (test_auth, test_cart, test_checkout, test_order_management)
- [ ] `test_coupon_system.py` — 18 acceptance criteria cover
- [ ] Security review pass

---

## 9. File Change Summary

| File | Type | Change |
|------|------|--------|
| `db.py` | Edit | `coupons` table in `migrate_db()`; 2 columns on `orders`; update `calculate_totals()` + `place_order()` |
| `coupons.py` | NEW | Validate + admin list/create/toggle endpoints |
| `app.py` | Edit | Register coupons blueprint |
| `frontend/src/components/AdminSidebar.jsx` | Edit | Add Coupons nav link |
| `frontend/src/pages/admin/AdminCoupons.jsx` | NEW | Admin coupon management page |
| `frontend/src/App.jsx` | Edit | `/admin/coupons` route |
| `frontend/src/api/admin.js` | Edit | `getCoupons`, `createCoupon`, `toggleCoupon` |
| `frontend/src/api/coupons.js` | NEW | `validateCoupon` |
| `frontend/src/pages/CheckoutPage.jsx` | Edit | Coupon input + discount line in order summary |

Total: 3 new files, 6 edits.

---

## 10. Browser Test Script

> Backend `python app.py` + frontend `npm run dev` chalu.

1. **Admin: coupon banao** → `/admin/coupons` → "SAVE10" (10%, min ₹0, 5 uses) create karo → list mein dikhe.
2. **Admin: duplicate test** → same code dobara create karo → error dikhe.
3. **Checkout: coupon apply** → ek product cart mein daalo, checkout pe jao, "SAVE10" enter karo → discount dikhe, total updated dikhe.
4. **Checkout: invalid code** → "FAKECODE" enter karo → red error.
5. **Checkout: order place** → coupon apply karo, order confirm karo → My Orders mein coupon_code dikhe (order detail mein).
6. **used_count check** → admin panel mein SAVE10 ka used_count = 1 dikhe.
7. **Max uses test** → SAVE10 ko 5 baar use karo (5 alag orders/users simulate) → 6th attempt pe "Usage limit" error.
8. **Toggle test** → admin se coupon deactivate karo → checkout pe wahi code "no longer active" error de.
9. **Min order test** → ek coupon banao min ₹1000 ke saath → ₹300 order pe error aaye.
10. **Mobile (375px)** → coupon input + button mobile pe sahi dikhein.
