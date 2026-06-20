# Plan 18 — Coupon / Discount Code System

**Spec:** `.claude/specs/18-coupon-system.md`
**Branch:** `feature/coupon-system`
**Effort:** ~5-6 hours | **Risk:** HIGH — money-touching

## Phase 0 — Verified State

| Item | Status |
|------|--------|
| `db.py` `calculate_totals(items)` — no discount param | EXISTS, needs edit |
| `db.py` `place_order(...)` — no coupon params | EXISTS, needs edit |
| `checkout.py` Blueprint url_prefix='/api' | EXISTS, needs edit |
| `utils.py` exports `admin_required` | EXISTS |
| `app.py` blueprint registration pattern | EXISTS |
| `frontend/src/api/admin.js` | EXISTS, needs 3 exports |
| `frontend/src/components/AdminSidebar.jsx` NAV array | EXISTS, needs 1 entry |
| `frontend/src/pages/admin/AdminCoupons.jsx` | DOES NOT EXIST |
| `frontend/src/api/coupons.js` | DOES NOT EXIST |
| `coupons.py` backend blueprint | DOES NOT EXIST |
| `orders` table coupon_code / discount_amount columns | DO NOT EXIST |
| `coupons` table | DOES NOT EXIST |

## Implementation Order

1. `db.py` — migrate_db + calculate_totals + place_order
2. `coupons.py` — new Blueprint
3. `app.py` — register blueprint
4. `frontend/src/api/admin.js` — 3 new exports
5. `frontend/src/api/coupons.js` — new file
6. `frontend/src/index.css` — coupon UI classes
7. `frontend/src/components/AdminSidebar.jsx` — Coupons nav entry
8. `frontend/src/pages/admin/AdminCoupons.jsx` — new page
9. `frontend/src/App.jsx` — route + import
10. `frontend/src/pages/CheckoutPage.jsx` — coupon UI
11. `checkout.py` — coupon re-validation
12. `test_coupon_system.py` — 18 AC tests

## Security Checklist
- [ ] `POST /api/coupons/validate` is `@login_required`
- [ ] All admin coupon endpoints are `@admin_required`
- [ ] `checkout.py` re-validates coupon server-side on every order POST
- [ ] `discount_amount` always server-computed — never trusted from client
- [ ] Atomic `used_count` increment in same transaction as order INSERT
- [ ] `discount = min(discount, subtotal)` — never negative total
- [ ] `coupon_code` regex validated before DB lookup
- [ ] All SQL uses `?` placeholders
